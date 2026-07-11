# -*- coding: utf-8 -*-
"""
data_prep.py
------------
원본 데이터(data/raw)를 읽어서 분석하기 좋은 형태로 정리한 뒤
data/processed 폴더에 저장하는 스크립트.

1) Sleep_health_and_lifestyle_dataset.csv (Kaggle)
   -> 컬럼 이름을 다루기 쉬운 형태(snake_case)로 변경, 결측치 확인

2) 기상청 동네예보 원자료 4종 (기온 / 습도 / 하늘상태 / 강수확률)
   -> 원본은 "day, hour(발표시각), forecast(+N시간 후), value" 구조이며
      중간중간 "Start : YYYYMMDD" 같은 구분 줄이 섞여 있어 그대로 읽을 수 없음.
   -> 이 스크립트가 하는 일:
      - 구분 줄을 걸러내고 실제 데이터 줄만 추출
      - 발표시각(hour) + 몇 시간 후(forecast) 값을 이용해
        "실제로 그 값이 적용되는 시각(target_datetime)"을 계산
      - 같은 target_datetime 을 여러 발표(예보)가 예측한 경우,
        "가장 최근에 발표된 예보(=forecast 값이 가장 작은 것)"만 남김
        (사용자가 이 방식을 선택함: 실제 값과 가장 가깝기 때문)
      - 기온/습도/하늘상태/강수확률을 target_datetime 기준으로 합쳐서
        weather_clean.csv 로 저장
"""

import io
import re
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# 기상청 하늘상태 코드 (동네예보 공통 코드)
SKY_CODE_MAP = {1: "맑음", 3: "구름많음", 4: "흐림"}


def _extract_base_year_month(filename: str) -> str:
    """파일명에서 연월(YYYYMM)을 추출. 예: '..._20260706_20260710.csv' -> '202607'"""
    m = re.search(r"(\d{8})_(\d{8})", filename)
    if not m:
        raise ValueError(f"파일명에서 날짜를 찾을 수 없습니다: {filename}")
    return m.group(1)[:6]  # YYYYMM


def parse_forecast_file(path: Path, value_name: str) -> pd.DataFrame:
    """기상청 동네예보 원자료 1개 파일을 읽어서
    target_datetime, value_name 두 컬럼을 가진 DataFrame으로 변환.
    같은 target_datetime 에 여러 예보가 있으면 forecast(리드타임)가
    가장 작은 것 = 가장 최근에 발표된 예보만 남긴다.
    """
    year_month = _extract_base_year_month(path.name)

    # "Start : ..." 로 시작하는 구분 줄과 "format:" 헤더 줄은 제외하고
    # 실제 데이터 줄(day,hour,forecast,value)만 모은다.
    data_lines = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "Start" in line or "format" in line:
                continue
            data_lines.append(line)

    df = pd.read_csv(
        io.StringIO("\n".join(data_lines)),
        header=None,
        names=["day", "base_hour", "forecast", "value"],
    )
    df = df.dropna(subset=["day", "base_hour", "forecast", "value"])

    # 타입 정리
    df["day"] = df["day"].astype(int)
    df["base_hour"] = df["base_hour"].astype(int)  # 예: 200 -> 02시, 2300 -> 23시
    df["forecast"] = df["forecast"].astype(int)  # +N 시간 후
    df["value"] = df["value"].astype(float)

    # 발표 시각(base_datetime) 계산
    df["base_datetime"] = pd.to_datetime(
        year_month + df["day"].astype(str).str.zfill(2)
        + (df["base_hour"] // 100).astype(str).str.zfill(2)
        + "00",
        format="%Y%m%d%H%M",
    )

    # 실제 값이 적용되는 시각 = 발표시각 + forecast(몇 시간 후)
    df["target_datetime"] = df["base_datetime"] + pd.to_timedelta(df["forecast"], unit="h")

    # 같은 target_datetime을 여러 예보가 예측 -> forecast(리드타임)가 가장 작은 것,
    # 즉 가장 최근에 발표된 예보만 채택
    df = df.sort_values("forecast").drop_duplicates(subset="target_datetime", keep="first")
    df = df.sort_values("target_datetime").reset_index(drop=True)

    return df[["target_datetime", "value"]].rename(columns={"value": value_name})


def build_weather_clean() -> pd.DataFrame:
    temp = parse_forecast_file(RAW_DIR / "연안동_1시간기온_20260706_20260710.csv", "temp_c")
    humidity = parse_forecast_file(RAW_DIR / "연안동_습도_20260706_20260710.csv", "humidity_pct")
    rain = parse_forecast_file(RAW_DIR / "연안동_강수확률_20260706_20260710.csv", "rain_prob_pct")
    sky = parse_forecast_file(RAW_DIR / "연안동_하늘상태_20260706_20260710.csv", "sky_code")

    weather = temp.merge(humidity, on="target_datetime", how="outer")
    weather = weather.merge(rain, on="target_datetime", how="outer")
    weather = weather.merge(sky, on="target_datetime", how="outer")
    weather = weather.sort_values("target_datetime").reset_index(drop=True)

    weather["sky_code"] = weather["sky_code"].round().astype("Int64")
    weather["sky_desc"] = weather["sky_code"].map(SKY_CODE_MAP)

    weather["date"] = weather["target_datetime"].dt.date
    weather["hour"] = weather["target_datetime"].dt.hour

    # 실제 예보 기간(2026-07-06 ~ 2026-07-10)만 남긴다.
    start, end = pd.Timestamp("2026-07-06"), pd.Timestamp("2026-07-11")
    weather = weather[(weather["target_datetime"] >= start) & (weather["target_datetime"] < end)]

    weather = weather.reset_index(drop=True)
    return weather


def build_sleep_clean() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "Sleep_health_and_lifestyle_dataset.csv")

    rename_map = {
        "Person ID": "person_id",
        "Gender": "gender",
        "Age": "age",
        "Occupation": "occupation",
        "Sleep Duration": "sleep_hours",
        "Quality of Sleep": "sleep_quality",
        "Physical Activity Level": "activity_level",
        "Stress Level": "stress_level",
        "BMI Category": "bmi_category",
        "Blood Pressure": "blood_pressure",
        "Heart Rate": "heart_rate",
        "Daily Steps": "daily_steps",
        "Sleep Disorder": "sleep_disorder",
    }
    df = df.rename(columns=rename_map)
    df["sleep_disorder"] = df["sleep_disorder"].fillna("None")

    # 혈압을 수축기/이완기로 분리 (필요하면 EDA에서 활용)
    bp_split = df["blood_pressure"].str.split("/", expand=True)
    df["bp_systolic"] = pd.to_numeric(bp_split[0], errors="coerce")
    df["bp_diastolic"] = pd.to_numeric(bp_split[1], errors="coerce")

    return df


def main():
    print("[1/2] 수면/생활습관 데이터(Kaggle) 정제 중...")
    sleep_df = build_sleep_clean()
    sleep_out = PROCESSED_DIR / "sleep_clean.csv"
    sleep_df.to_csv(sleep_out, index=False, encoding="utf-8-sig")
    print(f"   -> 저장 완료: {sleep_out} ({len(sleep_df)}행)")

    print("[2/2] 날씨(공공데이터) 정제 중...")
    weather_df = build_weather_clean()
    weather_out = PROCESSED_DIR / "weather_clean.csv"
    weather_df.to_csv(weather_out, index=False, encoding="utf-8-sig")
    print(f"   -> 저장 완료: {weather_out} ({len(weather_df)}행)")

    print("\n완료! data/processed 폴더를 확인하세요.")


if __name__ == "__main__":
    main()

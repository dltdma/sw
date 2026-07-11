# -*- coding: utf-8 -*-
"""
analysis.py
-----------
정제된 데이터(data/processed)를 불러와서
- 기술통계 요약
- 분포 그래프
- 상관관계 히트맵
- 날씨 추세 그래프
를 만드는 함수 모음. app.py(Streamlit)에서 그대로 가져다 쓴다.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROCESSED_DIR = Path(__file__).parent / "data" / "processed"

# 한글 폰트가 없는 환경(리눅스 서버 등)에서도 깨지지 않도록 처리
plt.rcParams["axes.unicode_minus"] = False


# --------------------------------------------------------------------------
# 데이터 로딩
# --------------------------------------------------------------------------
def load_sleep_data() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "sleep_clean.csv")


def load_weather_data() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "weather_clean.csv", parse_dates=["target_datetime"])
    df["date"] = pd.to_datetime(df["date"])
    return df


# --------------------------------------------------------------------------
# 기술통계
# --------------------------------------------------------------------------
def sleep_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["sleep_hours", "sleep_quality", "activity_level", "stress_level", "daily_steps"]
    return df[cols].describe().T.round(2)


def weather_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(df["date"].dt.date)[["temp_c", "humidity_pct", "rain_prob_pct"]]
        .mean()
        .round(1)
        .rename_axis("date")
    )


# --------------------------------------------------------------------------
# 그래프: 분포
# --------------------------------------------------------------------------
def plot_distribution(df: pd.DataFrame, column: str, title: str, xlabel: str) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(df[column].dropna(), bins=10, kde=True, color="#6C63FF", ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("count")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------
# 그래프: 상관관계 히트맵
# --------------------------------------------------------------------------
def plot_correlation_heatmap(df: pd.DataFrame) -> plt.Figure:
    cols = ["sleep_hours", "sleep_quality", "activity_level", "stress_level", "daily_steps", "heart_rate"]
    corr = df[cols].corr().round(2)

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
    ax.set_title("생활습관 지표 간 상관관계")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------
# 그래프: 날씨 추세 (기온 / 습도)
# --------------------------------------------------------------------------
def plot_weather_trend(df: pd.DataFrame) -> plt.Figure:
    fig, ax1 = plt.subplots(figsize=(8, 4.2))

    ax1.plot(df["target_datetime"], df["temp_c"], color="#FF6B6B", label="기온(°C)")
    ax1.set_ylabel("기온 (°C)", color="#FF6B6B")
    ax1.tick_params(axis="y", labelcolor="#FF6B6B")

    ax2 = ax1.twinx()
    ax2.plot(df["target_datetime"], df["humidity_pct"], color="#4D96FF", label="습도(%)")
    ax2.set_ylabel("습도 (%)", color="#4D96FF")
    ax2.tick_params(axis="y", labelcolor="#4D96FF")

    ax1.set_title("연안동 5일간 기온·습도 추세")
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------
# 오늘(또는 최신 날짜) 날씨 요약값 -> recommendation.py에서 사용
# --------------------------------------------------------------------------
def get_latest_weather_snapshot(df: pd.DataFrame) -> dict:
    latest_date = df["date"].max()
    day_df = df[df["date"] == latest_date]
    return {
        "date": latest_date.strftime("%Y-%m-%d"),
        "avg_temp_c": round(day_df["temp_c"].mean(), 1),
        "avg_humidity_pct": round(day_df["humidity_pct"].mean(), 1),
        "avg_rain_prob_pct": round(day_df["rain_prob_pct"].mean(), 1),
        "main_sky": day_df["sky_desc"].mode().iloc[0] if not day_df["sky_desc"].mode().empty else "정보없음",
    }


if __name__ == "__main__":
    # 간단한 동작 확인용
    sleep_df = load_sleep_data()
    weather_df = load_weather_data()
    print(sleep_summary_stats(sleep_df))
    print(weather_daily_summary(weather_df))
    print(get_latest_weather_snapshot(weather_df))

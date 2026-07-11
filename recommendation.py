# -*- coding: utf-8 -*-
"""
recommendation.py
------------------
사용자가 입력한 생활습관 정보(+ 오늘의 날씨)를 바탕으로
피부 컨디션 위험도 점수, 원인, 관리 추천을 계산한다.

점수 산출 방식(간단한 룰 기반 가중합):
  각 항목(수면, 스트레스, 수분섭취, 공부시간, 날씨)마다
  0~100점의 "위험 점수"를 매기고, 가중치를 곱해 합산한다.
  -> 최종 점수가 높을수록 피부 컨디션이 나빠질 위험이 크다.

가중치는 Kaggle 데이터의 EDA 결과(수면-스트레스 상관관계 등)를
참고해서 "수면 부족"과 "스트레스"의 비중을 조금 더 높게 잡았다.
"""

from dataclasses import dataclass, field


WEIGHTS = {
    "sleep": 0.30,
    "stress": 0.25,
    "water": 0.20,
    "study": 0.15,
    "weather": 0.10,
}


@dataclass
class RiskResult:
    score: int
    level: str          # "낮음" / "보통" / "높음"
    level_color: str     # streamlit 표시용 색상
    causes: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    sub_scores: dict = field(default_factory=dict)


def _sleep_risk(sleep_hours: float) -> tuple[float, str | None]:
    if sleep_hours >= 7:
        return 5, None
    elif sleep_hours >= 6:
        return 35, "수면 시간이 살짝 부족해요 (권장 7시간 이상)"
    elif sleep_hours >= 5:
        return 65, "수면 부족"
    else:
        return 95, "심각한 수면 부족"


def _stress_risk(stress_level: int) -> tuple[float, str | None]:
    # stress_level: 1(매우 낮음) ~ 10(매우 높음)
    score = stress_level * 10
    cause = None
    if stress_level >= 8:
        cause = "매우 높은 스트레스"
    elif stress_level >= 6:
        cause = "스트레스"
    return score, cause


def _water_risk(water_ml: int) -> tuple[float, str | None]:
    if water_ml >= 2000:
        return 5, None
    elif water_ml >= 1500:
        return 30, "물 섭취량이 조금 부족해요"
    elif water_ml >= 1000:
        return 60, "수분 부족"
    else:
        return 90, "심각한 수분 부족"


def _study_risk(study_hours: float) -> tuple[float, str | None]:
    if study_hours <= 4:
        return 5, None
    elif study_hours <= 8:
        return 30, None
    elif study_hours <= 12:
        return 60, "장시간 공부(화면/책상 앞 장시간 노출)"
    else:
        return 85, "매우 긴 공부 시간"


def _weather_risk(humidity_pct: float | None, temp_c: float | None, skin_type: str) -> tuple[float, str | None]:
    if humidity_pct is None or temp_c is None:
        return 0, None

    if humidity_pct < 40:
        cause = "낮은 습도로 인한 건조한 날씨"
        # 건성 피부는 더 큰 타격
        return (80 if skin_type == "건성" else 55), cause
    elif humidity_pct > 80 and temp_c >= 25:
        cause = "고온다습한 날씨(피지·트러블 위험)"
        return (75 if skin_type in ("지성", "복합성") else 45), cause
    else:
        return 10, None


def calculate_risk_score(
    sleep_hours: float,
    stress_level: int,
    water_ml: int,
    study_hours: float,
    skin_type: str,
    humidity_pct: float | None = None,
    temp_c: float | None = None,
) -> RiskResult:
    sleep_score, sleep_cause = _sleep_risk(sleep_hours)
    stress_score, stress_cause = _stress_risk(stress_level)
    water_score, water_cause = _water_risk(water_ml)
    study_score, study_cause = _study_risk(study_hours)
    weather_score, weather_cause = _weather_risk(humidity_pct, temp_c, skin_type)

    total = (
        sleep_score * WEIGHTS["sleep"]
        + stress_score * WEIGHTS["stress"]
        + water_score * WEIGHTS["water"]
        + study_score * WEIGHTS["study"]
        + weather_score * WEIGHTS["weather"]
    )
    total = round(min(max(total, 0), 100))

    if total >= 70:
        level, color = "높음", "#FF4B4B"
    elif total >= 40:
        level, color = "보통", "#FFA24B"
    else:
        level, color = "낮음", "#4CAF50"

    causes = [c for c in (sleep_cause, stress_cause, water_cause, study_cause, weather_cause) if c]

    recommendations = _build_recommendations(
        skin_type=skin_type,
        sleep_hours=sleep_hours,
        stress_level=stress_level,
        water_ml=water_ml,
        study_hours=study_hours,
        humidity_pct=humidity_pct,
    )

    return RiskResult(
        score=total,
        level=level,
        level_color=color,
        causes=causes if causes else ["특별한 위험 요인이 없어요. 지금처럼 관리하면 좋아요!"],
        recommendations=recommendations,
        sub_scores={
            "수면": round(sleep_score),
            "스트레스": round(stress_score),
            "수분": round(water_score),
            "공부시간": round(study_score),
            "날씨": round(weather_score),
        },
    )


def _build_recommendations(
    skin_type: str,
    sleep_hours: float,
    stress_level: int,
    water_ml: int,
    study_hours: float,
    humidity_pct: float | None,
) -> list[str]:
    tips = []

    if sleep_hours < 7:
        tips.append("💤 하루 7시간 이상 수면을 목표로 해보세요. 잠들기 전 스마트폰 사용을 줄이면 도움이 돼요.")
    if stress_level >= 6:
        tips.append("🧘 짧은 스트레칭이나 5분 명상으로 스트레스를 관리해보세요. 스트레스 호르몬(코르티솔)은 피지 분비를 늘려요.")
    if water_ml < 1500:
        tips.append("🥤 하루 물 섭취량을 1.5~2L까지 늘려보세요. 책상 위에 물병을 두면 잊지 않고 마실 수 있어요.")
    if study_hours > 8:
        tips.append("📚 50분 공부 후 5~10분은 눈과 얼굴을 쉬게 해주세요. 장시간 앉아있으면 혈액순환이 저하돼요.")
    if humidity_pct is not None and humidity_pct < 40:
        tips.append("🧴 건조한 날씨예요. 세안 후 3분 이내에 보습제를 발라 수분을 잡아주세요.")
    if humidity_pct is not None and humidity_pct > 80:
        tips.append("🧼 고습도 환경에서는 피지·땀이 늘어나요. 하루 2번 이상 부드러운 클렌징을 해주세요.")

    # 피부타입별 기본 팁
    skin_tips = {
        "건성": "💧 세라마이드/히알루론산 성분의 고보습 크림을 사용해보세요.",
        "지성": "🍃 논코메도제닉(non-comedogenic) 표시가 있는 가벼운 제품을 사용해보세요.",
        "복합성": "🧴 T존은 가볍게, 볼은 촉촉하게 부위별로 다르게 관리해보세요.",
        "민감성": "🌿 무향/저자극 제품을 사용하고 새로운 제품은 패치 테스트 후 사용하세요.",
    }
    if skin_type in skin_tips:
        tips.append(skin_tips[skin_type])

    if not tips:
        tips.append("👍 지금의 생활습관을 잘 유지하고 있어요. 이 페이스를 유지해보세요!")

    return tips

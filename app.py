# -*- coding: utf-8 -*-
"""
app.py
------
Exam Skin Guardian - 시험기간 피부 컨디션 분석 및 맞춤 관리 추천 시스템
Streamlit 대시보드 메인 파일.

실행 방법:
    streamlit run app.py
"""

import plotly.graph_objects as go
import streamlit as st

import analysis
from photo_analysis import analyze_skin_photo
from recommendation import calculate_risk_score

st.set_page_config(page_title="Exam Skin Guardian", page_icon="🧴", layout="wide")


# --------------------------------------------------------------------------
# 데이터 로딩 (캐시해서 매번 다시 안 읽도록)
# --------------------------------------------------------------------------
@st.cache_data
def get_data():
    sleep_df = analysis.load_sleep_data()
    weather_df = analysis.load_weather_data()
    return sleep_df, weather_df


sleep_df, weather_df = get_data()
weather_snapshot = analysis.get_latest_weather_snapshot(weather_df)


# --------------------------------------------------------------------------
# 사이드바
# --------------------------------------------------------------------------
st.sidebar.title("🧴 Exam Skin Guardian")
st.sidebar.caption("시험기간 피부 컨디션 분석 & 맞춤 관리 추천")
page = st.sidebar.radio("메뉴", ["🏠 프로젝트 소개", "📊 데이터 분석", "🔍 내 피부 컨디션 진단"])

st.sidebar.divider()
st.sidebar.markdown("**오늘 날씨 (연안동 기준 최신 예보)**")
st.sidebar.metric("평균 기온", f"{weather_snapshot['avg_temp_c']} °C")
st.sidebar.metric("평균 습도", f"{weather_snapshot['avg_humidity_pct']} %")
st.sidebar.caption(f"하늘상태: {weather_snapshot['main_sky']} · 강수확률 {weather_snapshot['avg_rain_prob_pct']}%")


# --------------------------------------------------------------------------
# 1. 프로젝트 소개
# --------------------------------------------------------------------------
if page == "🏠 프로젝트 소개":
    st.title("🧴 Exam Skin Guardian")
    st.subheader("시험기간 피부 컨디션 분석 및 맞춤 관리 추천 시스템")

    st.markdown(
        """
        시험 기간에는 수면 부족, 스트레스 증가, 수분 섭취 부족, 장시간 공부 등으로
        피부 컨디션이 나빠지기 쉽지만, 정작 **"왜" 나빠지는지, "어떻게" 관리해야 하는지**
        객관적으로 알기 어렵습니다.

        이 프로그램은 두 가지 데이터를 함께 분석합니다.
        """
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📁 Kaggle 생활습관 데이터")
        st.markdown("- 수면시간 / 수면의 질\n- 스트레스 지수\n- 활동량 / 걸음수\n- 총 **374명** 데이터")
    with col2:
        st.markdown("#### 📁 기상청 공공데이터 (연안동)")
        st.markdown("- 기온 / 습도\n- 하늘상태 / 강수확률\n- 2026-07-06 ~ 2026-07-10 (5일)")

    st.divider()
    st.markdown("#### 🖥 프로그램 흐름")
    st.markdown(
        """
        1. 데이터 수집(Kaggle + 공공데이터) → 2. 데이터 정제(`data_prep.py`) →
        3. 탐색적 데이터 분석(`analysis.py`) → 4. 사용자 정보 입력 →
        5. 피부 컨디션 위험도 점수 계산(`recommendation.py`) → 6. 원인 분석 및 맞춤 추천 제공
        """
    )
    st.info("왼쪽 메뉴에서 **📊 데이터 분석**으로 EDA 결과를, **🔍 내 피부 컨디션 진단**에서 나만의 결과를 확인해보세요.")


# --------------------------------------------------------------------------
# 2. 데이터 분석 (EDA)
# --------------------------------------------------------------------------
elif page == "📊 데이터 분석":
    st.title("📊 데이터 분석 (EDA)")

    tab1, tab2 = st.tabs(["생활습관 데이터 (Kaggle)", "날씨 데이터 (공공데이터)"])

    with tab1:
        st.markdown("#### 기술통계")
        st.dataframe(analysis.sleep_summary_stats(sleep_df), use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.pyplot(analysis.plot_distribution(sleep_df, "sleep_hours", "수면시간 분포", "수면시간(시간)"))
        with c2:
            st.pyplot(analysis.plot_distribution(sleep_df, "stress_level", "스트레스 지수 분포", "스트레스 지수(1~10)"))

        st.markdown("#### 상관관계 히트맵")
        st.pyplot(analysis.plot_correlation_heatmap(sleep_df))
        st.caption(
            "수면시간·수면의질이 낮을수록, 스트레스가 높을수록 나쁜 컨디션과 연관되는 경향을 참고해 "
            "진단 로직의 가중치를 정했습니다."
        )

    with tab2:
        st.markdown("#### 일자별 평균")
        st.dataframe(analysis.weather_daily_summary(weather_df), use_container_width=True)

        st.markdown("#### 기온 · 습도 추세 (시간별)")
        st.pyplot(analysis.plot_weather_trend(weather_df))
        st.caption("기상청 동네예보 원자료 중 각 시각에 대해 가장 최근 발표된 예보값만 사용해 정리했습니다.")


# --------------------------------------------------------------------------
# 3. 내 피부 컨디션 진단
# --------------------------------------------------------------------------
else:
    st.title("🔍 내 피부 컨디션 진단")
    st.caption("아래 정보를 입력하면 오늘의 날씨 데이터와 함께 피부 컨디션 위험도를 계산해드려요.")

    with st.form("diagnosis_form"):
        c1, c2 = st.columns(2)
        with c1:
            sleep_hours = st.slider("😴 어젯밤 수면 시간 (시간)", 0.0, 12.0, 6.0, 0.5)
            stress_level = st.slider("😫 오늘 스트레스 지수 (1: 매우낮음 ~ 10: 매우높음)", 1, 10, 5)
            water_ml = st.slider("🥤 오늘 물 섭취량 (ml)", 0, 3000, 1000, 100)
        with c2:
            study_hours = st.slider("📚 오늘(어제) 공부 시간 (시간)", 0.0, 16.0, 6.0, 0.5)
            skin_type = st.selectbox("🧴 피부 타입", ["건성", "지성", "복합성", "민감성", "중성"])
            use_weather = st.checkbox("오늘 날씨 데이터 반영하기", value=True)

        st.divider()
        st.markdown("#### 📷 피부 사진 업로드 (선택)")
        st.caption(
            "사진의 밝기·붉은 기운을 간단히 분석해서 참고 지표로 보여드려요. "
            "실제 피부과적 진단이 아니며, 업로드한 사진은 저장하지 않고 그 자리에서만 분석 후 버려요."
        )
        photo_file = st.file_uploader("얼굴/피부 사진 선택 (jpg, png)", type=["jpg", "jpeg", "png"])

        submitted = st.form_submit_button("피부 컨디션 진단하기", use_container_width=True)

    if submitted:
        humidity = weather_snapshot["avg_humidity_pct"] if use_weather else None
        temp = weather_snapshot["avg_temp_c"] if use_weather else None

        result = calculate_risk_score(
            sleep_hours=sleep_hours,
            stress_level=stress_level,
            water_ml=water_ml,
            study_hours=study_hours,
            skin_type=skin_type,
            humidity_pct=humidity,
            temp_c=temp,
        )

        st.divider()
        col_gauge, col_info = st.columns([1, 1.3])

        with col_gauge:
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=result.score,
                    title={"text": f"피부 컨디션 위험도 ({result.level})"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": result.level_color},
                        "steps": [
                            {"range": [0, 40], "color": "#E8F5E9"},
                            {"range": [40, 70], "color": "#FFF3E0"},
                            {"range": [70, 100], "color": "#FFEBEE"},
                        ],
                    },
                )
            )
            fig.update_layout(height=320, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col_info:
            st.markdown("#### ✔ 원인 분석")
            for cause in result.causes:
                st.markdown(f"- {cause}")

            st.markdown("#### 💡 맞춤 관리 추천")
            for tip in result.recommendations:
                st.markdown(f"- {tip}")

        st.markdown("#### 항목별 세부 위험 점수")
        st.bar_chart(result.sub_scores)

        if photo_file is not None:
            st.divider()
            st.markdown("#### 📷 사진 분석 결과 (참고용)")
            photo_col1, photo_col2 = st.columns([1, 1.5])

            with photo_col1:
                st.image(photo_file, caption="업로드한 사진", use_container_width=True)

            with photo_col2:
                photo_result = analyze_skin_photo(photo_file.getvalue())
                st.metric("평균 밝기", f"{photo_result.brightness} / 255")
                st.caption(photo_result.brightness_desc)
                st.metric("붉은 기운(홍조) 정도", photo_result.redness_level)
                st.caption(photo_result.redness_note)
                st.info(
                    "⚠️ 이 분석은 사진의 평균 색상값만 이용한 간단한 참고 지표예요. "
                    "조명이나 화장 여부에 따라 결과가 달라질 수 있으니 참고용으로만 봐주세요."
                )

# 🧴 Exam Skin Guardian

**시험기간 피부 컨디션 분석 및 맞춤 관리 추천 시스템**

시험 기간엔 수면 부족·스트레스·수분 부족·장시간 공부 등으로 피부 컨디션이 나빠지기 쉽지만,
정작 "왜" 나빠지는지 "어떻게" 관리해야 하는지 알기 어렵습니다.
이 프로젝트는 **Kaggle 생활습관 데이터**와 **기상청 공공데이터(연안동)** 를 함께 분석해서,
사용자에게 피부 컨디션 위험도 점수 · 원인 · 맞춤 관리법을 알려주는 Streamlit 웹앱입니다.

---

## 📂 폴더 구조

```
ExamSkinGuardian/
├── app.py                # Streamlit 메인 화면 (실행 파일)
├── analysis.py            # EDA(기술통계·분포·상관관계·날씨 추세) 함수 모음
├── recommendation.py       # 위험도 점수 계산 + 원인/추천 로직
├── photo_analysis.py        # 업로드한 피부 사진의 밝기/홍조 간단 분석 (참고용)
├── data_prep.py            # 원본 데이터 -> 정제된 데이터 변환 스크립트
├── data/
│   ├── raw/                 # 원본 데이터 (Kaggle + 기상청 공공데이터)
│   └── processed/            # data_prep.py 실행 후 생성되는 정제 데이터
│       ├── sleep_clean.csv
│       └── weather_clean.csv
├── requirements.txt
└── README.md
```

## 📊 사용 데이터

| 데이터 | 출처 | 내용 |
|---|---|---|
| `Sleep_health_and_lifestyle_dataset.csv` | Kaggle | 수면시간, 수면의 질, 스트레스, 활동량, 걸음수 등 374명 |
| `연안동_1시간기온_...csv` | 기상청 공공데이터포털 (data.go.kr) | 시간별 기온 |
| `연안동_습도_...csv` | 기상청 공공데이터포털 | 시간별 습도 |
| `연안동_하늘상태_...csv` | 기상청 공공데이터포털 | 시간별 하늘상태(맑음/구름많음/흐림) |
| `연안동_강수확률_...csv` | 기상청 공공데이터포털 | 시간별 강수확률 |

> 기상청 원자료는 "동네예보" 형식이라, 하루에도 여러 번(02, 05, 08 ... 23시) 예보가 발표되고
> 같은 시각을 여러 번 예측합니다. `data_prep.py`에서 **가장 최근에 발표된 예보값**만 골라
> 시간별로 하나의 값만 남도록 정리합니다.

## 🖥 프로그램 흐름

```
① Kaggle 데이터 읽기 → ② 공공데이터 읽기 → ③ 데이터 정제(data_prep.py)
→ ④ 데이터 분석/시각화(analysis.py) → ⑤ 사용자 정보 입력
→ ⑥ 피부 컨디션 위험도 점수 계산(recommendation.py) → ⑦ 원인 분석 및 맞춤 추천
```

---

## 🚀 로컬에서 실행하기

```bash
# 1) 저장소 클론
git clone https://github.com/<본인계정>/ExamSkinGuardian.git
cd ExamSkinGuardian

# 2) 가상환경(선택) + 패키지 설치
pip install -r requirements.txt

# 3) 원본 데이터 정제 (최초 1회, 또는 data/raw 변경 시)
python data_prep.py

# 4) 앱 실행
streamlit run app.py
```

실행 후 터미널에 뜨는 `http://localhost:8501` 주소로 접속하면 됩니다.

---

## ☁️ GitHub 업로드 + Streamlit Cloud로 웹사이트처럼 배포하기

### 1) GitHub에 업로드

```bash
cd ExamSkinGuardian
git init
git add .
git commit -m "Exam Skin Guardian 프로젝트 최초 업로드"
git branch -M main
git remote add origin https://github.com/<본인계정>/ExamSkinGuardian.git
git push -u origin main
```

> `data/processed/` 는 `data_prep.py`로 다시 만들 수 있으므로 원본 raw 데이터와 함께 올려도 되고,
> raw 데이터만 올리고 processed는 `.gitignore`에 추가해도 됩니다. (지금은 둘 다 포함되어 있습니다.)

### 2) Streamlit Community Cloud로 배포 (무료)

1. https://share.streamlit.io 접속 후 GitHub 계정으로 로그인
2. **New app** 클릭
3. 방금 올린 저장소(`ExamSkinGuardian`) 선택
4. Main file path에 `app.py` 입력
5. **Deploy** 클릭

몇 분 후 `https://<앱이름>.streamlit.app` 같은 주소가 생기고, 이 링크를 그대로 공유하면
누구나 웹사이트처럼 접속해서 사용할 수 있습니다.

> ⚠️ 배포 전에 `data/processed/sleep_clean.csv`, `data/processed/weather_clean.csv`가
> 저장소에 포함되어 있는지 확인하세요. (Streamlit Cloud에서는 `data_prep.py`를 별도로
> 실행해주지 않으므로, 정제된 데이터 파일 자체를 커밋해야 합니다.)

---

## ⭐ 프로젝트 포인트

- 공공데이터포털 API/CSV 활용
- Kaggle 공개 데이터셋 활용
- Pandas 기반 데이터 정제 (결측치 처리, 형식이 지저분한 시계열 예보 데이터 파싱)
- EDA (평균/분포/상관관계 히트맵)
- 시각화 (Matplotlib/Seaborn + Plotly 게이지)
- Streamlit 대시보드 및 웹 배포

## 🛠 다음에 개선하면 좋은 것

- 여러 날짜에 대한 사용자 기록을 저장해 컨디션 변화 추이 보기
- 다른 지역 날씨 데이터 추가해서 지역별 비교
- 통계적 가설검정(t-검정 등)으로 "수면부족 그룹 vs 충분한 그룹"의 스트레스 차이 검증

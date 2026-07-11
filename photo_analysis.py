# -*- coding: utf-8 -*-
"""
photo_analysis.py
------------------
사용자가 업로드한 얼굴/피부 사진에서 "색상 정보"만 이용해
아주 간단한 참고 지표(밝기, 홍조 정도)를 계산한다.

⚠️ 주의:
- 이것은 실제 피부과적 진단이 아니라, 사진의 평균 RGB 값을 이용한
  "색상 기반 참고 지표"일 뿐이다. 조명, 카메라, 화장 여부에 따라
  결과가 크게 달라질 수 있다.
- 업로드된 사진은 서버/디스크에 저장하지 않고, 그 자리에서 분석 후 버린다.
"""

import io
from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass
class PhotoAnalysisResult:
    brightness: float          # 0~255, 평균 밝기
    brightness_desc: str
    redness_score: float        # R 채널이 G/B 평균보다 얼마나 높은지
    redness_level: str          # "낮음" / "보통" / "높음"
    redness_note: str


def analyze_skin_photo(image_bytes: bytes) -> PhotoAnalysisResult:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # 너무 큰 사진은 축소해서 평균 계산 속도를 높임 (분석 자체는 저해상도로도 충분)
    img_small = img.resize((150, 150))
    arr = np.asarray(img_small).astype(float)

    r_mean = arr[:, :, 0].mean()
    g_mean = arr[:, :, 1].mean()
    b_mean = arr[:, :, 2].mean()

    brightness = round((r_mean + g_mean + b_mean) / 3, 1)
    redness_score = round(r_mean - (g_mean + b_mean) / 2, 1)

    if brightness < 80:
        brightness_desc = "사진이 다소 어두워요. 밝은 곳에서 다시 찍으면 더 정확해요."
    elif brightness > 210:
        brightness_desc = "사진이 다소 밝아요 (조명/플래시 영향일 수 있어요)."
    else:
        brightness_desc = "밝기가 적당해서 분석하기 좋은 사진이에요."

    if redness_score > 15:
        redness_level = "높음"
        redness_note = "사진에서 붉은 기운이 두드러져요. 자극적인 성분(고농도 각질제거제 등)은 피하고 진정 성분(판테놀·병풀추출물 등) 위주로 케어해보세요."
    elif redness_score > 5:
        redness_level = "보통"
        redness_note = "약간의 붉은 기운이 보여요. 자외선차단제와 저자극 제품을 챙겨보세요."
    else:
        redness_level = "낮음"
        redness_note = "붉은 기운이 크게 두드러지지 않아요."

    return PhotoAnalysisResult(
        brightness=brightness,
        brightness_desc=brightness_desc,
        redness_score=redness_score,
        redness_level=redness_level,
        redness_note=redness_note,
    )

# Week 10: SAR Flood Detection & Sensor Fusion — ARIA v7.0

## 第十週：SAR 淹水偵測與多源融合 — ARIA v7.0（全天候決策引擎）

**Course**: 遙測與空間資訊之分析與應用 | Remote Sensing Analysis & Applications  
**Institution**: National Taiwan University (NTU)  
**Instructor**: Prof. Su Wen-Ray (蘇文瑞教授)  
**Case**: 2025 馬太鞍溪堰塞湖 — SAR 全天候監測  

---

## Overview

This notebook demonstrates the use of Synthetic Aperture Radar (SAR) for flood detection and multi-source sensor fusion using the ARIA v7.0 framework. The exercise focuses on detecting a landslide-dammed lake using Sentinel-1 SAR data and fusing it with Sentinel-2 optical imagery to create a confidence map for disaster response.

本實驗展示如何使用合成孔徑雷達（SAR）進行淹水偵測，並使用 ARIA v7.0 框架進行多源資料融合。練習重點在使用 Sentinel-1 SAR 資料偵測堰塞湖，並與 Sentinel-2 光學影像融合以建立防災決策信心圖。

---

## Lab Structure / 實驗結構

| Lab | Topic | Duration | 主題 |
|-----|-------|----------|------|
| **Lab 1** | SAR Flood Detection (STAC → Sentinel-1) | 35 min | 災前/災後 VV 對比 |
| **Lab 2** | ARIA v7.0 Sensor Fusion | 30 min | SAR + Optical 融合 |

---

## Key Concepts / 核心概念

### SAR vs Optical Remote Sensing

| Week | Sensor | STAC Collection | Key Difference |
|------|--------|-----------------|----------------|
| W8–W9 | Sentinel-2（光學）| `sentinel-2-l2a` | 受雲遮蔽 → 需 SCL 雲遮罩 |
| **W10** | **Sentinel-1（SAR）** | **`sentinel-1-rtc`** | **穿透雲層 → 不需要雲量過濾！** |

### SAR Backscatter in dB

SAR backscatter is expressed in decibels (dB) using the formula:
```
dB = 10 × log₁₀(σ⁰)
```

| Surface | Typical VV (dB) | Scattering | 中文 |
|---|---|---|---|
| Calm water | -25 to -20 | Specular reflection | 鏡面反射 |
| Rough water | -15 to -10 | Partial diffuse | 部分散射 |
| Bare soil | -10 to -5 | Surface scattering | 表面散射 |
| Forest | -8 to -3 | Volume scattering | 體散射 |
| Buildings | > 0 | Double-bounce | 雙次彈跳 |

### ARIA v7.0 Confidence Map

| Code | Label | Condition |
|------|-------|-----------|
| 3 | High Confidence | SAR ✓ + NDWI ✓ |
| 2 | SAR Only (Cloudy) | SAR ✓ + Cloud ✓ |
| 1 | Optical Only | NDWI ✓ + SAR ✗ |
| 0 | No Detection | Both ✗ |

---

## Requirements / 需求

### Python Environment

This notebook requires a Python virtual environment with the following packages:

```bash
# Create virtual environment
python -m venv remo_env
source remo_env/bin/activate  # On macOS/Linux
# or
remo_env\Scripts\activate  # On Windows

# Install required packages
pip install rasterio rioxarray pystac_client stackstac scikit-learn matplotlib numpy pandas scipy
```

### Data Sources

- **Sentinel-1 RTC**: Accessed via Planetary Computer STAC API
- **Sentinel-2 L2A**: Accessed via Planetary Computer STAC API
- **Copernicus DEM GLO-30**: Accessed via Planetary Computer STAC API

No local file downloads required — all data is streamed via cloud-native COGs.

---

## Usage / 使用方法

### 1. Environment Setup

Activate your virtual environment and launch Jupyter:

```bash
source remo_env/bin/activate
jupyter notebook Week10-Student.ipynb
```

### 2. Run the Notebook

Execute cells sequentially from top to bottom. The notebook is divided into:

- **Cell [S1]**: Environment + STAC Setup
- **Cell [S2]**: Search Sentinel-1 RTC (orbit filtering)
- **Cell [S3]**: Stream SAR data
- **Cell [S4]**: Load & Convert to dB
- **Cell [S5]**: Visualize Pre vs Post SAR
- **Cell [S6]**: Speckle Filter + Threshold + Morphological Cleanup
- **Cell [S7]**: Lab 1 Visualization
- **Cell [S8]**: Search Sentinel-2 for Optical Comparison
- **Cell [S9]**: Build Optical + Cloud Masks
- **Cell [S9b]**: Optical vs SAR Comparison
- **Cell [S10]**: Sensor Fusion — Build 4-Class Confidence Map
- **Cell [S11]**: DEM Topographic Analysis
- **Cell [S12]**: Confidence Map + DEM Context
- **Cell [S13]**: ARIA v7.0 Summary Report
- **Classroom Challenge**: SAR Threshold Comparison

---

## Case Study: 馬太鞍溪堰塞湖

### Event Timeline / 事件時序

- 2025/7/18–19 薇帕颱風 → 上游崩塌形成堰塞湖
- 7/23 面積 4 ha → 8月擴大 → 9/21 達 80 ha → 9/23 潰決
- **本週任務：用 SAR 偵測潰決前堰塞湖的水體範圍**

### Study Area / 研究區域

```
LAKE_BBOX = [121.270, 23.685, 121.310, 23.715]
```

Located in eastern Taiwan, this area experienced a landslide dam formation following Typhoon Vipa, requiring continuous monitoring for flood risk assessment.

---

## Key Parameters / 關鍵參數

| Parameter | Value | Description |
|-----------|-------|-------------|
| `SAR_THRESHOLD` | -14 dB | 寬鬆門檻，搭配形態學後處理去除雜訊 |
| `THRESHOLD_NEW` | -18 dB | ARIA 文獻預設值（課堂挑戰用） |
| `NDWI_THRESHOLD` | 0.0 | 濁水降低閾值 |
| `MIN_WATER_PIXELS` | 50 px | 連通元件過濾最小面積 (0.5 ha) |
| `OUTPUT_DIR` | 'output' | 輸出圖片資料夾 |

---

## Output Files / 輸出檔案

The notebook generates the following visualization files in the `output/` directory:

1. `W10_sar_before_after.png` — SAR pre/post disaster comparison
2. `W10_L1_sar_flood.png` — Lab 1: SAR flood detection results
3. `W10_optical_vs_sar.png` — Optical vs SAR comparison
4. `W10_L2_confidence_map.png` — Lab 2: ARIA v7.0 confidence map

---

## Discussion Points / 討論重點

### 1. Cloud Penetration
SAR can detect the landslide-dammed lake during typhoon season when Sentinel-2 imagery may be completely cloud-covered.

### 2. Water Surface Detection
VV < threshold regions indicate specular reflection = water bodies.

### 3. Speckle Effect
Direct thresholding on unfiltered SAR produces numerous false water pixels. Median filtering (5×5) is essential before thresholding.

### 4. Area Underestimation
SAR side-looking geometry in valleys can underestimate water area due to foreshortening, layover, and radar shadow effects.

---

## Classroom Challenge / 課堂挑戰

Compare two SAR thresholds:
- **-14 dB** (寬鬆 + morphological cleanup)
- **-18 dB** (嚴格, ARIA 文獻預設值)

**Question**: Which strategy is more suitable for early disaster warning? Why?

**Answer**: 寬鬆門檻(-14) + morphological 清理更適合防災早期預警。原因：寬鬆門檻確保不漏掉潛在淹水區，morphological 清理可有效去除 speckle 雜訊。相較之下，嚴格門檻(-18)雖然精確度高，但可能低估淹水範圍，錯過早期預警時機。

---

## References / 參考文獻

- ARIA (Advanced Rapid Imaging and Analysis) Project, JPL/NASA
- Planetary Computer STAC API
- Sentinel-1 RTC Product Specification
- Copernicus DEM GLO-30 Documentation

---

## License / 授權

This educational material is for academic use in the NTU Remote Sensing Analysis & Applications course.

---

## Contact / 聯絡

**Instructor**: Prof. Su Wen-Ray (蘇文瑞教授)  
**Course**: 遙測與空間資訊之分析與應用 | Remote Sensing Analysis & Applications  
**Institution**: National Taiwan University (NTU)

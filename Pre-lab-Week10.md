# Week 10 Pre-Lab: SAR & Sensor Fusion — ARIA v7.0 Setup

**Course:** NTU Remote Sensing & Spatial Information Analysis (遙測與空間資訊之分析與應用)  
**Instructor:** Prof. Su Wen-Ray  
**Week:** 10 | **Theme:** All-Weather Monitoring & Sensor Fusion  
**Time Required:** ~20 minutes

---

## Objectives

By the end of this pre-lab, you will:
- Verify that your W8/W9 environment and results are still accessible
- Install SAR-specific Python packages (rasterio, rioxarray)
- Understand the fundamental physics of SAR (radar backscatter)
- Review the concept of sensor fusion and why it matters for disaster monitoring
- Prepare your W9 optical change detection outputs for fusion with SAR data

---

## Step 1: Verify Week 8/9 Environment

### 1a. Activate Your Virtual Environment

```bash
# Example for conda
conda activate remo_w8
# OR if using venv
source ~/remo_env/bin/activate
```

### 1b. Confirm Key Packages Are Available

```python
import pystac_client
import stackstac
import sklearn
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import rasterio

print("✓ pystac_client:", pystac_client.__version__)
print("✓ rasterio:", rasterio.__version__)
print("✓ All core dependencies loaded successfully")
```

If any import fails, install:

```bash
pip install pystac_client stackstac scikit-learn rasterio rioxarray
```

---

## Step 2: Install SAR-Specific Packages

This week we add `rasterio` and `rioxarray` for loading pre-processed SAR GeoTIFF files.

```bash
pip install rasterio rioxarray
```

**Verify installation:**

```python
import rasterio
import rioxarray
print("✓ rasterio:", rasterio.__version__)
print("✓ rioxarray ready for SAR GeoTIFF loading")
```

---

## Step 3: SAR Physics — Conceptual Review

### What Is SAR?

**SAR** (Synthetic Aperture Radar) is an **active** remote sensing system:
- The satellite **emits** microwave pulses and **measures** the returned signal (backscatter)
- Operates at microwave wavelengths (C-band ~5.6 cm for Sentinel-1)
- **Works through clouds, rain, and at night** — "all-weather, day-and-night"

### Key Backscatter Mechanisms

| Surface Type | Backscatter Mechanism | Signal Strength | Typical dB |
|---|---|---|---|
| **Calm water** | Specular reflection (mirror-like, energy bounces away) | Very low | < -20 dB |
| **Rough water / wetland** | Partial diffuse scattering | Low–Medium | -15 to -10 dB |
| **Bare soil / urban** | Surface scattering | Medium–High | -10 to -5 dB |
| **Forest / vegetation** | Volume scattering (multiple bounces inside canopy) | High | -8 to -3 dB |
| **Buildings (double-bounce)** | Corner reflector effect | Very high | > 0 dB |

### Why Is This Useful for Flood Detection?

During a flood:
- **Water appears very dark** in SAR imagery (low backscatter from specular reflection)
- **Surrounding land remains bright** (high backscatter from vegetation/soil)
- Simple threshold: **VV < -18 dB → Water**（ARIA 文獻預設值，課堂會依場景調整）

This complements optical remote sensing, which **cannot see through clouds** during typhoons.

> **Note:** -18 dB 是全球通用的預設閾值，但最佳值因場景而異。
> 課堂案例（堰塞湖泥沙水）會使用不同閾值 + 形態學後處理（morphological post-processing）。

---

## Step 4: SAR vs. Optical — Comparison Table

Complete this table from memory before class:

| Feature | Optical (Sentinel-2) | SAR (Sentinel-1) |
|---|---|---|
| Energy source | Sun (passive) | Satellite transmitter (active) |
| Wavelength | Visible + NIR + SWIR (0.4–2.2 μm) | Microwave C-band (~5.6 cm) |
| Cloud penetration | ❌ Cannot see through clouds | ✅ _____ |
| Night operation | ❌ Needs sunlight | ✅ _____ |
| Water detection method | NDWI = (Green − NIR)/(Green + NIR) | Backscatter threshold: VV < _____ dB |
| Vegetation detection | NDVI = (NIR − Red)/(NIR + Red) | Volume scattering (high backscatter) |
| Spatial resolution | 10 m (B2–B4, B8) | 10 m (IW GRD) |
| Revisit time | 5 days (2-satellite constellation) | 6 days (2-satellite constellation) |

**Answers:** Cloud penetration = Yes; Night = Yes; Water threshold ≈ -18 dB（ARIA 預設值，課堂會依案例調整）

---

## Step 5: Understand the Data You Will Use

### 課堂 Demo/Lab：STAC API 即時串流

延續 W8–W9 的工作流，本週直接從 **Microsoft Planetary Computer** 串流 Sentinel-1 RTC 資料：

| 步驟 | 說明 | 誰做？ |
|---|---|---|
| STAC 搜尋 `sentinel-1-rtc` | `pystac_client` → `planetary_computer` | 🔧 你（課堂 Lab） |
| 串流讀取 VV/VH band | `stackstac.stack()` → `xarray` | 🔧 你（課堂 Lab） |
| Linear → dB 轉換 | `10 * np.log10(value)` | 🔧 你（課堂 Lab） |
| Speckle filtering | `scipy.ndimage.median_filter(size=5)` | 🔧 你（課堂 Lab） |

**Sentinel-1 RTC** = Radiometrically Terrain Corrected（已由 Planetary Computer 預處理完成：輻射校正 + 地形校正）。你只需要做 dB 轉換和 speckle filtering。

> **與 W8 的差異：**
> - collection 從 `sentinel-2-l2a` 改成 `sentinel-1-rtc`
> - assets 從 `['B02','B03','B04','B08']` 改成 `['vv']` 或 `['vh']`
> - 不需要除以 10000，也**不需要雲量過濾**！

### 作業：預處理 GeoTIFF

作業用的是另一個案例（花蓮鳳凰颱風），會提供預處理好的 `S1_Hualien_dB.tif`。

SAR 預處理流程（了解即可，作業已做好）：

| Processing Step | Tool |
|---|---|
| Download raw GRD | ASF Data Search / Copernicus DataSpace |
| Apply orbit file + Thermal noise removal | SNAP / ASF HyP3 |
| Radiometric calibration (σ⁰) | SNAP / ASF HyP3 |
| Terrain correction (Range-Doppler) | SNAP / ASF HyP3 |
| Convert to dB | 10 × log₁₀(σ⁰) |

---

## Step 6: 課前準備

### 課堂 Lab

課堂的 Sensor Fusion Lab 會在 notebook 內直接從 STAC 載入 Sentinel-2 光學資料（同 W8–W9 的 `stream_cube()` 模式），**不需要事先準備 W9 輸出檔案**。

### 作業

作業的 Sensor Fusion 需要用到你的 W9 光學結果：

| Item | File/Variable | Status |
|---|---|---|
| Optical water mask | Binary mask from NDWI thresholding | ☐ Ready |
| Cloud mask | SCL-based cloud mask | ☐ Ready |

If you don't have these, re-run your W9 notebook before doing the homework.

---

## Step 7: Self-Test — dB Conversion

**Scenario:** A Sentinel-1 pixel has backscatter σ⁰ = 0.001 (linear scale).

**Calculate:**
1. Convert to dB: $\sigma^0_{dB} = 10 \times \log_{10}(0.001) = $ _____ dB
2. Is this pixel likely **water** or **land**?
3. If threshold is -18 dB, would this pixel be classified as water?

**Answers:**
- $10 \times \log_{10}(0.001) = 10 \times (-3) = -30$ dB
- This is very low backscatter → **water** (specular reflection)
- Yes, -30 dB < -18 dB → classified as water ✅

---

## Step 8: Reflection Questions (Optional)

1. **Why can't we just use SAR instead of optical?** What information does SAR miss that optical provides?
2. **Speckle noise:** SAR images look "grainy" compared to optical. Why? (Hint: coherent illumination → constructive/destructive interference)
3. **Sensor fusion logic:** If optical says "water" AND SAR says "water" → high confidence. What if they disagree? What could cause disagreement?

---

## Checklist Before Class

- [ ] Verified rasterio and rioxarray are installed
- [ ] Reviewed SAR backscatter mechanisms (specular, volume, double-bounce)
- [ ] Completed SAR vs. Optical comparison table
- [ ] Completed dB conversion self-test
- [ ] W9 optical outputs accessible（作業用；課堂 Lab 會從 STAC 即時載入）
- [ ] 了解課堂使用 STAC API 串流 Sentinel-1 RTC（延續 W8 工作流）
- [ ] Optional: reflected on sensor fusion logic

**You're ready for Week 10!**

---

*Note: If you encounter any environment issues, post on NTUCool or email Prof. Su before class.*

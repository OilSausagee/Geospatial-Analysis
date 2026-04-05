# Week 6 Pre-lab: Kriging + ML Environment Setup

> Please complete the following steps **before class** to ensure your environment is ready.
> Estimated time: 15–20 minutes

---

## Step 1: Install New Packages

```bash
# Activate your virtual environment first!
# macOS / Linux:
source gis-env/bin/activate
# Windows:
gis-env\Scripts\activate

# Install pykrige (Kriging), scikit-learn (ML), and supporting packages
pip install pykrige scipy scikit-learn matplotlib rasterio rasterstats
```

Verify installation:

```python
import pykrige
from pykrige.ok import OrdinaryKriging
import scipy
import sklearn
import rasterio
print(f"PyKrige version: {pykrige.__version__}")
print(f"SciPy version: {scipy.__version__}")
print(f"scikit-learn version: {sklearn.__version__}")
print("✅ All packages ready for Week 6!")
```

Quick ML test:

```python
from sklearn.ensemble import RandomForestRegressor
rf = RandomForestRegressor(n_estimators=10, random_state=42)
print("✅ RandomForestRegressor imported successfully!")
```

> **注意**：`pykrige` 依賴 `scipy` 和 `numpy`。`scikit-learn` 依賴 `numpy` 和 `scipy`。如果你已經有 Week 3-5 的環境，這些通常已經安裝了。

---

## Step 2: Review Week 5 ARIA v3.0 Outputs

Week 6 will build directly on your Week 5 results. Make sure you have:

1. **雨量站 GeoDataFrame**（from `parse_rainfall_json()`）— 含 station_name, lat, lon, rain_1hr
2. **ARIA v3.0 動態風險分級結果** — CRITICAL/URGENT/WARNING/SAFE
3. **花蓮縣+宜蘭縣鄉鎮界** — from TGOS

> **Why?** Week 5 treats rainfall as **discrete points** (station locations). Week 6 answers: "What about the 95% of land area with no station?" We'll compare **Kriging (statistical)** and **Random Forest (ML)** to fill those gaps — and see which one the Commander should trust.

---

## Step 3: Understand the Problem

Look at your Week 5 Folium map. Notice:

- 花蓮山區有大片**無站區域** — 那裡的降雨量是多少？
- HeatMap 只是視覺化的「熱度」，**不是真正的空間內插**
- 指揮官問：「秀林鄉山區的降雨量估計是多少？可信度如何？」

**Kriging** 是地統計學（Geostatistics）的核心方法，不只給你內插值，還告訴你**估計的不確定性（variance）**。

---

## Step 4: Quick Concept Preview

### What is Kriging?

Kriging is a **Best Linear Unbiased Estimator (BLUE)** that:

1. 分析已知點之間的**空間自相關**（Variogram）
2. 根據距離和方向給每個已知點**最佳權重**
3. 產出**內插值 + 變異數（不確定性）**

### Key Terms You'll See in Class

| 英文 | 中文 | 說明 |
|------|------|------|
| Variogram | 變異元/半變異元 | 描述空間自相關結構的函數 |
| Sill | 基台值 | 變異達到的最大值 |
| Range | 影響範圍 | 超過此距離，資料不再有空間相關性 |
| Nugget | 塊金效應 | 零距離時的變異（量測誤差 + 微尺度變異） |
| Ordinary Kriging | 普通克利金 | 最常用的 Kriging 類型（假設未知均值） |

### What is Random Forest?

Random Forest 是一種 **機器學習（Machine Learning）** 方法。核心想法很直覺：

1. 把每個測站的**座標 (easting, northing)** 當作輸入特徵
2. 把**降雨量**當作要預測的目標值
3. 用大量「決策樹」投票取平均，產出預測結果

換句話說：`f(座標) → 降雨量`

**Kriging vs Random Forest — 課堂會比較兩者的差異**：

| | Kriging | Random Forest |
|--|---------|---------------|
| 邏輯基礎 | 空間自相關（距離近的站值相似） | 資料模式辨識（從資料中學規則） |
| 不確定性 | ✅ 提供 Sigma Map（誤差地圖） | ❌ 無法原生提供 |
| 優勢 | 物理意義明確、有信心度 | 容易加入額外特徵（海拔、坡度） |

> **課堂會回答的核心問題**：「兩種方法在同一份資料上會給出多不一樣的答案？指揮官該信誰？」

---

## Step 5: (Optional) Google Colab Preparation

如果你的電腦 RAM < 8GB，建議在 Colab 上執行 Kriging：

```python
# Colab cell
!pip install pykrige scikit-learn rasterio rasterstats
```

上傳你的 Week 5 雨量站 GeoDataFrame（存成 GeoJSON 或 CSV with lat/lon/rain）。

---

## Troubleshooting

**Q: `pykrige` import fails?**
A: Try: `pip install --upgrade pykrige`. On some systems you may need: `pip install pykrige[plot]`

**Q: `scipy` version conflict?**
A: Ensure scipy >= 1.7. Try: `pip install --upgrade scipy`

**Q: What if my Week 5 notebook doesn't work yet?**
A: We'll provide a pre-made rainfall GeoDataFrame in class as fallback. Focus on getting `pykrige` installed.

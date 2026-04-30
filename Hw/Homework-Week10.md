# Week 10 Homework: ARIA v7.0 — The All-Weather Auditor

**Course:** NTU Remote Sensing & Spatial Information Analysis (遙測與空間資訊之分析與應用)  
**Instructor:** Prof. Su Wen-Ray  
**Assignment:** Week 10 Homework  
**Due Date:** See NTUCool (typically 1 week after class)  
**Case Study:** 花蓮馬太鞍溪流域 — 2025 鳳凰颱風後淹水與堰塞湖偵測

---

## Overview

This week you build ARIA v7.0 — the **All-Weather Auditor** — by integrating SAR radar data with optical change detection. The key innovation is **cloud-piercing capability**: when optical satellites are blinded by clouds during a typhoon, SAR provides ground truth through the white wall.

**工作流延續 W8–W9：** 使用 Planetary Computer STAC API 串流 Sentinel-1 RTC 和 Sentinel-2 資料，完全不需要下載檔案。

**Scenario:** 2025 年 11 月鳳凰颱風登陸後，花蓮馬太鞍溪（見晴溪）上游崩塌形成堰塞湖（壩高約 40 公尺），溢流後造成下游萬榮鄉明利村、光復鄉、鳳林鎮大範圍淹水。颱風期間雲覆蓋嚴重，光學衛星幾乎看不到地面。你的 ARIA 系統必須利用 SAR 穿透雲層的能力，搭配光學資料進行多源融合，評估受災範圍。

**Key Deliverable:** A Jupyter notebook + markdown report that combines:
- STAC API 搜尋 + 串流 Sentinel-1 RTC 資料
- SAR flood extraction with speckle filtering + morphological cleanup
- Multi-source sensor fusion (optical NDWI + SAR)
- Confidence-graded flood map
- DEM 地形展示 + 適用性討論
- AI-generated strategic briefing
- Comparison with W9's optical-only results

---

## 研究區與時間設定

### BBOX（馬太鞍溪流域：光復、萬榮、鳳林三鄉鎮受災區）

```python
HUALIEN_BBOX = [121.2574, 23.6546, 121.4984, 23.7447]
```

> **BBOX 說明：** 左上 (23.7447, 121.2574)、右下 (23.6546, 121.4984)，涵蓋馬太鞍溪上游（萬榮鄉）至下游沖積扇（光復鄉、鳳林鎮），包含堰塞湖位置及溢流後淹水區域。

### 時間範圍

鳳凰颱風於 2025-11-12 登陸（恆春），花蓮萬榮鄉馬太鞍溪（見晴溪）溢流成災。搜尋範圍設定如下：

```python
# 災前基準期（颱風前 1 個月內的影像）
PRE_DATE_RANGE = '2025-10-01/2025-11-05'

# 災後觀測期（颱風登陸後 2-3 週）
POST_DATE_RANGE = '2025-11-12/2025-11-30'
```

> **Note:** 日期僅供參考。你需要用 STAC API 搜尋，從結果中選擇最適合的場景。
> 如果上述範圍沒有影像，可適度擴大搜尋範圍。

---

## Core Requirements (4 Tasks)

### Task 1: SAR All-Weather Flood Detection (25%)

**Procedure（延續課堂 STAC 工作流）：**

1. **STAC 搜尋 Sentinel-1 RTC：**
   ```python
   import pystac_client, planetary_computer as pc, stackstac
   
   catalog = pystac_client.Client.open(
       'https://planetarycomputer.microsoft.com/api/stac/v1',
       modifier=pc.sign_inplace,
   )
   search = catalog.search(
       collections=['sentinel-1-rtc'],
       bbox=HUALIEN_BBOX,
       datetime=POST_DATE_RANGE,
   )
   items = list(search.items())
   ```
   - 列出所有搜尋到的場景（日期、軌道方向）
   - ⚠ **災前災後必須用相同軌道方向**（ascending 或 descending）— 參考 Demo notebook D2 的自動偵測邏輯

2. **串流讀取 VV band + 轉換 dB：**
   ```python
   cube = stackstac.stack([pc.sign(item)], assets=['vv'], epsg=32651,
                          resolution=10, bounds_latlon=HUALIEN_BBOX)
   vv_linear = cube.squeeze('time').compute()
   vv_db = 10 * np.log10(vv_linear.values.squeeze().astype(np.float32))
   ```

3. **Speckle filtering：** `scipy.ndimage.median_filter(vv_db, size=5)`

4. **Threshold + Morphological cleanup：**
   - 先觀察 VV 直方圖，選擇合適的閾值（ARIA 預設 -18 dB，可依場景調整）
   - 套用閾值 → morphological opening → connected component filtering（參考 Demo D6）
   - 計算淹水面積（pixel size = 10m × 10m）

**Deliverable:**
- 2×2 subplot: (a) Raw SAR, (b) Filtered SAR, (c) Binary flood mask, (d) Overlay on base image
- Table: flooded area (km²), number of water pixels, mean backscatter in flood zone
- 直方圖：顯示你選擇的閾值位置
- Statement: "SAR detected X km² of flooding that optical sensors could not see due to cloud cover"

---

### Task 2: Sensor Fusion — Multi-Source Confidence Map (30%)

**Fusion Logic:**

Combine optical NDWI with SAR flood mask:

| Optical (NDWI > threshold) | SAR Water Mask | Cloud Masked? | Classification |
|---|---|---|---|
| ✅ Yes | ✅ Yes | No | **High Confidence** — dual evidence |
| ❌ No (cloudy) | ✅ Yes | Yes | **SAR Only (Cloudy)** — radar sees through clouds |
| ✅ Yes | ❌ No | No | **Optical Only** — needs manual review |
| ❌ No | ❌ No | — | **No Detection** |

**Note:** NDWI 閾值需依水質調整（清水 ~0.3，濁水 ~0.0）。請觀察你的場景決定。

**Procedure（全部用 STAC）：**

1. **搜尋 Sentinel-2：** 用 `catalog.search(collections=['sentinel-2-l2a'], ...)` 搜尋同時期光學影像
   - 列出搜尋結果（日期、雲量）
   - 選擇雲量最低的場景
   - 如果完全沒有光學影像（颱風季全雲覆蓋），說明這個情況並建立 100% 雲遮罩

2. **計算 NDWI + Cloud Mask：** 延續 W8–W9 的 `stream_cube()` 模式
   - NDWI = (Green - NIR) / (Green + NIR)
   - Cloud mask from SCL band（同 W9）

3. **Grid alignment：** 確保 SAR 和光學在同一網格
   - 使用 `scipy.ndimage.zoom` 或 `rioxarray.reproject_match()`
   - `assert sar_mask.shape == ndwi_mask.shape`

4. **Apply fusion logic：** 建立 4-class confidence map

**Deliverable:**
- Color-coded confidence map (4 classes with legend)
- Area statistics table for each confidence class
- Interpretation: "High confidence zones cover X km². SAR-only zones add Y km² of flood detection in cloudy areas."

---

### Task 3: Topographic Analysis — DEM & Slope Assessment (20%)

**Motivation:** SAR images suffer from geometric distortions on steep terrain (foreshortening, layover). These can create false "water" signals on mountain slopes.

**Procedure（用 STAC 載入 Copernicus DEM）：**

1. **載入 DEM：**
   ```python
   search = catalog.search(collections=['cop-dem-glo-30'], bbox=HUALIEN_BBOX)
   # 參考 Demo notebook D11 的 load_dem() 函式
   ```

2. **計算坡度：** `slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))`

3. **Apply topographic filter：**
   - Rule: slope > 25° → 不可能積水 → 判定為 False Positive
   - ⚠ **重要考量：** DEM 是否反映「現在」的地形？
     - 花蓮平原區域：Copernicus DEM 可直接使用
     - 如果是災後崩塌區：舊 DEM 的坡度不再正確（課堂案例示範了這個限制）

4. **Before/after comparison：** 地形校正前 vs 校正後

5. **討論（必答）：** 在你的案例中，DEM 是否適合用於地形校正？為什麼？如果 DEM 不適用，你會用什麼替代方法清理假水體？（提示：morphological opening, connected component filtering）

**Deliverable:**
- Side-by-side maps: fusion result before and after topographic correction
- Table: false positives removed by slope class (25–35°, 35–45°, >45°)
- 討論段落：DEM 適用性分析（2-3 句）

---

### Task 4: AI Strategic Briefing + ARIA v7.0 Report (25%)

**Part A: AI Strategic Briefing (15%)**

Feed your fusion results to an LLM (Gemini, ChatGPT, Claude, etc.) and request a strategic operational briefing:

1. Prepare a summary of key metrics:
   ```
   - High confidence flood area: X km²
   - SAR-only (cloudy) flood area: Y km²
   - False positives removed by topographic filter: Z km²
   - Cloud cover percentage: W%
   - SAR threshold: [your value] dB (explain why you chose this value)
   - NDWI threshold: [your value] (explain your choice)
   ```

2. Prompt the LLM:
   > "You are an emergency management advisor for Hualien County after Typhoon Fung-wong (November 2025). The Matai'an Creek barrier lake has overflowed, flooding Wanrong, Guangfu, and Fenglin townships.
   > Based on these ARIA v7.0 sensor fusion results, generate a strategic briefing that covers:
   > 1. Which areas require immediate evacuation?
   > 2. How should resources be allocated between high-confidence and SAR-only zones?
   > 3. What are the limitations of the current assessment?
   > 4. What additional data would improve confidence?"

3. **Document the exchange:** Copy exact prompt and response into your notebook
4. **Your reflection:** Add 3–4 sentences on what the LLM got right/wrong

**Part B: ARIA v7.0 Evolution Report (10%)**

Write a markdown section comparing W9 (optical-only) vs. W10 (fused) results:

| Metric | W9 (Optical Only) | W10 (Fused) | Improvement |
|---|---|---|---|
| Total detected flood area | X km² | Y km² | +Z km² |
| Cloud-covered area analyzed | 0 km² | W km² | — |
| False positives (pre-correction) | A | B | — |
| Confidence levels | 3-zone | 4-class | Finer granularity |

**Deliverable:**
- Markdown section "## AI Strategic Briefing" with prompt, response, and reflection
- Markdown section "## ARIA v7.0 vs. v6.0 Comparison" with comparison table

---

## Professional Standards

### 1. Environment Reproducibility

**`.env` file (do NOT commit to GitHub):**
```
# 研究區
BBOX_WEST=121.2574
BBOX_SOUTH=23.6546
BBOX_EAST=121.4984
BBOX_NORTH=23.7447

# 時間範圍
PRE_DATE_RANGE=2025-10-01/2025-11-05
POST_DATE_RANGE=2025-11-12/2025-11-30

# 閾值（依你的直方圖分析調整）
SAR_THRESHOLD=-18      # ARIA 預設；課堂堰塞湖用 -14 + morphological cleanup
NDWI_THRESHOLD=0.3     # 清水 ~0.3；濁水 ~0.0（依場景調整）
SLOPE_THRESHOLD=25     # 保守值；若 DEM 不適用可改用 morphological 替代
MIN_WATER_PIXELS=50    # connected component 最小面積（50 px = 0.5 ha）
```

### 2. Captain's Log (Markdown Cells)

Between each major code section, insert a markdown cell describing:
- What you're doing and why
- Expected output
- Any insights or surprises

### 3. Code Documentation

- Each function has a docstring with 1-line summary, parameters, returns
- Comments explain *why*, not just *what*
- Variable names are self-documenting

---

## Important: Academic Responsibility & Output Verification

> **⚠️ 警告：你必須對作業內容負責。**

SAR outputs are especially prone to false positives due to speckle noise and terrain distortion. Before you submit:

1. **Does your flood map make physical sense?** Water on mountaintops is wrong. If your flood area covers the entire study region, something is broken.
2. **Did you apply the Median Filter BEFORE thresholding?** Thresholding raw SAR produces garbage.
3. **Did you consider topographic effects?** 如果有合適的 DEM，用 slope 過濾；如果 DEM 不適用（如災後地形改變），改用 morphological cleaning。
4. **Can you explain the fusion logic?** If someone asks "Why is this zone High Confidence?", can you answer?

**不懂可以提問（NTUCool、office hours、課堂上都可以），但不要敷衍交差。**  
**Submitting unverified outputs will result in point deductions.**

---

## Grading Rubric (100%)

| Task | Component | Points | Criteria |
|------|-----------|--------|----------|
| **1. SAR Detection** | STAC search + scene selection | 8% | Sentinel-1 RTC loaded via STAC; orbit direction consistent |
| | Speckle filtering | 7% | Median filter applied; before/after comparison |
| | Threshold + morphological cleanup | 5% | Binary mask correct; area computed; histogram shown |
| | Visualization | 5% | 2×2 subplot; labeled; professional |
| **2. Sensor Fusion** | Fusion logic | 12% | 4-class confidence map correctly implemented |
| | Grid alignment | 8% | SAR and optical on same grid |
| | Area statistics | 5% | All classes quantified in km² |
| | Visualization | 5% | Color-coded map with legend |
| **3. Topographic Audit** | DEM loading via STAC | 5% | Copernicus DEM loaded; slope computed |
| | Filter application | 8% | Slope > 25° pixels removed; before/after shown |
| | DEM 適用性討論 | 7% | Thoughtful discussion of DEM limitations |
| **4. AI Briefing + Report** | LLM prompt & response | 8% | Thoughtful prompt; documented response |
| | Reflection | 7% | Your analysis of LLM's answer |
| | W9 vs W10 comparison | 10% | Table with quantitative comparison |
| **Professional Standards** | .env reproducibility | 3% | Parameters in .env; code reads from environment |
| | Captain's Log | 3% | ≥3 markdown cells explain reasoning |
| | Code quality | 2% | Well-commented; documented functions |
| | **Output verification** | 2% | Evidence of sanity checks in Captain's Log |

**Total: 100%**

---

## Bilingual Resources

### English Terms
- Synthetic Aperture Radar = 合成孔徑雷達
- Backscatter = 後向散射
- Specular Reflection = 鏡面反射
- Speckle = 斑點雜訊
- Sensor Fusion = 資料融合 / 感測器融合
- Confidence Map = 確信度圖
- Topographic Filter = 地形過濾
- Foreshortening = 前縮效應
- Layover = 疊置效應

### Chinese Concepts
- **鏡面反射** = 平滑水面將雷達能量反射走 → 低回波 → 暗色
- **體散射** = 植被冠層內多重散射 → 高回波 → 亮色
- **確信度分級** = 高（雙證據）/ 中（單SAR）/ 低（單光學）/ 無
- **地形審計** = 用坡度圖排除陡坡上的誤報

---

## Submission Checklist

- [ ] **All outputs verified**: Every metric, figure, and table checked for reasonableness
- [ ] Jupyter notebook named `Week10_ARIA_v70_[Your_Name].ipynb`
- [ ] `.env` file (with thresholds and parameters)
- [ ] All 4 tasks completed with deliverables
- [ ] STAC 搜尋結果列表（場景日期、軌道方向、雲量）
- [ ] 災前災後使用相同軌道方向
- [ ] Professional presentation: clear markdown, figures, tables
- [ ] Captain's Log cells throughout notebook
- [ ] Topographic analysis completed (DEM 適用性討論 included)
- [ ] AI briefing includes your own reflection
- [ ] W9 vs. W10 comparison table filled with real numbers
- [ ] Code is reproducible (runs without errors for TAs)
- [ ] Uploaded to NTUCool by due date (before 23:59)

---

## 常見問題

| 問題 | 解法 |
|------|------|
| STAC 搜尋沒有結果 | 擴大時間範圍；確認 BBOX 正確；檢查網路連線 |
| COG read failed | 重新執行 D1 取得新 SAS token；增加 safe_compute retry 次數 |
| SAR 和光學 shape 不同 | 使用 `scipy.ndimage.zoom` 或 `rioxarray.reproject_match()` 對齊 |
| 災前災後軌道方向不同 | 參考 Demo D2 的自動偵測邏輯，選擇共同軌道方向 |
| 光學完全被雲遮蔽 | 正常！建立 100% 雲遮罩，所有 SAR 偵測都歸類為 "SAR Only" |
| 淹水面積不合理 | 檢查：(1) 閾值是否合理 (2) 有無做 median filter (3) 有無做 morphological cleanup |

---

## Additional Resources

- **SAR fundamentals:** https://www.asf.alaska.edu/information/sar-information/
- **Sentinel-1 user guide:** https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-1-sar
- **Planetary Computer STAC Explorer:** https://planetarycomputer.microsoft.com/explore
- **Prof. Su's Week 9 & 10 Demo notebooks:** Available on NTUCool

---

## Contact & Support

- **Questions?** Post on NTUCool Discussion or attend office hours
- **STAC connection issues?** 確認教室/宿舍網路可連線至 planetarycomputer.microsoft.com
- **Environment errors?** Verify pystac_client/stackstac/planetary_computer in Pre-Lab

**The Captain's Final Thought:**
"A commander doesn't care if it's cloudy. He needs the truth. ARIA v7.0 delivers it."

---

*End of Homework Assignment — Week 10*

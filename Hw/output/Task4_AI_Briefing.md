# Task 4 — AI Strategic Briefing
## ARIA v7.0 — 2025 鳳凰颱風 馬太鞍溪堰塞湖溢流淹水評估

> 本檔由 Notebook cell `[S15]` 自動覆寫產出。下方為 prompt 與 reflection 模板；實際 LLM 回應將在執行 notebook 後寫入。

---

## 1. Prompt sent to LLM

```
You are an emergency management advisor for Hualien County after Typhoon Fung-wong (November 2025).
The Matai'an Creek barrier lake has overflowed, flooding Wanrong, Guangfu, and Fenglin townships.

Based on these ARIA v7.0 sensor fusion results:
{
  "pre_date": "2025-10-XX",
  "post_date": "2025-11-XX",
  "orbit_state": "descending",
  "sar_threshold_db": -16,
  "ndwi_threshold": 0.0,
  "slope_threshold_deg": 25,
  "flood_area_km2 (Task 1 SAR)": <runtime>,
  "high_confidence_km2": <runtime>,
  "sar_only_cloudy_km2": <runtime>,
  "optical_only_km2": <runtime>,
  "cloud_cover_pct": <runtime>,
  "false_positives_removed_km2": <runtime>,
  "townships_affected": ["萬榮鄉 Wanrong", "光復鄉 Guangfu", "鳳林鎮 Fenglin"]
}

Generate a strategic briefing (≤ 400 words) covering:
1. Which areas require immediate evacuation, and why?
2. How should resources be allocated between High-Confidence zones and SAR-Only (Cloudy) zones?
3. Key limitations of the current assessment (sensor, threshold, DEM).
4. What additional data or sensors would improve confidence in the next 24 h?
```

---

## 2. LLM Response (Gemini 2.5 Flash)

> *(Notebook 執行後會將 Gemini 回應自動覆寫至此處。若 API 不可用，可手動將 ChatGPT/Claude 回應貼入下方。)*

```
[paste LLM response here after running [S15]]
```

---

## 3. My Reflection — What did the LLM get right / wrong?

> *(請執行 notebook 後，閱讀真實 LLM 回應並填寫 3–4 句反思。下面是空白模板，建議至少回應這四個面向:)*

### 3.1 ✅ What the LLM got right
LLM 通常能正確抓到「High Confidence 區應優先疏散」、「SAR-Only 區因雲遮無法雙重驗證需保守處理」這類**邏輯推理**。它也能把面積數字轉換成可執行的優先順序（例如：先處理面積最大的鄉鎮）。

### 3.2 ⚠ Where the LLM was wrong or over-generalized
LLM 缺乏**地理空間直覺** — 它看不到河流走向、聚落位置、聯外道路，所以資源分配建議往往流於通則化（"prioritize the larger area"），而非真正的戰術建議。它也容易**過度推論**從未提供的細節（如人口、建築數），生成看似專業但缺乏依據的「估計」。

### 3.3 🔍 Critical limitations the LLM missed
LLM 不會主動指出 **Copernicus DEM 是災前地形**這個關鍵限制（除非我們在 prompt 中明寫）；它也容易忽略 **VV 單偏振**的限制（VH 對水體更敏感，但本作業未使用）。它也不會提到 **Sentinel-1 重訪週期 6–12 天**對應急監測的時效性問題。

### 3.4 🚀 How I would improve the next prompt
下次 prompt 應該:
1. 提供**地名與地貌脈絡**（馬太鞍溪上游、下游沖積扇、鄉鎮中心位置）
2. 明確要求引用**具體面積與信心等級**而非泛談
3. 要求 LLM 列出**三個資料盲點**而非空泛免責聲明
4. 限制 LLM **不要編造未提供的數字**（如人口、建築數）

---

## 4. Operational Takeaway

The LLM is best treated as a **draft-generator and counter-argument tester**, not a decision-maker. ARIA v7.0's value lies in the **quantitative sensor fusion** (Tasks 1–3); the LLM merely turns those numbers into prose. A field commander still needs to overlay this onto a road / settlement map before issuing evacuation orders.

# Week 10 Homework — ARIA v7.0 The All-Weather Auditor

**Course:** 遙測與空間資訊之分析與應用 (NTU)
**Instructor:** Prof. Su Wen-Ray
**Case Study:** 2025 鳳凰颱風後馬太鞍溪流域淹水與堰塞湖偵測（萬榮、光復、鳳林）

---

## 📁 檔案結構

```
Week-10/Hw/
├── Homework-Week10.md              # 作業說明（題目）
├── Week10_ARIA_v70_Homework.ipynb  # ⭐ 主交付物（Jupyter notebook）
├── .env                            # 參數設定（不要 commit）
├── .gitignore
├── requirements.txt
├── README.md                       # 本檔
└── output/
    ├── Task1_histogram.png         # SAR VV 直方圖（執行後產生）
    ├── Task1_sar_flood_2x2.png     # 2×2 SAR 偵測面板
    ├── Task2_confidence_map.png    # 4-class 融合信心圖
    ├── Task3_topo_correction.png   # 地形校正前後對比
    ├── Task4_AI_Briefing.md        # AI 戰略簡報 + 反思
    ├── ARIA_v7_Comparison.md       # W9 vs W10 比較報告
    └── aria_v7_metrics.json        # 結構化指標摘要
```

---

## ▶️ 執行方式

```bash
cd Week-10/Hw

# 1) 安裝依賴（沿用 W9 的 venv 也可以）
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2) 啟動 Jupyter
jupyter notebook Week10_ARIA_v70_Homework.ipynb

# 3) 由上而下執行所有 cells（Run All）
#    第一次執行會經由 Planetary Computer STAC API 串流資料，需要網路。
```

> **注意:** 所有資料皆**雲端串流**，不需要下載任何衛星檔案。第一次執行 [S3] / [S8] / [S11] 大約需要 3–8 分鐘（視網路速度）。

---

## 🎯 4 Tasks Overview

| Task | Topic | Points | Key deliverable |
|------|-------|--------|----------------|
| **1** | SAR All-Weather Flood Detection | 25% | `Task1_sar_flood_2x2.png` + 直方圖 |
| **2** | Sensor Fusion: 4-class confidence map | 30% | `Task2_confidence_map.png` + 面積表 |
| **3** | Topographic Audit (DEM slope filter) | 20% | `Task3_topo_correction.png` + DEM 適用性討論 |
| **4** | AI Briefing + ARIA v7.0 Evolution Report | 25% | `Task4_AI_Briefing.md` + `ARIA_v7_Comparison.md` |

---

## 🔑 Key Parameters（從 `.env` 讀取）

| Variable | Value | Reason |
|----------|------:|--------|
| `BBOX` | `[121.2574, 23.6546, 121.4984, 23.7447]` | 涵蓋萬榮（上游）→ 光復、鳳林（下游沖積扇） |
| `PRE_DATE_RANGE` | `2025-10-01/2025-11-05` | 颱風前 1 個月 |
| `POST_DATE_RANGE` | `2025-11-12/2025-11-30` | 鳳凰颱風登陸後 2-3 週 |
| `SAR_THRESHOLD` | `-16 dB` | 馬太鞍溪溢流為**濁水**（含泥沙）→ 較 ARIA 預設 -18 寬鬆 |
| `NDWI_THRESHOLD` | `0.0` | 同上，濁水降低閾值（清水通常用 0.3） |
| `SLOPE_THRESHOLD` | `25°` | 平原沖積扇有效；上游崩塌區改用 morphological 替代 |
| `MIN_WATER_PIXELS` | `50 px (0.5 ha)` | connected component 最小面積 |

---

## 🧭 Captain's Logs (notebook 內 ≥ 6 個 markdown cells)

1. 環境與設定
2. SAR 偵測思路
3. 為什麼要融合？
4. 地形稽核的兩難（DEM 適用性）
5. LLM 的角色
6. Final Sanity Checks

---

## ✅ Submission Checklist

- [ ] All notebook cells executed successfully (no errors)
- [ ] `.env` 所有閾值有調整 / 解釋
- [ ] STAC 搜尋結果列表已印出（場景日期、軌道方向、雲量）
- [ ] 災前/災後使用**相同軌道方向**（assertion 檢查通過）
- [ ] 4 個 PNG 都有產出
- [ ] `Task4_AI_Briefing.md` 已執行 LLM 並寫入 reflection
- [ ] `ARIA_v7_Comparison.md` 已填入真實 W9 / W10 數字
- [ ] DEM 適用性討論 ≥ 2-3 句（在 notebook Task 3 markdown）
- [ ] Captain's Log markdown cells ≥ 3 個
- [ ] 上傳 NTUCool（截止前 23:59）

---

## 🔍 Sanity Checks Built In

- ✅ Pre/Post orbit direction match (assertion)
- ✅ VV histogram visualization before threshold (avoid hidden bad threshold)
- ✅ Speckle filter applied **before** thresholding
- ✅ Connected component ≥ 0.5 ha (no isolated speckle blobs)
- ✅ Grid alignment assertion (`sar_water.shape == ndwi_mask.shape`)
- ✅ Slope-class breakdown (verify 25–35° band has few removals)

---

## 🆘 Troubleshooting

| Symptom | Fix |
|---------|------|
| `STAC search returns 0 items` | 擴大 date range；檢查網路；嘗試不同 bbox |
| `RasterioIOError on COG read` | `safe_compute()` 已內建重試；若仍失敗，重啟 kernel |
| `cloud_cover_pct == 100` | 正常！代表颱風期間全雲覆蓋；SAR 是唯一資料源 |
| `Pre/Post orbit mismatch` | 自動偵測會挑共同軌道；若都無，notebook 會 fallback 並警告 |
| `nan in dB array` | linear backscatter 可能有 0 值；已用 `np.where(np.isfinite, ..., nan)` 處理 |

---

## 📚 W8 → W9 → W10 連續性

| Week | Sensor | Innovation |
|------|--------|------------|
| W8 | Sentinel-2 | STAC streaming pipeline 建立 |
| W9 | Sentinel-2 | ARIA v6.0 — 雲遮罩 + 3-zone 信心 + ground truth Kappa |
| **W10** | **Sentinel-1 + Sentinel-2** | **ARIA v7.0 — SAR 穿雲 + 4-class fusion + DEM 稽核** |

**所有 weeks 共用同一個 STAC + stackstac + xarray pipeline，只換感測器。**

---

*"A commander doesn't care if it's cloudy. He needs the truth. ARIA v7.0 delivers it."*

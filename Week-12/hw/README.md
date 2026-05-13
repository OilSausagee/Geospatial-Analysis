# Week 12 Homework — ARIA v8.0 : The Classification Engine

**Course:** 遙測與空間資訊之分析與應用 (NTU)
**Instructor:** Prof. Su Wen-Ray
**Case Study:** 2024-04-03 花蓮地震（M7.4）後秀林 / 太魯閣土地覆蓋分類

---

## 📁 File structure

```
Week-12/hw/
├── Homework-Week12.md                 # 作業說明（題目）
├── Week12_ARIA_v80_Homework.ipynb     # ⭐ 主交付物（Jupyter notebook）
├── build_notebook.py                  # 產生 .ipynb 的 helper（可重生）
├── ARIA_v80_Report.md                 # 報告（abstract + per-task 討論）
├── .env                               # 參數設定（不要 commit）
├── .env.example                       # 範本（可 commit）
├── .gitignore
├── requirements.txt
├── README.md                          # 本檔
├── data/
│   └── 20240802新生崩塌地.kml          # SWCB 崩塌資料（Task 3 Part B）
└── output/
    ├── kmeans_classification.png      # Task 1 — K-means 分類圖
    ├── Task1_cluster_spectra.png      # Task 1 — cluster 平均光譜
    ├── Task1_cluster_means.csv        # Task 1 — cluster 平均反射率表
    ├── rf_classification.png          # Task 2 — Random Forest 分類圖
    ├── Task2_training_rois.png        # Task 2 — 訓練 ROI 位置
    ├── Task2_feature_importance.png   # Task 2 — 波段重要性
    ├── confusion_matrix.png           # Task 3a — 混淆矩陣
    ├── Task3_per_class_metrics.csv    # Task 3a — 每類別 metrics
    ├── swcb_overlay.png               # Task 3b — SWCB TP/FN/FP overlay
    ├── class_area_stats.csv           # Task 4 — 各類面積
    ├── Task4_AI_Briefing.md           # Task 4 — Gemini 報告 + 評論
    └── aria_v8_metrics.json           # 結構化 metrics（程式可讀）
```

---

## ▶️ 執行方式

```bash
cd Week-12/hw

# 1) 沿用全專案 .venv（W9 / W10 已建好）
source ../../.venv/bin/activate
pip install -r requirements.txt

# 2) 下載 SWCB KML 到 data/（已內建一份，若沒有可重下）
gdown 1VGe6ZY7QBCswqZEPRQaFWIJBylYK0qur -O data/20240802新生崩塌地.kml

# 3) 啟動 Jupyter
jupyter notebook Week12_ARIA_v80_Homework.ipynb

# 4) Run-All （第一次 STAC 串流 + RF 推論大約 3-8 分鐘）
```

如要重新產生 notebook 結構：

```bash
python build_notebook.py
```

---

## 🎯 4 Tasks Overview

| Task | Topic | Points | Key deliverable |
|------|-------|--------|----------------|
| **1** | K-means unsupervised | 15% | `kmeans_classification.png` + cluster 光譜表 |
| **2** | Random Forest supervised | 25% | `rf_classification.png` + feature importance |
| **3** | Accuracy + SWCB external validation | 35% | `confusion_matrix.png` + `swcb_overlay.png` + IoU |
| **4** | LLM commander briefing | 25% | `Task4_AI_Briefing.md` + 批判性評估 |

---

## 🔑 Key Parameters（從 `.env` 讀取）

| Variable | Value | Reason |
|----------|------:|--------|
| `BBOX` | `[121.40, 24.10, 121.80, 24.25]` | Xiulin/Taroko — 含中央山脈東緣 + 太平洋海岸 |
| `RESOLUTION` | `20 m` | 沿用 B11/B12 原生解析度，避免重採樣失真 |
| `KMEANS_K` | `5` | 對應 5 個目標土地覆蓋類別 |
| `RF_TREES` | `200` | 穩定 + 速度的折衷 |
| `RANDOM_STATE` | `42` | 確保可重現 |

---

## 🧭 STAC 漸進式搜尋策略

太魯閣 4–5 月正值梅雨季，雲量大。三階段：

| Phase | 時間範圍 | CC < |
|-------|----------|-----:|
| 1 | 2024-04-15 ~ 2024-05-31 | 20% |
| 2 | 2024-04-03 ~ 2024-08-31 | 30% |
| 3 | 2024-04-03 ~ 2024-12-31 | 50% |

找到任何一個 phase 有資料就停。最後挑「雲量最低」的場景。

---

## 📚 W8 → W9 → W10 → W12 連續性

| Week | Sensor / Method | Innovation |
|------|----------------|------------|
| W8 | Sentinel-2 視覺判讀 | STAC streaming pipeline |
| W9 | Sentinel-2 ΔNDVI + Kappa | 變遷信心三區 |
| W10 | Sentinel-1 + Sentinel-2 + DEM | SAR 穿雲 + 4-class fusion + 地形稽核 |
| **W12** | **Sentinel-2 + KMeans + Random Forest** | **多類分類 + 外部 SWCB 驗證** |

所有 weeks 共用相同 STAC + stackstac + xarray pipeline，
這週把「閾值法」升級成「分類器」。

---

## ✅ Submission Checklist

- [ ] 所有 notebook cells 成功執行（無錯誤）
- [ ] STAC 漸進搜尋結果有印出（場景日期、雲量）
- [ ] K-means cluster 光譜表 + 推測 label
- [ ] 5 個訓練類別都有 ≥ 50 像素
- [ ] Random Forest test acc 已計算
- [ ] Confusion matrix + classification report 已輸出
- [ ] SWCB 多邊形 clip 至 BBOX，IoU 已計算
- [ ] SWCB overlay (TP/FN/FP) 圖已產出
- [ ] AI briefing 已執行，並有批判性評論段
- [ ] `ARIA_v80_Report.md` 已填入真實數字
- [ ] 上傳 NTUCool

---

## 🆘 Troubleshooting

| Symptom | Fix |
|---------|------|
| STAC 0 results | 已內建三階段 fallback；若仍 0，擴大 BBOX 或日期 |
| `KML decode error` | 用 `gdown 1VGe6...` 重下，檔案大小 ~4.8 MB |
| K-means too slow | 已 sub-sample 至 200K 像素 fit、predict 全圖 |
| Gemini 連線失敗 | 檢查 `.env` 的 `GEMINI_API_KEY`；網路問題可重試 |
| 分類圖出現條紋 | SCL mask 已過濾雲；如殘留可加 morphological cleanup |

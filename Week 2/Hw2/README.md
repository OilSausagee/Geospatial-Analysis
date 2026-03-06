# Week 2: 避難收容處所空間分析

## 📋 專案概述

本專案進行台灣避難收容處所的空間品質審計與疊圖分析，結合空氣品質監測站資料，評估避難設施的空間分佈與環境品質關係。

## 🗂️ 專案結構

**完整分析結果請參考: `/aqi-analysis/` 目錄**

```
📂 aqi-analysis/
├── 📂 data/
│   ├── shelters_cleaned.csv              # 原始避難所資料
│   └── shelters_wgs84.csv              # CRS 轉換後資料
├── 📂 scripts/
│   ├── shelter_aqi_analysis.py           # 主要分析腳本
│   └── crs_conversion.py               # CRS 轉換工具
└── 📂 outputs/
    ├── shelter_aqi_analysis.csv           # 完整分析結果
    ├── shelter_aqi_risk_analysis.png      # 風險分析視覺化
    ├── shelter_aqi_risk_report.html      # 詳細分析報告
    ├── audit_report.md                   # 空間審計報告
    └── reflection.md                     # 深度反思報告
```

## 🎯 分析任務

### Task 1: 空間審計 (Spatial Audit)

#### 🗺️ CRS 混淆檢測
- **座標系統**: TWD97 (EPSG:3826)
- **偵測結果**: 確認資料使用 TWD97 投影座標系統
- **處理方式**: 實作 CRS 轉換功能確保分析準確性

#### 🚨 離群值偵測
- **總測站數**: 5,973 個避難所
- **有效座標**: 5,973 個 (100%)
- **離群值**: 95+ 個異常坐標（主要是金門、馬祖離島）
- **主要問題**: 離島地區座標位於台灣本島邊界外

#### 🏠 資料增強
- **室內避難所**: 5,711 個 (95.6%)
- **室外避難所**: 262 個 (4.4%)
- **分類方法**: 基於設施名稱關鍵字自動推斷
- **新增欄位**: `is_indoor`, `indoor_reason`

### Task 2: 空間疊圖分析 (Spatial Overlay)

#### 圖層整合
- **AQI 測站**: 12 個監測站，依嚴重程度分色顯示
- **避難所**: 5,973 個有效避難所，區分室內外圖標
- **互動功能**: 圖圖層控制、彈出視窗、統計面板

#### 鄰近性分析
- **平均距離**: 32,886.51 公尺
- **1公里內覆蓋**: 75 個測站 (89.3%)
- **5公里內覆蓋**: 82 個測站 (97.6%)

### Task 3: 最近測站分析與情境模擬

#### 演算法實作
- **距離計算**: Haversine 公式計算地理座標距離
- **最近測站**: 為每個避難所找出最近的 AQI 測站
- **風險標籤**: 基於 AQI 值和避難所類型分配風險等級

#### 情境模擬
- **觸發條件**: 全台空氣品質良好 (AQI < 50)
- **注入策略**: 將高雄測站 AQI 設為 150
- **驗證結果**: 成功產生 680 個高風險避難所標籤

## 📊 主要成果

### 風險分佈統計
- **🔴 High Risk**: 680 個避難所 (11.4%)
- **🟡 Warning**: 0 個避難所
- **🟢 Safe**: 5,293 個避難所 (88.6%)

### 技術亮點
- **CRS 轉換**: 自動檢測並轉換坐標系統
- **情境模擬**: 主動檢測並觸發分析邏輯驗證
- **複合風險**: 結合 AQI 值與避難所類型的雙重標準
- **完整分析**: 從審計到風險評估的完整流程

## 📁 輸出檔案

### 主要成果
- `shelter_aqi_analysis.csv`: 完整的風險分析結果
- `shelter_aqi_risk_analysis.png`: 風險分析視覺化
- `shelter_aqi_risk_report.html`: 詳細分析報告
- `audit_report.md`: 完整的審計報告
- `reflection.md`: 深度反思報告

### 資料檔案
- `shelters_cleaned.csv`: 原始避難所資料
- `shelters_wgs84.csv`: CRS 轉換後資料

## 🚀 執行方式

```bash
# 執行完整分析
cd aqi-analysis
python3 scripts/shelter_aqi_analysis.py
```

## 🔗 相關連結

- **GitHub**: https://github.com/OilSausagee/Geospatial-Analysis
- **分支**: `week2-shelter-analysis`
- **分析時間**: 2026年3月6日

---

*本專案結合空間資訊科學與災害管理，致力於提升台灣避難設施的空間規劃品質。*

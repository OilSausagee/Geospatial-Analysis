# 遙測與空間資訊之分析與應用 - Week 4

本專案包含 Week 4 課程的教材與練習，主要聚焦於數位高程模型 (DEM) 分析與地形特徵計算。

## 課程概述

Week 4 專注於進階地理空間分析技術，包括：

- **數位高程模型 (DEM) 處理與視覺化**
- **坡度 (Slope) 計算與分析**
- **坡向 (Aspect) 計算與視覺化**
- **坡度重分類與風險評估**
- **坡面陰影 (Hillshade) 生成**
- **地形特徵的三維視覺化**

## 專案結構

```
├── Week4_Colab_Test.ipynb    # 主要實作筆記本 - 完整的 DEM 分析流程
├── Week4-Student.ipynb       # 學生版本筆記本
├── README.md                 # 本檔案
├── .gitignore               # Git 忽略檔案設定
└── .venv/                   # Python 虛擬環境
```

## 主要實作內容

### 1. 數位高程模型載入與視覺化
- 載入花蓮地區 20m 解析度 DEM 資料
- 使用 `rioxarray` 處理地理空間資料
- 地形色彩圖視覺化高程分佈

### 2. 地形特徵計算
- **坡度計算**：使用梯度計算地形陡峭程度 (0°-85.45°)
- **坡向計算**：計算坡面朝向 (0°-360°)
- **數據處理**：處理 NoData 值 (-32767) 轉換為 NaN

### 3. 坡度重分類與風險評估
根據坡度值進行風險分級：
- **0-15°** → 低風險 (值為 1)
- **15-30°** → 中風險 (值為 2)  
- **>30°** → 高風險 (值為 3)

使用紅黍綠色彩地圖進行視覺化，便於決策分析。

### 4. 坡面陰影生成
- 設定太陽參數：高度角 45°，方位角 315°
- 計算地形光照效果，增強三維視覺效果
- 使用灰度圖呈現坡面陰影

## 技術規格

- **資料來源**：花蓮地區 20m DEM (`dem_20m_hualien.tif`)
- **座標系統**：WGS84 / UTM Zone 51N (EPSG:32651)
- **解析度**：20m × 20m
- **資料範圍**：7054 × 3997 像素
- **高程範圍**：處理後 0m - 3824m

## 環境需求

### Python 版本
- Python 3.8+

### 必要套件
```bash
pip install rioxarray rasterstats numpy matplotlib
```

### 主要套件功能
- **rioxarray**: 地理空間資料處理
- **numpy**: 數值計算與梯度運算
- **matplotlib**: 資料視覺化
- **rasterstats**: 空間統計分析

## 使用方法

### 1. 環境設定
```bash
# 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Mac/Linux

# 安裝依賴套件
pip install rioxarray rasterstats numpy matplotlib
```

### 2. 執行分析
```bash
# 啟動 Jupyter Notebook
jupyter notebook

# 開啟 Week4_Colab_Test.ipynb 按順序執行各個區塊
```

### 3. 分析流程
1. 載入 DEM 資料與環境設定
2. 視覺化原始高程資料
3. 計算坡度與坡向
4. 進行坡度重分類
5. 生成坡面陰影效果

## 重要檔案說明

### Week4_Colab_Test.ipynb
完整的實作筆記本，包含：
- Google Drive 掛接 (Colab 環境)
- DEM 資料載入與處理
- 地形特徵計算完整流程
- 視覺化與結果輸出

### 資料處理關鍵步驟
- NoData 值處理：`dem_data[dem_data == -32767] = np.nan`
- 梯度計算：`np.gradient(dem_data, y_res, x_res)`
- 坡度公式：`np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))`
- 坡向公式：`np.arctan2(dz_dy, -dz_dx)`

## 課程資訊

- **課程名稱**：遙測與空間資訊之分析與應用
- **週次**：第 4 週
- **主題**：數位高程模型分析與地形特徵計算
- **學期**：2026 春季

## 注意事項

- 大型 `.tif` 檔案已加入 `.gitignore` 避免提交至版本控制
- 所有計算均已處理 NoData 值，確保結果準確性
- 視覺化圖表均包含完整標籤與單位資訊

## 授權與使用

本專案僅供教育用途使用，請遵循課程規範與授權條款。

## 聯絡方式

如有關於 Week 4 課程內容的問題，請聯繫課程助教或授課教師。

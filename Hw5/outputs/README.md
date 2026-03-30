# ARIA v3.0: 全自動區域受災衝擊評估系統（動態監測版）

## 專案概述

ARIA v3.0 是一個整合即時雨量監測與避難所風險評估的動態系統，能在颱風期間提供即時的災害風險地圖。本系統針對 2025 年鳳凰颱風的極端情境進行壓力測試。

## 核心功能

### 🔄 模式切換器
- **LIVE 模式**: 呼叫 CWA O-A0002-001 API 獲取即時雨量
- **SIMULATION 模式**: 載入鳳凰颱風歷史快照 (`fungwong_202511.json`)
- **Fallback 機制**: API 失敗自動切換至本地快照

### 🌧️ 資料標準化
- `normalize_cwa_json()` 函數統一處理 CWA API 與 CoLife 歷史資料格式差異
- 自動過濾無效值 (-998)
- 支援不同座標格式 (TWD67/WGS84)

### 🗺️ 動態風險分級
- **CRITICAL**: 時雨量 > 80mm 影響範圍內的避難所
- **URGENT**: 時雨量 > 40mm 且地形風險為 HIGH
- **WARNING**: 時雨量 > 40mm 或地形風險為 HIGH  
- **SAFE**: 其餘

### 📊 互動視覺化
- Folium 多圖層地圖 (雨量站、避難所、HeatMap)
- 豐富的 Popup 資訊
- 圖層控制功能

## 檔案結構

```
Hw5/
├── .env                          # 環境變數設定
├── ARIA_v3.ipynb                 # 主要分析 Notebook
├── ARIA_v3_Fungwong.html         # 輸出的互動地圖
├── README.md                     # 本檔案
├── data/
│   ├── fungwong_202511.json      # 鳳凰颱風歷史快照
│   ├── terrain_risk_audit.json   # Week 3-4 地形風險審計
│   ├── 避難收容處所.csv          # 原始避難所資料
│   └── ...                       # 其他資料檔案
└── outputs/                      # 輸出檔案目錄
```

## 環境設定

### 必要套件
```bash
pip install pandas geopandas folium requests python-dotenv
```

### 環境變數 (.env)
```env
APP_MODE=SIMULATION
CWA_API_KEY=your-api-key-here
SIMULATION_DATA=data/fungwong_202511.json
TARGET_COUNTY=花蓮縣, 宜蘭縣
CRITICAL_RAINFALL_MM=80
URGENT_RAINFALL_MM=40
BUFFER_RADIUS_KM=5
```

## 使用方法

1. **環境設定**
   ```bash
   # 複製環境變數範本
   cp .env.example .env
   # 編輯 .env 檔案，設定 API Key 與參數
   ```

2. **執行分析**
   ```bash
   jupyter notebook ARIA_v3.ipynb
   # 依序執行所有 cells
   ```

3. **查看結果**
   - 開啟 `ARIA_v3_Fungwong.html` 查看互動地圖
   - 在 Jupyter Notebook 中查看統計結果

## AI 診斷日誌

### 🔧 解決的技術問題

#### 1. CWA API 與 CoLife 格式差異
**問題**: CWA Live API 回傳兩組座標 (TWD67, WGS84)，CoLife 歷史資料只有一組 WGS84，且數值型態不同 (字串 vs 數字)。

**解決方案**: 
- 實作 `normalize_cwa_json()` 函數自動偵測座標格式
- 統一轉換為數字型態，取 WGS84 座標
- 增加錯誤處理，跳過無效站點

#### 2. CRS 坐標系統對齊
**問題**: 雨量站 (EPSG:4326) 與避難所 (EPSG:3826) CRS 不同，導致 `sjoin()` 結果為空。

**解決方案**:
- 在空間疊合前將雨量站轉換為 EPSG:3826
- 加入 CRS 檢查斷言確保一致性
- Folium 視覺化時轉回 EPSG:4326

#### 3. Folium 座標順序錯誤
**問題**: Folium 需要 `[latitude, longitude]` 順序，但 GeoDataFrame 預設為 `[longitude, latitude]`。

**解決方案**:
- 在建立 Marker 時明確提取 `lat, lon = shelter.geometry.y, shelter.geometry.x`
- 確保所有 Folium 元素使用正確的座標順序

#### 4. -998 無效值處理
**問題**: CWA API 使用 -998 表示無資料，直接繪製會導致地圖異常。

**解決方案**:
- 在 `normalize_cwa_json()` 中過濾 -998 和負值
- HeatMap 只包含有效雨量站點

#### 5. Buffer 單位混淆
**問題**: EPSG:4326 下 buffer(5000) = 5000 度 ≈ 地球半圈，造成錯誤分析。

**解決方案**:
- 確保在 EPSG:3826 (TWD97) 下執行 buffer 操作
- 5km = 5000 公尺在正確坐標系統下

### 🎯 系統優化

#### 效能提升
- 使用 `gpd.sjoin()` 替代迴圈計算，大幅提升空間查詢效率
- 預先計算 buffer，避免重複幾何運算
- 批次處理 Folium 元素建立

#### 韌性設計
- API 呼叫加入 try/except 與 timeout
- 自動 fallback 至本地快照
- 完整的錯誤日誌記錄

#### 使用者體驗
- 豐富的 Popup 資訊顯示
- 直觀的顏色編碼系統
- 圖層控制讓使用者客製化顯示

## 數據洞察

### 鳳凰颱風情境分析
- **時雨量巔峰**: 蘇澳站 130.5mm
- **累積雨量**: 南澳站 1,062mm (多日總計)
- **影響範圍**: 5km buffer 內的避難所動態風險評估

### 風險分佈模式
- 地形風險與暴雨風險的疊加效應明顯
- 河川附近的高坡度避難所風險顯著提升
- 即時監測能及時識別新興風險點

## 未來改進方向

1. **預測功能**: 整合氣象預報資料
2. **歷史分析**: 時序動態變化視覺化
3. **AI 顧問**: Gemini SDK 整合提供指揮建議
4. **警報系統**: 自動化風險通知機制
5. **多災害整合**: 加入地震、洪水等其他災害風險

---

*"A monitoring system that works in the sun is a toy. A system that survives Typhoon Fung-wong is a tool."*

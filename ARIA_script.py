#!/usr/bin/env python
# coding: utf-8

# # Automated Regional Impact Auditor (ARIA)
# ## 河川洪災避難所風險評估
# 
# **Captain's Log**: 開始執行河川洪災避難所風險評估分析。本分析將結合水利署河川圖資與消防署避難收容所資料，建立多級警戒緩衝區並評估各行政區的避難所洪災風險與收容量缺口。

# In[ ]:


# 安裝必要套件
get_ipython().system('pip install geopandas folium mapclassify python-dotenv')


# In[ ]:


import geopandas as gpd
import pandas as pd
import numpy as np
import folium
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
import os
import json
from urllib.parse import quote
import warnings
warnings.filterwarnings('ignore')

# 載入環境變數
load_dotenv()

print("套件載入完成")


# ## 1. 資料載入與清理
# 
# **Captain's Log**: 載入水利署河川面資料、消防署避難收容所資料與國土測繪中心鄉鎮界資料。重點關注座標清理與CRS轉換。

# In[ ]:


# 1.1 載入水利署河川面資料
print("載入水利署河川面資料...")
rivers = gpd.read_file('https://gic.wra.gov.tw/Gis/gic/API/Google/DownLoad.aspx?fname=RIVERPOLY&filetype=SHP')
print(f"河川資料原始CRS: {rivers.crs}")
print(f"河川筆數: {len(rivers)}")

# 確保河川資料為EPSG:3826
if rivers.crs != 'EPSG:3826':
    rivers = rivers.to_crs('EPSG:3826')
    print(f"河川資料轉換為EPSG:3826")

print(f"河川資料範圍: {rivers.total_bounds}")


# In[ ]:


# 1.2 載入消防署避難收容所資料
print("\n載入消防署避難收容所資料...")

# 嘗試不同編碼
try:
    shelters_csv = pd.read_csv('避難收容處所.csv', encoding='utf-8')
except:
    shelters_csv = pd.read_csv('避難收容處所.csv', encoding='big5')

print(f"原始避難所資料筆數: {len(shelters_csv)}")
print(f"欄位: {list(shelters_csv.columns)}")
print(shelters_csv.head())


# In[ ]:


# 1.3 資料清理 - 移除無效座標
print("\n開始資料清理...")

# 檢查座標欄位名稱
print(f"CSV欄位: {list(shelters_csv.columns)}")

# 假設欄位名稱為 '經度' 和 '緯度'
lon_col = '經度'
lat_col = '緯度'

# 記錄清理前的筆數
original_count = len(shelters_csv)

# 移除座標為0或空值的記錄
shelters_clean = shelters_csv.dropna(subset=[lon_col, lat_col])
shelters_clean = shelters_clean[(shelters_clean[lon_col] != 0) & (shelters_clean[lat_col] != 0)]

# 移除超出台灣範圍的座標 (經度: 119-122, 緯度: 21-26)
shelters_clean = shelters_clean[
    (shelters_clean[lon_col] >= 119) & (shelters_clean[lon_col] <= 122) &
    (shelters_clean[lat_col] >= 21) & (shelters_clean[lat_col] <= 26)
]

cleaned_count = len(shelters_clean)
print(f"清理前筆數: {original_count}")
print(f"清理後筆數: {cleaned_count}")
print(f"移除無效記錄: {original_count - cleaned_count} 筆")


# In[ ]:


# 1.4 轉換為GeoDataFrame並設定CRS
print("\n轉換為GeoDataFrame...")

shelters = gpd.GeoDataFrame(
    shelters_clean,
    geometry=gpd.points_from_xy(shelters_clean[lon_col], shelters_clean[lat_col]),
    crs='EPSG:4326'
)

# 轉換至EPSG:3826以進行buffer分析
shelters = shelters.to_crs('EPSG:3826')
print(f"避難所資料CRS: {shelters.crs}")
print(f"避難所筆數: {len(shelters)}")

# 檢查收容人數欄位
capacity_col = '預計收容人數'
if capacity_col not in shelters.columns:
    print(f"警告: 找不到收容人數欄位 '{capacity_col}'")
    print(f"可用欄位: {list(shelters.columns)}")
else:
    print(f"收容人數欄位: {capacity_col}")
    print(f"收容人數統計:")
    print(shelters[capacity_col].describe())


# In[ ]:


# 1.5 載入鄉鎮市區界資料
print("\n載入鄉鎮市區界資料...")

url = 'https://www.tgos.tw/tgos/VirtualDir/Product/3fe61d4a-ca23-4f45-8aca-4a536f40f290/' + quote('鄉(鎮、市、區)界線1140318.zip')
townships = gpd.read_file(url)

# 轉換至EPSG:3826
townships = townships.to_crs('EPSG:3826')
print(f"鄉鎮界資料CRS: {townships.crs}")
print(f"鄉鎮界筆數: {len(townships)}")
print(f"鄉鎮界欄位: {list(townships.columns)}")


# ## 2. 多級緩衝區分析
# 
# **Captain's Log**: 建立三級河川警戒緩衝區（高風險500m、中風險1km、低風險2km），為後續空間連接分析做準備。

# In[ ]:


# 2.1 讀取緩衝區參數
print("讀取緩衝區參數...")

# 從環境變數讀取參數，若無則使用預設值
BUFFER_HIGH = int(os.getenv('BUFFER_HIGH', 500))
BUFFER_MED = int(os.getenv('BUFFER_MED', 1000))
BUFFER_LOW = int(os.getenv('BUFFER_LOW', 2000))

print(f"高風險緩衝區: {BUFFER_HIGH}m")
print(f"中風險緩衝區: {BUFFER_MED}m")
print(f"低風險緩衝區: {BUFFER_LOW}m")


# In[ ]:


# 2.2 建立三級緩衝區
print("\n建立三級河川警戒緩衝區...")

# 合併所有河川面
rivers_union = rivers.unary_union
rivers_buffer = gpd.GeoDataFrame(
    geometry=[rivers_union], 
    crs=rivers.crs
)

# 建立三級緩衝區
buffer_high = rivers_buffer.buffer(BUFFER_HIGH)
buffer_med = rivers_buffer.buffer(BUFFER_MED)
buffer_low = rivers_buffer.buffer(BUFFER_LOW)

# 轉換為GeoDataFrame
buffer_high_gdf = gpd.GeoDataFrame(geometry=buffer_high, crs=rivers.crs)
buffer_med_gdf = gpd.GeoDataFrame(geometry=buffer_med, crs=rivers.crs)
buffer_low_gdf = gpd.GeoDataFrame(geometry=buffer_low, crs=rivers.crs)

# 添加風險等級標籤
buffer_high_gdf['risk_level'] = 'high'
buffer_med_gdf['risk_level'] = 'medium'
buffer_low_gdf['risk_level'] = 'low'

print(f"高風險緩衝區面積: {buffer_high_gdf.geometry.area.sum():.2f} 平方公尺")
print(f"中風險緩衝區面積: {buffer_med_gdf.geometry.area.sum():.2f} 平方公尺")
print(f"低風險緩衝區面積: {buffer_low_gdf.geometry.area.sum():.2f} 平方公尺")


# ## 3. 空間連接與風險分級
# 
# **Captain's Log**: 使用空間連接技術識別各級緩衝區內的避難所，並為每個避難所分配風險等級。處理一對多問題，取最高風險等級。

# In[ ]:


# 3.1 空間連接 - 找出各級緩衝區內的避難所
print("執行空間連接分析...")

# 高風險區避難所
shelters_high = gpd.sjoin(shelters, buffer_high_gdf, how='inner', predicate='within')
print(f"高風險區內避難所數量: {len(shelters_high)}")

# 中風險區避難所
shelters_med = gpd.sjoin(shelters, buffer_med_gdf, how='inner', predicate='within')
print(f"中風險區內避難所數量: {len(shelters_med)}")

# 低風險區避難所
shelters_low = gpd.sjoin(shelters, buffer_low_gdf, how='inner', predicate='within')
print(f"低風險區內避難所數量: {len(shelters_low)}")


# In[ ]:


# 3.2 風險等級分配 - 處理一對多問題
print("\n分配風險等級...")

# 為每個避難所分配風險等級
shelters_with_risk = shelters.copy()
shelters_with_risk['risk_level'] = 'safe'  # 預設為安全

# 獲取各級風險區的避難所索引
high_risk_indices = set(shelters_high.index)
med_risk_indices = set(shelters_med.index)
low_risk_indices = set(shelters_low.index)

# 分配風險等級（優先度：高 > 中 > 低 > 安全）
for idx in shelters_with_risk.index:
    if idx in high_risk_indices:
        shelters_with_risk.loc[idx, 'risk_level'] = 'high'
    elif idx in med_risk_indices:
        shelters_with_risk.loc[idx, 'risk_level'] = 'medium'
    elif idx in low_risk_indices:
        shelters_with_risk.loc[idx, 'risk_level'] = 'low'

# 統計各風險等級的避難所數量
risk_counts = shelters_with_risk['risk_level'].value_counts()
print("\n風險等級統計:")
for risk_level, count in risk_counts.items():
    print(f"{risk_level}: {count} 個避難所")

print(f"\n總避難所數量: {len(shelters_with_risk)}")
print(f"風險區內避難所比例: {(len(shelters_with_risk) - risk_counts.get('safe', 0)) / len(shelters_with_risk) * 100:.1f}%")


# ## 4. 收容量缺口分析
# 
# **Captain's Log**: 按鄉鎮市區彙總避難所風險分佈與收容量，識別安全避難所收容量不足的行政區。

# In[ ]:


# 4.1 空間連接避難所與鄉鎮界
print("將避難所連接到鄉鎮界...")

# 確保避難所資料有唯一的索引
shelters_with_risk = shelters_with_risk.reset_index(drop=True)

# 空間連接避難所與鄉鎮界
shelters_with_township = gpd.sjoin(shelters_with_risk, townships, how='inner', predicate='within')
print(f"成功連接到鄉鎮界的避難所: {len(shelters_with_township)}")

# 檢查鄉鎮名稱欄位
print(f"鄉鎮界欄位: {list(townships.columns)}")
township_name_col = None
for col in townships.columns:
    if '名稱' in col or '名' in col:
        township_name_col = col
        break

if township_name_col:
    print(f"使用鄉鎮名稱欄位: {township_name_col}")
else:
    print("警告: 找不到鄉鎮名稱欄位，使用第一個欄位")
    township_name_col = townships.columns[0]


# In[ ]:


# 4.2 分區統計 - 按鄉鎮市區彙總
print("\n進行分區統計...")

# 確保收容人數欄位存在且為數值型
if capacity_col in shelters_with_township.columns:
    # 轉換收容人數為數值型，無效值設為0
    shelters_with_township[capacity_col] = pd.to_numeric(shelters_with_township[capacity_col], errors='coerce').fillna(0)

    # 按鄉鎮和風險等級分組統計
    township_stats = shelters_with_township.groupby([township_name_col, 'risk_level']).agg({
        capacity_col: 'sum',
        'geometry': 'count'
    }).rename(columns={'geometry': 'shelter_count'})

    # 重新整理統計結果
    township_stats = township_stats.reset_index()

    print("鄉鎮風險統計 (前10筆):")
    print(township_stats.head(10))
else:
    print(f"警告: 收容人數欄位 '{capacity_col}' 不存在")
    # 只統計避難所數量
    township_stats = shelters_with_township.groupby([township_name_col, 'risk_level']).size().reset_index(name='shelter_count')
    township_stats[capacity_col] = 0  # 設為0以保持一致性


# In[ ]:


# 4.3 計算各鄉鎮的風險指標
print("\n計算各鄉鎮風險指標...")

# 建立完整的風險統計表
risk_levels = ['high', 'medium', 'low', 'safe']
township_risk_summary = []

for township in township_stats[township_name_col].unique():
    township_data = township_stats[township_stats[township_name_col] == township]

    # 初始化統計值
    stats = {
        township_name_col: township,
        'high_risk_shelters': 0,
        'medium_risk_shelters': 0,
        'low_risk_shelters': 0,
        'safe_shelters': 0,
        'high_risk_capacity': 0,
        'medium_risk_capacity': 0,
        'low_risk_capacity': 0,
        'safe_capacity': 0
    }

    # 填入實際統計值
    for _, row in township_data.iterrows():
        risk = row['risk_level']
        count = row['shelter_count']
        cap = row[capacity_col]

        if risk == 'high':
            stats['high_risk_shelters'] = count
            stats['high_risk_capacity'] = cap
        elif risk == 'medium':
            stats['medium_risk_shelters'] = count
            stats['medium_risk_capacity'] = cap
        elif risk == 'low':
            stats['low_risk_shelters'] = count
            stats['low_risk_capacity'] = cap
        elif risk == 'safe':
            stats['safe_shelters'] = count
            stats['safe_capacity'] = cap

    # 計算總風險避難所和收容量
    stats['total_risk_shelters'] = stats['high_risk_shelters'] + stats['medium_risk_shelters'] + stats['low_risk_shelters']
    stats['total_risk_capacity'] = stats['high_risk_capacity'] + stats['medium_risk_capacity'] + stats['low_risk_capacity']
    stats['total_shelters'] = stats['total_risk_shelters'] + stats['safe_shelters']
    stats['total_capacity'] = stats['total_risk_capacity'] + stats['safe_capacity']

    # 計算安全比例
    if stats['total_capacity'] > 0:
        stats['safe_capacity_ratio'] = stats['safe_capacity'] / stats['total_capacity']
    else:
        stats['safe_capacity_ratio'] = 0

    township_risk_summary.append(stats)

# 轉換為DataFrame
township_risk_df = pd.DataFrame(township_risk_summary)

print(f"完成 {len(township_risk_df)} 個鄉鎮的風險統計")
print("\n風險統計摘要:")
print(township_risk_df[['high_risk_shelters', 'medium_risk_shelters', 'low_risk_shelters', 'safe_shelters']].sum())


# In[ ]:


# 4.4 識別風險最高的行政區
print("\n識別風險最高的行政區...")

# 計算風險指數（高風險避難所數量 + 0.5*中風險 + 0.2*低風險）
township_risk_df['risk_score'] = (
    township_risk_df['high_risk_shelters'] * 1.0 +
    township_risk_df['medium_risk_shelters'] * 0.5 +
    township_risk_df['low_risk_shelters'] * 0.2
)

# 排序獲取Top 10高風險行政區
top_10_risk = township_risk_df.sort_values('risk_score', ascending=False).head(10)

print("\n=== 風險最高的 Top 10 行政區 ===")
print(top_10_risk[[
    township_name_col, 'high_risk_shelters', 'medium_risk_shelters', 
    'low_risk_shelters', 'safe_shelters', 'risk_score'
]].to_string(index=False))


# ## 5. 視覺化分析
# 
# **Captain's Log**: 建立互動式風險地圖與靜態統計圖，直觀展示避難所風險分佈與行政區排名。

# In[ ]:


# 5.1 建立互動式風險地圖
print("建立互動式風險地圖...")

# 計算地圖中心點
center_lat = shelters_with_risk.geometry.y.mean()
center_lon = shelters_with_risk.geometry.x.mean()

# 建立地圖
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=8,
    tiles='OpenStreetMap'
)

# 定義風險等級顏色
risk_colors = {
    'high': 'red',
    'medium': 'orange', 
    'low': 'yellow',
    'safe': 'green'
}

# 添加河川面（藍色）
folium.GeoJson(
    rivers.to_crs('EPSG:4326'),
    style_function=lambda x: {
        'fillColor': 'blue',
        'color': 'blue',
        'weight': 2,
        'fillOpacity': 0.3
    },
    name='河川'
).add_to(m)

# 添加三級緩衝區
folium.GeoJson(
    buffer_low_gdf.to_crs('EPSG:4326'),
    style_function=lambda x: {
        'fillColor': 'yellow',
        'color': 'orange',
        'weight': 1,
        'fillOpacity': 0.1
    },
    name='低風險緩衝區 (2km)'
).add_to(m)

folium.GeoJson(
    buffer_med_gdf.to_crs('EPSG:4326'),
    style_function=lambda x: {
        'fillColor': 'orange',
        'color': 'orange',
        'weight': 1,
        'fillOpacity': 0.15
    },
    name='中風險緩衝區 (1km)'
).add_to(m)

folium.GeoJson(
    buffer_high_gdf.to_crs('EPSG:4326'),
    style_function=lambda x: {
        'fillColor': 'red',
        'color': 'red',
        'weight': 1,
        'fillOpacity': 0.2
    },
    name='高風險緩衝區 (500m)'
).add_to(m)

print("地圖底圖和緩衝區添加完成")


# In[ ]:


# 5.2 添加避難所點位
print("添加避難所點位...")

# 轉換避難所回EPSG:4326用於地圖顯示
shelters_4326 = shelters_with_risk.to_crs('EPSG:4326')

# 為每個避難所添加標記
for idx, shelter in shelters_4326.iterrows():
    risk_level = shelter['risk_level']
    color = risk_colors[risk_level]

    # 獲取避難所名稱和收容人數
    name = shelter.get('避難收容處所名稱', f'避難所 {idx}')
    capacity = shelter.get(capacity_col, 0)

    # 建立彈出視窗內容
    popup_content = f"""
    <b>{name}</b><br>
    風險等級: {risk_level}<br>
    收容人數: {capacity}<br>
    經緯度: ({shelter.geometry.y:.4f}, {shelter.geometry.x:.4f})
    """

    folium.CircleMarker(
        location=[shelter.geometry.y, shelter.geometry.x],
        radius=5,
        popup=folium.Popup(popup_content, max_width=300),
        color=color,
        fillColor=color,
        fillOpacity=0.7,
        weight=2
    ).add_to(m)

# 添加圖例
legend_html = '''
<div style="position: fixed; 
     top: 10px; right: 10px; width: 150px; height: 120px; 
     background-color: white; border:2px solid grey; z-index:9999; 
     font-size:14px; padding: 10px">
<h4>風險等級圖例</h4>
<i class="fa fa-circle" style="color:red"></i> 高風險 (500m)<br>
<i class="fa fa-circle" style="color:orange"></i> 中風險 (1km)<br>
<i class="fa fa-circle" style="color:yellow"></i> 低風險 (2km)<br>
<i class="fa fa-circle" style="color:green"></i> 安全區<br>
</div>
'''

m.get_root().html.add_child(folium.Element(legend_html))
m.add_child(folium.LayerControl())

print("互動式地圖建立完成")
display(m)


# In[ ]:


# 5.3 建立靜態統計圖 - Top 10高風險行政區
print("建立靜態統計圖...")

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 建立子圖
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# 圖1: Top 10高風險行政區的避難所數量
top_10_for_plot = top_10_risk.copy()
x_pos = np.arange(len(top_10_for_plot))

# 堆疊長條圖
ax1.bar(x_pos, top_10_for_plot['high_risk_shelters'], label='高風險', color='red', alpha=0.7)
ax1.bar(x_pos, top_10_for_plot['medium_risk_shelters'], bottom=top_10_for_plot['high_risk_shelters'], 
        label='中風險', color='orange', alpha=0.7)
ax1.bar(x_pos, top_10_for_plot['low_risk_shelters'], 
        bottom=top_10_for_plot['high_risk_shelters'] + top_10_for_plot['medium_risk_shelters'], 
        label='低風險', color='yellow', alpha=0.7)
ax1.bar(x_pos, top_10_for_plot['safe_shelters'], 
        bottom=top_10_for_plot['high_risk_shelters'] + top_10_for_plot['medium_risk_shelters'] + top_10_for_plot['low_risk_shelters'], 
        label='安全', color='green', alpha=0.7)

ax1.set_xlabel('行政區排名')
ax1.set_ylabel('避難所數量')
ax1.set_title('Top 10 高風險行政區 - 避難所數量分佈')
ax1.set_xticks(x_pos)
ax1.set_xticklabels([f"{i+1}" for i in range(len(top_10_for_plot))])
ax1.legend()
ax1.grid(True, alpha=0.3)

# 圖2: 收容量分析
if capacity_col in top_10_for_plot.columns:
    ax2.bar(x_pos, top_10_for_plot['total_risk_capacity'], label='風險區收容量', color='red', alpha=0.7)
    ax2.bar(x_pos, top_10_for_plot['safe_capacity'], label='安全區收容量', color='green', alpha=0.7)

    ax2.set_xlabel('行政區排名')
    ax2.set_ylabel('收容人數')
    ax2.set_title('Top 10 高風險行政區 - 收容量分析')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([f"{i+1}" for i in range(len(top_10_for_plot))])
    ax2.legend()
    ax2.grid(True, alpha=0.3)
else:
    ax2.text(0.5, 0.5, '收容人數資料不可用', ha='center', va='center', transform=ax2.transAxes)
    ax2.set_title('收容量分析')

plt.tight_layout()
plt.savefig('risk_map.png', dpi=300, bbox_inches='tight')
plt.show()

print("靜態統計圖已儲存為 risk_map.png")


# ## 6. 輸出結果
# 
# **Captain's Log**: 生成避難所風險清單JSON檔案，包含每個避難所的詳細風險評估結果。

# In[ ]:


# 6.1 生成避難所風險清單
print("生成避難所風險清單...")

# 準備輸出資料
shelter_risk_audit = []

for idx, shelter in shelters_with_risk.iterrows():
    # 獲取避難所基本資訊
    shelter_info = {
        'shelter_id': str(idx),
        'name': shelter.get('避難收容處所名稱', f'避難所 {idx}'),
        'address': shelter.get('避難收容處所地址', ''),
        'risk_level': shelter['risk_level'],
        'capacity': int(shelter.get(capacity_col, 0)),
        'longitude': float(shelter.geometry.x),
        'latitude': float(shelter.geometry.y),
        'county': shelter.get('縣市', ''),
        'township': shelter.get('鄉鎮市區', '')
    }

    shelter_risk_audit.append(shelter_info)

# 儲存為JSON檔案
with open('shelter_risk_audit.json', 'w', encoding='utf-8') as f:
    json.dump(shelter_risk_audit, f, ensure_ascii=False, indent=2)

print(f"已生成 {len(shelter_risk_audit)} 個避難所的風險清單")
print("檔案已儲存為 shelter_risk_audit.json")

# 顯示統計摘要
risk_summary = {}
for shelter in shelter_risk_audit:
    risk = shelter['risk_level']
    if risk not in risk_summary:
        risk_summary[risk] = {'count': 0, 'capacity': 0}
    risk_summary[risk]['count'] += 1
    risk_summary[risk]['capacity'] += shelter['capacity']

print("\n=== 風險清單統計摘要 ===")
for risk, stats in risk_summary.items():
    print(f"{risk}: {stats['count']} 個避難所, 總收容量 {stats['capacity']} 人")


# In[ ]:


# 6.2 儲存互動式地圖為HTML
print("\n儲存互動式地圖...")
m.save('interactive_risk_map.html')
print("互動式地圖已儲存為 interactive_risk_map.html")

# 6.3 儲存鄉鎮風險統計
township_risk_df.to_csv('township_risk_analysis.csv', index=False, encoding='utf-8-sig')
print("鄉鎮風險統計已儲存為 township_risk_analysis.csv")

print("\n=== 分析完成 ===")
print("輸出檔案:")
print("1. shelter_risk_audit.json - 避難所風險清單")
print("2. interactive_risk_map.html - 互動式風險地圖")
print("3. risk_map.png - 靜態統計圖")
print("4. township_risk_analysis.csv - 鄉鎮風險統計")


# ## 7. 總結與建議
# 
# **Captain's Log**: 分析完成，總結主要發現與政策建議。

# In[ ]:


# 7.1 分析總結
print("=== 河川洪災避難所風險評估 - 分析總結 ===")
print(f"\n📊 基本統計:")
print(f"• 分析避難所總數: {len(shelters_with_risk)} 個")
print(f"• 高風險區避難所: {risk_counts.get('high', 0)} 個 ({risk_counts.get('high', 0)/len(shelters_with_risk)*100:.1f}%)")
print(f"• 中風險區避難所: {risk_counts.get('medium', 0)} 個 ({risk_counts.get('medium', 0)/len(shelters_with_risk)*100:.1f}%)")
print(f"• 低風險區避難所: {risk_counts.get('low', 0)} 個 ({risk_counts.get('low', 0)/len(shelters_with_risk)*100:.1f}%)")
print(f"• 安全區避難所: {risk_counts.get('safe', 0)} 個 ({risk_counts.get('safe', 0)/len(shelters_with_risk)*100:.1f}%)")

print(f"\n🚨 風險最高的行政區:")
for i, (_, row) in enumerate(top_10_risk.head(3).iterrows()):
    print(f"{i+1}. {row[township_name_col]} - 風險分數: {row['risk_score']:.1f}")
print(f"   (完整排名請參考 township_risk_analysis.csv)")

if capacity_col in shelters_with_township.columns:
    total_capacity = shelters_with_township[capacity_col].sum()
    safe_capacity = shelters_with_township[shelters_with_township['risk_level'] == 'safe'][capacity_col].sum()
    risk_capacity = total_capacity - safe_capacity

    print(f"\n🏠 收容量分析:")
    print(f"• 總收容量: {int(total_capacity):,} 人")
    print(f"• 安全區收容量: {int(safe_capacity):,} 人 ({safe_capacity/total_capacity*100:.1f}%)")
    print(f"• 風險區收容量: {int(risk_capacity):,} 人 ({risk_capacity/total_capacity*100:.1f}%)")

print(f"\n📋 政策建議:")
print(f"1. 優先檢視風險分數最高的前10個行政區的避難所配置")
print(f"2. 評估高風險區避難所的遷移或加固可行性")
print(f"3. 在安全區不足的行政區規劃新增避難所")
print(f"4. 建立動態監測系統，定期更新河川與避難所資料")
print(f"5. 結合人口分佈資料，進行更精確的收容量缺口分析")

print(f"\n✅ 分析完成時間: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")


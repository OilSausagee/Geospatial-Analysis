#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARIA - Automated Regional Impact Auditor
河川洪災避難所風險評估分析腳本
"""

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

def main():
    print("=== ARIA 河川洪災避難所風險評估分析 ===")
    
    # 載入環境變數
    load_dotenv()
    
    # 讀取緩衝區參數
    BUFFER_HIGH = int(os.getenv('BUFFER_HIGH', 500))
    BUFFER_MED = int(os.getenv('BUFFER_MED', 1000))
    BUFFER_LOW = int(os.getenv('BUFFER_LOW', 2000))
    
    print(f"緩衝區參數: 高={BUFFER_HIGH}m, 中={BUFFER_MED}m, 低={BUFFER_LOW}m")
    
    # 1. 載入水利署河川面資料
    print("\n1. 載入水利署河川面資料...")
    rivers = gpd.read_file('https://gic.wra.gov.tw/Gis/gic/API/Google/DownLoad.aspx?fname=RIVERPOLY&filetype=SHP')
    print(f"河川資料原始CRS: {rivers.crs}")
    print(f"河川筆數: {len(rivers)}")
    
    if rivers.crs != 'EPSG:3826':
        rivers = rivers.to_crs('EPSG:3826')
        print(f"河川資料轉換為EPSG:3826")
    
    # 2. 載入消防署避難收容所資料
    print("\n2. 載入消防署避難收容所資料...")
    try:
        shelters_csv = pd.read_csv('避難收容處所.csv', encoding='utf-8')
    except:
        shelters_csv = pd.read_csv('避難收容處所.csv', encoding='big5')
    
    print(f"原始避難所資料筆數: {len(shelters_csv)}")
    
    # 3. 資料清理
    print("\n3. 資料清理...")
    lon_col = '經度'
    lat_col = '緯度'
    original_count = len(shelters_csv)
    
    # 移除無效座標
    shelters_clean = shelters_csv.dropna(subset=[lon_col, lat_col])
    shelters_clean = shelters_clean[(shelters_clean[lon_col] != 0) & (shelters_clean[lat_col] != 0)]
    shelters_clean = shelters_clean[
        (shelters_clean[lon_col] >= 119) & (shelters_clean[lon_col] <= 122) &
        (shelters_clean[lat_col] >= 21) & (shelters_clean[lat_col] <= 26)
    ]
    
    cleaned_count = len(shelters_clean)
    print(f"清理前筆數: {original_count}")
    print(f"清理後筆數: {cleaned_count}")
    print(f"移除無效記錄: {original_count - cleaned_count} 筆")
    
    # 4. 轉換為GeoDataFrame
    print("\n4. 轉換為GeoDataFrame...")
    shelters = gpd.GeoDataFrame(
        shelters_clean,
        geometry=gpd.points_from_xy(shelters_clean[lon_col], shelters_clean[lat_col]),
        crs='EPSG:4326'
    )
    shelters = shelters.to_crs('EPSG:3826')
    print(f"避難所資料CRS: {shelters.crs}")
    print(f"避難所筆數: {len(shelters)}")
    
    # 5. 建立三級緩衝區
    print("\n5. 建立三級緩衝區...")
    rivers_union = rivers.unary_union
    rivers_buffer = gpd.GeoDataFrame(geometry=[rivers_union], crs=rivers.crs)
    
    buffer_high = rivers_buffer.buffer(BUFFER_HIGH)
    buffer_med = rivers_buffer.buffer(BUFFER_MED)
    buffer_low = rivers_buffer.buffer(BUFFER_LOW)
    
    buffer_high_gdf = gpd.GeoDataFrame(geometry=buffer_high, crs=rivers.crs)
    buffer_med_gdf = gpd.GeoDataFrame(geometry=buffer_med, crs=rivers.crs)
    buffer_low_gdf = gpd.GeoDataFrame(geometry=buffer_low, crs=rivers.crs)
    
    buffer_high_gdf['risk_level'] = 'high'
    buffer_med_gdf['risk_level'] = 'medium'
    buffer_low_gdf['risk_level'] = 'low'
    
    print(f"高風險緩衝區面積: {buffer_high_gdf.geometry.area.sum():.2f} 平方公尺")
    print(f"中風險緩衝區面積: {buffer_med_gdf.geometry.area.sum():.2f} 平方公尺")
    print(f"低風險緩衝區面積: {buffer_low_gdf.geometry.area.sum():.2f} 平方公尺")
    
    # 6. 空間連接與風險分級
    print("\n6. 空間連接與風險分級...")
    shelters_high = gpd.sjoin(shelters, buffer_high_gdf, how='inner', predicate='within')
    shelters_med = gpd.sjoin(shelters, buffer_med_gdf, how='inner', predicate='within')
    shelters_low = gpd.sjoin(shelters, buffer_low_gdf, how='inner', predicate='within')
    
    print(f"高風險區內避難所數量: {len(shelters_high)}")
    print(f"中風險區內避難所數量: {len(shelters_med)}")
    print(f"低風險區內避難所數量: {len(shelters_low)}")
    
    # 分配風險等級
    shelters_with_risk = shelters.copy()
    shelters_with_risk['risk_level'] = 'safe'
    
    high_risk_indices = set(shelters_high.index)
    med_risk_indices = set(shelters_med.index)
    low_risk_indices = set(shelters_low.index)
    
    for idx in shelters_with_risk.index:
        if idx in high_risk_indices:
            shelters_with_risk.loc[idx, 'risk_level'] = 'high'
        elif idx in med_risk_indices:
            shelters_with_risk.loc[idx, 'risk_level'] = 'medium'
        elif idx in low_risk_indices:
            shelters_with_risk.loc[idx, 'risk_level'] = 'low'
    
    risk_counts = shelters_with_risk['risk_level'].value_counts()
    print("\n風險等級統計:")
    for risk_level, count in risk_counts.items():
        print(f"{risk_level}: {count} 個避難所")
    
    # 7. 生成避難所風險清單
    print("\n7. 生成避難所風險清單...")
    capacity_col = '預計收容人數'
    
    shelter_risk_audit = []
    for idx, shelter in shelters_with_risk.iterrows():
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
    
    # 儲存到outputs資料夾
    with open('outputs/shelter_risk_audit.json', 'w', encoding='utf-8') as f:
        json.dump(shelter_risk_audit, f, ensure_ascii=False, indent=2)
    
    print(f"已生成 {len(shelter_risk_audit)} 個避難所的風險清單")
    
    # 8. 建立簡化版統計圖
    print("\n8. 建立統計圖...")
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    risk_levels = ['high', 'medium', 'low', 'safe']
    risk_counts_list = [risk_counts.get(level, 0) for level in risk_levels]
    risk_colors = ['red', 'orange', 'yellow', 'green']
    risk_labels = ['高風險', '中風險', '低風險', '安全']
    
    bars = ax.bar(risk_labels, risk_counts_list, color=risk_colors, alpha=0.7)
    ax.set_xlabel('風險等級')
    ax.set_ylabel('避難所數量')
    ax.set_title('避難所風險等級分佈')
    ax.grid(True, alpha=0.3)
    
    # 在柱狀圖上顯示數值
    for bar, count in zip(bars, risk_counts_list):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{count}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('outputs/risk_map.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("統計圖已儲存為 outputs/risk_map.png")
    
    # 9. 生成簡化版互動式地圖
    print("\n9. 建立互動式地圖...")
    center_lat = shelters_with_risk.geometry.y.mean()
    center_lon = shelters_with_risk.geometry.x.mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    risk_colors = {
        'high': 'red',
        'medium': 'orange', 
        'low': 'yellow',
        'safe': 'green'
    }
    
    # 添加避難所點位
    shelters_4326 = shelters_with_risk.to_crs('EPSG:4326')
    
    for idx, shelter in shelters_4326.iterrows():
        risk_level = shelter['risk_level']
        color = risk_colors[risk_level]
        
        name = shelter.get('避難收容處所名稱', f'避難所 {idx}')
        capacity = shelter.get(capacity_col, 0)
        
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
    
    m.save('outputs/interactive_risk_map.html')
    print("互動式地圖已儲存為 outputs/interactive_risk_map.html")
    
    # 10. 總結報告
    print("\n=== 分析完成 ===")
    print(f"• 分析避難所總數: {len(shelters_with_risk)} 個")
    print(f"• 高風險區避難所: {risk_counts.get('high', 0)} 個 ({risk_counts.get('high', 0)/len(shelters_with_risk)*100:.1f}%)")
    print(f"• 中風險區避難所: {risk_counts.get('medium', 0)} 個 ({risk_counts.get('medium', 0)/len(shelters_with_risk)*100:.1f}%)")
    print(f"• 低風險區避難所: {risk_counts.get('low', 0)} 個 ({risk_counts.get('low', 0)/len(shelters_with_risk)*100:.1f}%)")
    print(f"• 安全區避難所: {risk_counts.get('safe', 0)} 個 ({risk_counts.get('safe', 0)/len(shelters_with_risk)*100:.1f}%)")
    
    print("\n輸出檔案:")
    print("1. outputs/shelter_risk_audit.json - 避難所風險清單")
    print("2. outputs/interactive_risk_map.html - 互動式風險地圖")
    print("3. outputs/risk_map.png - 靜態統計圖")
    
    print(f"\n✅ 分析完成時間: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

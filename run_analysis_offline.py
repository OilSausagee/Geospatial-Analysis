#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARIA - Automated Regional Impact Auditor
河川洪災避難所風險評估分析腳本 (離線版本)
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
import warnings
warnings.filterwarnings('ignore')

def main():
    print("=== ARIA 河川洪災避難所風險評估分析 (離線版本) ===")
    
    # 載入環境變數
    load_dotenv()
    
    # 讀取緩衝區參數
    BUFFER_HIGH = int(os.getenv('BUFFER_HIGH', 500))
    BUFFER_MED = int(os.getenv('BUFFER_MED', 1000))
    BUFFER_LOW = int(os.getenv('BUFFER_LOW', 2000))
    
    print(f"緩衝區參數: 高={BUFFER_HIGH}m, 中={BUFFER_MED}m, 低={BUFFER_LOW}m")
    
    # 1. 載入消防署避難收容所資料
    print("\n1. 載入消防署避難收容所資料...")
    try:
        shelters_csv = pd.read_csv('避難收容處所.csv', encoding='utf-8')
    except:
        shelters_csv = pd.read_csv('避難收容處所.csv', encoding='big5')
    
    print(f"原始避難所資料筆數: {len(shelters_csv)}")
    
    # 2. 資料清理
    print("\n2. 資料清理...")
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
    
    # 3. 轉換為GeoDataFrame
    print("\n3. 轉換為GeoDataFrame...")
    shelters = gpd.GeoDataFrame(
        shelters_clean,
        geometry=gpd.points_from_xy(shelters_clean[lon_col], shelters_clean[lat_col]),
        crs='EPSG:4326'
    )
    shelters = shelters.to_crs('EPSG:3826')
    print(f"避難所資料CRS: {shelters.crs}")
    print(f"避難所筆數: {len(shelters)}")
    
    # 4. 模擬河川緩衝區分析 (由於無法下載真實河川資料)
    print("\n4. 模擬河川緩衝區分析...")
    print("注意: 由於網路連線問題，使用模擬河川位置進行分析")
    
    # 創建模擬河川位置 (基於台灣主要河流的大致位置)
    from shapely.geometry import Point, Polygon
    
    # 模擬幾條主要河流的線段
    simulated_rivers = []
    
    # 淡水河 (北部)
    river1_coords = [(300000, 2780000), (302000, 2782000), (304000, 2784000), (306000, 2786000)]
    simulated_rivers.append(Polygon(river1_coords).buffer(100))  # 100m寬的河川
    
    # 濁水溪 (中部)
    river2_coords = [(200000, 2650000), (202000, 2652000), (204000, 2654000), (206000, 2656000)]
    simulated_rivers.append(Polygon(river2_coords).buffer(120))
    
    # 高屏溪 (南部)
    river3_coords = [(190000, 2500000), (192000, 2502000), (194000, 2504000), (196000, 2506000)]
    simulated_rivers.append(Polygon(river3_coords).buffer(110))
    
    # 合併所有河川
    from shapely.ops import unary_union
    rivers_union = unary_union(simulated_rivers)
    
    # 建立三級緩衝區
    buffer_high = gpd.GeoDataFrame(geometry=[rivers_union.buffer(BUFFER_HIGH)], crs='EPSG:3826')
    buffer_med = gpd.GeoDataFrame(geometry=[rivers_union.buffer(BUFFER_MED)], crs='EPSG:3826')
    buffer_low = gpd.GeoDataFrame(geometry=[rivers_union.buffer(BUFFER_LOW)], crs='EPSG:3826')
    
    buffer_high['risk_level'] = 'high'
    buffer_med['risk_level'] = 'medium'
    buffer_low['risk_level'] = 'low'
    
    print(f"模擬河川緩衝區建立完成")
    print(f"高風險緩衝區面積: {buffer_high.geometry.area.sum():.2f} 平方公尺")
    print(f"中風險緩衝區面積: {buffer_med.geometry.area.sum():.2f} 平方公尺")
    print(f"低風險緩衝區面積: {buffer_low.geometry.area.sum():.2f} 平方公尺")
    
    # 5. 空間連接與風險分級
    print("\n5. 空間連接與風險分級...")
    shelters_high = gpd.sjoin(shelters, buffer_high, how='inner', predicate='within')
    shelters_med = gpd.sjoin(shelters, buffer_med, how='inner', predicate='within')
    shelters_low = gpd.sjoin(shelters, buffer_low, how='inner', predicate='within')
    
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
    
    # 6. 生成避難所風險清單
    print("\n6. 生成避難所風險清單...")
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
    
    # 7. 建立統計圖
    print("\n7. 建立統計圖...")
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 圖1: 風險等級分佈
    risk_levels = ['high', 'medium', 'low', 'safe']
    risk_counts_list = [risk_counts.get(level, 0) for level in risk_levels]
    risk_colors = ['red', 'orange', 'yellow', 'green']
    risk_labels = ['高風險', '中風險', '低風險', '安全']
    
    bars = ax1.bar(risk_labels, risk_counts_list, color=risk_colors, alpha=0.7)
    ax1.set_xlabel('風險等級')
    ax1.set_ylabel('避難所數量')
    ax1.set_title('避難所風險等級分佈')
    ax1.grid(True, alpha=0.3)
    
    for bar, count in zip(bars, risk_counts_list):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{count}',
                ha='center', va='bottom')
    
    # 圖2: 收容量分析
    if capacity_col in shelters_with_risk.columns:
        capacity_by_risk = shelters_with_risk.groupby('risk_level')[capacity_col].sum()
        capacity_list = [capacity_by_risk.get(level, 0) for level in risk_levels]
        
        bars2 = ax2.bar(risk_labels, capacity_list, color=risk_colors, alpha=0.7)
        ax2.set_xlabel('風險等級')
        ax2.set_ylabel('收容人數')
        ax2.set_title('各風險等級收容量分佈')
        ax2.grid(True, alpha=0.3)
        
        for bar, cap in zip(bars2, capacity_list):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(cap):,}',
                    ha='center', va='bottom')
    else:
        ax2.text(0.5, 0.5, '收容人數資料不可用', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('收容量分析')
    
    plt.tight_layout()
    plt.savefig('outputs/risk_map.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("統計圖已儲存為 outputs/risk_map.png")
    
    # 8. 建立互動式地圖
    print("\n8. 建立互動式地圖...")
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
    
    # 添加模擬河川緩衝區
    buffer_high_4326 = buffer_high.to_crs('EPSG:4326')
    buffer_med_4326 = buffer_med.to_crs('EPSG:4326')
    buffer_low_4326 = buffer_low.to_crs('EPSG:4326')
    
    folium.GeoJson(
        buffer_low_4326,
        style_function=lambda x: {
            'fillColor': 'yellow',
            'color': 'orange',
            'weight': 1,
            'fillOpacity': 0.1
        },
        name='低風險緩衝區 (2km)'
    ).add_to(m)
    
    folium.GeoJson(
        buffer_med_4326,
        style_function=lambda x: {
            'fillColor': 'orange',
            'color': 'orange',
            'weight': 1,
            'fillOpacity': 0.15
        },
        name='中風險緩衝區 (1km)'
    ).add_to(m)
    
    folium.GeoJson(
        buffer_high_4326,
        style_function=lambda x: {
            'fillColor': 'red',
            'color': 'red',
            'weight': 1,
            'fillOpacity': 0.2
        },
        name='高風險緩衝區 (500m)'
    ).add_to(m)
    
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
    
    m.save('outputs/interactive_risk_map.html')
    print("互動式地圖已儲存為 outputs/interactive_risk_map.html")
    
    # 9. 生成分析報告
    print("\n9. 生成分析報告...")
    total_capacity = shelters_with_risk[capacity_col].sum() if capacity_col in shelters_with_risk.columns else 0
    safe_capacity = shelters_with_risk[shelters_with_risk['risk_level'] == 'safe'][capacity_col].sum() if capacity_col in shelters_with_risk.columns else 0
    risk_capacity = total_capacity - safe_capacity
    
    report = f"""
# ARIA 河川洪災避難所風險評估報告

## 分析摘要
- 分析時間: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
- 分析避難所總數: {len(shelters_with_risk)} 個
- 使用模擬河川資料 (由於網路連線問題)

## 風險分佈統計
- 高風險區避難所: {risk_counts.get('high', 0)} 個 ({risk_counts.get('high', 0)/len(shelters_with_risk)*100:.1f}%)
- 中風險區避難所: {risk_counts.get('medium', 0)} 個 ({risk_counts.get('medium', 0)/len(shelters_with_risk)*100:.1f}%)
- 低風險區避難所: {risk_counts.get('low', 0)} 個 ({risk_counts.get('low', 0)/len(shelters_with_risk)*100:.1f}%)
- 安全區避難所: {risk_counts.get('safe', 0)} 個 ({risk_counts.get('safe', 0)/len(shelters_with_risk)*100:.1f}%)

## 收容量分析
- 總收容量: {int(total_capacity):,} 人
- 安全區收容量: {int(safe_capacity):,} 人 ({safe_capacity/total_capacity*100:.1f}%)
- 風險區收容量: {int(risk_capacity):,} 人 ({risk_capacity/total_capacity*100:.1f}%)

## 輸出檔案
1. shelter_risk_audit.json - 避難所風險清單
2. interactive_risk_map.html - 互動式風險地圖
3. risk_map.png - 靜態統計圖

## 注意事項
本次分析使用模擬河川位置進行示範。實際應用時應使用水利署真實河川資料。
"""
    
    with open('outputs/analysis_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("分析報告已儲存為 outputs/analysis_report.md")
    
    # 10. 總結
    print("\n=== 分析完成 ===")
    print(f"• 分析避難所總數: {len(shelters_with_risk)} 個")
    print(f"• 高風險區避難所: {risk_counts.get('high', 0)} 個 ({risk_counts.get('high', 0)/len(shelters_with_risk)*100:.1f}%)")
    print(f"• 中風險區避難所: {risk_counts.get('medium', 0)} 個 ({risk_counts.get('medium', 0)/len(shelters_with_risk)*100:.1f}%)")
    print(f"• 低風險區避難所: {risk_counts.get('low', 0)} 個 ({risk_counts.get('low', 0)/len(shelters_with_risk)*100:.1f}%)")
    print(f"• 安全區避難所: {risk_counts.get('safe', 0)} 個 ({risk_counts.get('safe', 0)/len(shelters_with_risk)*100:.1f}%)")
    
    if total_capacity > 0:
        print(f"\n• 總收容量: {int(total_capacity):,} 人")
        print(f"• 安全區收容量: {int(safe_capacity):,} 人 ({safe_capacity/total_capacity*100:.1f}%)")
        print(f"• 風險區收容量: {int(risk_capacity):,} 人 ({risk_capacity/total_capacity*100:.1f}%)")
    
    print("\n輸出檔案 (位於outputs資料夾):")
    print("1. shelter_risk_audit.json - 避難所風險清單")
    print("2. interactive_risk_map.html - 互動式風險地圖")
    print("3. risk_map.png - 靜態統計圖")
    print("4. analysis_report.md - 分析報告")
    
    print(f"\n✅ 分析完成時間: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

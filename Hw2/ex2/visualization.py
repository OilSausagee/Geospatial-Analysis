#!/usr/bin/env python3
"""
視覺化模組
提供地圖和統計圖表的視覺化功能
"""

import folium
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from matplotlib.patches import FancyBboxPatch
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class CoordinateVisualizer:
    def __init__(self):
        self.color_palette = {
            'wgs84': '#1f77b4',  # 藍色
            'twd97': '#ff7f0e',  # 橙色
            'twd67': '#2ca02c',  # 綠色
            'connection': '#d62728',  # 紅色
            'background': '#f8f9fa'
        }
        
    def create_interactive_map(self, df, lat_col1, lon_col1, lat_col2, lon_col2,
                             station_col, system1_name="WGS84", system2_name="TWD97"):
        """
        創建互動式地圖
        
        Args:
            df: 包含座標資料的DataFrame
            lat_col1, lon_col1: 第一組座標欄位
            lat_col2, lon_col2: 第二組座標欄位
            station_col: 測站名稱欄位
            system1_name, system2_name: 座標系統名稱
        
        Returns:
            folium.Map: 互動式地圖物件
        """
        # 計算地圖中心點
        all_lats = pd.concat([df[lat_col1], df[lat_col2]])
        all_lons = pd.concat([df[lon_col1], df[lon_col2]])
        center_lat = all_lats.mean()
        center_lon = all_lons.mean()
        
        # 建立地圖
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # 添加不同的圖層
        feature_group1 = folium.FeatureGroup(name=system1_name)
        feature_group2 = folium.FeatureGroup(name=system2_name)
        connection_group = folium.FeatureGroup(name="座標連線")
        
        # 添加測站座標和連線
        for idx, row in df.iterrows():
            station_name = row[station_col]
            
            # 第一組座標
            folium.CircleMarker(
                location=[row[lat_col1], row[lon_col1]],
                radius=8,
                popup=f"{station_name}<br>{system1_name}<br>({row[lat_col1]:.6f}, {row[lon_col1]:.6f})",
                color=self.color_palette['wgs84'],
                fill=True,
                fillColor=self.color_palette['wgs84'],
                weight=2,
                opacity=0.8
            ).add_to(feature_group1)
            
            # 第二組座標
            folium.CircleMarker(
                location=[row[lat_col2], row[lon_col2]],
                radius=8,
                popup=f"{station_name}<br>{system2_name}<br>({row[lat_col2]:.6f}, {row[lon_col2]:.6f})",
                color=self.color_palette['twd97'],
                fill=True,
                fillColor=self.color_palette['twd97'],
                weight=2,
                opacity=0.8
            ).add_to(feature_group2)
            
            # 連線
            distance = self._calculate_distance(
                row[lat_col1], row[lon_col1], row[lat_col2], row[lon_col2]
            )
            
            folium.PolyLine(
                locations=[
                    [row[lat_col1], row[lon_col1]],
                    [row[lat_col2], row[lon_col2]]
                ],
                color=self.color_palette['connection'],
                weight=3,
                opacity=0.6,
                popup=f"{station_name}<br>距離: {distance:.2f}公尺"
            ).add_to(connection_group)
        
        # 添加圖層到地圖
        feature_group1.add_to(m)
        feature_group2.add_to(m)
        connection_group.add_to(m)
        
        # 添加圖層控制
        folium.LayerControl().add_to(m)
        
        # 添加圖例
        self._add_map_legend(m, system1_name, system2_name)
        
        # 添加比例尺
        folium.plugins.MeasureControl().add_to(m)
        
        return m
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """計算兩點間距離"""
        from geopy.distance import geodesic
        return geodesic((lat1, lon1), (lat2, lon2)).meters
    
    def _add_map_legend(self, map_obj, system1_name, system2_name):
        """添加地圖圖例"""
        legend_html = f'''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px">
        <h4 style="margin: 0 0 10px 0;">圖例</h4>
        <p style="margin: 5px 0;">
            <i class="fa fa-circle" style="color:{self.color_palette['wgs84']}"></i> 
            {system1_name}
        </p>
        <p style="margin: 5px 0;">
            <i class="fa fa-circle" style="color:{self.color_palette['twd97']}"></i> 
            {system2_name}
        </p>
        <p style="margin: 5px 0;">
            <i class="fa fa-minus" style="color:{self.color_palette['connection']}"></i> 
            座標連線
        </p>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def create_statistical_plots(self, df, distance_col, lat_diff_col, lon_diff_col):
        """
        創建統計圖表
        
        Args:
            df: 包含統計資料的DataFrame
            distance_col: 距離欄位名稱
            lat_diff_col: 緯度差異欄位名稱
            lon_diff_col: 經度差異欄位名稱
        
        Returns:
            matplotlib.Figure: 圖表物件
        """
        # 設定中文字體
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 創建子圖
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('氣象站座標系統比較分析', fontsize=16, fontweight='bold')
        
        # 1. 距離差距分佈直方圖
        axes[0, 0].hist(df[distance_col], bins=30, alpha=0.7, 
                       color=self.color_palette['connection'], edgecolor='black')
        axes[0, 0].set_title('座標距離差距分佈')
        axes[0, 0].set_xlabel('距離 (公尺)')
        axes[0, 0].set_ylabel('測站數量')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 距離差距箱型圖
        axes[0, 1].boxplot(df[distance_col], patch_artist=True,
                          boxprops=dict(facecolor=self.color_palette['connection'], alpha=0.7))
        axes[0, 1].set_title('座標距離差距箱型圖')
        axes[0, 1].set_ylabel('距離 (公尺)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 緯度差距分佈
        axes[0, 2].hist(df[lat_diff_col] * 111000, bins=30, alpha=0.7,
                       color=self.color_palette['wgs84'], edgecolor='black')
        axes[0, 2].set_title('緯度差距分佈')
        axes[0, 2].set_xlabel('緯度差距 (公尺)')
        axes[0, 2].set_ylabel('測站數量')
        axes[0, 2].grid(True, alpha=0.3)
        
        # 4. 經度差距分佈
        axes[1, 0].hist(df[lon_diff_col] * 111000, bins=30, alpha=0.7,
                       color=self.color_palette['twd97'], edgecolor='black')
        axes[1, 0].set_title('經度差距分佈')
        axes[1, 0].set_xlabel('經度差距 (公尺)')
        axes[1, 0].set_ylabel('測站數量')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 5. 散點圖比較
        axes[1, 1].scatter(df[f'{lon_diff_col}_1'], df[f'{lat_diff_col}_1'], 
                          alpha=0.7, label='系統1', color=self.color_palette['wgs84'], s=50)
        axes[1, 1].scatter(df[f'{lon_diff_col}_2'], df[f'{lat_diff_col}_2'], 
                          alpha=0.7, label='系統2', color=self.color_palette['twd97'], s=50)
        axes[1, 1].set_title('座標分佈比較')
        axes[1, 1].set_xlabel('經度')
        axes[1, 1].set_ylabel('緯度')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        # 6. 距離差距統計摘要
        stats_text = f"""
        統計摘要:
        總測站數: {len(df)}
        平均距離: {df[distance_col].mean():.2f} 公尺
        中位數距離: {df[distance_col].median():.2f} 公尺
        標準差: {df[distance_col].std():.2f} 公尺
        最小距離: {df[distance_col].min():.2f} 公尺
        最大距離: {df[distance_col].max():.2f} 公尺
        """
        axes[1, 2].text(0.1, 0.5, stats_text, transform=axes[1, 2].transAxes,
                        fontsize=12, verticalalignment='center',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        axes[1, 2].set_title('統計摘要')
        axes[1, 2].axis('off')
        
        plt.tight_layout()
        return fig
    
    def create_plotly_dashboard(self, df, lat_col1, lon_col1, lat_col2, lon_col2,
                               station_col, distance_col):
        """
        創建Plotly互動式儀表板
        
        Args:
            df: 包含座標資料的DataFrame
            lat_col1, lon_col1: 第一組座標欄位
            lat_col2, lon_col2: 第二組座標欄位
            station_col: 測站名稱欄位
            distance_col: 距離欄位名稱
        
        Returns:
            plotly.graph_objects.Figure: 互動式圖表
        """
        # 創建子圖
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('座標分佈圖', '距離差距分佈', '距離差距箱型圖', '統計摘要'),
            specs=[[{"type": "scatter"}, {"type": "histogram"}],
                   [{"type": "box"}, {"type": "table"}]]
        )
        
        # 1. 座標分佈圖
        fig.add_trace(
            go.Scatter(
                x=df[lon_col1], y=df[lat_col1],
                mode='markers',
                name='系統1',
                marker=dict(color='blue', size=8),
                text=df[station_col],
                hovertemplate='<b>%{text}</b><br>經度: %{x:.6f}<br>緯度: %{y:.6f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df[lon_col2], y=df[lat_col2],
                mode='markers',
                name='系統2',
                marker=dict(color='red', size=8),
                text=df[station_col],
                hovertemplate='<b>%{text}</b><br>經度: %{x:.6f}<br>緯度: %{y:.6f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. 距離差距分佈
        fig.add_trace(
            go.Histogram(
                x=df[distance_col],
                nbinsx=30,
                name='距離差距',
                marker_color='green',
                opacity=0.7
            ),
            row=1, col=2
        )
        
        # 3. 距離差距箱型圖
        fig.add_trace(
            go.Box(
                y=df[distance_col],
                name='距離差距',
                marker_color='orange'
            ),
            row=2, col=1
        )
        
        # 4. 統計摘要表格
        stats_data = [
            ['總測站數', len(df)],
            ['平均距離', f'{df[distance_col].mean():.2f} 公尺'],
            ['中位數距離', f'{df[distance_col].median():.2f} 公尺'],
            ['標準差', f'{df[distance_col].std():.2f} 公尺'],
            ['最小距離', f'{df[distance_col].min():.2f} 公尺'],
            ['最大距離', f'{df[distance_col].max():.2f} 公尺']
        ]
        
        fig.add_trace(
            go.Table(
                header=dict(values=['統計項', '數值'],
                           fill_color='lightblue',
                           align='left'),
                cells=dict(values=list(zip(*stats_data)),
                          fill_color='white',
                          align='left')
            ),
            row=2, col=2
        )
        
        # 更新佈局
        fig.update_layout(
            title_text='氣象站座標系統比較分析儀表板',
            height=800,
            showlegend=True
        )
        
        # 更新子圖標題
        fig.update_xaxes(title_text="經度", row=1, col=1)
        fig.update_yaxes(title_text="緯度", row=1, col=1)
        fig.update_xaxes(title_text="距離 (公尺)", row=1, col=2)
        fig.update_xaxes(title_text="統計項", row=2, col=2)
        fig.update_yaxes(title_text="距離 (公尺)", row=2, col=1)
        
        return fig
    
    def create_heatmap(self, df, lat_col, lon_col, value_col, title="座標熱力圖"):
        """
        創建熱力圖
        
        Args:
            df: 包含座標資料的DataFrame
            lat_col: 緯度欄位名稱
            lon_col: 經度欄位名稱
            value_col: 數值欄位名稱
            title: 圖表標題
        
        Returns:
            folium.Map: 熱力圖地圖
        """
        # 計算地圖中心點
        center_lat = df[lat_col].mean()
        center_lon = df[lon_col].mean()
        
        # 建立地圖
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # 準備熱力圖資料
        heat_data = [[row[lat_col], row[lon_col], row[value_col]] 
                    for idx, row in df.iterrows()]
        
        # 添加熱力圖
        from folium.plugins import HeatMap
        HeatMap(
            heat_data,
            min_opacity=0.2,
            radius=25,
            blur=15,
            gradient={0.4: 'blue', 0.6: 'cyan', 0.8: 'lime', 1: 'red'}
        ).add_to(m)
        
        # 添加標題
        title_html = f'''
        <h3 align="center" style="font-size:16px"><b>{title}</b></h3>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        return m
    
    def save_visualizations(self, map_obj, fig, dashboard, output_dir='output'):
        """
        保存視覺化結果
        
        Args:
            map_obj: 互動式地圖物件
            fig: 統計圖表物件
            dashboard: Plotly儀表板物件
            output_dir: 輸出目錄
        """
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存互動式地圖
        if map_obj:
            map_obj.save(f'{output_dir}/interactive_map.html')
            print(f"互動式地圖已保存: {output_dir}/interactive_map.html")
        
        # 保存統計圖表
        if fig:
            fig.savefig(f'{output_dir}/statistical_plots.png', 
                       dpi=300, bbox_inches='tight')
            print(f"統計圖表已保存: {output_dir}/statistical_plots.png")
        
        # 保存Plotly儀表板
        if dashboard:
            dashboard.write_html(f'{output_dir}/dashboard.html')
            print(f"互動式儀表板已保存: {output_dir}/dashboard.html")
            
            # 同時保存為靜態圖片
            dashboard.write_image(f'{output_dir}/dashboard.png', 
                                width=1200, height=800, scale=2)
            print(f"儀表板圖片已保存: {output_dir}/dashboard.png")

# 使用範例
if __name__ == "__main__":
    # 創建範例資料
    np.random.seed(42)
    n_stations = 50
    
    data = {
        'station_name': [f'測站_{i}' for i in range(n_stations)],
        'coord1_lat': np.random.uniform(22, 25, n_stations),
        'coord1_lon': np.random.uniform(120, 122, n_stations),
        'coord2_lat': np.random.uniform(22, 25, n_stations),
        'coord2_lon': np.random.uniform(120, 122, n_stations),
        'distance_m': np.random.uniform(10, 500, n_stations),
        'lat_diff': np.random.uniform(0, 0.01, n_stations),
        'lon_diff': np.random.uniform(0, 0.01, n_stations)
    }
    
    df = pd.DataFrame(data)
    
    # 創建視覺化
    visualizer = CoordinateVisualizer()
    
    # 創建互動式地圖
    map_obj = visualizer.create_interactive_map(
        df, 'coord1_lat', 'coord1_lon', 'coord2_lat', 'coord2_lon',
        'station_name', 'WGS84', 'TWD97'
    )
    
    # 創建統計圖表
    fig = visualizer.create_statistical_plots(
        df, 'distance_m', 'lat_diff', 'lon_diff'
    )
    
    # 創建儀表板
    dashboard = visualizer.create_plotly_dashboard(
        df, 'coord1_lat', 'coord1_lon', 'coord2_lat', 'coord2_lon',
        'station_name', 'distance_m'
    )
    
    # 保存結果
    visualizer.save_visualizations(map_obj, fig, dashboard)
    
    print("視覺化範例完成！")

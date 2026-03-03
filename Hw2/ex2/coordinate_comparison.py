#!/usr/bin/env python3
"""
座標系統比較模組
提供各種座標系統轉換和比較功能
"""

import numpy as np
import pandas as pd
from geopy.distance import geodesic
import math

class CoordinateComparator:
    def __init__(self):
        self.supported_systems = ['WGS84', 'TWD97', 'TWD67']
        
    def twd97_to_wgs84(self, x, y):
        """
        TWD97座標轉WGS84
        使用精確的轉換公式
        """
        # TWD97參數
        a = 6378137.0  # WGS84長半徑
        b = 6356752.314245  # WGS84短半徑
        e2 = (a*a - b*b) / (a*a)
        
        # TWD97投影參數
        k0 = 0.9999  # 尺度比例
        lon0 = math.radians(121)  # 中央經線
        lat0 = 0  # 原點緯度
        east0 = 250000  # 東偏移
        north0 = 0  # 北偏移
        
        # 反投影計算
        dx = x - east0
        dy = y - north0
        
        # 計算經度
        M = dy / k0
        mu = M / (a * (1 - e2/4 - 3*e2**2/64 - 5*e2**3/256))
        
        e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
        
        J1 = 3*e1/2 - 27*e1**3/32
        J2 = 21*e1**2/16 - 55*e1**4/32
        J3 = 151*e1**3/96
        J4 = 1097*e1**4/512
        
        lat = mu + J1*math.sin(2*mu) + J2*math.sin(4*mu) + J3*math.sin(6*mu) + J4*math.sin(8*mu)
        
        N1 = a / math.sqrt(1 - e2 * math.sin(lat)**2)
        T1 = math.tan(lat)**2
        C1 = e2 * math.cos(lat)**2 / (1 - e2)
        R1 = a * (1 - e2) / (1 - e2 * math.sin(lat)**2)**1.5
        
        dlat = -math.tan(lat) * dx**2 / (2 * R1 * N1 * k0**2)
        dlon = dx / (N1 * k0 * math.cos(lat))
        
        lat = lat + dlat
        lon = lon0 + dlon
        
        return math.degrees(lat), math.degrees(lon)
    
    def wgs84_to_twd97(self, lat, lon):
        """
        WGS84座標轉TWD97
        """
        # TWD97參數
        a = 6378137.0
        b = 6356752.314245
        e2 = (a*a - b*b) / (a*a)
        
        k0 = 0.9999
        lon0 = math.radians(121)
        lat0 = 0
        east0 = 250000
        north0 = 0
        
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        # 計算子午線弧長
        M = a * ((1 - e2/4 - 3*e2**2/64 - 5*e2**3/256) * lat_rad - 
                 (3*e2/8 + 3*e2**2/32 + 45*e2**3/1024) * math.sin(2*lat_rad) +
                 (15*e2**2/256 + 45*e2**3/1024) * math.sin(4*lat_rad) -
                 (35*e2**3/3072) * math.sin(6*lat_rad))
        
        N = a / math.sqrt(1 - e2 * math.sin(lat_rad)**2)
        T = math.tan(lat_rad)**2
        C = e2 * math.cos(lat_rad)**2 / (1 - e2)
        A = (lon_rad - lon0) * math.cos(lat_rad)
        
        # 計算平面座標
        x = east0 + k0 * N * (A + (1 - T + C) * A**3/6 + 
                              (5 - 18*T + T**2 + 72*C - 58*e2) * A**5/120)
        
        y = north0 + k0 * (M + N * math.tan(lat_rad) * 
                           (A**2/2 + (5 - T + 9*C + 4*C**2) * A**4/24 +
                            (61 - 58*T + T**2 + 600*C - 330*e2) * A**6/720))
        
        return x, y
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """計算兩點間距離"""
        return geodesic((lat1, lon1), (lat2, lon2)).meters
    
    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """計算兩點間方位角"""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def compare_coordinates(self, coord1, coord2, system1="WGS84", system2="WGS84"):
        """
        比較兩組座標
        
        Args:
            coord1: (lat, lon) 第一組座標
            coord2: (lat, lon) 第二組座標
            system1: 第一組座標系統
            system2: 第二組座標系統
        
        Returns:
            dict: 比較結果
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # 計算距離
        distance = self.calculate_distance(lat1, lon1, lat2, lon2)
        
        # 計算方位角
        bearing = self.calculate_bearing(lat1, lon1, lat2, lon2)
        
        # 計算座標差異
        lat_diff = abs(lat1 - lat2)
        lon_diff = abs(lon1 - lon2)
        
        # 轉換為公尺
        lat_diff_m = lat_diff * 111320  # 1度緯度約111320公尺
        lon_diff_m = lon_diff * 111320 * math.cos(math.radians((lat1 + lat2) / 2))
        
        return {
            'distance_m': distance,
            'bearing_deg': bearing,
            'lat_diff_deg': lat_diff,
            'lon_diff_deg': lon_diff,
            'lat_diff_m': lat_diff_m,
            'lon_diff_m': lon_diff_m,
            'system1': system1,
            'system2': system2
        }
    
    def batch_compare(self, df, lat_col1, lon_col1, lat_col2, lon_col2, 
                     system1="WGS84", system2="WGS84"):
        """
        批量比較座標
        
        Args:
            df: DataFrame
            lat_col1, lon_col1: 第一組座標欄位名稱
            lat_col2, lon_col2: 第二組座標欄位名稱
            system1, system2: 座標系統名稱
        
        Returns:
            DataFrame: 比較結果
        """
        results = []
        
        for idx, row in df.iterrows():
            coord1 = (row[lat_col1], row[lon_col1])
            coord2 = (row[lat_col2], row[lon_col2])
            
            comparison = self.compare_coordinates(coord1, coord2, system1, system2)
            comparison['index'] = idx
            
            # 添加原始資料
            for col in df.columns:
                if col not in comparison:
                    comparison[f'original_{col}'] = row[col]
            
            results.append(comparison)
        
        return pd.DataFrame(results)
    
    def analyze_coordinate_differences(self, comparison_df):
        """
        分析座標差異統計
        
        Args:
            comparison_df: 比較結果DataFrame
        
        Returns:
            dict: 統計分析結果
        """
        distance_stats = {
            'mean': comparison_df['distance_m'].mean(),
            'median': comparison_df['distance_m'].median(),
            'std': comparison_df['distance_m'].std(),
            'min': comparison_df['distance_m'].min(),
            'max': comparison_df['distance_m'].max(),
            'q25': comparison_df['distance_m'].quantile(0.25),
            'q75': comparison_df['distance_m'].quantile(0.75)
        }
        
        bearing_stats = {
            'mean': comparison_df['bearing_deg'].mean(),
            'std': comparison_df['bearing_deg'].std(),
            'min': comparison_df['bearing_deg'].min(),
            'max': comparison_df['bearing_deg'].max()
        }
        
        lat_diff_stats = {
            'mean_m': comparison_df['lat_diff_m'].mean(),
            'std_m': comparison_df['lat_diff_m'].std(),
            'mean_deg': comparison_df['lat_diff_deg'].mean(),
            'std_deg': comparison_df['lat_diff_deg'].std()
        }
        
        lon_diff_stats = {
            'mean_m': comparison_df['lon_diff_m'].mean(),
            'std_m': comparison_df['lon_diff_m'].std(),
            'mean_deg': comparison_df['lon_diff_deg'].mean(),
            'std_deg': comparison_df['lon_diff_deg'].std()
        }
        
        # 分類距離差距
        distance_categories = {
            'small': (comparison_df['distance_m'] < 10).sum(),
            'medium': ((comparison_df['distance_m'] >= 10) & (comparison_df['distance_m'] < 100)).sum(),
            'large': ((comparison_df['distance_m'] >= 100) & (comparison_df['distance_m'] < 1000)).sum(),
            'very_large': (comparison_df['distance_m'] >= 1000).sum()
        }
        
        return {
            'total_points': len(comparison_df),
            'distance_stats': distance_stats,
            'bearing_stats': bearing_stats,
            'lat_diff_stats': lat_diff_stats,
            'lon_diff_stats': lon_diff_stats,
            'distance_categories': distance_categories
        }
    
    def generate_report(self, analysis_results):
        """
        生成分析報告
        
        Args:
            analysis_results: 分析結果字典
        
        Returns:
            str: 報告文字
        """
        report = []
        report.append("=" * 60)
        report.append("座標系統比較分析報告")
        report.append("=" * 60)
        
        # 基本統計
        report.append(f"分析點數: {analysis_results['total_points']}")
        report.append("")
        
        # 距離統計
        dist_stats = analysis_results['distance_stats']
        report.append("距離差距統計:")
        report.append(f"  平均距離: {dist_stats['mean']:.2f} 公尺")
        report.append(f"  中位數距離: {dist_stats['median']:.2f} 公尺")
        report.append(f"  標準差: {dist_stats['std']:.2f} 公尺")
        report.append(f"  最小距離: {dist_stats['min']:.2f} 公尺")
        report.append(f"  最大距離: {dist_stats['max']:.2f} 公尺")
        report.append(f"  25%分位數: {dist_stats['q25']:.2f} 公尺")
        report.append(f"  75%分位數: {dist_stats['q75']:.2f} 公尺")
        report.append("")
        
        # 方位角統計
        bear_stats = analysis_results['bearing_stats']
        report.append("方位角統計:")
        report.append(f"  平均方位角: {bear_stats['mean']:.2f}°")
        report.append(f"  標準差: {bear_stats['std']:.2f}°")
        report.append(f"  範圍: {bear_stats['min']:.2f}° - {bear_stats['max']:.2f}°")
        report.append("")
        
        # 座標差異統計
        lat_stats = analysis_results['lat_diff_stats']
        lon_stats = analysis_results['lon_diff_stats']
        report.append("座標差異統計:")
        report.append(f"  緯度差距平均: {lat_stats['mean_m']:.2f} 公尺 ({lat_stats['mean_deg']:.8f}°)")
        report.append(f"  經度差距平均: {lon_stats['mean_m']:.2f} 公尺 ({lon_stats['mean_deg']:.8f}°)")
        report.append("")
        
        # 距離分類
        categories = analysis_results['distance_categories']
        report.append("距離差距分類:")
        report.append(f"  小於10公尺: {categories['small']} 點 ({categories['small']/analysis_results['total_points']*100:.1f}%)")
        report.append(f"  10-100公尺: {categories['medium']} 點 ({categories['medium']/analysis_results['total_points']*100:.1f}%)")
        report.append(f"  100-1000公尺: {categories['large']} 點 ({categories['large']/analysis_results['total_points']*100:.1f}%)")
        report.append(f"  大於1000公尺: {categories['very_large']} 點 ({categories['very_large']/analysis_results['total_points']*100:.1f}%)")
        report.append("")
        
        # 建議
        report.append("建議:")
        if dist_stats['mean'] > 100:
            report.append("  ⚠️  平均距離差距較大，建議檢查座標系統轉換")
        if dist_stats['std'] > 50:
            report.append("  ⚠️  距離差距變異較大，建議檢查資料品質")
        if categories['very_large'] > 0:
            report.append("  ⚠️  存在極大距離差距，建議檢查異常值")
        
        return "\n".join(report)

# 使用範例
if __name__ == "__main__":
    comparator = CoordinateComparator()
    
    # 測試座標轉換
    lat, lon = 25.0375, 121.5625  # 台北車站
    x, y = comparator.wgs84_to_twd97(lat, lon)
    lat_back, lon_back = comparator.twd97_to_wgs84(x, y)
    
    print(f"原始WGS84: ({lat}, {lon})")
    print(f"TWD97: ({x:.2f}, {y:.2f})")
    print(f"轉回WGS84: ({lat_back:.8f}, {lon_back:.8f})")
    
    # 測試距離計算
    distance = comparator.calculate_distance(lat, lon, lat_back, lon_back)
    print(f"轉換誤差: {distance:.4f} 公尺")

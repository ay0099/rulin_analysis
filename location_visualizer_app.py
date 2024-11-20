import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re
from collections import defaultdict
from pathlib import Path
import plotly.express as px

class LocationAnalyzer:
    def __init__(self):
        self.location_mapping = {
            '南京': ['金陵', '建康'],
            '蘇州': ['姑蘇'],
            '杭州': ['西湖'],
            '北京': ['京城', '燕京'],
            '揚州': ['揚子', '瘦西湖'],
            '濟南': ['泉城'],
            '湖州': ['吳興']
        }
        
        # 添加地理坐标
        self.coordinates = {
            '南京': [32.0584, 118.7965],
            '蘇州': [31.2989, 120.5853],
            '杭州': [30.2741, 120.1551],
            '北京': [39.9042, 116.4074],
            '揚州': [32.3947, 119.4142],
            '濟南': [36.6512, 117.1201],
            '湖州': [30.8940, 120.0868]
        }
        
        self.chapter_data = defaultdict(lambda: defaultdict(int))
        self.location_contexts = defaultdict(list)

    def analyze_file(self, file_path, chapter_num):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for main_location, aliases in self.location_mapping.items():
                    # 统计主要地名
                    main_count = len(re.findall(main_location, content))
                    self.chapter_data[chapter_num][main_location] += main_count
                    
                    # 记录上下文
                    for match in re.finditer(main_location, content):
                        context = content[max(0, match.start()-30):min(len(content), match.end()+30)]
                        self.location_contexts[main_location].append({
                            'chapter': chapter_num,
                            'context': context.strip(),
                            'term': main_location
                        })
                    
                    # 统计别称
                    for alias in aliases:
                        alias_count = len(re.findall(alias, content))
                        self.chapter_data[chapter_num][main_location] += alias_count
                        
                        # 记录别称上下文
                        for match in re.finditer(alias, content):
                            context = content[max(0, match.start()-30):min(len(content), match.end()+30)]
                            self.location_contexts[main_location].append({
                                'chapter': chapter_num,
                                'context': context.strip(),
                                'term': alias
                            })
            
            return True
        except Exception as e:
            st.error(f"处理第{chapter_num}章时出错：{str(e)}")
            return False

    def create_map(self):
        m = folium.Map(location=[35.0, 105.0], zoom_start=5, tiles="CartoDB positron")
        
        # 计算总频次
        total_counts = defaultdict(int)
        for chapter_counts in self.chapter_data.values():
            for location, count in chapter_counts.items():
                total_counts[location] += count
        
        # 添加地点标记
        for location, coords in self.coordinates.items():
            count = total_counts[location]
            if count > 0:
                folium.CircleMarker(
                    location=coords,
                    radius=count * 2,
                    popup=f"<b>{location}</b><br>出现次数：{count}次",
                    color='red',
                    fill=True,
                    fill_color='red',
                    fill_opacity=0.7
                ).add_to(m)
        
        return m

    def get_frequency_data(self):
        # 准备频次数据
        data = []
        for chapter_num, counts in self.chapter_data.items():
            for location, count in counts.items():
                if count > 0:
                    data.append({
                        '章节': f'第{chapter_num}章',
                        '地名': location,
                        '出现次数': count
                    })
        return pd.DataFrame(data)

def main():
    st.set_page_config(page_title="儒林外史地名分析", layout="wide")
    
    st.title('《儒林外史》地名分析可视化')
    
    analyzer = LocationAnalyzer()
    
    # 分析文本
    base_path = Path('/Users/anthony/Desktop/CHC5904/Assignment2/儒林外史')
    with st.spinner('正在分析文本...'):
        for chapter_num in range(10, 21):
            file_path = base_path / f'chapter{chapter_num}.txt'
            analyzer.analyze_file(file_path, chapter_num)
    
    # 创建两列布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader('地名出现频次地图')
        m = analyzer.create_map()
        # 使用新的 st_folium
        st_folium(m, width=700, height=500)
    
    with col2:
        st.subheader('频次统计')
        freq_df = analyzer.get_frequency_data()
        total_by_location = freq_df.groupby('地名')['出现次数'].sum().sort_values(ascending=False)
        st.write("总体出现次数：")
        st.dataframe(total_by_location)
    
    # 显示详细统计图表
    st.subheader('各章节地名分布')
    fig = px.bar(freq_df, 
                 x='地名', 
                 y='出现次数',
                 color='章节',
                 title='各章节地名出现频次',
                 barmode='group')
    st.plotly_chart(fig, use_container_width=True)
    
    # 添加交互式上下文查看器
    st.subheader('地名上下文查看')
    selected_location = st.selectbox('选择地名', list(analyzer.location_mapping.keys()))
    
    if selected_location:
        contexts = analyzer.location_contexts[selected_location]
        for context in contexts:
            with st.expander(f"第{context['chapter']}章 - {context['term']}"):
                st.write(context['context'])

if __name__ == "__main__":
    main() 
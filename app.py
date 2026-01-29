import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json

# 페이지 설정
st.set_page_config(
    page_title="Trade Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .status-complete {
        background-color: #4CAF50;
        color: white;
        padding: 8px 16px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-progress {
        background-color: #4CAF50;
        color: white;
        padding: 8px 16px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-waiting {
        background-color: #e0e0e0;
        color: #666;
        padding: 8px 16px;
        border-radius: 50%;
        display: inline-block;
    }
    .deadline-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Mock 데이터 생성 함수들
def get_trade_progress():
    return {
        "stages": [
            {"name": "Q1 Planning", "status": "Completed", "progress": 100},
            {"name": "Q2 Execution", "status": "Completed", "progress": 100},
            {"name": "Q3 Analysis", "status": "In Progress", "progress": 67},
            {"name": "Q4 Forecast", "status": "Waiting", "progress": 0}
        ],
        "launch_date": "2026-12-15",
        "days_remaining": 320
    }

def get_trade_budget():
    return {
        "total": 52000000,
        "used": 43230000,
        "remaining": 8770000,
        "categories": {
            "Export Operations": 15000000,
            "Import Management": 18500000,
            "Logistics": 9730000
        }
    }

def get_overdue_shipments():
    return pd.DataFrame({
        "Overdue": ["1 Day", "4 Days", "10 Days", "24 Days"],
        "Shipment": ["Electronics to USA", "Textiles to EU", "Auto Parts to Japan", "Machinery to China"],
        "Deadline": ["2026-01-28", "2026-01-25", "2026-01-19", "2026-01-05"],
        "Partner": ["TechCorp", "FashionHub", "AutoLink", "IndustrialCo"]
    })

def get_trade_volume_by_region():
    return pd.DataFrame({
        "Region": ["Asia", "Europe", "Americas", "Middle East", "Africa"],
        "Volume": [67.5, 65.3, 48.7, 45.2, 30.1]
    })

def get_upcoming_deadlines():
    return pd.DataFrame({
        "Partner": ["TechCorp", "FashionHub", "AutoLink", "IndustrialCo"],
        "Shipment": ["Consumer Electronics", "Winter Collection", "Engine Components", "Heavy Machinery"],
        "Deadline": ["2026-02-15", "2026-02-06", "2026-02-01", "2026-02-18"],
        "Status": ["34%", "56%", "15%", "11%"]
    })

def get_world_trade_data():
    """세계 무역 지도용 데이터"""
    return pd.DataFrame({
        "Country": ["USA", "China", "Germany", "Japan", "UK", "France", "India", "Italy", "Canada", "South Korea"],
        "Trade_Volume": [450, 520, 380, 290, 210, 195, 180, 165, 145, 135],
        "Lat": [37.09, 35.86, 51.16, 36.20, 55.37, 46.22, 20.59, 41.87, 56.13, 37.56],
        "Lon": [-95.71, 104.19, 10.45, 138.25, -3.43, 2.21, 78.96, 12.56, -106.34, 126.97]
    })

def get_trade_by_category():
    """품목별 무역 비중 데이터"""
    return pd.DataFrame({
        "Category": ["Electronics", "Machinery", "Automotive", "Textiles", "Chemicals", "Food"],
        "Value": [23, 19, 15, 12, 18, 13]
    })

# 사이드바
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/4CAF50/FFFFFF?text=Trade+Dashboard", use_container_width=True)
    st.markdown("---")
    
    menu = st.radio(
        "📑 Menu",
        ["📊 Overview", "🌍 Global Trade Map", "📈 Trade Analysis", "🌐 Live Trade Globe"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 🔔 Quick Stats")
    st.metric("Total Trade Volume", "$52B", "+12.5%")
    st.metric("Active Partners", "247", "+18")
    st.metric("Pending Shipments", "42", "-5")

# 메인 컨텐츠
if menu == "📊 Overview":
    # 상단 진행 상황
    progress_data = get_trade_progress()
    
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1.5])
    
    stages = progress_data["stages"]
    for idx, col in enumerate([col1, col2, col3, col4]):
        if idx < len(stages):
            stage = stages[idx]
            with col:
                if stage["status"] == "Completed":
                    st.markdown(f"""
                    <div style='text-align: center;'>
                        <div class='status-complete'>✓</div>
                        <p style='margin-top: 10px; font-weight: bold;'>{stage['name']}</p>
                        <p style='color: #666; font-size: 0.85rem;'>Completed</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif stage["status"] == "In Progress":
                    st.markdown(f"""
                    <div style='text-align: center;'>
                        <div class='status-progress'>{stage['progress']}%</div>
                        <p style='margin-top: 10px; font-weight: bold;'>{stage['name']}</p>
                        <p style='color: #666; font-size: 0.85rem;'>In Progress</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='text-align: center;'>
                        <div class='status-waiting'>⏱</div>
                        <p style='margin-top: 10px; font-weight: bold;'>{stage['name']}</p>
                        <p style='color: #666; font-size: 0.85rem;'>Waiting</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class='deadline-box'>
            <p style='font-weight: bold; margin: 0;'>Projected Year End</p>
            <p style='font-size: 1.5rem; margin: 10px 0; font-weight: bold;'>{progress_data['days_remaining']} Days</p>
            <p style='color: #666; font-size: 0.85rem; margin: 0;'>{progress_data['launch_date']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 중간 섹션
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Trade Budget")
        budget_data = get_trade_budget()
        
        # 막대 그래프
        fig = go.Figure()
        
        categories = list(budget_data["categories"].keys())
        values = list(budget_data["categories"].values())
        
        fig.add_trace(go.Bar(
            x=categories,
            y=values,
            marker_color=['#4CAF50', '#66BB6A', '#A5D6A7'],
            text=[f"${v/1000000:.1f}M" for v in values],
            textposition='outside'
        ))
        
        fig.update_layout(
            height=300,
            showlegend=False,
            yaxis_title="Amount (Million USD)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total Budget", f"${budget_data['total']/1000000:.0f}M")
        col_b.metric("Remaining", f"${budget_data['remaining']/1000000:.1f}M")
        col_c.metric("Currently", "83%", delta="-17% Over Target", delta_color="inverse")
    
    with col2:
        st.subheader("⚠️ Overdue Shipments")
        overdue_df = get_overdue_shipments()
        
        # 스타일링된 테이블
        def color_overdue(val):
            if "Day" in str(val):
                days = int(val.split()[0])
                if days == 1:
                    return 'background-color: #FFF9C4'
                elif days <= 4:
                    return 'background-color: #FFE082'
                elif days <= 10:
                    return 'background-color: #FFAB91'
                else:
                    return 'background-color: #EF9A9A'
            return ''
        
        styled_df = overdue_df.style.applymap(color_overdue, subset=['Overdue'])
        st.dataframe(styled_df, use_container_width=True, height=280)
    
    st.markdown("---")
    
    # 하단 섹션
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Trade Volume by Region")
        volume_df = get_trade_volume_by_region()
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=volume_df["Region"],
            y=volume_df["Volume"],
            marker_color='#4CAF50',
            text=volume_df["Volume"].apply(lambda x: f"{x}%"),
            textposition='outside'
        ))
        
        fig.update_layout(
            height=300,
            showlegend=False,
            yaxis_title="Volume (%)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📅 Upcoming Deadlines")
        deadlines_df = get_upcoming_deadlines()
        
        # 진행률 바 추가
        def make_progress_bar(val):
            percent = int(val.replace('%', ''))
            color = '#4CAF50' if percent > 50 else '#FF9800' if percent > 20 else '#F44336'
            return f"""
            <div style='width: 100%; background-color: #e0e0e0; border-radius: 4px;'>
                <div style='width: {percent}%; background-color: {color}; height: 20px; border-radius: 4px; text-align: center; color: white; font-size: 0.8rem; line-height: 20px;'>
                    {val}
                </div>
            </div>
            """
        
        for idx, row in deadlines_df.iterrows():
            st.markdown(f"**{row['Partner']}** - {row['Shipment']}")
            st.markdown(f"Deadline: {row['Deadline']}")
            st.markdown(make_progress_bar(row['Status']), unsafe_allow_html=True)
            st.markdown("---")

elif menu == "🌍 Global Trade Map":
    st.markdown("<h1 class='main-header'>🌍 Global Trade Map</h1>", unsafe_allow_html=True)
    
    trade_data = get_world_trade_data()
    
    # 세계 지도에 무역 데이터 표시
    fig = go.Figure()
    
    fig.add_trace(go.Scattergeo(
        lon=trade_data['Lon'],
        lat=trade_data['Lat'],
        text=trade_data['Country'] + '<br>Trade: $' + trade_data['Trade_Volume'].astype(str) + 'B',
        mode='markers',
        marker=dict(
            size=trade_data['Trade_Volume'] / 10,
            color=trade_data['Trade_Volume'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Trade Volume<br>(Billion USD)"),
            line=dict(width=1, color='white')
        )
    ))
    
    fig.update_layout(
        title='Global Trade Volume by Country',
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(230, 245, 255)',
        ),
        height=700
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 하단 통계
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Countries", len(trade_data), "+5 YoY")
    col2.metric("Total Trade", f"${trade_data['Trade_Volume'].sum()}B", "+8.2%")
    col3.metric("Avg per Country", f"${trade_data['Trade_Volume'].mean():.1f}B", "+3.1%")
    col4.metric("Top Trader", trade_data.loc[trade_data['Trade_Volume'].idxmax(), 'Country'], "China")

elif menu == "📈 Trade Analysis":
    st.markdown("<h1 class='main-header'>📈 Trade Analysis by Category</h1>", unsafe_allow_html=True)
    
    category_data = get_trade_by_category()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 방사형 차트 (Polar Chart)
        fig = go.Figure()
        
        fig.add_trace(go.Barpolar(
            r=category_data['Value'],
            theta=category_data['Category'],
            marker_color=px.colors.sequential.Viridis,
            marker_line_color="white",
            marker_line_width=2,
            opacity=0.8
        ))
        
        fig.update_layout(
            title="Trade Distribution by Category (Radial View)",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(category_data['Value']) * 1.2]
                )
            ),
            showlegend=False,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 파이 차트
        fig = go.Figure()
        
        fig.add_trace(go.Pie(
            labels=category_data['Category'],
            values=category_data['Value'],
            hole=0.4,
            marker=dict(colors=px.colors.sequential.Viridis)
        ))
        
        fig.update_layout(
            title="Trade Share by Category",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 하단 테이블
    st.subheader("📊 Detailed Breakdown")
    
    detailed_df = category_data.copy()
    detailed_df['Percentage'] = (detailed_df['Value'] / detailed_df['Value'].sum() * 100).round(1).astype(str) + '%'
    detailed_df['Value (Billion)'] = detailed_df['Value'].apply(lambda x: f"${x}B")
    
    st.dataframe(
        detailed_df[['Category', 'Value (Billion)', 'Percentage']],
        use_container_width=True,
        height=300
    )

elif menu == "🌐 Live Trade Globe":
    st.markdown("<h1 class='main-header'>🌐 Live Trade Activity Globe</h1>", unsafe_allow_html=True)
    
    st.info("🔄 This view shows real-time trade activities across the globe. Click on markers to see details.")
    
    trade_data = get_world_trade_data()
    
    # 3D 지구본 스타일 맵
    fig = go.Figure()
    
    fig.add_trace(go.Scattergeo(
        lon=trade_data['Lon'],
        lat=trade_data['Lat'],
        text=trade_data['Country'],
        mode='markers+text',
        marker=dict(
            size=trade_data['Trade_Volume'] / 8,
            color=trade_data['Trade_Volume'],
            colorscale='Plasma',
            showscale=True,
            colorbar=dict(title="Trade Volume"),
            line=dict(width=2, color='white')
        ),
        textposition="top center"
    ))
    
    fig.update_layout(
        title='Live Global Trade Activity',
        geo=dict(
            projection_type='orthographic',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            countrycolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(0, 0, 50)',
            showcountries=True,
            bgcolor='rgb(0, 0, 20)'
        ),
        height=700,
        paper_bgcolor='rgb(0, 0, 20)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 실시간 활동 로그
    st.subheader("📡 Recent Trade Activities")
    
    activity_df = pd.DataFrame({
        "Time": ["2 min ago", "5 min ago", "8 min ago", "12 min ago", "15 min ago"],
        "Activity": [
            "🚢 Shipment departed from Shanghai to Los Angeles",
            "✅ Container cleared customs in Rotterdam",
            "📦 New order placed: Electronics to Germany",
            "🚚 Delivery completed in Tokyo",
            "⚡ Urgent shipment requested: Medical supplies to India"
        ],
        "Status": ["In Transit", "Completed", "Processing", "Delivered", "Urgent"]
    })
    
    st.dataframe(activity_df, use_container_width=True, height=250)

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>Trade Dashboard v1.0 | Last Updated: {} | 📊 Data refreshes every 5 minutes</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)
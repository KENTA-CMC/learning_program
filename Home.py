import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Streamlit BI x Claude Code Starter", layout="wide")

st.title("Streamlit BI x Claude Code Starter")
@st.cache_data
def load_data():
    try:
        orders_df = pd.read_csv("sample_data/orders.csv")
        users_df = pd.read_csv("sample_data/users.csv")
        return orders_df, users_df
    except FileNotFoundError as e:
        st.error(f"データファイルが見つかりません: {e}")
        return None, None
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return None, None

@st.cache_data
def process_monthly_data(orders_df):
    if orders_df is None:
        return None
    
    # 日時データの前処理
    orders_df['created_at'] = pd.to_datetime(orders_df['created_at'])
    orders_df['year_month'] = orders_df['created_at'].dt.to_period('M').astype(str)
    
    # キャンセル判定
    orders_df['is_cancelled'] = orders_df['status'].isin(['Cancelled', 'Returned'])
    
    # 月別集計
    monthly_stats = orders_df.groupby('year_month').agg({
        'order_id': 'count',
        'is_cancelled': 'sum'
    }).reset_index()
    
    monthly_stats.columns = ['year_month', 'total_orders', 'cancelled_orders']
    monthly_stats['cancel_rate'] = (monthly_stats['cancelled_orders'] / monthly_stats['total_orders'] * 100).round(2)
    
    return monthly_stats

orders_df, users_df = load_data()

# 月別分析の追加
if orders_df is not None:
    st.header("📊 月別オーダー分析")
    
    monthly_data = process_monthly_data(orders_df)
    
    if monthly_data is not None:
        # 月別オーダー数の棒グラフ
        st.subheader("月別オーダー数推移")
        fig_orders = px.bar(
            monthly_data, 
            x='year_month', 
            y='total_orders',
            title='月別オーダー数推移',
            labels={'year_month': '年月', 'total_orders': 'オーダー数'}
        )
        fig_orders.update_layout(height=400)
        st.plotly_chart(fig_orders, use_container_width=True)
        
        # 月別キャンセル率の線グラフ
        st.subheader("月別キャンセル率推移")
        fig_cancel = px.line(
            monthly_data, 
            x='year_month', 
            y='cancel_rate',
            title='月別キャンセル率推移',
            labels={'year_month': '年月', 'cancel_rate': 'キャンセル率(%)'},
            markers=True
        )
        fig_cancel.update_layout(height=400)
        st.plotly_chart(fig_cancel, use_container_width=True)

st.header("Orders Data (Top 10 rows)")
st.dataframe(orders_df.head(10))

st.header("Users Data (Top 10 rows)")
st.dataframe(users_df.head(10))
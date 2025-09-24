import streamlit as st
import pandas as pd
import plotly.express as px

# アプリのタイトルと説明
st.title('Plotly基礎')
st.write('Plotlyを使ってインタラクティブなグラフを作成してみましょう！')

# CSVファイルを読み込む（dateをDatetimeに変換）
df = pd.read_csv('data/sample_sales.csv', parse_dates=['date'])

st.subheader('地域別・週次売上の推移（積み上げ棒グラフ・落ち着いた色）')

# 週毎×地域で売上を集計
weekly_region_revenue = (
    df.groupby([pd.Grouper(key='date', freq='W'), 'region'], as_index=False)['revenue']
      .sum()
      .sort_values('date')
)

# Plotlyで積み上げ棒グラフを作成（落ち着いた色を使用）
fig = px.bar(
    weekly_region_revenue,
    x='date',
    y='revenue',
    color='region',
    barmode='stack',
    color_discrete_sequence=px.colors.qualitative.Pastel,  # 落ち着いた色合いに変更
    title='地域別・週次売上の推移（積み上げ・Pastelカラー）',
    labels={'date': '週', 'revenue': '売上合計 (円)', 'region': '地域'},
    hover_data={'date': '|%Y-%m-%d', 'revenue': ':.0f'}
)

fig.update_layout(
    xaxis_title='週',
    yaxis_title='売上合計 (円)',
    legend_title='地域',
)

# Streamlitに表示
st.plotly_chart(fig, use_container_width=True)

st.write('---')
st.write('Pastelカラーで落ち着いた雰囲気の積み上げ棒グラフになっています。')

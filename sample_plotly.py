import streamlit as st
import pandas as pd
import plotly.express as px

st.title('Plotly基礎')
st.write('Plotlyを使ってインタラクティブなグラフを作成してみましょう！')

# まずは素で読み込む（parse_datesは使わない）
df = pd.read_csv('data/sample_sales.csv')

# 日付列を推定して処理：'date' 優先、なければ 'created_at' を使う
date_col = None
for cand in ['date', 'created_at', 'order_date']:
    if cand in df.columns:
        date_col = cand
        break

if date_col is None:
    st.error("CSVに日付列が見つかりませんでした。'date' か 'created_at'（または 'order_date'）の列を用意してください。")
    st.stop()

# 日付型に変換して標準名 'date' にそろえる
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
df = df.rename(columns={date_col: 'date'})

# 変換失敗（NaT）だけの行になっていないかチェック
if df['date'].isna().all():
    st.error(f"日付のパースに失敗しました。CSVの {date_col!r} 列のフォーマットを確認してください。")
    st.stop()

st.subheader('日毎の売上推移')

# 日ごとの売上合計を集計
if 'revenue' not in df.columns:
    st.error("CSVに 'revenue' 列がありません。売上金額の列名を 'revenue' にしてください。")
    st.stop()

daily_revenue = df.groupby('date', as_index=False)['revenue'].sum()

# 折れ線グラフ（線の色を赤）
fig = px.line(
    daily_revenue,
    x='date',
    y='revenue',
    title='日毎の売上推移',
    labels={'date': '日付', 'revenue': '売上 (円)'},
    line_shape='linear'
)
fig.update_traces(line_color='red')  # ←赤色

st.plotly_chart(fig, use_container_width=True)

st.write('---')
st.write('このグラフはインタラクティブです！日付にカーソルを合わせると、その日の正確な売上が表示されます。')

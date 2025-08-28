# -*- coding: utf-8 -*-
"""
販売データBIダッシュボード
- データ: data/sample_sales.csv
- 機能: 日付範囲フィルタ、KPI表示（売上合計・数量合計・カテゴリ数）、
        カテゴリ別売上の棒グラフ、日次売上の折れ線グラフ
- ルール: システムプロンプトのコード作成ルールに準拠
"""

import traceback
from typing import Tuple, Dict

import pandas as pd
import streamlit as st
import plotly.express as px

# ===== Section: Page Config =====
st.set_page_config(
    page_title="販売データBIダッシュボード",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== Section: Constants =====
CSV_PATH = "data/sample_sales.csv"
PRICE_MISMATCH_TOL = 1  # 円（units * unit_price と revenue の許容誤差）
DATE_COL = "date"

def _format_jpy(x: float) -> str:
    """円表記（千区切り、少数切り捨て）"""
    try:
        return f"¥{x:,.0f}"
    except Exception:
        return "—"

# ===== Section: Data Load =====
@st.cache_data(ttl=300)
def load_data(path: str) -> pd.DataFrame:
    """CSVを読み込み、型を整える"""
    df = pd.read_csv(
        path,
        parse_dates=[DATE_COL],
        dtype={
            "category": "string",
            "units": "Int64",
            "unit_price": "Int64",
            "region": "string",
            "sales_channel": "string",
            "customer_segment": "string",
            "revenue": "Int64",
        },
    )

    # category型に最適化（メモリと速度）
    cat_cols = ["category", "region", "sales_channel", "customer_segment"]
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype("category")

    # 明示的にソート
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    return df


def quality_checks(df: pd.DataFrame) -> Dict[str, int]:
    """簡易データ品質チェック"""
    issues = {}

    # 欠損・負値検知
    issues["missing_values"] = int(df.isna().sum().sum())
    neg_cols = ["units", "unit_price", "revenue"]
    if all(col in df.columns for col in neg_cols):
        issues["negative_values"] = int((df[neg_cols] < 0).sum().sum())
    else:
        issues["negative_values"] = 0

    # revenue ≈ units * unit_price
    if all(col in df.columns for col in ["units", "unit_price", "revenue"]):
        calc = (df["units"].astype("float") * df["unit_price"].astype("float")).round()
        mismatch = (calc - df["revenue"].astype("float")).abs() > PRICE_MISMATCH_TOL
        issues["price_mismatch_rows"] = int(mismatch.sum())
    else:
        issues["price_mismatch_rows"] = 0

    return issues


def build_sidebar_filters(df: pd.DataFrame) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """サイドバーの共通フィルタ（日付範囲）"""
    st.sidebar.header("フィルタ")

    min_d = df[DATE_COL].min().date() if not df.empty else None
    max_d = df[DATE_COL].max().date() if not df.empty else None

    # 日付範囲ピッカー
    date_range = st.sidebar.date_input(
        "期間（開始日・終了日）",
        value=(min_d, max_d) if min_d and max_d else (),
        min_value=min_d,
        max_value=max_d,
        format="YYYY-MM-DD",
    )

    # リセット
    if st.sidebar.button("リセット", use_container_width=True):
        st.session_state["date_input"] = (min_d, max_d)

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date, end_date = pd.to_datetime(min_d), pd.to_datetime(max_d)

    return start_date, end_date


def filter_df_by_date(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """日付範囲でフィルタ"""
    if df.empty:
        return df
    mask = (df[DATE_COL] >= start) & (df[DATE_COL] <= end)
    return df.loc[mask].copy()


def compute_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """KPI（売上合計、数量合計、カテゴリ数）"""
    total_revenue = float(df["revenue"].sum()) if "revenue" in df.columns else 0.0
    total_units = int(df["units"].sum()) if "units" in df.columns else 0
    n_categories = int(df["category"].nunique()) if "category" in df.columns else 0
    return {
        "total_revenue": total_revenue,
        "total_units": total_units,
        "n_categories": n_categories,
    }


# ===== Section: Main App =====
st.title("販売データBIダッシュボード")

try:
    df = load_data(CSV_PATH)
except FileNotFoundError:
    st.error("データファイルが見つかりませんでした: data/sample_sales.csv")
    st.stop()
except Exception as e:
    st.error("データ読み込み時にエラーが発生しました。")
    with st.expander("詳細（スタックトレース）"):
        st.code(traceback.format_exc())
    st.stop()

# 品質チェック（読み込み時点）
issues = quality_checks(df)
if issues.get("missing_values", 0) > 0 or issues.get("negative_values", 0) > 0 or issues.get("price_mismatch_rows", 0) > 0:
    st.warning(
        f"データ注意: 欠損={issues['missing_values']}件 / 負値={issues['negative_values']}件 / "
        f"金額不整合={issues['price_mismatch_rows']}件（許容誤差±{PRICE_MISMATCH_TOL}円）"
    )

# ===== Filters (Sidebar) =====
start, end = build_sidebar_filters(df)
df_f = filter_df_by_date(df, start, end)

# ===== Empty State =====
if df_f.empty:
    st.info("選択された期間に該当データがありません。日付範囲を調整してください。")
    st.stop()

# ===== KPI =====
kpis = compute_kpis(df_f)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("売上合計", _format_jpy(kpis["total_revenue"]))
with col2:
    st.metric("販売数量合計", f"{kpis['total_units']:,}")
with col3:
    st.metric("商品カテゴリ数", f"{kpis['n_categories']:,}")

# ===== Charts =====
st.markdown("### 可視化")

# 1) 商品カテゴリごとの売上（棒グラフ）
category_rev = (
    df_f.groupby("category", as_index=False)["revenue"].sum()
    .sort_values("revenue", ascending=False)
)
fig_bar = px.bar(
    category_rev,
    x="category",
    y="revenue",
    title="カテゴリ別 売上合計",
    text="revenue",
)
fig_bar.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
fig_bar.update_layout(yaxis_title="売上（円）", xaxis_title="カテゴリ", uniformtext_minsize=8, uniformtext_mode="hide")
st.plotly_chart(fig_bar, use_container_width=True)

# 2) 日毎の売上推移（折れ線グラフ）
daily_rev = df_f.groupby(DATE_COL, as_index=False)["revenue"].sum()
fig_line = px.line(
    daily_rev,
    x=DATE_COL,
    y="revenue",
    markers=True,
    title="日次 売上推移",
)
fig_line.update_layout(yaxis_title="売上（円）", xaxis_title="日付")
st.plotly_chart(fig_line, use_container_width=True)

# ===== Table (optional, helpful for確認) =====
with st.expander("明細データ（フィルタ後）を表示"):
    st.dataframe(
        df_f.assign(
            revenue_fmt=df_f["revenue"].map(_format_jpy),
            unit_price_fmt=df_f["unit_price"].map(_format_jpy),
        )[["date", "category", "units", "unit_price_fmt", "region", "sales_channel", "customer_segment", "revenue_fmt"]],
        use_container_width=True,
    )

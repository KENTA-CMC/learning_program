"""自動可視化モジュール."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from typing import Optional, Union
import numpy as np


def detect_column_types(df: pd.DataFrame) -> dict:
    """DataFrameの列タイプを検出する.
    
    Args:
        df: 分析対象のDataFrame
        
    Returns:
        {列名: タイプ} の辞書 (タイプ: 'datetime', 'numeric', 'categorical')
    """
    column_types = {}
    
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            column_types[col] = 'datetime'
        elif pd.api.types.is_numeric_dtype(df[col]):
            column_types[col] = 'numeric'
        else:
            column_types[col] = 'categorical'
    
    return column_types


def create_automatic_visualization(df: pd.DataFrame, title: str = "") -> Optional[Union[go.Figure, list]]:
    """結果データに基づいて自動的に適切な可視化を作成する.
    
    Args:
        df: 可視化対象のDataFrame
        title: グラフタイトル
        
    Returns:
        Plotlyの図、または複数の図のリスト、またはNone
    """
    if df.empty:
        return None
    
    column_types = detect_column_types(df)
    datetime_cols = [col for col, typ in column_types.items() if typ == 'datetime']
    numeric_cols = [col for col, typ in column_types.items() if typ == 'numeric']
    categorical_cols = [col for col, typ in column_types.items() if typ == 'categorical']
    
    # データが少ない場合は可視化をスキップ
    if len(df) < 2:
        return None
    
    # パターン1: 時系列 + 数値 → 折れ線グラフ
    if len(datetime_cols) >= 1 and len(numeric_cols) >= 1:
        return create_timeseries_chart(df, datetime_cols[0], numeric_cols, categorical_cols, title)
    
    # パターン2: カテゴリ2つ + 数値 → 積み上げ棒グラフ
    elif len(categorical_cols) >= 2 and len(numeric_cols) >= 1:
        return create_stacked_bar_chart(df, categorical_cols[:2], numeric_cols[0], title)
    
    # パターン3: カテゴリ1つ + 数値 → 棒グラフ
    elif len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        return create_bar_chart(df, categorical_cols[0], numeric_cols[0], title)
    
    # パターン4: 数値のみ → ヒストグラムまたは散布図
    elif len(numeric_cols) >= 2:
        return create_numeric_chart(df, numeric_cols, title)
    
    return None


def create_timeseries_chart(df: pd.DataFrame, time_col: str, numeric_cols: list, 
                          categorical_cols: list, title: str) -> go.Figure:
    """時系列折れ線グラフを作成する.
    
    Args:
        df: データ
        time_col: 時間軸の列名
        numeric_cols: 数値列のリスト
        categorical_cols: カテゴリ列のリスト
        title: タイトル
        
    Returns:
        Plotlyの折れ線グラフ
    """
    primary_numeric = numeric_cols[0]
    
    # カテゴリがある場合は色分けする
    if categorical_cols:
        color_col = categorical_cols[0]
        fig = px.line(df, 
                     x=time_col, 
                     y=primary_numeric,
                     color=color_col,
                     markers=True,
                     title=title or f"{primary_numeric}の時系列推移（{color_col}別）")
    else:
        fig = px.line(df, 
                     x=time_col, 
                     y=primary_numeric,
                     markers=True,
                     title=title or f"{primary_numeric}の時系列推移")
    
    fig.update_layout(
        xaxis_title=time_col,
        yaxis_title=primary_numeric,
        hovermode='x unified'
    )
    
    return fig


def create_bar_chart(df: pd.DataFrame, category_col: str, numeric_col: str, title: str) -> go.Figure:
    """棒グラフを作成する.
    
    Args:
        df: データ
        category_col: カテゴリ列名
        numeric_col: 数値列名
        title: タイトル
        
    Returns:
        Plotlyの棒グラフ
    """
    # データが多い場合は上位を表示
    if len(df) > 20:
        df_plot = df.nlargest(20, numeric_col)
    else:
        df_plot = df.copy()
    
    fig = px.bar(df_plot, 
                x=category_col, 
                y=numeric_col,
                title=title or f"{category_col}別 {numeric_col}")
    
    fig.update_layout(
        xaxis_title=category_col,
        yaxis_title=numeric_col,
        xaxis_tickangle=-45 if len(df_plot) > 10 else 0
    )
    
    return fig


def create_stacked_bar_chart(df: pd.DataFrame, category_cols: list, numeric_col: str, title: str) -> go.Figure:
    """積み上げ棒グラフを作成する.
    
    Args:
        df: データ
        category_cols: カテゴリ列のリスト（2つ）
        numeric_col: 数値列名
        title: タイトル
        
    Returns:
        Plotly の積み上げ棒グラフ
    """
    x_col, color_col = category_cols[0], category_cols[1]
    
    # データが多い場合は上位カテゴリのみ
    if df[x_col].nunique() > 15:
        top_categories = df.groupby(x_col)[numeric_col].sum().nlargest(15).index
        df_plot = df[df[x_col].isin(top_categories)].copy()
    else:
        df_plot = df.copy()
    
    fig = px.bar(df_plot, 
                x=x_col, 
                y=numeric_col,
                color=color_col,
                title=title or f"{x_col}別 {numeric_col}（{color_col}別）")
    
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=numeric_col,
        xaxis_tickangle=-45 if df_plot[x_col].nunique() > 10 else 0,
        barmode='stack'
    )
    
    return fig


def create_numeric_chart(df: pd.DataFrame, numeric_cols: list, title: str) -> go.Figure:
    """数値データの可視化（ヒストグラムまたは散布図）.
    
    Args:
        df: データ
        numeric_cols: 数値列のリスト
        title: タイトル
        
    Returns:
        Plotlyの図
    """
    if len(numeric_cols) >= 2:
        # 散布図
        fig = px.scatter(df, 
                        x=numeric_cols[0], 
                        y=numeric_cols[1],
                        title=title or f"{numeric_cols[0]} vs {numeric_cols[1]}")
    else:
        # ヒストグラム
        fig = px.histogram(df, 
                          x=numeric_cols[0],
                          title=title or f"{numeric_cols[0]}の分布")
    
    return fig


def display_visualization_with_data(df: pd.DataFrame, sql: str, title: str = ""):
    """データテーブルと可視化を表示する.
    
    Args:
        df: 表示するDataFrame
        sql: 実行したSQL
        title: 可視化のタイトル
    """
    # 実行SQLを表示
    st.subheader("🔍 実行されたSQL")
    st.code(sql, language='sql')
    
    # 結果テーブル表示
    st.subheader("📊 分析結果")
    st.dataframe(df, use_container_width=True)
    
    # CSVダウンロード
    if not df.empty:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 結果をCSVでダウンロード",
            data=csv,
            file_name="analysis_result.csv",
            mime="text/csv"
        )
    
    # 可視化
    if not df.empty:
        fig = create_automatic_visualization(df, title)
        if fig is not None:
            st.subheader("📈 可視化")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("このデータタイプでは自動可視化を生成できませんでした。")
    else:
        st.warning("結果が0件のため、可視化は表示されません。")
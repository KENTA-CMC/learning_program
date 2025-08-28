"""データ読み込みとDuckDB登録モジュール."""

import pandas as pd
import duckdb
import streamlit as st
from typing import Optional


@st.cache_data
def load_csv_to_dataframe(csv_path: str = 'data/sample_sales.csv') -> Optional[pd.DataFrame]:
    """CSVファイルを読み込んでDataFrameを返す.
    
    Args:
        csv_path: CSVファイルのパス
        
    Returns:
        DataFrame または None（読み込み失敗時）
    """
    try:
        df = pd.read_csv(csv_path, parse_dates=['date'])
        return df
    except FileNotFoundError:
        st.error("売上データファイルが見つかりません。data/sample_sales.csvが存在することを確認してください。")
        return None
    except Exception as e:
        st.error(f"CSVファイルの読み込みでエラーが発生しました: {e}")
        return None


@st.cache_resource
def create_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """DuckDBコネクションを作成し、salesテーブルを登録する.
    
    Returns:
        DuckDBコネクション
    """
    conn = duckdb.connect(':memory:')
    
    # CSVデータを読み込み
    df = load_csv_to_dataframe()
    if df is not None:
        # salesテーブルとして登録
        conn.register('sales', df)
    
    return conn


def get_data_info(df: pd.DataFrame) -> dict:
    """データの基本情報を取得する.
    
    Args:
        df: 分析対象のDataFrame
        
    Returns:
        データ情報の辞書
    """
    if df is None or df.empty:
        return {}
    
    return {
        'record_count': len(df),
        'date_range': {
            'min': df['date'].min().strftime('%Y-%m-%d') if 'date' in df.columns else 'N/A',
            'max': df['date'].max().strftime('%Y-%m-%d') if 'date' in df.columns else 'N/A'
        },
        'category_count': df['category'].nunique() if 'category' in df.columns else 0,
        'region_count': df['region'].nunique() if 'region' in df.columns else 0,
        'columns': list(df.columns)
    }
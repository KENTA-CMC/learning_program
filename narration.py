"""結果サマリー生成モジュール."""

import pandas as pd
from typing import Optional
from llm_client import LLMClient


def create_summary_prompt(user_query: str, sql: str, result_df: pd.DataFrame) -> str:
    """サマリー生成用のプロンプトを作成する.
    
    Args:
        user_query: ユーザーの元の質問
        sql: 実行したSQL
        result_df: 実行結果のDataFrame
        
    Returns:
        LLM用のプロンプト
    """
    # 結果データを先頭200行のCSV形式に変換
    result_csv = result_df.head(200).to_csv(index=False)
    
    prompt = f"""以下の売上データ分析結果を100-200字で日本語で要約してください。

ユーザーの質問: {user_query}
実行したSQL: {sql}

結果データ（CSV形式）:
{result_csv}

要約のポイント:
- 箇条書き3-5点
- 具体的な数値を2-3個含める
- ビジネス観点での洞察を含める
- データの傾向や特徴を明確に示す

例:
• 2024年の総売上は1,234,567円で前年比15%増加
• Electronics カテゴリが売上の45%を占め最大セグメント
• 第4四半期の伸びが特に顕著で全体の30%を記録
"""
    
    return prompt


def generate_summary_with_llm(llm_client: LLMClient, user_query: str, sql: str, result_df: pd.DataFrame) -> str:
    """LLMを使って分析結果のサマリーを生成する.
    
    Args:
        llm_client: LLMクライアント
        user_query: ユーザーの質問
        sql: 実行したSQL
        result_df: 結果データ
        
    Returns:
        生成されたサマリーテキスト
    """
    try:
        # 結果データを先頭200行のCSV形式に変換
        result_csv = result_df.head(200).to_csv(index=False)
        
        # LLMでサマリー生成
        summary = llm_client.generate_summary(user_query, sql, result_csv)
        
        return summary
        
    except Exception as e:
        return f"サマリー生成中にエラーが発生しました: {str(e)}"


def create_fallback_summary(user_query: str, sql: str, result_df: pd.DataFrame, template_name: str = None) -> str:
    """フォールバック時の基本的なサマリーを生成する.
    
    Args:
        user_query: ユーザーの質問
        sql: 実行したSQL
        result_df: 結果データ
        template_name: 使用されたテンプレート名
        
    Returns:
        基本的なサマリーテキスト
    """
    if result_df.empty:
        return "• 指定された条件に該当するデータが見つかりませんでした"
    
    summary_parts = []
    
    # 基本統計
    row_count = len(result_df)
    summary_parts.append(f"• {row_count:,} 件のレコードが該当しました")
    
    # 数値列がある場合の統計
    numeric_cols = result_df.select_dtypes(include=['number']).columns
    for col in numeric_cols[:2]:  # 最大2つの数値列
        if col.lower() in ['revenue', 'total_revenue', 'sales', 'amount']:
            total_value = result_df[col].sum()
            summary_parts.append(f"• {col}の合計: {total_value:,.0f}")
            avg_value = result_df[col].mean()
            summary_parts.append(f"• {col}の平均: {avg_value:,.0f}")
        elif col.lower() in ['units', 'count', 'quantity']:
            total_units = result_df[col].sum()
            summary_parts.append(f"• {col}の合計: {total_units:,.0f}")
    
    # カテゴリカル列の場合
    categorical_cols = result_df.select_dtypes(include=['object']).columns
    for col in categorical_cols[:1]:  # 最大1つのカテゴリ列
        unique_count = result_df[col].nunique()
        summary_parts.append(f"• {col}のユニーク数: {unique_count} 種類")
    
    # フォールバック使用時の注記
    if template_name:
        summary_parts.append(f"• 【注記】定型クエリ「{template_name}」を使用して分析しました")
    
    return "\n".join(summary_parts)


def generate_analysis_summary(llm_client: Optional[LLMClient], user_query: str, sql: str, 
                            result_df: pd.DataFrame, is_fallback: bool = False, 
                            template_name: str = None) -> str:
    """分析結果の総合的なサマリーを生成する.
    
    Args:
        llm_client: LLMクライアント（Noneの場合はフォールバックのみ）
        user_query: ユーザーの質問
        sql: 実行したSQL
        result_df: 結果データ
        is_fallback: フォールバッククエリが使用されたかどうか
        template_name: 使用されたテンプレート名
        
    Returns:
        生成されたサマリー
    """
    # 結果が空の場合
    if result_df.empty:
        return create_fallback_summary(user_query, sql, result_df, template_name)
    
    # LLMクライアントが利用可能で、フォールバックでない場合はLLMを使用
    if llm_client and not is_fallback:
        try:
            llm_summary = generate_summary_with_llm(llm_client, user_query, sql, result_df)
            
            # フォールバック時の注記を追加
            if template_name:
                llm_summary += f"\n\n【注記】定型クエリ「{template_name}」を使用して分析しました"
                
            return llm_summary
            
        except Exception:
            # LLM失敗時はフォールバックサマリーを使用
            pass
    
    # フォールバックまたはLLM失敗時
    return create_fallback_summary(user_query, sql, result_df, template_name)
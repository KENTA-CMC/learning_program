"""フォールバック用の定型SQLクエリとマッピングロジック."""

from typing import Dict, List, Tuple
import re


class QueryTemplate:
    """定型SQLクエリテンプレート."""
    
    def __init__(self, name: str, sql: str, description: str, keywords: List[str]):
        self.name = name
        self.sql = sql
        self.description = description
        self.keywords = keywords


def get_fallback_templates() -> List[QueryTemplate]:
    """フォールバック用の定型SQLテンプレートを取得する.
    
    Returns:
        QueryTemplateのリスト
    """
    templates = [
        QueryTemplate(
            name="月次カテゴリ別売上",
            sql="""
SELECT 
    date_trunc('month', date) AS month,
    category,
    SUM(revenue) AS total_revenue,
    SUM(units) AS total_units
FROM sales 
GROUP BY date_trunc('month', date), category
ORDER BY month, category
            """.strip(),
            description="月毎のカテゴリー別売上分析",
            keywords=["月", "カテゴリ", "月毎", "月別", "category", "month"]
        ),
        
        QueryTemplate(
            name="チャネル別売上",
            sql="""
SELECT 
    sales_channel,
    SUM(revenue) AS total_revenue,
    SUM(units) AS total_units,
    COUNT(*) AS transaction_count
FROM sales 
GROUP BY sales_channel
ORDER BY total_revenue DESC
            """.strip(),
            description="販売チャネル別の売上分析",
            keywords=["チャネル", "チャンネル", "channel", "販売", "経路"]
        ),
        
        QueryTemplate(
            name="地域別売上",
            sql="""
SELECT 
    region,
    SUM(revenue) AS total_revenue,
    SUM(units) AS total_units,
    COUNT(*) AS transaction_count
FROM sales 
GROUP BY region
ORDER BY total_revenue DESC
            """.strip(),
            description="地域別の売上分析",
            keywords=["地域", "地方", "region", "エリア", "場所"]
        ),
        
        QueryTemplate(
            name="顧客セグメント別売上",
            sql="""
SELECT 
    customer_segment,
    SUM(revenue) AS total_revenue,
    SUM(units) AS total_units,
    COUNT(*) AS transaction_count
FROM sales 
GROUP BY customer_segment
ORDER BY total_revenue DESC
            """.strip(),
            description="顧客セグメント別の売上分析",
            keywords=["顧客", "セグメント", "segment", "customer", "クライアント"]
        )
    ]
    
    return templates


def get_default_query() -> str:
    """デフォルトのフォールバッククエリを取得する.
    
    Returns:
        総売上を返すSQL
    """
    return """
SELECT 
    SUM(revenue) AS total_revenue,
    SUM(units) AS total_units,
    COUNT(*) AS total_transactions
FROM sales
    """.strip()


def find_best_template(user_query: str) -> Tuple[str, str]:
    """ユーザークエリに最適なテンプレートを見つける.
    
    Args:
        user_query: ユーザーの自然言語クエリ
        
    Returns:
        (選択されたSQL, テンプレート名)
    """
    templates = get_fallback_templates()
    user_query_lower = user_query.lower()
    
    best_template = None
    max_score = 0
    
    # 各テンプレートのキーワードマッチングスコアを計算
    for template in templates:
        score = 0
        for keyword in template.keywords:
            if keyword.lower() in user_query_lower:
                score += 1
        
        # より長いキーワードにはボーナス点
        for keyword in template.keywords:
            if len(keyword) > 3 and keyword.lower() in user_query_lower:
                score += 1
        
        if score > max_score:
            max_score = score
            best_template = template
    
    # マッチするテンプレートがない場合はデフォルト
    if best_template is None or max_score == 0:
        return get_default_query(), "デフォルト（総売上）"
    
    return best_template.sql, best_template.name


def get_template_by_name(template_name: str) -> str:
    """テンプレート名でSQLを取得する.
    
    Args:
        template_name: テンプレート名
        
    Returns:
        SQL文
    """
    templates = get_fallback_templates()
    
    for template in templates:
        if template.name == template_name:
            return template.sql
    
    return get_default_query()


def list_available_templates() -> Dict[str, str]:
    """利用可能なテンプレートの一覧を取得する.
    
    Returns:
        {テンプレート名: 説明} の辞書
    """
    templates = get_fallback_templates()
    return {template.name: template.description for template in templates}
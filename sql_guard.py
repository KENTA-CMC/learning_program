"""SQLサニタイゼーションとセキュリティチェックモジュール."""

import re
from typing import Optional


class SQLSecurityException(Exception):
    """SQL セキュリティ違反例外."""
    pass


def extract_sql_from_response(response: str) -> Optional[str]:
    """LLM応答からSQLコードブロックを抽出する.
    
    Args:
        response: LLMからの応答テキスト
        
    Returns:
        抽出されたSQL文、または None
    """
    sql_pattern = r'```sql\s*(.*?)\s*```'
    matches = re.findall(sql_pattern, response, re.DOTALL | re.IGNORECASE)
    
    if matches:
        return matches[0].strip()
    
    return None


def sanitize_sql(sql: str) -> str:
    """SQLを清浄化する.
    
    Args:
        sql: 元のSQL文
        
    Returns:
        清浄化されたSQL文
        
    Raises:
        SQLSecurityException: セキュリティ違反が検出された場合
    """
    if not sql:
        raise SQLSecurityException("空のSQLクエリです")
    
    sql_clean = sql.strip()
    
    # 改行と末尾セミコロンを除去
    sql_clean = re.sub(r'\n+', ' ', sql_clean)
    sql_clean = re.sub(r';+$', '', sql_clean)
    sql_clean = re.sub(r'\s+', ' ', sql_clean)
    
    # SELECT文で開始することを強制
    if not sql_clean.upper().strip().startswith('SELECT'):
        raise SQLSecurityException("SELECT文のみ許可されています")
    
    # 禁止語チェック
    forbidden_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE',
        'ATTACH', 'COPY', 'EXPORT', 'IMPORT', 'PRAGMA', 'CALL',
        'LOAD', 'SET', 'RESET', 'EXPLAIN', 'DESCRIBE', 'EXEC'
    ]
    
    sql_upper = sql_clean.upper()
    for keyword in forbidden_keywords:
        if re.search(r'\b' + keyword + r'\b', sql_upper):
            raise SQLSecurityException(f"禁止されたキーワードが含まれています: {keyword}")
    
    # 複数ステートメント禁止（セミコロンチェック）
    if ';' in sql_clean:
        raise SQLSecurityException("複数のSQL文は実行できません")
    
    # SQLコメント禁止
    if '--' in sql_clean or '/*' in sql_clean:
        raise SQLSecurityException("SQLコメントは許可されていません")
    
    # salesテーブル以外のアクセス禁止
    table_pattern = r'\bFROM\s+(\w+)'
    matches = re.findall(table_pattern, sql_upper)
    for table in matches:
        if table.upper() != 'SALES':
            raise SQLSecurityException(f"salesテーブル以外のアクセスは禁止されています: {table}")
    
    # JOINのチェック（他テーブルとの結合を防ぐ）
    if re.search(r'\bJOIN\b', sql_upper):
        join_pattern = r'JOIN\s+(\w+)'
        join_matches = re.findall(join_pattern, sql_upper)
        for join_table in join_matches:
            if join_table.upper() != 'SALES':
                raise SQLSecurityException(f"salesテーブル以外との結合は禁止されています: {join_table}")
    
    return sql_clean


def validate_and_sanitize_sql(llm_response: str) -> str:
    """LLM応答からSQLを抽出・検証・清浄化する.
    
    Args:
        llm_response: LLMからの応答
        
    Returns:
        清浄化されたSQL文
        
    Raises:
        SQLSecurityException: SQL抽出失敗またはセキュリティ違反
    """
    # SQLコードブロック抽出
    sql = extract_sql_from_response(llm_response)
    if not sql:
        raise SQLSecurityException("SQLコードブロックが見つかりません")
    
    # サニタイズして返す
    return sanitize_sql(sql)


def is_sql_safe(sql: str) -> tuple[bool, str]:
    """SQLが安全かどうかをチェックする.
    
    Args:
        sql: チェック対象のSQL文
        
    Returns:
        (安全かどうか, エラーメッセージ)
    """
    try:
        sanitize_sql(sql)
        return True, ""
    except SQLSecurityException as e:
        return False, str(e)
"""LLM抽象化レイヤー（OpenAI/Anthropic対応）."""

import os
from typing import Optional
from abc import ABC, abstractmethod

from openai import OpenAI
from anthropic import Anthropic


class LLMClient(ABC):
    """LLMクライアントの抽象基底クラス."""
    
    @abstractmethod
    def generate_sql(self, user_query: str, schema_info: str) -> str:
        """Text-to-SQLを実行する.
        
        Args:
            user_query: ユーザーの自然言語クエリ
            schema_info: テーブルスキーマ情報
            
        Returns:
            生成されたSQL文
        """
        pass
    
    @abstractmethod
    def generate_summary(self, query: str, sql: str, result_csv: str) -> str:
        """結果の要約を生成する.
        
        Args:
            query: 元のユーザークエリ
            sql: 実行したSQL
            result_csv: 結果データのCSV形式文字列（先頭200行）
            
        Returns:
            要約テキスト
        """
        pass


class OpenAIClient(LLMClient):
    """OpenAI APIクライアント."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.sql_model = os.getenv('OPENAI_MODEL_SQL', 'gpt-4o-mini')
        self.text_model = os.getenv('OPENAI_MODEL_TEXT', 'gpt-4o-mini')
    
    def generate_sql(self, user_query: str, schema_info: str) -> str:
        """OpenAIでSQL生成."""
        system_prompt = f"""あなたは売上データ分析のSQLエキスパートです。
以下のテーブル情報を基に、ユーザーの質問に答えるSQLクエリを生成してください。

{schema_info}

制約:
- SELECT文のみ使用可能
- salesテーブルのみ使用
- 月次集計にはdate_trunc('month', date)を使用
- エイリアスを明示的に指定
- SQLコードのみを```sqlブロックで出力

例:
```sql
SELECT date_trunc('month', date) AS month, category, SUM(revenue) AS total_revenue
FROM sales
GROUP BY date_trunc('month', date), category
ORDER BY month, category
```
"""
        
        response = self.client.chat.completions.create(
            model=self.sql_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.1
        )
        
        return response.choices[0].message.content
    
    def generate_summary(self, query: str, sql: str, result_csv: str) -> str:
        """OpenAIで要約生成."""
        prompt = f"""以下の売上データ分析結果を100-200字で日本語で要約してください。

ユーザーの質問: {query}
実行したSQL: {sql}

結果データ（CSV形式）:
{result_csv}

要約のポイント:
- 箇条書き3-5点
- 具体的な数値を2-3個含める
- ビジネス観点での洞察を含める
"""
        
        response = self.client.chat.completions.create(
            model=self.text_model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content


class AnthropicClient(LLMClient):
    """Anthropic APIクライアント."""
    
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.sql_model = os.getenv('ANTHROPIC_MODEL_SQL', 'claude-3-haiku-20240307')
        self.text_model = os.getenv('ANTHROPIC_MODEL_TEXT', 'claude-3-haiku-20240307')
    
    def generate_sql(self, user_query: str, schema_info: str) -> str:
        """AnthropicでSQL生成."""
        system_prompt = f"""あなたは売上データ分析のSQLエキスパートです。
以下のテーブル情報を基に、ユーザーの質問に答えるSQLクエリを生成してください。

{schema_info}

制約:
- SELECT文のみ使用可能
- salesテーブルのみ使用
- 月次集計にはdate_trunc('month', date)を使用
- エイリアスを明示的に指定
- SQLコードのみを```sqlブロックで出力

例:
```sql
SELECT date_trunc('month', date) AS month, category, SUM(revenue) AS total_revenue
FROM sales
GROUP BY date_trunc('month', date), category
ORDER BY month, category
```
"""
        
        response = self.client.messages.create(
            model=self.sql_model,
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_query}
            ],
            temperature=0.1
        )
        
        return response.content[0].text
    
    def generate_summary(self, query: str, sql: str, result_csv: str) -> str:
        """Anthropicで要約生成."""
        prompt = f"""以下の売上データ分析結果を100-200字で日本語で要約してください。

ユーザーの質問: {query}
実行したSQL: {sql}

結果データ（CSV形式）:
{result_csv}

要約のポイント:
- 箇条書き3-5点
- 具体的な数値を2-3個含める
- ビジネス観点での洞察を含める
"""
        
        response = self.client.messages.create(
            model=self.text_model,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.content[0].text


def create_llm_client() -> Optional[LLMClient]:
    """環境変数に基づいてLLMクライアントを作成する.
    
    Returns:
        LLMクライアントインスタンス、または None（設定不正時）
    """
    provider = os.getenv('PROVIDER', 'openai').lower()
    
    try:
        if provider == 'openai':
            if not os.getenv('OPENAI_API_KEY'):
                raise ValueError("OPENAI_API_KEYが設定されていません")
            return OpenAIClient()
        elif provider == 'anthropic':
            if not os.getenv('ANTHROPIC_API_KEY'):
                raise ValueError("ANTHROPIC_API_KEYが設定されていません")
            return AnthropicClient()
        else:
            raise ValueError(f"未対応のプロバイダー: {provider}")
    except Exception as e:
        print(f"LLMクライアント作成エラー: {e}")
        return None
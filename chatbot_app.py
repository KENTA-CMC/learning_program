import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# モジュールインポート
from data_loader import load_csv_to_dataframe, create_duckdb_connection, get_data_info
from llm_client import create_llm_client
from sql_guard import validate_and_sanitize_sql, SQLSecurityException
from query_templates import find_best_template
from viz import display_visualization_with_data
from narration import generate_analysis_summary

# 環境変数読み込み
load_dotenv()

# LLMクライアントを初期化
llm_client = create_llm_client()

# データとDuckDB接続を初期化
sales_data = load_csv_to_dataframe()
db_conn = create_duckdb_connection()

# アプリのタイトルを設定します
st.title('売上データ分析AIチャットボット')

# サイドバーにデータ情報を表示
with st.sidebar:
    st.header("📊 売上データ情報")
    if sales_data is not None:
        data_info = get_data_info(sales_data)
        st.success(f"✅ データ読み込み完了")
        st.write(f"**レコード数:** {data_info['record_count']:,} 件")
        st.write(f"**期間:** {data_info['date_range']['min']} ～ {data_info['date_range']['max']}")
        st.write(f"**カテゴリ数:** {data_info['category_count']} 種類")
        st.write(f"**地域数:** {data_info['region_count']} 地域")
        
        with st.expander("📋 データプレビュー"):
            st.dataframe(sales_data.head(10), use_container_width=True)
            
        with st.expander("📈 基本統計"):
            st.dataframe(sales_data.describe(), use_container_width=True)
            
        # LLMクライアント状態表示
        if llm_client:
            provider = os.getenv('PROVIDER', 'openai')
            st.success(f"🤖 LLM: {provider.upper()}")
        else:
            st.error("❌ LLMクライアントの初期化に失敗")
    else:
        st.error("❌ データの読み込みに失敗しました")

# チャット履歴を保存するための場所を用意します
# もし履歴がなければ、最初のメッセージを設定します
if "messages" not in st.session_state:
    st.session_state.messages = []

# これまでのチャット履歴を表示します
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def execute_sql_query(sql: str) -> pd.DataFrame:
    """SQLクエリを実行してDataFrameを返す."""
    try:
        result = db_conn.execute(sql).fetchdf()
        return result
    except Exception as e:
        st.error(f"SQLクエリ実行エラー: {e}")
        return pd.DataFrame()

def process_user_query(user_query: str) -> tuple[str, pd.DataFrame, bool, str]:
    """ユーザークエリを処理し、SQL生成・実行・結果を返す."""
    is_fallback = False
    template_name = None
    executed_sql = None
    result_df = pd.DataFrame()
    
    # データが利用できない場合
    if sales_data is None:
        return "データが読み込まれていません。", result_df, True, None
        
    # LLMクライアントが利用可能な場合、SQL生成を試行
    if llm_client:
        try:
            # スキーマ情報作成
            schema_info = f"""テーブル名: sales
カラム: {', '.join(sales_data.columns)}
レコード数: {len(sales_data):,} 件
期間: {sales_data['date'].min()} ～ {sales_data['date'].max()}"""
            
            # LLMでSQL生成
            llm_response = llm_client.generate_sql(user_query, schema_info)
            
            # SQLを抽出・検証・サニタイズ
            executed_sql = validate_and_sanitize_sql(llm_response)
            
            # SQL実行
            result_df = execute_sql_query(executed_sql)
            
        except SQLSecurityException as e:
            st.warning(f"セキュリティ上の理由でSQLを実行できませんでした: {e}")
            st.info("代わりに定型クエリを使用します。")
            is_fallback = True
        except Exception as e:
            st.warning(f"SQL生成/実行中にエラーが発生しました: {e}")
            st.info("代わりに定型クエリを使用します。")
            is_fallback = True
    else:
        st.warning("LLMクライアントが利用できません。定型クエリを使用します。")
        is_fallback = True
    
    # フォールバック処理
    if is_fallback or result_df.empty:
        executed_sql, template_name = find_best_template(user_query)
        result_df = execute_sql_query(executed_sql)
        is_fallback = True
    
    return executed_sql, result_df, is_fallback, template_name

# ユーザーからの新しいメッセージを受け取る入力欄を表示します
if prompt := st.chat_input("売上データについて何でも質問してください..."):
    # ユーザーのメッセージを履歴に追加して表示します
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AIに応答を生成してもらう部分です
    with st.chat_message("assistant"):
        # ユーザークエリを処理
        executed_sql, result_df, is_fallback, template_name = process_user_query(prompt)
        
        # 結果表示
        if executed_sql and not result_df.empty:
            # 可視化とデータ表示
            display_visualization_with_data(result_df, executed_sql, f"分析結果: {prompt}")
            
            # サマリー生成・表示
            st.subheader("💡 分析サマリー")
            summary = generate_analysis_summary(
                llm_client, prompt, executed_sql, result_df, is_fallback, template_name
            )
            st.markdown(summary)
            
            # 応答を履歴に追加
            response_content = f"分析を完了しました。\n\n{summary}"
            
        elif executed_sql and result_df.empty:
            st.warning("🔍 該当するデータが見つかりませんでした。")
            st.code(executed_sql, language='sql')
            response_content = "該当するデータが見つかりませんでした。条件を変更して再度お試しください。"
            
        else:
            st.error("❌ 分析の実行中にエラーが発生しました。")
            response_content = "申し訳ございません。分析の実行中にエラーが発生しました。"
        
        # AIの応答を履歴に追加します
        st.session_state.messages.append({"role": "assistant", "content": response_content})
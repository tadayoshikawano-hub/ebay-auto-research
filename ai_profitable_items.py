import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client
from slack_sdk import WebClient

load_dotenv()

# ==============================
# 環境変数の読み込み
# ==============================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)
slack_client = WebClient(token=SLACK_TOKEN)


# ==============================
# Slack送信
# ==============================
def send_slack(message: str):
    slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=message)


# ==============================
# Supabaseから最新の市場データを取得
# ==============================
def fetch_latest_data():
    response = supabase.table("sales_data") \
        .select("*") \
        .order("date", desc=True) \
        .limit(1) \
        .execute()

    if len(response.data) == 0:
        return None
    return response.data[0]


# ==============================
# ChatGPTに「利益商品」を選ばせる
# ==============================
def generate_profitable_items_report(data: dict):

    prompt = f"""
あなたはeBay転売の利益分析アドバイザーです。
以下の最新市場データを読んで、
「利益率が高くなりそうなカード」を3つ選んでください。

【市場データ】
- 販売件数: {data['total_sales']}
- 平均価格: {data['avg_price']}
- 中央価格: {data['median_price']}
- 最低価格: {data['min_price']}
- 最高価格: {data['max_price']}
- 人気キーワード: {data['top_keywords']}
- 人気キャラ価格分析: {data['top_characters']}

以下のフォーマットで回答してください：

① 商品名
　・推定仕入れ目安価格
　・予想販売価格（eBay）
　・想定利益率（％）
　・理由（市場傾向・需要・キーワードなどから判断）

② 商品名
　（同上）

③ 商品名
　（同上）
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


# ==============================
# メイン処理
# ==============================
def main():
    latest = fetch_latest_data()

    if not latest:
        send_slack("⚠️ Supabaseに市場データがありません。利益商品を分析できません。")
        return

    report = generate_profitable_items_report(latest)

    message = f"""
💰 **利益商品レポート（AI分析）**
{report}
"""

    send_slack(message)
    print("✅ AI利益商品レポートをSlackへ送信しました！")


# ==============================
# エントリーポイント
# ==============================
if __name__ == "__main__":
    main()

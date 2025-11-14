import os
from dotenv import load_dotenv
from openai import OpenAI
from slack_sdk import WebClient
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)
slack_client = WebClient(token=SLACK_TOKEN)


def send_slack(msg):
    slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=msg)


# ==========================
# 過去データ（最大4回）取得
# ==========================
def fetch_past_sales_data(limit=4):
    response = (
        supabase.table("sales_data")
        .select("*")
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data


# ==========================
# AIトレンド利益分析
# ==========================
def generate_trend_profit_report(data_list):

    prompt = f"""
あなたはeBayの利益分析スペシャリストです。
以下は過去{len(data_list)}回分のポケモンカード市場データです。

このデータを使って、
「過去のトレンドを踏まえた利益商品候補TOP3」を提案してください。

=== 市場データ ===
"""

    for idx, data in enumerate(data_list, 1):
        prompt += f"""
【第{idx}回目】
- 日付: {data.get('date')}
- 販売件数: {data.get('total_sales')}
- 平均価格: {data.get('avg_price')}
- 中央価格: {data.get('median_price')}
- 最低価格: {data.get('min_price')}
- 最高価格: {data.get('max_price')}
- 人気キーワード: {data.get('top_keywords')}
- キャラ別平均価格: {data.get('top_characters')}
"""

    prompt += """
=== 指示 ===
上記のデータを分析し、
・価格トレンド（上昇/下降）
・需要トレンド（販売数推移）
・キーワードトレンド
・キャラ別の価格変動

これらを踏まえて、以下の形式で「利益が出る可能性が最も高いカード」TOP3を出力してください。

① 商品名
　・過去トレンド（価格・販売数）
　・仕入れ目安価格
　・予想販売価格
　・利益率（％）
　・提案理由（市場の変化をもとに）

② 商品名
　（同上）

③ 商品名
　（同上）
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def main():
    past_data = fetch_past_sales_data(limit=4)

    if len(past_data) < 2:
        send_slack("⚠️トレンド分析に必要な過去データが不足しています。")
        return

    report = generate_trend_profit_report(past_data)

    msg = f"""
💹 **利益商品レポート（トレンドAI分析）**
{report}
"""
    send_slack(msg)
    print("✅ トレンド利益商品レポート送信完了！")


if __name__ == "__main__":
    main()

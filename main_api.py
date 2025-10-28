import os
import requests
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# ===============================
# ① .envファイルを読み込む
# ===============================
load_dotenv()

# ===============================
# ② 環境変数を取得
# ===============================
SLACK_BOT_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")  # ← Productionトークン
MARKETPLACE_ID = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US")
SEARCH_QUERY = os.getenv("EBAY_QUERY", "iphone")  # デフォルト検索ワード

# ===============================
# ③ Slack通知関数
# ===============================
def send_slack_message(message):
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL:
        print("⚠️ Slackトークンまたはチャンネルが設定されていません。")
        return
    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        print(f"✅ Slack通知成功: {message[:50]}...")
    except SlackApiError as e:
        print(f"⚠️ Slack通知失敗: {e.response['error']}")

# ===============================
# ④ eBay Browse API版データ取得
# ===============================
def fetch_ebay_items(query, limit=5):
    """Browse APIで商品を検索"""
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE_ID
    }
    params = {"q": query, "limit": limit}

    print(f"🌍 eBay API接続中: {query}")
    res = requests.get(url, headers=headers, params=params)
    print("HTTP Status:", res.status_code)

    if res.status_code != 200:
        raise Exception(f"APIエラー: {res.status_code} {res.text}")

    data = res.json()
    items = data.get("itemSummaries", [])

    results = []
    for item in items:
        results.append({
            "title": item.get("title"),
            "price": f"{item.get('price', {}).get('value')} {item.get('price', {}).get('currency')}",
            "url": item.get("itemWebUrl")
        })
    return results

# ===============================
# ⑤ メイン処理
# ===============================
def main():
    send_slack_message(f"🔍 eBayリサーチ開始: {SEARCH_QUERY}")

    try:
        items = fetch_ebay_items(SEARCH_QUERY, limit=5)

        if not items:
            send_slack_message("⚠️ 商品が見つかりませんでした。")
            return

        message_lines = [
            "✅ eBay API取得成功！ 最新の出品はこちら👇",
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        for item in items:
            message_lines.append(f"- {item['title']} ({item['price']})\n{item['url']}")

        send_slack_message("\n".join(message_lines))

    except Exception as e:
        send_slack_message(f"❌ エラー発生: {e}")
        print(f"❌ エラー詳細: {e}")

# ===============================
# ⑥ 実行
# ===============================
if __name__ == "__main__":
    main()

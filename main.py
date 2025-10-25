import os
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# ==== 環境変数読み込み ====
SLACK_BOT_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")

# ==== Slack通知関数 ====
def send_slack_message(message):
    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        print(f"✅ Slack通知成功: {message}")
    except SlackApiError as e:
        print(f"⚠️ Slack通知失敗: {e.response['error']}")

# ==== メイン処理 ====
def main():
    send_slack_message("🔍 eBayスクレイピング（テストモード）を開始します。")

    # 仮のテスト処理
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"現在時刻: {now}")

    # 完了通知
    send_slack_message("✅ GitHub ActionsからのSlack通知テスト完了！")

if __name__ == "__main__":
    main()

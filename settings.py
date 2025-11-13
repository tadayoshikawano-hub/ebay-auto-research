import os
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# Slack Bot Token（環境変数から読み込む）
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# 通知先チャンネル
SLACK_CHANNEL = "#ebay-auto-research"
# eBay API設定
EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_GLOBAL_ID = "EBAY-US"  # 米国eBayを対象

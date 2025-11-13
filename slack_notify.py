from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

# Slack通知クラス
class SlackNotifier:
    def __init__(self, bot_token):
        self.client = WebClient(token=bot_token)

    def send_message(self, channel, message):
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=message
            )
            print(f"✅ Slack通知成功: {response['ts']}")
        except SlackApiError as e:
            print(f"❌ Slack通知失敗: {e.response['error']}")

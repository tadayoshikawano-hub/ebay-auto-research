import os
import json
from datetime import datetime
from supabase import create_client
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# ===============================
# ① 環境設定
# ===============================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#profit-finder")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
slack = WebClient(token=SLACK_TOKEN)

# ===============================
# ② Slack送信関数
# ===============================
def send_slack(message):
    """Slackにメッセージ送信"""
    try:
        slack.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        print(f"✅ Slack通知成功: {message[:40]}...")
    except SlackApiError as e:
        print(f"⚠️ Slack送信エラー: {e.response['error']}")

# ===============================
# ③ Supabaseから最新データ2件を取得
# ===============================
def get_latest_data():
    res = supabase.table("sales_data").select("*").order("date", desc=True).limit(2).execute()
    data = res.data
    if len(data) < 2:
        print("⚠️ 比較できるデータが2件未満です。")
        return None, None
    return data[1], data[0]  # (前回, 最新)

# ===============================
# ④ 変化率を計算
# ===============================
def calc_change(old, new, field):
    try:
        old_val = float(old.get(field, 0))
        new_val = float(new.get(field, 0))
        if old_val == 0:
            return 0
        return round(((new_val - old_val) / old_val) * 100, 2)
    except Exception:
        return 0

# ===============================
# ⑤ レポート生成
# ===============================
def create_report(old, new):
    avg_change = calc_change(old, new, "avg_price")
    sales_change = calc_change(old, new, "total_sales")

    msg = f"🗓 {new['date']} 市場変化レポート（ポケモンカード）\n"
    msg += f"📊 販売件数：{new['total_sales']}件（{sales_change:+.2f}%）\n"
    msg += f"💰 平均価格：${new['avg_price']:.2f}（{avg_change:+.2f}%）\n"

    # キーワード比較
    old_kw = json.loads(json.dumps(old.get("top_keywords", {})))
    new_kw = json.loads(json.dumps(new.get("top_keywords", {})))
    trending = [k for k in new_kw if new_kw[k] > old_kw.get(k, 0) + 2]

    if trending:
        msg += "🔥 新たに上昇したキーワード: " + ", ".join(trending[:5]) + "\n"

    # キャラ比較
    old_char = json.loads(json.dumps(old.get("top_characters", {})))
    new_char = json.loads(json.dumps(new.get("top_characters", {})))
    rising = []
    falling = []
    for name, val in new_char.items():
        old_avg = old_char.get(name, {}).get("avg", 0)
        new_avg = val.get("avg", 0)
        if old_avg == 0:
            continue
        rate = ((new_avg - old_avg) / old_avg) * 100
        if rate > 20:
            rising.append(name)
        elif rate < -20:
            falling.append(name)

    if rising:
        msg += "📈 高騰キャラ: " + ", ".join(rising) + "\n"
    if falling:
        msg += "📉 下落キャラ: " + ", ".join(falling) + "\n"

    if abs(avg_change) < 5 and abs(sales_change) < 5 and not rising and not falling:
        msg += "📋 市場は安定しています。大きな変化はありません。"

    return msg

# ===============================
# ⑥ メイン処理
# ===============================
def main():
    old, new = get_latest_data()
    if not new or not old:
        return
    report = create_report(old, new)
    print("\n" + report)
    send_slack(report)

# ===============================
# ⑦ 実行
# ===============================
if __name__ == "__main__":
    main()

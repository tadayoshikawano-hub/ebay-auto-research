from config.settings import SLACK_BOT_TOKEN, SLACK_CHANNEL
from modules.slack_notify import SlackNotifier
from modules.google_sheet import GoogleSheet
from modules.ebay_scraper import EbayScraper
from modules.supabase_db import insert_item  # ← 追加
from datetime import datetime


def main():
    notifier = SlackNotifier(SLACK_BOT_TOKEN)
    notifier.send_message(SLACK_CHANNEL, "🔍 eBayスクレイピング開始...")

    sheet = GoogleSheet("eBayリサーチ管理シート")
    scraper = EbayScraper()

    try:
        items = scraper.search_sold_items("pokemon card", max_items=10)

        if not items:
            notifier.send_message(SLACK_CHANNEL, "⚠️ 商品が見つかりませんでした。")
            return

        for item in items:
            title = item["title"]
            price = item["price"]
            url = item["url"]

            # ✅ Googleスプレッド書き込み
            sheet.write_row([
                "", title, "", "ポケカ", "", url, "",
                price, "", "", "", "", "", "", "", "仕入候補", ""
            ])

            # ✅ Supabaseへ保存
            insert_item(
                title=title,
                price=price,
                profit=0,  # 後で利益計算ロジック追加予定
                date=datetime.now().isoformat(),
                source="eBay"
            )

        notifier.send_message(SLACK_CHANNEL, f"✅ {len(items)}件の商品を取得＆Supabaseへ保存しました！")

    except Exception as e:
        notifier.send_message(SLACK_CHANNEL, f"❌ エラー発生: {e}")
        raise


if __name__ == "__main__":
    main()

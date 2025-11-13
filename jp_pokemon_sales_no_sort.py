import os
import re
import time
import requests
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import Counter
from dotenv import load_dotenv
from supabase import create_client

# ===============================
# ① .envの読み込みと設定
# ===============================
load_dotenv()

EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
MARKETPLACE_ID = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabaseクライアント作成
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===============================
# ② 検索期間設定（過去90日）
# ===============================
end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=90)
start_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
end_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

# ===============================
# ③ eBay APIの共通設定
# ===============================
BASE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
COMMON_FILTER = f"itemLocationCountry:JP,soldDate:[{start_str}..{end_str}],price:[1..20000],buyingOptions:FIXED_PRICE"
HEADERS = {
    "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE_ID
}

# ===============================
# ④ ページネーションで販売データ取得
# ===============================
def fetch_all_items(category_id="183454", limit=100, max_pages=10):
    all_items = []
    offset = 0

    for page in range(max_pages):
        params = {
            "category_ids": category_id,
            "filter": COMMON_FILTER,
            "limit": str(limit),
            "offset": str(offset)
        }

        print(f"📦 ページ {page + 1} を取得中... (offset={offset})")
        res = requests.get(BASE_URL, headers=HEADERS, params=params)

        if res.status_code != 200:
            print("⚠️ APIエラー:", res.text)
            break

        data = res.json()
        items = data.get("itemSummaries", [])
        if not items:
            print("🔚 データ取得終了。")
            break

        all_items.extend(items)
        offset += limit
        time.sleep(1)

        if len(items) < limit:
            break

    print(f"✅ 総取得件数: {len(all_items)} 件")
    return all_items

# ===============================
# ⑤ Supabaseに保存
# ===============================
def save_sales_data(category, total, avg, median, min_price, top_keywords, top_characters):
    """Supabaseに分析結果を保存"""
    if not supabase:
        print("⚠️ Supabase接続情報が設定されていません。.envを確認してください。")
        return

    try:
        data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "category": category,
            "total_sales": total,
            "avg_price": avg,
            "median_price": median,
            "min_price": min_price,
            "top_keywords": top_keywords,
            "top_characters": top_characters
        }
        supabase.table("sales_data").insert(data).execute()
        print("✅ Supabaseへ保存完了！")
    except Exception as e:
        print(f"⚠️ Supabase保存エラー: {e}")

# ===============================
# ⑥ データ分析処理
# ===============================
def analyze_items(items):
    exclude_keywords = [
        "yugioh", "one piece", "weiss", "digimon",
        "dragon ball", "vanguard", "magic the gathering"
    ]

    filtered = []
    for item in items:
        title = item.get("title", "").lower()
        seller = item.get("seller", {}).get("username", "").lower()
        if (not any(ex in title for ex in exclude_keywords)) and ("japan" in seller or "japan" in title):
            filtered.append(item)

    print(f"📊 フィルタ後の有効データ数: {len(filtered)} 件")

    prices, titles = [], []
    for item in filtered:
        try:
            price = float(item["price"]["value"])
            if 1 <= price <= 20000:
                prices.append(price)
                titles.append(item.get("title", "").lower())
        except:
            continue

    if not prices:
        print("⚠️ 有効な販売データなし。")
        return

    avg_price = np.mean(prices)
    median_price = np.median(prices)
    min_price = np.min(prices)
    max_price = np.max(prices)

    print("\n📈 価格統計（sort解除・自然順）")
    print(f"平均価格: ${avg_price:.2f}")
    print(f"中央値: ${median_price:.2f}")
    print(f"最低: ${min_price:.2f}, 最高: ${max_price:.2f}")

    ignore_words = [
        "pokemon", "card", "japan", "tcg", "game",
        "rare", "set", "promo", "new", "used",
        "sealed", "edition", "japanese"
    ]
    words = []
    for title in titles:
        clean = re.sub(r"[^a-zA-Z0-9\s]", "", title)
        for w in clean.split():
            if len(w) > 2 and w not in ignore_words:
                words.append(w.lower())

    counter = Counter(words)
    print("\n🔥 売れ筋キーワードTOP15")
    for word, count in counter.most_common(15):
        print(f"- {word.title()} : {count}件")

    targets = ["charizard", "pikachu", "mewtwo", "eevee", "gengar", "lugia", "rayquaza", "snorlax"]
    print("\n🐉 特定カード別の販売傾向")
    top_characters = {}
    for name in targets:
        related = [
            float(item["price"]["value"])
            for item in filtered if re.search(name, item.get("title", "").lower())
        ]
        if related:
            avg_val = float(np.mean(related))
            print(f"{name.title()} : {len(related)}件, 平均 ${avg_val:.2f}")
            top_characters[name] = {"count": len(related), "avg": avg_val}
        else:
            print(f"{name.title()} : 該当なし")
            top_characters[name] = {"count": 0, "avg": 0}

    # Supabaseに保存
    save_sales_data(
        category="ポケモンカード",
        total=len(filtered),
        avg=float(avg_price),
        median=float(median_price),
        top_keywords=dict(counter.most_common(15)),
        top_characters=top_characters
    )

# ===============================
# ⑦ メイン処理
# ===============================
if __name__ == "__main__":
    print("🌍 eBay ポケモンカード市場分析（sort解除＋Supabase保存対応）")
    items = fetch_all_items(limit=100, max_pages=10)
    analyze_items(items)

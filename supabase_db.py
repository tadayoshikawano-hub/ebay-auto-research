from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_sales_data(category, total, avg, median, top_keywords, top_characters):
    """リサーチ結果をSupabaseに保存"""
    try:
        data = {
            "date": __import__("datetime").datetime.now().strftime("%Y-%m-%d"),
            "category": category,
            "total_sales": total,
            "avg_price": avg,
            "median_price": median,
            "top_keywords": top_keywords,
            "top_characters": top_characters
        }
        supabase.table("sales_data").insert(data).execute()
        print("✅ Supabaseへ保存完了！")
    except Exception as e:
        print(f"⚠️ Supabase保存エラー: {e}")

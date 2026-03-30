import os
from supabase import create_client, Client

# These lines safely ask Railway for the keys!
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def save_new_user(user_id, username):
    user_data = supabase.table("users").select("*").eq("user_id", user_id).execute()
    
    if not user_data.data:
        supabase.table("users").insert({
            "user_id": user_id,
            "username": username,
            "join_date": "2026-03-30"
        }).execute()
        print("✅ New user saved to Supabase!")

def save_new_trade(user_id, symbol, side, amount, pnl):
    supabase.table("trades").insert({
        "user_id": user_id,
        "symbol": symbol,
        "side": side,
        "amount": amount,
        "pnl": pnl
    }).execute()
    print("✅ Trade saved to Supabase!")

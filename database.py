import os
from supabase import create_client, Client

# 1. This connects to the keys you added to Railway
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 2. This function saves a new user when they join
def save_new_user(user_id, username):
    # Check if the user is already in our 'users' folder
    user_data = supabase.table("users").select("*").eq("user_id", user_id).execute()
    
    # If they are not in there, add them!
    if not user_data.data:
        supabase.table("users").insert({
            "user_id": user_id,
            "username": username,
            "join_date": "2026-03-30"
        }).execute()
        print("✅ New user saved to Supabase!")

# 3. This function saves a trade when the bot buys/sells
def save_new_trade(user_id, symbol, side, amount, pnl):
    supabase.table("trades").insert({
        "user_id": user_id,
        "symbol": symbol,
        "side": side,
        "amount": amount,
        "pnl": pnl
    }).execute()
    print("✅ Trade saved to Supabase!")

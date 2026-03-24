import os
import ccxt
from datetime import datetime

class Trader:
    def __init__(self):
        self.exchange = ccxt.bitget({
            'apiKey': os.getenv("BITGET_API_KEY"),
            'secret': os.getenv("BITGET_SECRET_KEY"),
            'password': os.getenv("BITGET_PASSPHRASE"),
            'options': {'defaultType': 'spot'},
        })

    def get_portfolio(self) -> str:
        try:
            balance = self.exchange.fetch_balance()
            lines = ["💼 *Portfolio*\n"]
            total_usdt = 0.0

            for asset, data in balance['total'].items():
                if data > 0:
                    usdt_value = 0.0
                    if asset == 'USDT':
                        usdt_value = data
                    else:
                        try:
                            ticker = self.exchange.fetch_ticker(f"{asset}/USDT")
                            usdt_value = data * ticker['last']
                        except Exception:
                            pass
                    if usdt_value > 0.01:
                        total_usdt += usdt_value
                        lines.append(f"• *{asset}*: {data:.6f} ≈ ${usdt_value:.2f}")

            lines.append(f"\n📊 *Total Est. Value*: ${total_usdt:.2f} USDT")
            lines.append(f"🕐 Updated: {datetime.utcnow().strftime('%H:%M UTC')}")
            return "\n".join(lines)
        except Exception as e:
            raise RuntimeError(f"Portfolio error: {e}")

    def market_buy(self, symbol: str, amount_usdt: float) -> str:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            quantity = amount_usdt / price
            order = self.exchange.create_market_buy_order(symbol, quantity)
            return (
                f"✅ *Buy Order Executed*\n\n"
                f"Symbol: `{symbol}`\n"
                f"Spent: ${amount_usdt:.2f} USDT\n"
                f"Received: {quantity:.6f}\n"
                f"Price: ${price:,.2f}\n"
                f"Order ID: `{order['id']}`"
            )
        except Exception as e:
            raise RuntimeError(f"Buy error: {e}")

    def market_sell(self, symbol: str, quantity: float) -> str:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            total_usdt = quantity * price
            order = self.exchange.create_market_sell_order(symbol, quantity)
            return (
                f"✅ *Sell Order Executed*\n\n"
                f"Symbol: `{symbol}`\n"
                f"Sold: {quantity:.6f}\n"
                f"Received: ${total_usdt:.2f} USDT\n"
                f"Price: ${price:,.2f}\n"
                f"Order ID: `{order['id']}`"
            )
        except Exception as e:
            raise RuntimeError(f"Sell error: {e}")

    def auto_sell(self, symbol: str) -> str:
        try:
            base_asset = symbol.replace("/USDT", "")
            balance = self.exchange.fetch_balance()
            quantity = balance['free'].get(base_asset, 0.0)
            if quantity <= 0:
                return f"⚠️ No {base_asset} balance to sell."
            return self.market_sell(symbol, quantity)
        except Exception as e:
            raise RuntimeError(f"Auto-sell error: {e}")

    def get_price(self, symbol: str) -> float:
        ticker = self.exchange.fetch_ticker(symbol)
        return ticker['last']

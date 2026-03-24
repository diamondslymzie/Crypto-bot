import os
from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime

class Trader:
    def __init__(self):
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        testnet = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.testnet = testnet

    def get_portfolio(self) -> str:
        account = self.client.get_account()
        balances = [
            b for b in account["balances"]
            if float(b["free"]) > 0 or float(b["locked"]) > 0
        ]
        if not balances:
            return "💼 *Portfolio*\n\nNo assets found."
        lines = [f"💼 *Portfolio* {'(Testnet)' if self.testnet else ''}\n"]
        total_usdt = 0.0
        for b in balances:
            asset = b["asset"]
            free = float(b["free"])
            locked = float(b["locked"])
            total = free + locked
            usdt_value = 0.0
            if asset == "USDT":
                usdt_value = total
            else:
                try:
                    ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDT")
                    usdt_value = total * float(ticker["price"])
                except Exception:
                    pass
            total_usdt += usdt_value
            if usdt_value > 0.01:
                lines.append(
                    f"• *{asset}*: {total:.6f}"
                    + (f" ≈ ${usdt_value:.2f}" if usdt_value > 0 else "")
                    + (f" 🔒{locked:.6f}" if locked > 0 else "")
                )
        lines.append(f"\n📊 *Total Est. Value*: ${total_usdt:.2f} USDT")
        lines.append(f"🕐 Updated: {datetime.utcnow().strftime('%H:%M UTC')}")
        return "\n".join(lines)

    def market_buy(self, symbol: str, amount_usdt: float) -> str:
        try:
            order = self.client.order_market_buy(
                symbol=symbol,
                quoteOrderQty=amount_usdt
            )
            filled_qty = sum(float(f["qty"]) for f in order["fills"])
            avg_price = sum(float(f["price"]) * float(f["qty"]) for f in order["fills"]) / filled_qty
            return (
                f"✅ *Buy Order Executed*\n\n"
                f"Symbol: `{symbol}`\n"
                f"Spent: ${amount_usdt:.2f} USDT\n"
                f"Received: {filled_qty:.6f}\n"
                f"Avg Price: ${avg_price:,.2f}\n"
                f"Order ID: `{order['orderId']}`"
            )
        except BinanceAPIException as e:
            raise RuntimeError(f"Binance error: {e.message}")

    def market_sell(self, symbol: str, quantity: float) -> str:
        try:
            order = self.client.order_market_sell(
                symbol=symbol,
                quantity=self._format_quantity(symbol, quantity)
            )
            filled_qty = sum(float(f["qty"]) for f in order["fills"])
            total_usdt = sum(float(f["price"]) * float(f["qty"]) for f in order["fills"])
            avg_price = total_usdt / filled_qty
            return (
                f"✅ *Sell Order Executed*\n\n"
                f"Symbol: `{symbol}`\n"
                f"Sold: {filled_qty:.6f}\n"
                f"Received: ${total_usdt:.2f} USDT\n"
                f"Avg Price: ${avg_price:,.2f}\n"
                f"Order ID: `{order['orderId']}`"
            )
        except BinanceAPIException as e:
            raise RuntimeError(f"Binance error: {e.message}")

    def auto_sell(self, symbol: str) -> str:
        base_asset = symbol.replace("USDT", "")
        account = self.client.get_account()
        balance = next(
            (float(b["free"]) for b in account["balances"] if b["asset"] == base_asset),
            0.0
        )
        if balance <= 0:
            return f"⚠️ No {base_asset} balance to sell."
        return self.market_sell(symbol, balance)

    def _format_quantity(self, symbol: str, quantity: float) -> str:
        info = self.client.get_symbol_info(symbol)
        lot_filter = next(f for f in info["filters"] if f["filterType"] == "LOT_SIZE")
        step_size = float(lot_filter["stepSize"])
        precision = len(str(step_size).rstrip("0").split(".")[-1]) if "." in str(step_size) else 0
        return f"{quantity:.{precision}f}"

    def get_price(self, symbol: str) -> float:
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])

import os
import json
import ccxt
import anthropic
import pandas as pd
import ta
from datetime import datetime

class AIStrategy:
    def __init__(self):
        self.anthropic = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.exchange = ccxt.bitget({
            'apiKey': os.getenv("BITGET_API_KEY"),
            'secret': os.getenv("BITGET_SECRET_KEY"),
            'password': os.getenv("BITGET_PASSPHRASE"),
            'options': {'defaultType': 'spot'},
        })

    def _get_klines(self, symbol: str, interval="1h", limit=100) -> pd.DataFrame:
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["open_time", "open", "high", "low", "close", "volume"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df

    def _compute_indicators(self, df: pd.DataFrame) -> dict:
        close = df["close"]
        rsi = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]
        macd = ta.trend.MACD(close)
        macd_line = macd.macd().iloc[-1]
        macd_signal = macd.macd_signal().iloc[-1]
        bb = ta.volatility.BollingerBands(close, window=20)
        bb_upper = bb.bollinger_hband().iloc[-1]
        bb_lower = bb.bollinger_lband().iloc[-1]
        ema_20 = ta.trend.EMAIndicator(close, window=20).ema_indicator().iloc[-1]
        ema_50 = ta.trend.EMAIndicator(close, window=50).ema_indicator().iloc[-1]
        current_price = close.iloc[-1]
        price_24h_ago = close.iloc[-24] if len(close) >= 24 else close.iloc[0]
        change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
        return {
            "price": round(current_price, 2),
            "change_24h": round(change_24h, 2),
            "rsi_14": round(rsi, 2),
            "macd": round(macd_line, 4),
            "macd_signal": round(macd_signal, 4),
            "macd_histogram": round(macd_line - macd_signal, 4),
            "bb_upper": round(bb_upper, 2),
            "bb_lower": round(bb_lower, 2),
            "ema_20": round(ema_20, 2),
            "ema_50": round(ema_50, 2),
            "volume_latest": round(df["volume"].iloc[-1], 2),
            "volume_avg": round(df["volume"].tail(20).mean(), 2),
        }

    def analyze(self, symbol: str) -> str:
        df = self._get_klines(symbol)
        indicators = self._compute_indicators(df)
        prompt = f"""You are a professional crypto trading analyst. Analyze the following technical indicators for {symbol} and provide a concise trading analysis.

Technical Data:
{json.dumps(indicators, indent=2)}

Provide:
1. Market sentiment (Bullish/Bearish/Neutral)
2. Key observations (2-3 bullet points)
3. Trading signal: BUY / SELL / HOLD
4. Confidence level: Low / Medium / High
5. Brief rationale (1-2 sentences)

Format your response for Telegram using *bold* for labels. Keep it under 200 words."""

        message = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        analysis_text = message.content[0].text
        header = (
            f"🤖 *AI Analysis — {symbol}*\n"
            f"💰 Price: ${indicators['price']:,} ({indicators['change_24h']:+.2f}% 24h)\n"
            f"📊 RSI: {indicators['rsi_14']} | MACD: {'+' if indicators['macd_histogram'] > 0 else ''}{indicators['macd_histogram']}\n\n"
        )
        return header + analysis_text

    def get_signal(self, symbol: str) -> str:
        df = self._get_klines(symbol)
        indicators = self._compute_indicators(df)
        prompt = f"""You are a crypto trading bot. Given these indicators for {symbol}, respond with ONLY a JSON object:
{{"signal": "BUY|SELL|HOLD", "confidence": "low|medium|high", "reason": "one sentence"}}

Indicators:
{json.dumps(indicators)}"""

        message = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        try:
            raw = message.content[0].text.strip()
            data = json.loads(raw)
            signal = data.get("signal", "HOLD")
            confidence = data.get("confidence", "low")
            reason = data.get("reason", "")
            emoji = {"BUY": "📈", "SELL": "📉", "HOLD": "⏸️"}.get(signal, "⏸️")
            return f"{emoji} Signal: *{signal}* (Confidence: {confidence})\n_{reason}_"
        except Exception:
            return "Signal check completed."

    def get_action(self, symbol: str) -> str:
        df = self._get_klines(symbol)
        indicators = self._compute_indicators(df)
        prompt = f"""Crypto trading signal for {symbol}. Respond ONLY with JSON:
{{"signal": "BUY|SELL|HOLD", "confidence": "low|medium|high"}}

Indicators: {json.dumps(indicators)}"""

        message = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        try:
            data = json.loads(message.content[0].text.strip())
            if data.get("confidence") == "high":
                return data.get("signal", "HOLD")
        except Exception:
            pass
        return "HOLD"

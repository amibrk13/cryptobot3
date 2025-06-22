from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
import pandas as pd
import ta
from concurrent.futures import ThreadPoolExecutor  # Parallelize requests
import asyncio

app = FastAPI()

BYBIT_API = "https://api.bybit.com"
SYMBOLS = ["BTCUSDT", "BONKUSDT"]
TIMEFRAMES = {
    "1m": "1", "3m": "3", "5m": "5", "15m": "15", 
    "30m": "30", "1h": "60", "2h": "120", "4h": "240", "1d": "D"
}

def fetch_candles(symbol: str, interval: str, limit: int = 100) -> dict:
    """Fetch candles for a single timeframe from Bybit."""
    url = f"{BYBIT_API}/spot/v3/public/quote/kline?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url).json()
    if response["retCode"] != 0:
        return {"error": f"Bybit API error for {interval}"}
    return response["result"]["list"]

def calculate_indicators(df: pd.DataFrame) -> dict:
    """Calculate all indicators for a single timeframe."""
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    # EMAs
    df["ema_50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["ema_200"] = ta.trend.ema_indicator(df["close"], window=200)

    # RSI & Stoch RSI
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)
    stoch_rsi = ta.momentum.StochRSIIndicator(df["close"], window=14, smooth1=3, smooth2=3)
    df["stoch_rsi_k"] = stoch_rsi.stochrsi_k()
    df["stoch_rsi_d"] = stoch_rsi.stochrsi_d()

    latest = df.iloc[-1]
    return {
        "close_price": latest["close"],
        "volume": latest["volume"],
        "indicators": {
            "ema_50": latest["ema_50"],
            "ema_200": latest["ema_200"],
            "rsi": latest["rsi"],
            "stoch_rsi_k": latest["stoch_rsi_k"],
            "stoch_rsi_d": latest["stoch_rsi_d"],
        }
    }

async def process_timeframe(symbol: str, tf: str, executor: ThreadPoolExecutor) -> dict:
    """Process one timeframe asynchronously."""
    loop = asyncio.get_event_loop()
    candles = await loop.run_in_executor(executor, fetch_candles, symbol, TIMEFRAMES[tf])
    if "error" in candles:
        return {tf: candles["error"]}
    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    return {tf: calculate_indicators(df)}

@app.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    if symbol not in SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbol not supported. Use: {SYMBOLS}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        tasks = [process_timeframe(symbol, tf, executor) for tf in TIMEFRAMES]
        results = await asyncio.gather(*tasks)

    return JSONResponse({
        "symbol": symbol,
        "timeframes": {k: v for res in results for k, v in res.items()}
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
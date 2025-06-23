import os
from fastapi import FastAPI, HTTPException
import requests
from fastapi.responses import JSONResponse

app = FastAPI()

# Configuration
BYBIT_API = "https://api.bybit.com/v5/market"
TIMEFRAMES = {
    "1m": "1", "3m": "3", "5m": "5", "15m": "15",
    "30m": "30", "1h": "60", "2h": "120", "4h": "240", "1d": "D"
}
SYMBOLS = ["BTCUSDT", "BONKUSDT"]
REQUEST_TIMEOUT = 5  # seconds

@app.get("/health")
async def health_check():
    return {"status": "alive"}

@app.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    symbol = symbol.upper()
    if symbol not in SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Supported symbols: {SYMBOLS}")

    try:
        # Get ticker data (for indicators)
        ticker_url = f"{BYBIT_API}/tickers?category=spot&symbol={symbol}"
        ticker = requests.get(ticker_url, timeout=REQUEST_TIMEOUT).json()
        ticker = ticker["result"]["list"][0]

        # Get all timeframes
        results = {"symbol": symbol, "timeframes": {}}
        for tf_name, tf_code in TIMEFRAMES.items():
            kline_url = f"{BYBIT_API}/kline?category=spot&symbol={symbol}&interval={tf_code}&limit=1"
            kline = requests.get(kline_url, timeout=REQUEST_TIMEOUT).json()
            candle = kline["result"]["list"][0]

            results["timeframes"][tf_name] = {
                "close": float(candle[4]),
                "volume": float(candle[5]),
                "indicators": {
                    "ema_50": float(ticker["ema50"]),
                    "ema_200": float(ticker["ema200"]),
                    "rsi": float(ticker["rsi"]),
                    "stoch_rsi_k": float(ticker["stochRsiK"]),
                    "stoch_rsi_d": float(ticker["stochRsiD"])
                }
            }

        return JSONResponse(results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

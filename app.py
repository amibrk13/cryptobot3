from fastapi import FastAPI, HTTPException
import requests
from fastapi.responses import JSONResponse

app = FastAPI()
BYBIT_API = "https://api.bybit.com/v5/market/tickers?category=spot"

# Supported timeframes (Bybit's interval codes)
TIMEFRAMES = {
    "1m": "1", "3m": "3", "5m": "5", "15m": "15", 
    "30m": "30", "1h": "60", "2h": "120", "4h": "240", "1d": "D"
}

@app.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    try:
        # Fetch precomputed indicators from Bybit
        ticker_url = f"{BYBIT_API}&symbol={symbol}"
        ticker_data = requests.get(ticker_url, timeout=5).json()
        ticker = ticker_data["result"]["list"][0]

        # Fetch latest close price for each timeframe
        results = {"symbol": symbol, "timeframes": {}}
        for tf_name, tf_code in TIMEFRAMES.items():
            kline_url = f"https://api.bybit.com/v5/market/kline?category=spot&symbol={symbol}&interval={tf_code}&limit=1"
            kline_data = requests.get(kline_url, timeout=5).json()
            latest_candle = kline_data["result"]["list"][0]

            results["timeframes"][tf_name] = {
                "close_price": latest_candle[4],  # Close price
                "volume": latest_candle[5],       # Volume
                "indicators": {
                    "ema_50": ticker["ema50"],    # Global EMA (same for all timeframes)
                    "ema_200": ticker["ema200"],
                    "rsi": ticker["rsi"],
                    "stoch_rsi_k": ticker["stochRsiK"],
                    "stoch_rsi_d": ticker["stochRsiD"]
                }
            }

        return JSONResponse(results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

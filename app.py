from fastapi import FastAPI
import requests

app = FastAPI()
BYBIT_API = "https://api.bybit.com/v5/market/tickers?category=spot"

@app.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    response = requests.get(f"{BYBIT_API}&symbol={symbol}").json()
    ticker = response["result"]["list"][0]
    return {
        "symbol": symbol,
        "price": ticker["lastPrice"],
        "ema_50": ticker["ema50"],
        "ema_200": ticker["ema200"],
        "rsi": ticker["rsi"]
    }

# ↓ Keep this for local runs ↓
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

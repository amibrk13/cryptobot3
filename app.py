from fastapi import FastAPI, HTTPException
import requests
import os
from fastapi.responses import JSONResponse

app = FastAPI()

BYBIT_API = os.getenv("BYBIT_API", "https://api.bybit.com/v5/market/tickers?category=spot")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "5"))  # seconds

@app.get("/health")
async def health_check():
    return {"status": "OK"}

@app.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    try:
        # Validate symbol
        symbol = symbol.upper()
        if symbol not in ["BTCUSDT", "BONKUSDT"]:
            raise HTTPException(status_code=400, detail="Unsupported symbol")

        # Fetch data with timeout
        response = requests.get(
            f"{BYBIT_API}&symbol={symbol}",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        ticker = response.json().get("result", {}).get("list", [{}])[0]

        return JSONResponse({
            "symbol": symbol,
            "price": ticker.get("lastPrice"),
            "ema_50": ticker.get("ema50"),
            "ema_200": ticker.get("ema200"),
            "rsi": ticker.get("rsi")
        })

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Bybit API timeout")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI
import requests

app = FastAPI()
BYBIT_API = "https://api.bybit.com/v5/market/tickers?category=spot"

# Timeframes mapped to Bybit's kline intervals
TIMEFRAMES = {
    "1m": "1", "3m": "3", "5m": "5", "15m": "15", 
    "30m": "30", "1h": "60", "2h": "120", "4h": "240", "1d": "D"
}

@app.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    # Fetch the latest ticker data (all precomputed indicators)
    ticker_url = f"{BYBIT_API}&symbol={symbol}"
    ticker_data = requests.get(ticker_url).json()["result"]["list"][0]
    
    # For timeframes, use Bybit's "kline" endpoint (limit=1 for latest candle)
    results = {"symbol": symbol, "timeframes": {}}
    
    for tf_name, tf_code in TIMEFRAMES.items():
        kline_url = f"https://api.bybit.com/v5/market/kline?category=spot&symbol={symbol}&interval={tf_code}&limit=1"
        kline_data = requests.get(kline_url).json()
        
        # Extract close price and volume
        latest_candle = kline_data["result"]["list"][0]
        results["timeframes"][tf_name] = {
            "close_price": latest_candle[4],  # 4th field is "close"
            "volume": latest_candle[5],       # 5th field is "volume"
            "indicators": {
                # Note: Bybit's V5 doesn't provide timeframe-specific EMAs/RSI. 
                # We use the global ticker values as placeholders.
                "ema_50": ticker_data["ema50"],  
                "ema_200": ticker_data["ema200"],
                "rsi": ticker_data["rsi"],
                "stoch_rsi_k": ticker_data["stochRsiK"],
                "stoch_rsi_d": ticker_data["stochRsiD"]
            }
        }
    
    return results

import yfinance as yf
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW_MARKET = os.path.join(BASE_DIR, "../../data/raw/market")

os.makedirs(DATA_RAW_MARKET, exist_ok=True)

tickers = {
    "msci_world": "URTH",                                               #MSCI WORLD ETF
    "gold": "GC=F",                                                     #gold futures
    "bitcoin": "BTC-USD"                                                #bitcoin price in USD
}

for name, ticker in tickers.items():
    df = yf.download(ticker, start="2025-01-01", interval="1h")         #fetch hourly data from the slightly befor the start of the presidency to now     
    df.to_csv(os.path.join(DATA_RAW_MARKET, f"{name}.csv"))                               #save the data to a the raw csv file
    print(f"Saved {name}, to file {os.path.join(DATA_RAW_MARKET, f'{name}.csv')}")                                              #print a message to indicate that the data has been saved

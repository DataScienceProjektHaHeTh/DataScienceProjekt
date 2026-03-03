import yfinance as yf

tickers = {
    "msci_world": "URTH",                               #MSCI WORLD ETF
    "gold": "GC=F",                                     #gold futures
    "bitcoin": "BTC-USD"                                #bitcoin price in USD
}

for name, ticker in tickers.items():
    df = yf.download(ticker, start="2025-01-20")        #fetch data from the start of the presidency to now     
    df.to_csv(f"data/raw/{name}_raw.csv")                   #save the data to a the raw csv file
    print(f"Saved {name}")                              #print a message to indicate that the data has been saved
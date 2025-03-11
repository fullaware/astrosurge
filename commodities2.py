import yfinance as yf

# Define the commodity symbols
commodities = {
    "gold": "GC=F",
    "silver": "SI=F",
    "platinum": "PL=F",
    "copper": "HG=F",
    "palladium": "PA=F"
}

# Fetch the current value of each commodity
for name, symbol in commodities.items():
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    current_price = data['Close'].iloc[-1]
    print(f"The current price of {name} is {current_price}")
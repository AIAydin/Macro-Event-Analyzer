# Macro Event Impact Tracker - Setup Guide

A real-time dashboard for analyzing market reactions to economic data releases.

## Requirements

- Python 3.10+
- pip

## Local Development

### 1. Clone the Repository

```bash
git clone https://github.com/AIAydin/Macro-Event-Analyzer.git
cd Macro-Event-Analyzer
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get a Free FRED API Key (Required for Live Data)

1. Go to [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
2. Create a free account and request an API key
3. Set the environment variable:

```bash
export FRED_API_KEY="your_api_key_here"
```

### 5. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Deployment (Streamlit Cloud)

### 1. Push to GitHub

Ensure your code is pushed to a GitHub repository.

### 2. Add Secrets in Streamlit Cloud

1. Go to your app → Settings → Secrets
2. Add: `FRED_API_KEY = "your_key_here"`

### 3. Deploy

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app**
3. Select your repository and branch
4. Set **Main file path** to `app.py`
5. Click **Deploy**

## Project Structure

```
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── data/
│   ├── economic_events.py # Economic events data fetcher (FRED API)
│   └── market_data.py     # Market data fetcher (yfinance)
└── .gitignore
```

## Features

- **Economic Events Table**: View recent macro events with actual vs. forecast data
- **Price Action Charts**: Candlestick charts showing market reaction around events
- **Multi-Asset Heatmap**: Cross-asset return comparison
- **Category Performance**: Aggregated returns by asset class
- **Time Windows**: Analyze 1m, 5m, 15m, 30m, 1h, and 4h reactions

## Live Data Sources

| Indicator | FRED Series | Description |
|-----------|-------------|-------------|
| CPI | CPIAUCSL | Consumer Price Index (YoY %) |
| Core CPI | CPILFESL | Core CPI ex food/energy |
| NFP | PAYEMS | Non-Farm Payrolls |
| Unemployment | UNRATE | Unemployment Rate |
| Fed Funds | FEDFUNDS | Federal Funds Rate |
| GDP | GDP | Gross Domestic Product |
| Retail Sales | RSAFS | Retail Sales (MoM %) |
| Industrial Production | INDPRO | Industrial Production |
| Housing Starts | HOUST | Housing Starts |

"""Fetch market data for equities, FX, rates, and volatility."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import pytz


class MarketDataFetcher:
    """Fetches market data around economic event times."""
    
    # Asset tickers by category
    ASSETS = {
        'Equities': {
            'SPY': 'S&P 500 ETF',
            'QQQ': 'Nasdaq 100 ETF', 
            'IWM': 'Russell 2000 ETF',
            'DIA': 'Dow Jones ETF',
        },
        'FX': {
            'EURUSD=X': 'EUR/USD',
            'GBPUSD=X': 'GBP/USD',
            'USDJPY=X': 'USD/JPY',
            'DX-Y.NYB': 'Dollar Index',
        },
        'Rates': {
            'TLT': '20+ Year Treasury',
            'IEF': '7-10 Year Treasury',
            'SHY': '1-3 Year Treasury',
            '^TNX': '10Y Yield',
        },
        'Volatility': {
            '^VIX': 'VIX Index',
            'UVXY': 'Ultra VIX ETF',
            'SVXY': 'Short VIX ETF',
        }
    }
    
    # Time windows for analysis (in minutes)
    TIME_WINDOWS = [1, 5, 15, 30, 60, 240]
    
    def __init__(self):
        self.tz = pytz.timezone('America/New_York')
        self._cache = {}
    
    def get_asset_categories(self) -> List[str]:
        """Get available asset categories."""
        return list(self.ASSETS.keys())
    
    def get_assets_by_category(self, category: str) -> Dict[str, str]:
        """Get assets for a specific category."""
        return self.ASSETS.get(category, {})
    
    def get_all_tickers(self) -> List[str]:
        """Get all available tickers."""
        tickers = []
        for category in self.ASSETS.values():
            tickers.extend(category.keys())
        return tickers
    
    def fetch_intraday_data(self, ticker: str, event_date: datetime,
                            hours_before: int = 2, hours_after: int = 6) -> Optional[pd.DataFrame]:
        """Fetch intraday data around an event. Uses appropriate interval based on recency."""
        try:
            now = datetime.now(self.tz)
            event_date_tz = event_date
            if event_date_tz.tzinfo is None:
                event_date_tz = self.tz.localize(event_date_tz)

            days_ago = (now - event_date_tz).days

            ticker_obj = yf.Ticker(ticker)

            # Try progressively coarser intervals
            intervals_to_try = []
            if days_ago <= 7:
                intervals_to_try = ['1m', '5m', '15m', '1h', '1d']
            elif days_ago <= 60:
                intervals_to_try = ['5m', '15m', '1h', '1d']
            else:
                intervals_to_try = ['1h', '1d']

            for interval in intervals_to_try:
                try:
                    if interval in ['1m', '5m', '15m']:
                        # For intraday: fetch the whole trading day(s)
                        fetch_start = event_date.replace(hour=0, minute=0, second=0)
                        fetch_end = (event_date + timedelta(days=1)).replace(hour=23, minute=59)
                    elif interval == '1h':
                        fetch_start = event_date - timedelta(days=2)
                        fetch_end = event_date + timedelta(days=2)
                    else:
                        fetch_start = event_date - timedelta(days=10)
                        fetch_end = event_date + timedelta(days=10)

                    # Include pre-market and after-hours data
                    df = ticker_obj.history(start=fetch_start, end=fetch_end, interval=interval, prepost=True)

                    if not df.empty:
                        # Ensure timezone aware
                        if df.index.tz is None:
                            df.index = df.index.tz_localize('America/New_York')
                        else:
                            df.index = df.index.tz_convert('America/New_York')
                        return df
                except Exception:
                    continue

            return None

        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None
    
    def fetch_daily_data(self, ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Fetch daily data for a ticker."""
        try:
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start_date, end=end_date, interval='1d')
            return df if not df.empty else None
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def calculate_returns(self, df: pd.DataFrame, event_time: datetime,
                         windows: Optional[List[int]] = None) -> Dict[str, float]:
        """Calculate returns for different time windows after event."""
        if df is None or df.empty:
            return {}

        windows = windows or self.TIME_WINDOWS
        returns = {}

        try:
            event_time_tz = event_time
            if event_time_tz.tzinfo is None:
                event_time_tz = self.tz.localize(event_time_tz)

            # Get price at or just before event
            before_event = df[df.index <= event_time_tz]
            if before_event.empty:
                if len(df) > 0:
                    base_price = df['Close'].iloc[0]
                    base_time = df.index[0]
                else:
                    return {}
            else:
                base_price = before_event['Close'].iloc[-1]
                base_time = before_event.index[-1]

            # Calculate returns for each time window
            for window in windows:
                end_time = event_time_tz + timedelta(minutes=window)
                after_window = df[(df.index > base_time) & (df.index <= end_time)]

                if not after_window.empty:
                    end_price = after_window['Close'].iloc[-1]
                    returns[f'{window}m'] = ((end_price / base_price) - 1) * 100
                else:
                    # Try to find closest available data point
                    after_event = df[df.index > base_time]
                    if not after_event.empty:
                        end_price = after_event['Close'].iloc[min(len(after_event)-1, windows.index(window))]
                        returns[f'{window}m'] = ((end_price / base_price) - 1) * 100
                    else:
                        returns[f'{window}m'] = np.nan

        except Exception as e:
            print(f"Error calculating returns: {e}")

        return returns

    def get_multi_asset_reaction(self, event_time: datetime,
                                 categories: Optional[List[str]] = None) -> pd.DataFrame:
        """Get reaction data for multiple assets around an event."""
        categories = categories or list(self.ASSETS.keys())
        results = []

        for category in categories:
            assets = self.ASSETS.get(category, {})
            for ticker, name in assets.items():
                df = self.fetch_intraday_data(ticker, event_time)
                if df is not None and not df.empty:
                    returns = self.calculate_returns(df, event_time)
                    results.append({
                        'Category': category,
                        'Ticker': ticker,
                        'Name': name,
                        **returns
                    })

        return pd.DataFrame(results)


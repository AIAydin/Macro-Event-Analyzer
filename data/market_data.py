"""Fetch market data from Yahoo Finance."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import yfinance as yf
import pytz


class MarketDataFetcher:
    """Fetches market data from Yahoo Finance."""
    
    ASSETS = {
        'Equities': {
            'SPY': 'S&P 500 ETF',
            'QQQ': 'Nasdaq 100 ETF',
            'IWM': 'Russell 2000 ETF',
            'DIA': 'Dow Jones ETF',
        },
        'Fixed Income': {
            '^TNX': '10-Year Treasury Yield',
            '^TYX': '30-Year Treasury Yield',
            'TLT': '20+ Year Treasury ETF',
            'IEF': '7-10 Year Treasury ETF',
        },
        'Currencies': {
            'DX-Y.NYB': 'US Dollar Index',
            'EURUSD=X': 'EUR/USD',
            'USDJPY=X': 'USD/JPY',
            'GBPUSD=X': 'GBP/USD',
        },
        'Commodities': {
            'GC=F': 'Gold Futures',
            'CL=F': 'Crude Oil Futures',
            'SI=F': 'Silver Futures',
        },
        'Volatility': {
            '^VIX': 'VIX Index',
        },
    }
    
    def __init__(self):
        self.tz = pytz.timezone('America/New_York')
    
    def get_asset_categories(self) -> List[str]:
        """Get list of asset categories."""
        return list(self.ASSETS.keys())
    
    def get_assets_by_category(self, category: str) -> Dict[str, str]:
        """Get assets in a category."""
        return self.ASSETS.get(category, {})
    
    def fetch_intraday_data(self, ticker: str, event_time: datetime,
                            hours_before: int = 1, hours_after: int = 2) -> Optional[pd.DataFrame]:
        """Fetch intraday data around an event time."""
        try:
            if event_time.tzinfo is None:
                event_time = self.tz.localize(event_time)
            
            start = event_time - timedelta(hours=hours_before)
            end = event_time + timedelta(hours=hours_after)
            
            now = datetime.now(self.tz)
            days_ago = (now - event_time).days
            
            if days_ago <= 7:
                interval = '1m'
            elif days_ago <= 60:
                interval = '5m'
            else:
                interval = '1h'
            
            stock = yf.Ticker(ticker)
            df = stock.history(start=start, end=end, interval=interval)
            
            if df.empty:
                df = stock.history(period='5d', interval='5m')
            
            if not df.empty:
                if df.index.tzinfo is None:
                    df.index = df.index.tz_localize('America/New_York')
                else:
                    df.index = df.index.tz_convert('America/New_York')
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
    
    def calculate_returns(self, df: pd.DataFrame, event_time: datetime) -> Dict[str, float]:
        """Calculate returns at different time windows after event."""
        if df is None or df.empty:
            return {}
        
        if event_time.tzinfo is None:
            event_time = self.tz.localize(event_time)
        
        try:
            event_idx = df.index.get_indexer([event_time], method='nearest')[0]
            if event_idx < 0 or event_idx >= len(df):
                return {}
            
            base_price = df.iloc[event_idx]['Close']
            
            returns = {}
            windows = {'1m': 1, '5m': 5, '15m': 15, '30m': 30, '60m': 60, '240m': 240}
            
            for label, minutes in windows.items():
                target_time = event_time + timedelta(minutes=minutes)
                target_idx = df.index.get_indexer([target_time], method='nearest')[0]
                
                if 0 <= target_idx < len(df):
                    end_price = df.iloc[target_idx]['Close']
                    returns[label] = ((end_price - base_price) / base_price) * 100
            
            return returns
            
        except Exception as e:
            print(f"Error calculating returns: {e}")
            return {}
    
    def get_multi_asset_reaction(self, event_time: datetime) -> pd.DataFrame:
        """Get reaction of multiple assets to an event."""
        results = []
        
        for category, assets in self.ASSETS.items():
            for ticker, name in assets.items():
                df = self.fetch_intraday_data(ticker, event_time)
                if df is not None and not df.empty:
                    returns = self.calculate_returns(df, event_time)
                    if returns:
                        row = {'Ticker': ticker, 'Name': name, 'Category': category}
                        row.update(returns)
                        results.append(row)
        
        return pd.DataFrame(results)

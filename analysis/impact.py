"""Impact analysis engine for macro events."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from data.economic_events import EconomicEventsFetcher
from data.market_data import MarketDataFetcher


class ImpactAnalyzer:
    """Analyzes market impact of economic events."""
    
    def __init__(self):
        self.events_fetcher = EconomicEventsFetcher()
        self.market_fetcher = MarketDataFetcher()
    
    def analyze_event(self, event_date: datetime, ticker: str) -> Dict:
        """Analyze market reaction for a single event and ticker."""
        df = self.market_fetcher.fetch_intraday_data(ticker, event_date)
        
        if df is None or df.empty:
            return {'error': 'No data available'}
        
        returns = self.market_fetcher.calculate_returns(df, event_date)
        
        # Calculate additional metrics
        stats = {
            'returns': returns,
            'max_move': df['High'].max() - df['Low'].min() if not df.empty else 0,
            'volume': df['Volume'].sum() if 'Volume' in df.columns else 0,
        }
        
        return stats
    
    def analyze_event_impact(self, event_row: pd.Series) -> pd.DataFrame:
        """Analyze full market impact for an event."""
        event_time = event_row['date']
        if isinstance(event_time, str):
            event_time = pd.to_datetime(event_time)
        
        results = self.market_fetcher.get_multi_asset_reaction(event_time)
        
        if not results.empty:
            results['Event'] = event_row['event']
            results['Event_Date'] = event_time
            results['Surprise'] = event_row.get('surprise', 0)
            results['Surprise_Pct'] = event_row.get('surprise_pct', 0)
        
        return results
    
    def get_historical_reactions(self, event_type: str, ticker: str,
                                  n_events: int = 10) -> pd.DataFrame:
        """Get historical reactions for an event type and ticker."""
        events = self.events_fetcher.get_events(event_types=[event_type]).head(n_events)
        
        results = []
        for _, event in events.iterrows():
            event_time = event['date']
            df = self.market_fetcher.fetch_intraday_data(ticker, event_time)
            
            if df is not None and not df.empty:
                returns = self.market_fetcher.calculate_returns(df, event_time)
                results.append({
                    'Date': event_time,
                    'Actual': event['actual'],
                    'Forecast': event['forecast'],
                    'Surprise': event['surprise'],
                    **returns
                })
        
        return pd.DataFrame(results)
    
    def compute_summary_stats(self, event_type: str) -> Dict:
        """Compute summary statistics for an event type's market impact."""
        events = self.events_fetcher.get_events(event_types=[event_type])
        
        stats = {
            'count': len(events),
            'avg_surprise': events['surprise'].mean() if not events.empty else 0,
            'std_surprise': events['surprise'].std() if not events.empty else 0,
        }
        
        # Get average reactions for major assets
        key_assets = ['SPY', 'EURUSD=X', '^TNX', '^VIX']
        for ticker in key_assets:
            reactions = self.get_historical_reactions(event_type, ticker, n_events=5)
            if not reactions.empty:
                for col in ['1m', '5m', '15m', '30m', '60m']:
                    if col in reactions.columns:
                        stats[f'{ticker}_{col}_avg'] = reactions[col].mean()
                        stats[f'{ticker}_{col}_std'] = reactions[col].std()
        
        return stats
    
    def get_correlation_matrix(self, event_type: str) -> pd.DataFrame:
        """Get correlation between surprise and asset reactions."""
        events = self.events_fetcher.get_events(event_types=[event_type])
        
        all_data = []
        for _, event in events.iterrows():
            row_data = {'surprise': event['surprise']}
            
            for category, assets in self.market_fetcher.ASSETS.items():
                for ticker, name in list(assets.items())[:2]:  # Limit for speed
                    df = self.market_fetcher.fetch_intraday_data(ticker, event['date'])
                    if df is not None:
                        returns = self.market_fetcher.calculate_returns(df, event['date'])
                        for window, ret in returns.items():
                            row_data[f'{ticker}_{window}'] = ret
            
            all_data.append(row_data)
        
        if all_data:
            df = pd.DataFrame(all_data)
            return df.corr()
        return pd.DataFrame()


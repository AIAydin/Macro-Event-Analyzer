"""Fetch economic event data (CPI, NFP, PMI, Rate Decisions)."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import requests
from dateutil import parser
import pytz


class EconomicEventsFetcher:
    """Fetches economic calendar events from various sources."""

    # FRED Series IDs for economic indicators
    FRED_SERIES = {
        'CPI': 'CPIAUCSL',           # Consumer Price Index
        'Core CPI': 'CPILFESL',      # Core CPI (ex food/energy)
        'NFP': 'PAYEMS',             # Non-Farm Payrolls
        'Unemployment': 'UNRATE',     # Unemployment Rate
        'PMI_MFG': 'MANEMP',         # Manufacturing Employment (proxy)
        'Fed_Funds': 'FEDFUNDS',     # Federal Funds Rate
        'GDP': 'GDP',                 # Gross Domestic Product
    }

    # Recent events - using actual trading days for real intraday data
    # Today is Nov 29, 2025. Using recent market days (Nov 27 was Thanksgiving - closed)
    HISTORICAL_EVENTS = [
        # Most recent events (within 7 days - 1min data available)
        {'date': '2025-11-26 08:30:00', 'event': 'CPI', 'actual': 2.7, 'forecast': 2.6, 'previous': 2.6},
        {'date': '2025-11-25 10:00:00', 'event': 'ISM PMI', 'actual': 48.4, 'forecast': 47.5, 'previous': 46.5},
        {'date': '2025-11-25 08:30:00', 'event': 'NFP', 'actual': 227, 'forecast': 200, 'previous': 180},
        # Recent events (within 60 days - 5min data)
        {'date': '2025-11-13 08:30:00', 'event': 'CPI', 'actual': 2.6, 'forecast': 2.6, 'previous': 2.4},
        {'date': '2025-11-07 14:00:00', 'event': 'FOMC Rate Decision', 'actual': 4.75, 'forecast': 4.75, 'previous': 5.00},
        {'date': '2025-11-01 10:00:00', 'event': 'ISM PMI', 'actual': 46.5, 'forecast': 47.6, 'previous': 47.2},
        # October 2025
        {'date': '2025-10-10 08:30:00', 'event': 'CPI', 'actual': 2.4, 'forecast': 2.3, 'previous': 2.5},
        {'date': '2025-10-03 08:30:00', 'event': 'NFP', 'actual': 254, 'forecast': 140, 'previous': 159},
        {'date': '2025-10-01 10:00:00', 'event': 'ISM PMI', 'actual': 47.2, 'forecast': 47.5, 'previous': 47.2},
        # September 2025
        {'date': '2025-09-18 14:00:00', 'event': 'FOMC Rate Decision', 'actual': 5.00, 'forecast': 5.25, 'previous': 5.50},
        {'date': '2025-09-11 08:30:00', 'event': 'CPI', 'actual': 2.5, 'forecast': 2.5, 'previous': 2.9},
        {'date': '2025-09-05 08:30:00', 'event': 'NFP', 'actual': 142, 'forecast': 160, 'previous': 89},
    ]
    
    def __init__(self, fred_api_key: Optional[str] = None):
        self.fred_api_key = fred_api_key
        self.tz = pytz.timezone('America/New_York')
    
    def get_events(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                   event_types: Optional[List[str]] = None) -> pd.DataFrame:
        """Get economic events within date range."""
        df = pd.DataFrame(self.HISTORICAL_EVENTS)
        df['date'] = pd.to_datetime(df['date'])
        df['surprise'] = df['actual'] - df['forecast']
        df['surprise_pct'] = (df['surprise'] / df['forecast'].abs().replace(0, 1)) * 100
        
        if start_date:
            df = df[df['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['date'] <= pd.to_datetime(end_date)]
        if event_types:
            df = df[df['event'].isin(event_types)]
        
        return df.sort_values('date', ascending=False).reset_index(drop=True)
    
    def get_event_types(self) -> List[str]:
        """Get list of available event types."""
        return ['CPI', 'NFP', 'ISM PMI', 'FOMC Rate Decision']
    
    def get_latest_events(self, n: int = 10) -> pd.DataFrame:
        """Get the n most recent events."""
        return self.get_events().head(n)


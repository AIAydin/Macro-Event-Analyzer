"""Streamlit app for Macro Event Impact Tracker."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

from data.economic_events import EconomicEventsFetcher
from data.market_data import MarketDataFetcher

# Page config
st.set_page_config(
    page_title="Macro Event Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
    }
    section[data-testid="stSidebar"] {
        background-color: #161b22;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #f0f6fc !important;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #c9d1d9 !important;
    }
    .stSelectbox > div > div {
        background-color: #21262d;
        color: #ffffff !important;
    }
    div[data-testid="metric-container"] {
        background-color: #21262d;
        border-radius: 8px;
        padding: 16px;
    }
    div[data-testid="metric-container"] label,
    [data-testid="stMetricLabel"] label,
    [data-testid="stMetricLabel"] p {
        font-size: 14px !important;
        color: #ffffff !important;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-size: 28px !important;
    }
    .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3, .stSubheader {
        color: #f0f6fc !important;
    }
    p, span, label {
        color: #c9d1d9 !important;
    }
    .stDataFrame {
        background-color: #0d1117;
    }
    .stDataFrame thead tr th {
        background-color: #161b22 !important;
        color: #8b949e !important;
        font-size: 13px !important;
        font-weight: 600 !important;
    }
    .stDataFrame tbody tr td {
        background-color: #0d1117 !important;
        color: #f0f6fc !important;
        font-size: 14px !important;
    }
    .stDataFrame tbody tr:hover td {
        background-color: #161b22 !important;
    }
</style>
""", unsafe_allow_html=True)

# Chart theme
DARK_LAYOUT = {
    'paper_bgcolor': '#161b22',
    'plot_bgcolor': '#161b22',
    'font': {'color': '#f0f6fc', 'size': 12},
}
COLORS = {'positive': '#3fb950', 'negative': '#f85149'}

# Initialize fetchers
@st.cache_resource
def get_fetchers():
    return EconomicEventsFetcher(), MarketDataFetcher()

events_fetcher, market_fetcher = get_fetchers()

# Header
st.title("📊 Macro Event Impact Tracker")
st.caption("Real-time analysis of market reactions to economic data releases")

# Sidebar filters
st.sidebar.header("Filters")

event_types = events_fetcher.get_event_types()
selected_event_type = st.sidebar.selectbox("Event Type", sorted(event_types))

categories = market_fetcher.get_asset_categories()
selected_category = st.sidebar.selectbox("Asset Category", categories)

assets = market_fetcher.get_assets_by_category(selected_category)
selected_ticker = st.sidebar.selectbox("Ticker", list(assets.keys()), 
                                        format_func=lambda x: f"{x} - {assets[x]}")

time_windows = {'1 minute': '1m', '5 minutes': '5m', '15 minutes': '15m', 
                '30 minutes': '30m', '1 hour': '60m', '4 hours': '240m'}
selected_window = st.sidebar.selectbox("Time Window", list(time_windows.keys()))
time_window = time_windows[selected_window]

# Get events
events = events_fetcher.get_events(event_types=[selected_event_type])

# Events table
st.subheader("Recent Economic Events")

if len(events) > 0:
    events_display = events[['date', 'event', 'actual', 'forecast', 'previous', 'surprise']].head(10)
    events_display['date'] = events_display['date'].dt.strftime('%Y-%m-%d %H:%M')

    selected_idx = st.selectbox("Select Event", range(len(events_display)), 
                                format_func=lambda i: f"{events_display.iloc[i]['date']} - {events_display.iloc[i]['event']} (Surprise: {events_display.iloc[i]['surprise']:.2f})")

    st.dataframe(events_display, use_container_width=True, hide_index=True)

    selected_event = events.iloc[selected_idx]
    event_time = pd.to_datetime(selected_event['date'])
    
    # Metrics
    st.subheader("Quick Metrics")
    
    metrics_data = {}
    for ticker, name in [('SPY', 'SPY'), ('DX-Y.NYB', 'Dollar'), ('^TNX', '10Y'), ('^VIX', 'VIX')]:
        df = market_fetcher.fetch_intraday_data(ticker, event_time)
        if df is not None and not df.empty:
            returns = market_fetcher.calculate_returns(df, event_time)
            metrics_data[name] = returns.get(time_window, np.nan)
    
    cols = st.columns(4)
    for col, (name, val) in zip(cols, metrics_data.items()):
        if not np.isnan(val):
            col.metric(name, f"{val:+.2f}%", delta_color="normal" if val >= 0 else "inverse")
        else:
            col.metric(name, "--")

    # Charts
    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        st.subheader("Price Action Around Event")

        window_minutes = int(time_window.replace('m', ''))
        hours_after = max(1, window_minutes // 60 + 1)

        df = market_fetcher.fetch_intraday_data(selected_ticker, event_time, hours_before=1, hours_after=hours_after)

        if df is not None and not df.empty:
            fig = go.Figure()

            if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'],
                    increasing_line_color='#3fb950', decreasing_line_color='#f85149',
                ))

            fig.add_vline(x=event_time, line_dash="dash", line_color="#a371f7", line_width=2)
            fig.add_annotation(x=event_time, y=1.05, yref='paper', text="Event",
                             showarrow=False, font=dict(color='#a371f7'))

            tz = pytz.timezone('America/New_York')
            if event_time.tzinfo is None:
                event_time_tz = tz.localize(event_time)
            else:
                event_time_tz = event_time

            x_start = event_time_tz - timedelta(minutes=15)
            x_end = event_time_tz + timedelta(minutes=window_minutes + 15)
            fig.update_xaxes(range=[x_start, x_end])

            visible_df = df[(df.index >= x_start) & (df.index <= x_end)]
            if not visible_df.empty:
                y_min, y_max = visible_df['Low'].min(), visible_df['High'].max()
                y_pad = (y_max - y_min) * 0.15
                fig.update_yaxes(range=[y_min - y_pad, y_max + y_pad])

            fig.update_layout(
                paper_bgcolor='#161b22', plot_bgcolor='#161b22',
                font=dict(color='#f0f6fc', size=12),
                title=dict(text=assets.get(selected_ticker, selected_ticker), font=dict(size=16, color='#f0f6fc')),
                showlegend=False, xaxis_rangeslider_visible=False,
                margin=dict(l=60, r=40, t=50, b=60)
            )
            fig.update_xaxes(gridcolor='#30363d', linecolor='#30363d', tickfont=dict(color='#c9d1d9'))
            fig.update_yaxes(gridcolor='#30363d', linecolor='#30363d', tickfont=dict(color='#c9d1d9'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No price data available for this event")

    with chart_col2:
        st.subheader("Category Performance")

        reactions = market_fetcher.get_multi_asset_reaction(event_time)

        if not reactions.empty and time_window in reactions.columns:
            cat_avg = reactions.groupby('Category')[time_window].mean().reset_index()
            colors = [COLORS['positive'] if v >= 0 else COLORS['negative'] for v in cat_avg[time_window]]

            fig = go.Figure(go.Bar(
                x=cat_avg['Category'], y=cat_avg[time_window],
                marker_color=colors,
                text=[f"{v:+.2f}%" for v in cat_avg[time_window]],
                textposition='outside', textfont=dict(color='#f0f6fc', size=13)
            ))
            fig.update_layout(
                paper_bgcolor='#161b22', plot_bgcolor='#161b22',
                font=dict(color='#f0f6fc', size=12),
                title=dict(text=f"Avg {time_window} Return", font=dict(color='#f0f6fc', size=16)),
                showlegend=False, margin=dict(l=60, r=40, t=50, b=60)
            )
            fig.update_xaxes(gridcolor='#30363d', linecolor='#30363d', tickfont=dict(color='#c9d1d9'))
            fig.update_yaxes(gridcolor='#30363d', linecolor='#30363d', tickfont=dict(color='#c9d1d9'))
            y_max = cat_avg[time_window].max()
            y_min = cat_avg[time_window].min()
            y_range = max(abs(y_max), abs(y_min)) * 1.4
            fig.update_yaxes(range=[-y_range if y_min < 0 else 0, y_range])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No reaction data available")

    # Heatmap
    st.subheader("Multi-Asset Reaction Heatmap")

    if not reactions.empty:
        time_cols = [col for col in reactions.columns if col.endswith('m')]
        if time_cols:
            z_values = reactions[time_cols].values
            y_labels = reactions['Name'].tolist()

            fig = go.Figure(go.Heatmap(
                z=z_values, x=time_cols, y=y_labels,
                colorscale=[[0, '#f85149'], [0.5, '#21262d'], [1, '#3fb950']],
                zmid=0, text=np.round(z_values, 2), texttemplate='%{text:.2f}%',
                textfont={"size": 12, "color": "#ffffff"},
                colorbar=dict(
                    title=dict(text='Return %', font=dict(color='#f0f6fc')),
                    tickfont=dict(color='#f0f6fc')
                )
            ))
            fig.update_layout(
                paper_bgcolor='#161b22', plot_bgcolor='#161b22',
                font=dict(color='#f0f6fc', size=12),
                height=max(450, len(y_labels) * 40),
                margin=dict(l=120, r=60, t=50, b=60)
            )
            fig.update_xaxes(tickfont=dict(color='#f0f6fc', size=12), side='bottom')
            fig.update_yaxes(tickfont=dict(color='#f0f6fc', size=12))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No heatmap data available")
else:
    st.warning("No events found. Make sure FRED_API_KEY is set for live data.")

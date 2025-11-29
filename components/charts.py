"""Chart components for the macro event tracker."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


# Dark theme layout
DARK_LAYOUT = {
    'paper_bgcolor': '#161b22',
    'plot_bgcolor': '#161b22',
    'font': {'color': '#f0f6fc', 'family': '-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial'},
    'xaxis': {
        'gridcolor': '#30363d',
        'linecolor': '#30363d',
        'tickcolor': '#8b949e',
    },
    'yaxis': {
        'gridcolor': '#30363d',
        'linecolor': '#30363d',
        'tickcolor': '#8b949e',
    },
    'margin': {'l': 50, 'r': 30, 't': 40, 'b': 40},
}

COLORS = {
    'Equities': '#58a6ff',
    'FX': '#3fb950',
    'Rates': '#d29922',
    'Volatility': '#f85149',
    'positive': '#3fb950',
    'negative': '#f85149',
    'neutral': '#8b949e',
}


def create_price_chart(df: pd.DataFrame, event_time: pd.Timestamp, 
                       ticker: str, title: str = '') -> go.Figure:
    """Create a price chart with event marker."""
    fig = go.Figure()
    
    if df is None or df.empty:
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color='#8b949e')
        )
        fig.update_layout(**DARK_LAYOUT, title=title or ticker)
        return fig
    
    # Add candlestick or line based on data
    if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=ticker,
            increasing_line_color='#3fb950',
            decreasing_line_color='#f85149',
            increasing_fillcolor='#3fb950',
            decreasing_fillcolor='#f85149',
            line=dict(width=2),
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Close'],
            mode='lines', name=ticker,
            line=dict(color='#58a6ff', width=1.5)
        ))

    # Add event marker
    fig.add_vline(x=event_time, line_dash="dash", line_color="#a371f7", line_width=2)
    fig.add_annotation(
        x=event_time, y=1.05, yref='paper',
        text="Event", showarrow=False,
        font=dict(color='#a371f7', size=11)
    )

    fig.update_layout(**DARK_LAYOUT, title=title or ticker, showlegend=False)
    fig.update_xaxes(rangeslider_visible=False)
    # Auto-scale y-axis to fit the visible data with padding
    fig.update_yaxes(autorange=True, fixedrange=False)

    return fig


def create_reaction_heatmap(df: pd.DataFrame) -> go.Figure:
    """Create a heatmap of asset reactions across time windows."""
    fig = go.Figure()
    
    if df is None or df.empty:
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color='#8b949e')
        )
        fig.update_layout(**DARK_LAYOUT, title="Reaction Heatmap")
        return fig
    
    time_cols = [col for col in df.columns if col.endswith('m')]
    if not time_cols:
        return fig
    
    z_values = df[time_cols].values
    y_labels = df['Name'].tolist() if 'Name' in df.columns else df['Ticker'].tolist()
    
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=time_cols,
        y=y_labels,
        colorscale=[[0, '#f85149'], [0.5, '#21262d'], [1, '#3fb950']],
        zmid=0,
        text=np.round(z_values, 2),
        texttemplate='%{text:.2f}%',
        textfont={"size": 10},
        hovertemplate='%{y}<br>%{x}: %{z:.2f}%<extra></extra>',
        colorbar=dict(
            title=dict(text='Return %', font=dict(color='#f0f6fc')),
            tickfont=dict(color='#f0f6fc')
        )
    ))
    
    fig.update_layout(
        **DARK_LAYOUT,
        title='Asset Reactions by Time Window',
        xaxis_title='Time After Event',
        yaxis_title='',
        height=max(300, len(y_labels) * 35)
    )
    
    return fig


def create_returns_bar(returns_data: Dict[str, Dict]) -> go.Figure:
    """Create grouped bar chart of returns by category."""
    fig = go.Figure()
    
    categories = list(returns_data.keys())
    time_windows = ['1m', '5m', '15m', '30m', '60m']
    
    for window in time_windows:
        values = [returns_data.get(cat, {}).get(window, 0) for cat in categories]
        colors = [COLORS['positive'] if v >= 0 else COLORS['negative'] for v in values]
        
        fig.add_trace(go.Bar(
            name=window,
            x=categories,
            y=values,
            marker_color=colors,
        ))
    
    fig.update_layout(**DARK_LAYOUT, barmode='group', title='Returns by Category')
    return fig


def create_surprise_scatter(events_df: pd.DataFrame, reactions_df: pd.DataFrame,
                            time_window: str = '5m') -> go.Figure:
    """Scatter plot of surprise vs market reaction."""
    fig = go.Figure()
    
    if events_df.empty or reactions_df.empty or time_window not in reactions_df.columns:
        fig.add_annotation(
            text="Insufficient data",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color='#8b949e')
        )
        fig.update_layout(**DARK_LAYOUT)
        return fig
    
    merged = pd.merge(events_df, reactions_df, left_index=True, right_index=True)
    
    fig.add_trace(go.Scatter(
        x=merged['surprise'],
        y=merged[time_window],
        mode='markers',
        marker=dict(
            size=10,
            color='#58a6ff',
            line=dict(width=1, color='#f0f6fc')
        ),
        text=merged['date'].dt.strftime('%Y-%m-%d'),
        hovertemplate='Date: %{text}<br>Surprise: %{x:.2f}<br>Return: %{y:.2f}%<extra></extra>'
    ))
    
    fig.update_layout(
        **DARK_LAYOUT,
        title=f'Surprise vs {time_window} Reaction',
        xaxis_title='Surprise (Actual - Forecast)',
        yaxis_title=f'{time_window} Return (%)'
    )
    
    return fig


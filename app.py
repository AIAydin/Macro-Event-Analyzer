"""Main Dash application for Macro Event Impact Tracker."""

import dash
from dash import dcc, html, dash_table, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import pytz

from data.economic_events import EconomicEventsFetcher
from data.market_data import MarketDataFetcher
from components.charts import (
    create_price_chart, create_reaction_heatmap, 
    create_returns_bar, DARK_LAYOUT, COLORS
)

# Initialize data fetchers
events_fetcher = EconomicEventsFetcher()
market_fetcher = MarketDataFetcher()

# Create Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    title="Macro Event Tracker"
)

# Color scheme
DARK_BG = '#0d1117'
CARD_BG = '#161b22'
BORDER = '#30363d'
TEXT = '#f0f6fc'
TEXT_MUTED = '#8b949e'


def create_header():
    """Create the application header."""
    return html.Div([
        html.H1("Macro Event Impact Tracker", style={'margin': 0, 'fontWeight': 600}),
        html.P("Real-time analysis of market reactions to economic data releases",
               style={'color': TEXT_MUTED, 'margin': '8px 0 0 0', 'fontSize': '14px'})
    ], className='header', style={
        'borderBottom': f'1px solid {BORDER}',
        'paddingBottom': '16px',
        'marginBottom': '24px'
    })


def create_filters():
    """Create the filter controls section."""
    event_types = events_fetcher.get_event_types()
    
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Event Type", style={'color': TEXT_MUTED, 'fontSize': '12px', 'marginBottom': '4px'}),
                    dcc.Dropdown(
                        id='event-type-dropdown',
                        options=[{'label': e, 'value': e} for e in event_types],
                        value=event_types[0] if event_types else None,
                        style={'backgroundColor': '#21262d'},
                        className='dark-dropdown'
                    )
                ], md=3),
                dbc.Col([
                    html.Label("Asset Category", style={'color': TEXT_MUTED, 'fontSize': '12px', 'marginBottom': '4px'}),
                    dcc.Dropdown(
                        id='category-dropdown',
                        options=[{'label': c, 'value': c} for c in market_fetcher.get_asset_categories()],
                        value='Equities',
                        style={'backgroundColor': '#21262d'}
                    )
                ], md=3),
                dbc.Col([
                    html.Label("Ticker", style={'color': TEXT_MUTED, 'fontSize': '12px', 'marginBottom': '4px'}),
                    dcc.Dropdown(
                        id='ticker-dropdown',
                        options=[],
                        value=None,
                        style={'backgroundColor': '#21262d'}
                    )
                ], md=3),
                dbc.Col([
                    html.Label("Time Window", style={'color': TEXT_MUTED, 'fontSize': '12px', 'marginBottom': '4px'}),
                    dcc.Dropdown(
                        id='window-dropdown',
                        options=[
                            {'label': '1 minute', 'value': '1m'},
                            {'label': '5 minutes', 'value': '5m'},
                            {'label': '15 minutes', 'value': '15m'},
                            {'label': '30 minutes', 'value': '30m'},
                            {'label': '1 hour', 'value': '60m'},
                            {'label': '4 hours', 'value': '240m'},
                        ],
                        value='5m',
                        style={'backgroundColor': '#21262d'}
                    )
                ], md=3),
            ])
        ])
    ], style={'backgroundColor': CARD_BG, 'border': f'1px solid {BORDER}', 'marginBottom': '16px'})


def create_events_table():
    """Create the events data table."""
    events = events_fetcher.get_latest_events(15)
    
    return dbc.Card([
        dbc.CardHeader("Recent Economic Events", 
                       style={'backgroundColor': CARD_BG, 'borderBottom': f'1px solid {BORDER}',
                              'fontWeight': 600, 'fontSize': '16px'}),
        dbc.CardBody([
            dash_table.DataTable(
                id='events-table',
                columns=[
                    {'name': 'Date', 'id': 'date', 'type': 'datetime'},
                    {'name': 'Event', 'id': 'event'},
                    {'name': 'Actual', 'id': 'actual', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': 'Forecast', 'id': 'forecast', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': 'Previous', 'id': 'previous', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': 'Surprise', 'id': 'surprise', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                ],
                data=events.to_dict('records'),
                row_selectable='single',
                selected_rows=[0] if len(events) > 0 else [],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'backgroundColor': CARD_BG,
                    'color': TEXT,
                    'border': f'1px solid {BORDER}',
                    'textAlign': 'left',
                    'padding': '12px',
                    'fontSize': '13px',
                },
                style_header={
                    'backgroundColor': '#21262d',
                    'fontWeight': 600,
                    'borderBottom': f'2px solid {BORDER}',
                },
                style_data_conditional=[
                    {'if': {'filter_query': '{surprise} > 0', 'column_id': 'surprise'},
                     'color': '#3fb950'},
                    {'if': {'filter_query': '{surprise} < 0', 'column_id': 'surprise'},
                     'color': '#f85149'},
                ],
            )
        ])
    ], style={'backgroundColor': CARD_BG, 'border': f'1px solid {BORDER}', 'marginBottom': '16px'})


def create_metrics_cards():
    """Create summary metrics cards."""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(id='metric-spy', children='--',
                             style={'fontSize': '28px', 'fontWeight': 700, 'textAlign': 'center'}),
                    html.Div("SPY Reaction",
                             style={'fontSize': '12px', 'color': TEXT_MUTED, 'textAlign': 'center',
                                    'textTransform': 'uppercase', 'letterSpacing': '0.5px'})
                ])
            ], style={'backgroundColor': '#21262d', 'border': 'none'})
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(id='metric-dxy', children='--',
                             style={'fontSize': '28px', 'fontWeight': 700, 'textAlign': 'center'}),
                    html.Div("Dollar Index",
                             style={'fontSize': '12px', 'color': TEXT_MUTED, 'textAlign': 'center',
                                    'textTransform': 'uppercase', 'letterSpacing': '0.5px'})
                ])
            ], style={'backgroundColor': '#21262d', 'border': 'none'})
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(id='metric-tnx', children='--',
                             style={'fontSize': '28px', 'fontWeight': 700, 'textAlign': 'center'}),
                    html.Div("10Y Yield",
                             style={'fontSize': '12px', 'color': TEXT_MUTED, 'textAlign': 'center',
                                    'textTransform': 'uppercase', 'letterSpacing': '0.5px'})
                ])
            ], style={'backgroundColor': '#21262d', 'border': 'none'})
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(id='metric-vix', children='--',
                             style={'fontSize': '28px', 'fontWeight': 700, 'textAlign': 'center'}),
                    html.Div("VIX Change",
                             style={'fontSize': '12px', 'color': TEXT_MUTED, 'textAlign': 'center',
                                    'textTransform': 'uppercase', 'letterSpacing': '0.5px'})
                ])
            ], style={'backgroundColor': '#21262d', 'border': 'none'})
        ], md=3),
    ], style={'marginBottom': '16px'})


# Main layout
app.layout = html.Div([
    html.Div([
        create_header(),
        create_filters(),
        create_metrics_cards(),

        dbc.Row([
            dbc.Col([create_events_table()], md=5),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Price Action Around Event",
                                   style={'backgroundColor': CARD_BG, 'borderBottom': f'1px solid {BORDER}',
                                          'fontWeight': 600, 'fontSize': '16px'}),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='price-chart', style={'height': '400px'}),
                            type='circle', color='#58a6ff'
                        )
                    ])
                ], style={'backgroundColor': CARD_BG, 'border': f'1px solid {BORDER}', 'marginBottom': '16px'})
            ], md=7),
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Multi-Asset Reaction Heatmap",
                                   style={'backgroundColor': CARD_BG, 'borderBottom': f'1px solid {BORDER}',
                                          'fontWeight': 600, 'fontSize': '16px'}),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='heatmap-chart', style={'height': '450px'}),
                            type='circle', color='#58a6ff'
                        )
                    ])
                ], style={'backgroundColor': CARD_BG, 'border': f'1px solid {BORDER}'})
            ], md=7),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Category Performance",
                                   style={'backgroundColor': CARD_BG, 'borderBottom': f'1px solid {BORDER}',
                                          'fontWeight': 600, 'fontSize': '16px'}),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='category-chart', style={'height': '450px'}),
                            type='circle', color='#58a6ff'
                        )
                    ])
                ], style={'backgroundColor': CARD_BG, 'border': f'1px solid {BORDER}'})
            ], md=5),
        ]),

        # Hidden store for event data
        dcc.Store(id='selected-event-store'),

        # Auto-refresh interval
        dcc.Interval(id='refresh-interval', interval=60000, n_intervals=0)

    ], style={'maxWidth': '1600px', 'margin': '0 auto', 'padding': '24px'})
], style={'backgroundColor': DARK_BG, 'minHeight': '100vh'})


# Callbacks
@callback(
    Output('ticker-dropdown', 'options'),
    Output('ticker-dropdown', 'value'),
    Input('category-dropdown', 'value')
)
def update_ticker_options(category):
    """Update ticker dropdown based on selected category."""
    if not category:
        return [], None
    assets = market_fetcher.get_assets_by_category(category)
    options = [{'label': name, 'value': ticker} for ticker, name in assets.items()]
    default_value = list(assets.keys())[0] if assets else None
    return options, default_value


@callback(
    Output('selected-event-store', 'data'),
    Input('events-table', 'selected_rows'),
    State('events-table', 'data')
)
def store_selected_event(selected_rows, table_data):
    """Store the selected event data."""
    if not selected_rows or not table_data:
        return None
    return table_data[selected_rows[0]]


@callback(
    Output('price-chart', 'figure'),
    Input('selected-event-store', 'data'),
    Input('ticker-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    Input('window-dropdown', 'value')
)
def update_price_chart(event_data, ticker, category, time_window):
    """Update the price chart based on selected event, ticker and time window."""
    fig = go.Figure()
    fig.update_layout(**DARK_LAYOUT, title="Select an event and ticker")

    if not event_data or not ticker:
        return fig

    event_time = pd.to_datetime(event_data['date'])

    # Parse time window to get minutes for chart range
    window_minutes = int(time_window.replace('m', '')) if time_window else 60
    hours_after = max(1, window_minutes // 60 + 1)

    df = market_fetcher.fetch_intraday_data(ticker, event_time, hours_before=1, hours_after=hours_after)

    assets = market_fetcher.get_assets_by_category(category) if category else {}
    ticker_name = assets.get(ticker, ticker)

    chart = create_price_chart(df, event_time, ticker,
                             title=f"{ticker_name} - {event_data['event']} ({event_time.strftime('%Y-%m-%d %H:%M')})")

    # Zoom chart to time window if we have intraday data
    if df is not None and not df.empty and window_minutes <= 240:
        tz = pytz.timezone('America/New_York')
        if event_time.tzinfo is None:
            event_time_tz = tz.localize(event_time)
        else:
            event_time_tz = event_time

        # Show 15 min before event and window_minutes after
        x_start = event_time_tz - timedelta(minutes=15)
        x_end = event_time_tz + timedelta(minutes=window_minutes + 15)

        chart.update_xaxes(range=[x_start, x_end])

        # Auto-scale y-axis to fit visible data with padding
        visible_df = df[(df.index >= x_start) & (df.index <= x_end)]
        if not visible_df.empty:
            y_min = visible_df['Low'].min()
            y_max = visible_df['High'].max()
            y_padding = (y_max - y_min) * 0.15  # 15% padding
            chart.update_yaxes(range=[y_min - y_padding, y_max + y_padding])

    return chart


@callback(
    Output('heatmap-chart', 'figure'),
    Input('selected-event-store', 'data')
)
def update_heatmap(event_data):
    """Update the reaction heatmap."""
    fig = go.Figure()
    fig.update_layout(**DARK_LAYOUT, title="Multi-Asset Reaction Heatmap")

    if not event_data:
        fig.add_annotation(text="Select an event to view reactions",
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                          font=dict(size=14, color='#8b949e'))
        return fig

    event_time = pd.to_datetime(event_data['date'])
    reactions = market_fetcher.get_multi_asset_reaction(event_time)

    return create_reaction_heatmap(reactions)


@callback(
    Output('category-chart', 'figure'),
    Input('selected-event-store', 'data'),
    Input('window-dropdown', 'value')
)
def update_category_chart(event_data, time_window):
    """Update the category performance chart."""
    fig = go.Figure()
    fig.update_layout(**DARK_LAYOUT, title="Category Performance")

    if not event_data:
        fig.add_annotation(text="Select an event to view performance",
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                          font=dict(size=14, color='#8b949e'))
        return fig

    event_time = pd.to_datetime(event_data['date'])
    reactions = market_fetcher.get_multi_asset_reaction(event_time)

    if reactions.empty or time_window not in reactions.columns:
        return fig

    # Aggregate by category
    category_avg = reactions.groupby('Category')[time_window].mean().reset_index()

    colors = [COLORS['positive'] if v >= 0 else COLORS['negative']
              for v in category_avg[time_window]]

    fig.add_trace(go.Bar(
        x=category_avg['Category'],
        y=category_avg[time_window],
        marker_color=colors,
        text=[f"{v:+.2f}%" for v in category_avg[time_window]],
        textposition='outside',
        textfont=dict(color='#f0f6fc')
    ))

    fig.update_layout(
        **DARK_LAYOUT,
        title=f"Average {time_window} Return by Category",
        xaxis_title="",
        yaxis_title="Return (%)",
        showlegend=False
    )

    return fig


@callback(
    Output('metric-spy', 'children'),
    Output('metric-spy', 'style'),
    Output('metric-dxy', 'children'),
    Output('metric-dxy', 'style'),
    Output('metric-tnx', 'children'),
    Output('metric-tnx', 'style'),
    Output('metric-vix', 'children'),
    Output('metric-vix', 'style'),
    Input('selected-event-store', 'data'),
    Input('window-dropdown', 'value')
)
def update_metrics(event_data, time_window):
    """Update the summary metric cards."""
    base_style = {'fontSize': '28px', 'fontWeight': 700, 'textAlign': 'center'}
    default = ('--', {**base_style, 'color': '#8b949e'})

    if not event_data:
        return default * 4

    event_time = pd.to_datetime(event_data['date'])

    metrics = []
    tickers = ['SPY', 'DX-Y.NYB', '^TNX', '^VIX']

    for ticker in tickers:
        df = market_fetcher.fetch_intraday_data(ticker, event_time)
        if df is not None and not df.empty:
            returns = market_fetcher.calculate_returns(df, event_time)
            value = returns.get(time_window, np.nan)
            if not np.isnan(value):
                color = '#3fb950' if value >= 0 else '#f85149'
                metrics.append((f"{value:+.2f}%", {**base_style, 'color': color}))
            else:
                metrics.append(default)
        else:
            metrics.append(default)

    # Flatten the list for return
    result = []
    for m in metrics:
        result.extend(m)
    return tuple(result)


@callback(
    Output('events-table', 'data'),
    Input('event-type-dropdown', 'value')
)
def filter_events_table(event_type):
    """Filter the events table by event type."""
    if event_type:
        events = events_fetcher.get_events(event_types=[event_type])
    else:
        events = events_fetcher.get_latest_events(15)
    return events.head(15).to_dict('records')


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  MACRO EVENT IMPACT TRACKER")
    print("  Starting server at http://127.0.0.1:8050")
    print("="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=8050)


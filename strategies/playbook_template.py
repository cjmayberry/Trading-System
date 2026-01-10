"""
Template for defining a trading playbook/strategy

Each strategy should define:
1. Entry conditions
2. Exit conditions
3. Position sizing rules
4. Required indicators/data
5. Backtest parameters
"""

STRATEGY_CONFIG = {
    "name": "Strategy Name",
    "description": "Brief description of the strategy",
    "source": "Book/Author name",
    "timeframe": "daily",  # daily, 60min, etc.
    
    "entry_conditions": {
        # Define specific entry rules
        "trend_filter": "20-day MA slope > 0",
        "momentum": "RSI > 50",
        "price_action": "Close > Open (bullish candle)",
        # Add more conditions
    },
    
    "exit_conditions": {
        "stop_loss": "2 x ATR(14) below entry",
        "profit_target": "3 x ATR(14) above entry",
        "time_stop": "10 days maximum hold",
        # Add more conditions
    },
    
    "position_sizing": {
        "method": "fixed_risk",
        "risk_per_trade": 0.01,  # 1% of capital
        "max_position_size": 0.10,  # 10% of capital max
    },
    
    "required_data": [
        "Close", "Open", "High", "Low", "Volume"
    ],
    
    "required_indicators": [
        {"name": "SMA", "period": 20},
        {"name": "ATR", "period": 14},
        {"name": "RSI", "period": 14},
    ],
    
    "backtest_params": {
        "start_date": "2010-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000,
        "commission": 0.001,  # 0.1%
    },
    
    "optimization_params": {
        # Parameters to test ranges for
        "sma_period": [10, 20, 50],
        "atr_multiplier_stop": [1.5, 2.0, 2.5],
        "atr_multiplier_target": [2.0, 3.0, 4.0],
    }
}

# Human-readable description for dashboard
PLAYBOOK_DESCRIPTION = """
## Strategy Overview
[Describe the strategy in plain English]

## When to Use
- Market is trending
- Volatility is moderate
- etc.

## Key Rules
1. Wait for [condition]
2. Enter when [trigger]
3. Stop at [level]
4. Target at [level]

## Expected Performance
- Win Rate: ~55%
- Avg Winner: 2.5R
- Avg Loser: 1R
- Max Drawdown: ~15%
"""

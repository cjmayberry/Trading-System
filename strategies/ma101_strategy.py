"""
MA101 Strategy - Moving Averages 101 (Burns)

Implements the MA crossover trend-following system from Burns
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from strategies.strategy_base import StrategyBase
from strategies.strategy_definitions import STRATEGIES


class MA101Strategy(StrategyBase):
    """
    Moving Averages 101 trend-following strategy
    
    Entry: EMA crossover when price above SMA(200)
    Exit: Close below trailing MA or RSI overbought
    """
    
    def __init__(self, config=None):
        # Load strategy definition
        strategy_def = STRATEGIES['moving_averages_101_burns_2015']
        super().__init__(strategy_def, config)
        
        # Extract specific parameters with defaults
        self.regime_ma = config.get('regime_ma', 200) if config else 200
        self.fast_ema = config.get('fast_ema', 10) if config else 10
        self.slow_ema = config.get('slow_ema', 30) if config else 30
        self.rsi_period = config.get('rsi_period', 14) if config else 14
        self.rsi_overbought = config.get('rsi_overbought', 70) if config else 70
        self.stop_ma = config.get('stop_ma', 10) if config else 10
    
    def calculate_indicators(self, df):
        """Calculate all required indicators"""
        df = df.copy()
        
        # Moving averages
        df[f'sma_{self.regime_ma}'] = df['close'].rolling(window=self.regime_ma).mean()
        df[f'ema_{self.fast_ema}'] = df['close'].ewm(span=self.fast_ema, adjust=False).mean()
        df[f'ema_{self.slow_ema}'] = df['close'].ewm(span=self.slow_ema, adjust=False).mean()
        df[f'ema_{self.stop_ma}'] = df['close'].ewm(span=self.stop_ma, adjust=False).mean()
        
        # RSI
        df[f'rsi_{self.rsi_period}'] = self._calculate_rsi(df['close'], self.rsi_period)
        
        # ATR for position sizing
        df['atr_14'] = self._calculate_atr(df, 14)
        
        return df
    
    def generate_signals(self, df):
        """
        Generate trading signals
        
        Returns DataFrame with:
        - signal: 1 (long), 0 (flat), -1 (short)
        - entry_price: suggested entry
        - stop_price: suggested stop
        - reason: why signal triggered
        """
        df = self.calculate_indicators(df)
        
        # Initialize signal column
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_price'] = np.nan
        df['reason'] = ''
        
        # Regime filter: only long when above SMA(200)
        regime = df['close'] > df[f'sma_{self.regime_ma}']
        
        # Crossover detection
        fast_col = f'ema_{self.fast_ema}'
        slow_col = f'ema_{self.slow_ema}'
        stop_col = f'ema_{self.stop_ma}'
        
        # EMA crossover: fast crosses above slow
        cross_above = (
            (df[fast_col].shift(1) <= df[slow_col].shift(1)) &
            (df[fast_col] > df[slow_col])
        )
        
        # Entry signal: crossover + regime filter
        entry_signal = cross_above & regime
        
        df.loc[entry_signal, 'signal'] = 1
        df.loc[entry_signal, 'entry_price'] = df.loc[entry_signal, 'close']
        df.loc[entry_signal, 'stop_price'] = df.loc[entry_signal, stop_col]
        df.loc[entry_signal, 'reason'] = f'EMA {self.fast_ema}/{self.slow_ema} cross above, price > SMA {self.regime_ma}'
        
        # Exit signal: close below stop MA
        # (This would be tracked in position management, not just signal generation)
        
        return df
    
    def check_current_signal(self, df):
        """
        Check if there's a signal on the most recent bar
        
        Returns:
            dict with signal info or None
        """
        df = self.generate_signals(df)
        
        if df.empty:
            return None
        
        latest = df.iloc[-1]
        
        if latest['signal'] == 1:
            return {
                'symbol': latest.get('symbol', 'Unknown'),
                'date': latest.name,
                'signal': 'LONG',
                'entry_price': latest['entry_price'],
                'stop_price': latest['stop_price'],
                'reason': latest['reason'],
                'strategy': self.name,
                'risk_per_share': latest['entry_price'] - latest['stop_price'],
                'atr': latest.get('atr_14', 0)
            }
        
        return None


# Example usage
if __name__ == "__main__":
    # Test the strategy
    from scripts.data_management.fetch_data import load_data
    
    symbol = 'SPY'
    df = load_data(symbol)
    
    strategy = MA101Strategy()
    signals_df = strategy.generate_signals(df)
    
    # Show recent signals
    recent_signals = signals_df[signals_df['signal'] != 0].tail(5)
    print(f"\nRecent {strategy.name} signals for {symbol}:")
    print(recent_signals[['signal', 'entry_price', 'stop_price', 'reason']])
    
    # Check current signal
    current = strategy.check_current_signal(df)
    if current:
        print(f"\n🎯 CURRENT SIGNAL:")
        print(f"   {current['signal']} at {current['entry_price']:.2f}")
        print(f"   Stop: {current['stop_price']:.2f}")
        print(f"   Reason: {current['reason']}")
    else:
        print("\n No current signal")

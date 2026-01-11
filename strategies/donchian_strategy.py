"""
Donchian Breakout Strategy - Buy/Sell Signals (Burns)

Classic trend-following breakout system
Entry: N-day high/low breakout
Exit: M-day opposite breakout or ATR-based stop
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from strategies.strategy_base import StrategyBase
from strategies.strategy_definitions import STRATEGIES


class DonchianStrategy(StrategyBase):
    """
    Donchian Channel Breakout Strategy
    
    Simple, robust trend-following system
    Enter on N-day breakout, exit on M-day opposite breakout
    """
    
    def __init__(self, config=None):
        # Load strategy definition
        strategy_def = STRATEGIES['buy_signals_sell_signals_burns_2015_donchian_breakout']
        super().__init__(strategy_def, config)
        
        # Extract parameters - default to 50/25 breakout
        self.entry_period = config.get('entry_period', 50) if config else 50
        self.exit_period = config.get('exit_period', 25) if config else 25
        self.atr_period = config.get('atr_period', 14) if config else 14
        self.atr_stop_multiple = config.get('atr_stop_multiple', 3.0) if config else 3.0
        self.use_atr_stop = config.get('use_atr_stop', False) if config else False
        self.allow_shorts = config.get('allow_shorts', False) if config else False
    
    def calculate_indicators(self, df):
        """Calculate Donchian channels and ATR"""
        df = df.copy()
        
        # Donchian Channel High (highest high over N periods, excluding current bar)
        df[f'donchian_high_{self.entry_period}'] = df['high'].shift(1).rolling(
            window=self.entry_period
        ).max()
        
        # Donchian Channel Low (lowest low over N periods, excluding current bar)
        df[f'donchian_low_{self.entry_period}'] = df['low'].shift(1).rolling(
            window=self.entry_period
        ).min()
        
        # Exit channels (shorter period)
        df[f'donchian_high_{self.exit_period}'] = df['high'].shift(1).rolling(
            window=self.exit_period
        ).max()
        
        df[f'donchian_low_{self.exit_period}'] = df['low'].shift(1).rolling(
            window=self.exit_period
        ).min()
        
        # ATR for optional stop
        df[f'atr_{self.atr_period}'] = self._calculate_atr(df, self.atr_period)
        
        return df
    
    def generate_signals(self, df):
        """
        Generate Donchian breakout signals
        
        Long entry: Close above N-day high
        Short entry: Close below N-day low (if enabled)
        """
        df = self.calculate_indicators(df)
        
        # Initialize signal columns
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_price'] = np.nan
        df['reason'] = ''
        
        entry_high = f'donchian_high_{self.entry_period}'
        entry_low = f'donchian_low_{self.entry_period}'
        exit_low = f'donchian_low_{self.exit_period}'
        exit_high = f'donchian_high_{self.exit_period}'
        atr_col = f'atr_{self.atr_period}'
        
        # Long entries: breakout above N-day high
        long_breakout = df['close'] > df[entry_high]
        
        # Calculate stop price
        if self.use_atr_stop:
            # ATR-based stop
            stop_price = df['close'] - (self.atr_stop_multiple * df[atr_col])
        else:
            # Exit channel stop
            stop_price = df[exit_low]
        
        # Long signals
        df.loc[long_breakout, 'signal'] = 1
        df.loc[long_breakout, 'entry_price'] = df.loc[long_breakout, 'close']
        df.loc[long_breakout, 'stop_price'] = stop_price[long_breakout]
        df.loc[long_breakout, 'reason'] = f'{self.entry_period}-day breakout high'
        
        # Short entries (optional)
        if self.allow_shorts:
            short_breakout = df['close'] < df[entry_low]
            
            if self.use_atr_stop:
                stop_price_short = df['close'] + (self.atr_stop_multiple * df[atr_col])
            else:
                stop_price_short = df[exit_high]
            
            df.loc[short_breakout, 'signal'] = -1
            df.loc[short_breakout, 'entry_price'] = df.loc[short_breakout, 'close']
            df.loc[short_breakout, 'stop_price'] = stop_price_short[short_breakout]
            df.loc[short_breakout, 'reason'] = f'{self.entry_period}-day breakdown low'
        
        return df
    
    def check_current_signal(self, df):
        """Check for signal on most recent bar"""
        df = self.generate_signals(df)
        
        if df.empty:
            return None
        
        latest = df.iloc[-1]
        
        if latest['signal'] != 0:
            signal_type = 'LONG' if latest['signal'] == 1 else 'SHORT'
            return {
                'symbol': latest.get('symbol', 'Unknown'),
                'date': latest.name,
                'signal': signal_type,
                'entry_price': latest['entry_price'],
                'stop_price': latest['stop_price'],
                'reason': latest['reason'],
                'strategy': self.name,
                'risk_per_share': abs(latest['entry_price'] - latest['stop_price']),
                'atr': latest.get(f'atr_{self.atr_period}', 0),
                'parameters': {
                    'entry_period': self.entry_period,
                    'exit_period': self.exit_period,
                    'use_atr_stop': self.use_atr_stop
                }
            }
        
        return None


# Example usage
if __name__ == "__main__":
    from scripts.data_management.fetch_data import load_data
    
    # Test different parameter sets
    param_sets = [
        {'name': '50/25', 'entry_period': 50, 'exit_period': 25},
        {'name': '30/15', 'entry_period': 30, 'exit_period': 15},
        {'name': '100/50', 'entry_period': 100, 'exit_period': 50}
    ]
    
    symbol = 'SPY'
    df = load_data(symbol)
    
    print(f"\nTesting Donchian Breakout strategies on {symbol}\n")
    print("="*70)
    
    for params in param_sets:
        strategy = DonchianStrategy(config=params)
        current = strategy.check_current_signal(df)
        
        print(f"\n{params['name']} Breakout ({strategy.name}):")
        if current:
            print(f"  🎯 {current['signal']} at {current['entry_price']:.2f}")
            print(f"  Stop: {current['stop_price']:.2f}")
            print(f"  Risk: ${current['risk_per_share']:.2f}/share")
        else:
            print(f"  No current signal")

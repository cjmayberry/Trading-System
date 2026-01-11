"""
Swing Trading Strategy - Ultimate Guide to Swing Trading (Burns)

Hybrid trend/swing approach with EMA crossovers and dip-buying
Multiple entry variants: crossover, 50-MA dip, 200-MA dip
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from strategies.strategy_base import StrategyBase
from strategies.strategy_definitions import STRATEGIES


class SwingTradingStrategy(StrategyBase):
    """
    Swing Trading Strategy with multiple entry patterns
    
    Entry patterns:
    1. EMA 5/20 crossover (trend entry)
    2. 50-day MA dip-buy (pullback to support)
    3. 200-day MA dip-buy (deep pullback)
    
    Exit: EMA cross down, close below MA, or RSI profit-taking
    """
    
    def __init__(self, config=None):
        strategy_def = STRATEGIES['ultimate_guide_swing_trading_burns_2021_trend_variant']
        super().__init__(strategy_def, config)
        
        # Parameters
        self.fast_ema = config.get('fast_ema', 5) if config else 5
        self.slow_ema = config.get('slow_ema', 20) if config else 20
        self.ma_50 = config.get('ma_50', 50) if config else 50
        self.ma_200 = config.get('ma_200', 200) if config else 200
        self.rsi_period = config.get('rsi_period', 14) if config else 14
        self.rsi_profit_target = config.get('rsi_profit_target', 70) if config else 70
        self.atr_period = config.get('atr_period', 14) if config else 14
        
        # Entry mode: 'crossover', 'dip_50', 'dip_200', 'all'
        self.entry_mode = config.get('entry_mode', 'all') if config else 'all'
    
    def calculate_indicators(self, df):
        """Calculate EMAs, SMAs, RSI, ATR"""
        df = df.copy()
        
        # EMAs for crossover
        df[f'ema_{self.fast_ema}'] = df['close'].ewm(span=self.fast_ema, adjust=False).mean()
        df[f'ema_{self.slow_ema}'] = df['close'].ewm(span=self.slow_ema, adjust=False).mean()
        
        # SMAs for dip-buying
        df[f'sma_{self.ma_50}'] = df['close'].rolling(window=self.ma_50).mean()
        df[f'sma_{self.ma_200}'] = df['close'].rolling(window=self.ma_200).mean()
        
        # RSI for profit-taking
        df[f'rsi_{self.rsi_period}'] = self._calculate_rsi(df['close'], self.rsi_period)
        
        # ATR for sizing
        df[f'atr_{self.atr_period}'] = self._calculate_atr(df, self.atr_period)
        
        return df
    
    def generate_signals(self, df):
        """Generate swing trading signals"""
        df = self.calculate_indicators(df)
        
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_price'] = np.nan
        df['reason'] = ''
        df['entry_type'] = ''
        
        fast_col = f'ema_{self.fast_ema}'
        slow_col = f'ema_{self.slow_ema}'
        ma50_col = f'sma_{self.ma_50}'
        ma200_col = f'sma_{self.ma_200}'
        
        # ENTRY PATTERN 1: EMA Crossover
        if self.entry_mode in ['crossover', 'all']:
            cross_above = (
                (df[fast_col].shift(1) <= df[slow_col].shift(1)) &
                (df[fast_col] > df[slow_col])
            )
            
            df.loc[cross_above, 'signal'] = 1
            df.loc[cross_above, 'entry_price'] = df.loc[cross_above, 'close']
            df.loc[cross_above, 'stop_price'] = df.loc[cross_above, slow_col]
            df.loc[cross_above, 'reason'] = f'EMA {self.fast_ema}/{self.slow_ema} bullish cross'
            df.loc[cross_above, 'entry_type'] = 'crossover'
        
        # ENTRY PATTERN 2: 50-day MA Dip-Buy
        if self.entry_mode in ['dip_50', 'all']:
            # Price touches or crosses below 50-MA but closes above it
            dip_50 = (
                (df['low'] <= df[ma50_col]) &
                (df['close'] > df[ma50_col]) &
                (df['close'].shift(1) > df[ma50_col].shift(1))  # Was above yesterday
            )
            
            # Only mark if not already signaled by crossover
            new_dip_50 = dip_50 & (df['signal'] == 0)
            
            df.loc[new_dip_50, 'signal'] = 1
            df.loc[new_dip_50, 'entry_price'] = df.loc[new_dip_50, 'close']
            df.loc[new_dip_50, 'stop_price'] = df.loc[new_dip_50, ma50_col] * 0.98  # 2% below
            df.loc[new_dip_50, 'reason'] = '50-day MA dip-buy (bounce)'
            df.loc[new_dip_50, 'entry_type'] = 'dip_50'
        
        # ENTRY PATTERN 3: 200-day MA Dip-Buy (Deep Pullback)
        if self.entry_mode in ['dip_200', 'all']:
            dip_200 = (
                (df['low'] <= df[ma200_col]) &
                (df['close'] > df[ma200_col]) &
                (df['close'].shift(1) > df[ma200_col].shift(1))
            )
            
            new_dip_200 = dip_200 & (df['signal'] == 0)
            
            df.loc[new_dip_200, 'signal'] = 1
            df.loc[new_dip_200, 'entry_price'] = df.loc[new_dip_200, 'close']
            df.loc[new_dip_200, 'stop_price'] = df.loc[new_dip_200, ma200_col] * 0.97  # 3% below
            df.loc[new_dip_200, 'reason'] = '200-day MA deep dip-buy'
            df.loc[new_dip_200, 'entry_type'] = 'dip_200'
        
        return df
    
    def check_current_signal(self, df):
        """Check for signal on most recent bar"""
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
                'entry_type': latest['entry_type'],
                'strategy': self.name,
                'risk_per_share': latest['entry_price'] - latest['stop_price'],
                'atr': latest.get(f'atr_{self.atr_period}', 0),
                'rsi': latest.get(f'rsi_{self.rsi_period}', 50)
            }
        
        return None


# Example usage
if __name__ == "__main__":
    from scripts.data_management.fetch_data import load_data
    
    symbol = 'SPY'
    df = load_data(symbol)
    
    # Test different entry modes
    modes = ['crossover', 'dip_50', 'dip_200', 'all']
    
    print(f"\nTesting Swing Trading strategies on {symbol}\n")
    print("="*70)
    
    for mode in modes:
        strategy = SwingTradingStrategy(config={'entry_mode': mode})
        signals = strategy.generate_signals(df)
        recent = signals[signals['signal'] != 0].tail(3)
        
        print(f"\n{mode.upper()} mode:")
        print(f"Recent signals: {len(recent)}")
        if not recent.empty:
            print(recent[['entry_price', 'stop_price', 'reason', 'entry_type']].to_string())
        
        current = strategy.check_current_signal(df)
        if current:
            print(f"\n  🎯 CURRENT: {current['signal']} at {current['entry_price']:.2f}")
            print(f"  Type: {current['entry_type']}")
            print(f"  Stop: {current['stop_price']:.2f}")

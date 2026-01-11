"""
Qullamaggie HTF Strategy - High Tight Flag

Breakout continuation pattern in strong leaders
Requires: Strong prior move (pole), tight consolidation (flag), volume expansion on breakout
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from strategies.strategy_base import StrategyBase
from strategies.strategy_definitions import STRATEGIES


class QullamaggieHTFStrategy(StrategyBase):
    """
    High Tight Flag Pattern Strategy
    
    Setup requirements:
    1. Strong leader (relative strength, volume, above 50-MA)
    2. Pole: 90-100% move in ~8 weeks
    3. Flag: Tight consolidation near highs (10/20 EMAs)
    4. Breakout: Volume expansion above flag high
    
    Exit: Close below 10 EMA or 20 SMA
    """
    
    def __init__(self, config=None):
        strategy_def = STRATEGIES['qullamaggie_plan_suite_202x']['sub_strategies']['HTF_high_tight_flag']
        super().__init__(strategy_def, config)
        
        # Parameters
        self.ema_10 = 10
        self.sma_20 = 20
        self.ma_50 = 50
        self.volume_lookback = config.get('volume_lookback', 20) if config else 20
        self.volume_breakout_multiplier = config.get('volume_multiplier', 1.5) if config else 1.5
        self.min_dollar_volume = config.get('min_dollar_volume', 50_000_000) if config else 50_000_000
        
        # Pole/flag parameters (simplified for now)
        self.pole_lookback = config.get('pole_lookback', 40) if config else 40  # ~8 weeks
        self.min_pole_move = config.get('min_pole_move', 0.50) if config else 0.50  # 50% minimum
        self.max_flag_retrace = config.get('max_flag_retrace', 0.25) if config else 0.25  # 25% max
    
    def calculate_indicators(self, df):
        """Calculate EMAs, volume metrics, and pattern detection"""
        df = df.copy()
        
        # Moving averages
        df['ema_10'] = df['close'].ewm(span=self.ema_10, adjust=False).mean()
        df['sma_20'] = df['close'].rolling(window=self.sma_20).mean()
        df['sma_50'] = df['close'].rolling(window=self.ma_50).mean()
        
        # Volume metrics
        df['avg_volume'] = df['volume'].rolling(window=self.volume_lookback).mean()
        df['volume_ratio'] = df['volume'] / df['avg_volume']
        
        # Dollar volume (for liquidity filter)
        df['dollar_volume'] = df['close'] * df['volume']
        df['avg_dollar_volume'] = df['dollar_volume'].rolling(window=self.volume_lookback).mean()
        
        # Pattern detection helpers
        df['high_20'] = df['high'].rolling(window=20).max()
        df['low_20'] = df['low'].rolling(window=20).min()
        
        # Pole detection: N-bar percentage change
        df['pole_move'] = (df['close'] / df['close'].shift(self.pole_lookback)) - 1
        
        return df
    
    def generate_signals(self, df):
        """Generate HTF breakout signals"""
        df = self.calculate_indicators(df)
        
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_price'] = np.nan
        df['reason'] = ''
        
        # FILTER 1: Liquidity (average dollar volume)
        liquidity_ok = df['avg_dollar_volume'] >= self.min_dollar_volume
        
        # FILTER 2: Above 50-day MA (in uptrend)
        above_50ma = df['close'] > df['sma_50']
        
        # FILTER 3: Pole exists (strong prior move)
        strong_pole = df['pole_move'] >= self.min_pole_move
        
        # FILTER 4: Near highs (simplified - close within 10% of 20-day high)
        near_highs = df['close'] >= (df['high_20'] * 0.90)
        
        # FILTER 5: Tight consolidation (price between EMAs)
        tight = (
            (df['close'] >= df['ema_10']) &
            (df['close'] >= df['sma_20'])
        )
        
        # ENTRY TRIGGER: Breakout of 20-day high with volume
        breakout = df['high'] > df['high_20'].shift(1)
        volume_confirmation = df['volume_ratio'] >= self.volume_breakout_multiplier
        
        # Combine all conditions
        htf_signal = (
            liquidity_ok &
            above_50ma &
            strong_pole &
            near_highs &
            tight &
            breakout &
            volume_confirmation
        )
        
        df.loc[htf_signal, 'signal'] = 1
        df.loc[htf_signal, 'entry_price'] = df.loc[htf_signal, 'high']  # Buy breakout
        df.loc[htf_signal, 'stop_price'] = df.loc[htf_signal, 'low']  # Stop at day's low
        df.loc[htf_signal, 'reason'] = 'HTF breakout: strong leader, pole+flag, volume'
        
        return df
    
    def check_current_signal(self, df):
        """Check for HTF signal on most recent bar"""
        df = self.generate_signals(df)
        
        if df.empty:
            return None
        
        latest = df.iloc[-1]
        
        if latest['signal'] == 1:
            pole_pct = latest.get('pole_move', 0) * 100
            
            return {
                'symbol': latest.get('symbol', 'Unknown'),
                'date': latest.name,
                'signal': 'LONG',
                'entry_price': latest['entry_price'],
                'stop_price': latest['stop_price'],
                'reason': latest['reason'],
                'strategy': self.name,
                'risk_per_share': latest['entry_price'] - latest['stop_price'],
                'volume_ratio': latest.get('volume_ratio', 1.0),
                'dollar_volume': latest.get('avg_dollar_volume', 0),
                'pole_move_pct': f"{pole_pct:.1f}%",
                'pattern': 'High Tight Flag'
            }
        
        return None
    
    def screen_universe(self, symbol_list, data_dict):
        """
        Screen multiple symbols for HTF setups
        
        Args:
            symbol_list: List of symbols to scan
            data_dict: Dict of {symbol: DataFrame}
            
        Returns:
            List of signals
        """
        signals = []
        
        for symbol in symbol_list:
            if symbol not in data_dict:
                continue
                
            df = data_dict[symbol].copy()
            df['symbol'] = symbol
            
            signal = self.check_current_signal(df)
            if signal:
                signals.append(signal)
        
        return signals


# Example usage
if __name__ == "__main__":
    from scripts.data_management.fetch_data import load_data, fetch_historical_data
    
    # Test on a few high-volume stocks
    symbols = ['AAPL', 'TSLA', 'NVDA', 'AMD', 'MSFT']
    
    print(f"\nScanning {len(symbols)} symbols for HTF setups\n")
    print("="*70)
    
    strategy = QullamaggieHTFStrategy()
    
    # Load data for all symbols
    data_dict = {}
    for symbol in symbols:
        try:
            data_dict[symbol] = load_data(symbol)
        except:
            print(f"Could not load {symbol}")
            continue
    
    # Screen for signals
    signals = strategy.screen_universe(symbols, data_dict)
    
    if signals:
        print(f"\n🎯 Found {len(signals)} HTF signals:\n")
        for sig in signals:
            print(f"{sig['symbol']:6} | Entry: ${sig['entry_price']:7.2f} | "
                  f"Stop: ${sig['stop_price']:7.2f} | "
                  f"Risk: ${sig['risk_per_share']:5.2f} | "
                  f"Vol: {sig['volume_ratio']:.1f}x | "
                  f"Pole: {sig['pole_move_pct']}")
    else:
        print("\nNo HTF signals found in current universe")

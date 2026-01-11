"""
Strategy Base Class - Execution Engine for Strategy Definitions

This class reads strategy definitions and generates signals.
All specific strategies inherit from this base.
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from config.config import RISK_CONFIG


class StrategyBase(ABC):
    """
    Base class for all trading strategies
    
    Reads structured strategy definitions and implements core logic:
    - Signal generation
    - Position sizing
    - Risk management
    - Entry/exit conditions
    """
    
    def __init__(self, strategy_def, config=None):
        """
        Initialize strategy with definition dictionary
        
        Args:
            strategy_def: Dictionary containing strategy rules
            config: Optional config overrides
        """
        self.strategy_def = strategy_def
        self.config = config or {}
        self.name = strategy_def.get('meta', {}).get('name', 'Unnamed Strategy')
        
        # Extract key parameters
        self.meta = strategy_def.get('meta', {})
        self.rules = strategy_def.get('structured_rule_set_if_then', [])
        self.required_data = strategy_def.get('required_data', {})
        self.entry_conditions = strategy_def.get('entry_conditions_specific_testable', {})
        self.exit_conditions = strategy_def.get('exit_conditions_stops_targets_time', {})
        self.position_sizing = strategy_def.get('position_sizing_rules', {})
        self.params_to_optimize = strategy_def.get('parameters_to_optimize', [])
        
    def calculate_indicators(self, df):
        """
        Calculate all required indicators for the strategy
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with indicators added
        """
        df = df.copy()
        
        # Extract indicator requirements from strategy definition
        indicators = self.required_data.get('indicators', [])
        
        for indicator_spec in indicators:
            # Parse indicator string (e.g., "SMA(200)")
            if 'SMA' in str(indicator_spec):
                periods = self._extract_periods(indicator_spec, 'SMA')
                for period in periods:
                    df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
                    
            if 'EMA' in str(indicator_spec):
                periods = self._extract_periods(indicator_spec, 'EMA')
                for period in periods:
                    df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
                    
            if 'RSI' in str(indicator_spec):
                periods = self._extract_periods(indicator_spec, 'RSI')
                for period in periods:
                    df[f'rsi_{period}'] = self._calculate_rsi(df['close'], period)
                    
            if 'ATR' in str(indicator_spec):
                periods = self._extract_periods(indicator_spec, 'ATR')
                for period in periods:
                    df[f'atr_{period}'] = self._calculate_atr(df, period)
                    
            if 'MACD' in str(indicator_spec):
                df = self._calculate_macd(df)
        
        return df
    
    def _extract_periods(self, indicator_spec, indicator_name):
        """Extract period numbers from indicator specification"""
        import re
        pattern = f'{indicator_name}\\((\\d+)\\)'
        matches = re.findall(pattern, str(indicator_spec))
        return [int(m) for m in matches]
    
    def _calculate_rsi(self, series, period=14):
        """Calculate RSI indicator"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def _calculate_macd(self, df, fast=12, slow=26, signal=9):
        """Calculate MACD indicator"""
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        return df
    
    @abstractmethod
    def generate_signals(self, df):
        """
        Generate buy/sell signals based on strategy rules
        Must be implemented by each specific strategy
        
        Args:
            df: DataFrame with OHLCV and indicators
            
        Returns:
            DataFrame with 'signal' column (1=long, -1=short, 0=flat)
        """
        pass
    
    def calculate_position_size(self, entry_price, stop_price, account_equity):
        """
        Calculate position size based on risk parameters
        
        Args:
            entry_price: Entry price
            stop_price: Stop loss price
            account_equity: Current account equity
            
        Returns:
            Number of shares/contracts
        """
        # Get risk percentage from strategy definition or use default
        risk_pct = self.position_sizing.get('default_params', {}).get('risk_pct', 0.01)
        
        # Risk amount in dollars
        risk_dollars = account_equity * risk_pct
        
        # Risk per share
        risk_per_share = abs(entry_price - stop_price)
        
        if risk_per_share == 0:
            return 0
        
        # Calculate shares
        shares = int(risk_dollars / risk_per_share)
        
        # Apply max position size limit
        max_position_pct = RISK_CONFIG.get('max_position_risk_pct', 0.02)
        max_shares = int((account_equity * max_position_pct) / entry_price)
        
        return min(shares, max_shares)
    
    def check_entry_conditions(self, df, index):
        """
        Check if entry conditions are met at given index
        
        Args:
            df: DataFrame with data and indicators
            index: Row index to check
            
        Returns:
            dict with {'signal': bool, 'reason': str, 'type': str}
        """
        # This will be overridden by specific strategies
        return {'signal': False, 'reason': '', 'type': None}
    
    def check_exit_conditions(self, df, index, position):
        """
        Check if exit conditions are met
        
        Args:
            df: DataFrame with data and indicators
            index: Current row index
            position: Current position info
            
        Returns:
            dict with {'exit': bool, 'reason': str}
        """
        # This will be overridden by specific strategies
        return {'exit': False, 'reason': ''}
    
    def get_strategy_info(self):
        """Return strategy metadata"""
        return {
            'name': self.name,
            'timeframe': self.meta.get('timeframe', 'Unknown'),
            'asset_class': self.meta.get('asset_class', 'Unknown'),
            'style': self.meta.get('style', 'Unknown'),
            'source': self.meta.get('source_file', 'Unknown')
        }
    
    def __repr__(self):
        return f"Strategy({self.name})"

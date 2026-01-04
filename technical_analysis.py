"""
技术分析模块 - 计算各种技术指标
"""

import pandas as pd
import numpy as np
from config import TECHNICAL_CONFIG


class TechnicalAnalyzer:
    """技术分析类"""
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化技术分析器
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
        """
        self.df = df.copy()
        self.indicators = {}
        self.signals = {}
        
    def calculate_all(self):
        """计算所有技术指标"""
        self.calculate_ma()
        self.calculate_rsi()
        self.calculate_macd()
        self.calculate_bollinger_bands()
        self.calculate_volume_indicators()
        self.calculate_atr()
        
    def calculate_ma(self):
        """计算移动平均线"""
        for period in TECHNICAL_CONFIG["ma_periods"]:
            self.df[f'MA{period}'] = self.df['Close'].rolling(window=period).mean()
        
        # 判断均线排列
        ma_values = [self.df[f'MA{p}'].iloc[-1] for p in TECHNICAL_CONFIG["ma_periods"]]
        is_bullish = all(ma_values[i] > ma_values[i+1] for i in range(len(ma_values)-1))
        is_bearish = all(ma_values[i] < ma_values[i+1] for i in range(len(ma_values)-1))
        
        self.indicators['ma_alignment'] = 'bullish' if is_bullish else ('bearish' if is_bearish else 'mixed')
        
        # 金叉/死叉检测 (MA5 和 MA20)
        if len(self.df) >= 2:
            ma5_curr = self.df['MA5'].iloc[-1]
            ma5_prev = self.df['MA5'].iloc[-2]
            ma20_curr = self.df['MA20'].iloc[-1]
            ma20_prev = self.df['MA20'].iloc[-2]
            
            if ma5_prev <= ma20_prev and ma5_curr > ma20_curr:
                self.signals['ma_cross'] = 'golden_cross'
            elif ma5_prev >= ma20_prev and ma5_curr < ma20_curr:
                self.signals['ma_cross'] = 'death_cross'
            else:
                self.signals['ma_cross'] = 'none'
    
    def calculate_rsi(self, period: int = None):
        """计算 RSI 指标"""
        if period is None:
            period = TECHNICAL_CONFIG["rsi_period"]
        
        delta = self.df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        self.df['RSI'] = 100 - (100 / (1 + rs))
        
        current_rsi = self.df['RSI'].iloc[-1]
        self.indicators['rsi'] = current_rsi
        
        # RSI 信号
        if current_rsi > 70:
            self.signals['rsi'] = 'overbought'
        elif current_rsi < 30:
            self.signals['rsi'] = 'oversold'
        else:
            self.signals['rsi'] = 'neutral'
    
    def calculate_macd(self):
        """计算 MACD 指标"""
        fast = TECHNICAL_CONFIG["macd_fast"]
        slow = TECHNICAL_CONFIG["macd_slow"]
        signal = TECHNICAL_CONFIG["macd_signal"]
        
        ema_fast = self.df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = self.df['Close'].ewm(span=slow, adjust=False).mean()
        
        self.df['MACD'] = ema_fast - ema_slow
        self.df['MACD_Signal'] = self.df['MACD'].ewm(span=signal, adjust=False).mean()
        self.df['MACD_Hist'] = self.df['MACD'] - self.df['MACD_Signal']
        
        # MACD 金叉/死叉
        if len(self.df) >= 2:
            macd_curr = self.df['MACD'].iloc[-1]
            macd_prev = self.df['MACD'].iloc[-2]
            signal_curr = self.df['MACD_Signal'].iloc[-1]
            signal_prev = self.df['MACD_Signal'].iloc[-2]
            
            if macd_prev <= signal_prev and macd_curr > signal_curr:
                self.signals['macd'] = 'golden_cross'
            elif macd_prev >= signal_prev and macd_curr < signal_curr:
                self.signals['macd'] = 'death_cross'
            else:
                self.signals['macd'] = 'none'
            
            self.indicators['macd_value'] = macd_curr
            self.indicators['macd_signal'] = signal_curr
            self.indicators['macd_hist'] = self.df['MACD_Hist'].iloc[-1]
    
    def calculate_bollinger_bands(self):
        """计算布林带"""
        period = TECHNICAL_CONFIG["bb_period"]
        std_dev = TECHNICAL_CONFIG["bb_std"]
        
        self.df['BB_Middle'] = self.df['Close'].rolling(window=period).mean()
        bb_std = self.df['Close'].rolling(window=period).std()
        self.df['BB_Upper'] = self.df['BB_Middle'] + (bb_std * std_dev)
        self.df['BB_Lower'] = self.df['BB_Middle'] - (bb_std * std_dev)
        
        current_price = self.df['Close'].iloc[-1]
        bb_upper = self.df['BB_Upper'].iloc[-1]
        bb_middle = self.df['BB_Middle'].iloc[-1]
        bb_lower = self.df['BB_Lower'].iloc[-1]
        
        self.indicators['bb_upper'] = bb_upper
        self.indicators['bb_middle'] = bb_middle
        self.indicators['bb_lower'] = bb_lower
        
        # 布林带位置
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) * 100
        self.indicators['bb_position'] = bb_position
        
        if current_price > bb_upper:
            self.signals['bollinger'] = 'above_upper'
        elif current_price < bb_lower:
            self.signals['bollinger'] = 'below_lower'
        else:
            self.signals['bollinger'] = 'within_bands'
    
    def calculate_volume_indicators(self):
        """计算成交量指标"""
        period = TECHNICAL_CONFIG["volume_ma_period"]
        
        self.df['Volume_MA'] = self.df['Volume'].rolling(window=period).mean()
        
        current_volume = self.df['Volume'].iloc[-1]
        avg_volume = self.df['Volume_MA'].iloc[-1]
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        self.indicators['volume_ratio'] = volume_ratio
        
        if volume_ratio > 1.5:
            self.signals['volume'] = 'high'
        elif volume_ratio < 0.5:
            self.signals['volume'] = 'low'
        else:
            self.signals['volume'] = 'normal'
    
    def calculate_atr(self, period: int = None):
        """计算 ATR (Average True Range)"""
        if period is None:
            period = TECHNICAL_CONFIG["rsi_period"]
        
        high = self.df['High']
        low = self.df['Low']
        close = self.df['Close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        self.df['ATR'] = tr.rolling(window=period).mean()
        
        self.indicators['atr'] = self.df['ATR'].iloc[-1]
    
    def get_trend_score(self) -> float:
        """
        计算趋势得分 (-100 到 +100)
        
        Returns:
            float: 趋势得分
        """
        score = 0
        
        # MA 排列 (30分)
        if self.indicators.get('ma_alignment') == 'bullish':
            score += 30
        elif self.indicators.get('ma_alignment') == 'bearish':
            score -= 30
        
        # MA 金叉/死叉 (20分)
        if self.signals.get('ma_cross') == 'golden_cross':
            score += 20
        elif self.signals.get('ma_cross') == 'death_cross':
            score -= 20
        
        # MACD (20分)
        if self.signals.get('macd') == 'golden_cross':
            score += 20
        elif self.signals.get('macd') == 'death_cross':
            score -= 20
        elif self.indicators.get('macd_hist', 0) > 0:
            score += 10
        elif self.indicators.get('macd_hist', 0) < 0:
            score -= 10
        
        # RSI (15分)
        rsi = self.indicators.get('rsi', 50)
        if rsi > 70:
            score -= 15  # 超买
        elif rsi < 30:
            score += 15  # 超卖（可能反弹）
        elif 40 <= rsi <= 60:
            score += 5   # 中性偏好
        
        # 布林带 (10分)
        if self.signals.get('bollinger') == 'below_lower':
            score += 10  # 超卖
        elif self.signals.get('bollinger') == 'above_upper':
            score -= 10  # 超买
        
        # 成交量 (5分)
        if self.signals.get('volume') == 'high':
            # 放量配合趋势
            if score > 0:
                score += 5
            else:
                score -= 5
        
        return max(-100, min(100, score))
    
    def get_current_price(self) -> float:
        """获取当前价格"""
        return self.df['Close'].iloc[-1]
    
    def get_price_change(self) -> dict:
        """获取价格变化"""
        current = self.df['Close'].iloc[-1]
        prev = self.df['Close'].iloc[-2] if len(self.df) >= 2 else current
        
        change = current - prev
        change_pct = (change / prev * 100) if prev > 0 else 0
        
        return {
            "current": current,
            "previous": prev,
            "change": change,
            "change_pct": change_pct
        }

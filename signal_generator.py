"""
信号生成和风险管理模块
"""

from typing import Dict
from config import SCORING_CONFIG, SIGNAL_THRESHOLDS, RISK_CONFIG


class SignalGenerator:
    """信号生成器"""
    
    def __init__(self, technical_score: float, sentiment_score: float, 
                 current_price: float, atr: float):
        """
        初始化信号生成器
        
        Args:
            technical_score: 技术分析得分
            sentiment_score: 情绪分析得分
            current_price: 当前价格
            atr: ATR 值
        """
        self.technical_score = technical_score
        self.sentiment_score = sentiment_score
        self.current_price = current_price
        self.atr = atr
        
        # 计算综合得分
        self.composite_score = (
            technical_score * SCORING_CONFIG["technical_weight"] +
            sentiment_score * SCORING_CONFIG["sentiment_weight"]
        )
    
    def generate_signal(self) -> Dict:
        """
        生成交易信号
        
        Returns:
            dict: 交易信号信息
        """
        score = self.composite_score
        
        # 判断信号类型
        if score > SIGNAL_THRESHOLDS["strong_buy"]:
            signal = "强烈买入"
            signal_emoji = "🟢🟢"
            action = "建议积极建仓或加仓"
            color = "green"
        elif score > SIGNAL_THRESHOLDS["buy"]:
            signal = "买入"
            signal_emoji = "🟢"
            action = "可考虑建仓或小幅加仓"
            color = "green"
        elif score > SIGNAL_THRESHOLDS["sell"]:
            signal = "持有"
            signal_emoji = "🟡"
            action = "维持现有仓位，观望为主"
            color = "yellow"
        elif score > SIGNAL_THRESHOLDS["strong_sell"]:
            signal = "卖出"
            signal_emoji = "🔴"
            action = "建议减仓或离场观望"
            color = "red"
        else:
            signal = "强烈卖出"
            signal_emoji = "🔴🔴"
            action = "建议清仓离场"
            color = "red"
        
        return {
            "signal": signal,
            "signal_emoji": signal_emoji,
            "action": action,
            "color": color,
            "composite_score": round(score, 2),
            "technical_score": round(self.technical_score, 2),
            "sentiment_score": round(self.sentiment_score, 2)
        }
    
    def calculate_risk_metrics(self) -> Dict:
        """
        计算风险指标
        
        Returns:
            dict: 风险指标
        """
        # 基于 ATR 的止损位
        atr_stop_loss = self.current_price - (self.atr * RISK_CONFIG["atr_multiplier"])
        atr_stop_loss_pct = ((self.current_price - atr_stop_loss) / self.current_price) * 100
        
        # 默认百分比止损位
        pct_stop_loss = self.current_price * (1 - RISK_CONFIG["stop_loss_pct"])
        pct_stop_loss_pct = RISK_CONFIG["stop_loss_pct"] * 100
        
        # 选择较宽松的止损位（风险较小）
        if atr_stop_loss > pct_stop_loss:
            stop_loss = atr_stop_loss
            stop_loss_pct = atr_stop_loss_pct
            stop_loss_method = "ATR"
        else:
            stop_loss = pct_stop_loss
            stop_loss_pct = pct_stop_loss_pct
            stop_loss_method = "固定百分比"
        
        # 目标位（基于风险回报比 1:2）
        risk_amount = self.current_price - stop_loss
        target_price = self.current_price + (risk_amount * 2)
        target_pct = ((target_price - self.current_price) / self.current_price) * 100
        
        # 波动率评估
        volatility_pct = (self.atr / self.current_price) * 100
        
        if volatility_pct < 1:
            volatility_level = "低"
            risk_level = "低"
        elif volatility_pct < 2:
            volatility_level = "中"
            risk_level = "中"
        else:
            volatility_level = "高"
            risk_level = "高"
        
        # 仓位建议
        if self.composite_score > 60:
            position_suggestion = "40-50%"
        elif self.composite_score > 30:
            position_suggestion = "30-40%"
        elif self.composite_score > 0:
            position_suggestion = "20-30%"
        elif self.composite_score > -30:
            position_suggestion = "10-20%"
        else:
            position_suggestion = "0-10%"
        
        return {
            "stop_loss": round(stop_loss, 2),
            "stop_loss_pct": round(stop_loss_pct, 2),
            "stop_loss_method": stop_loss_method,
            "target_price": round(target_price, 2),
            "target_pct": round(target_pct, 2),
            "volatility_pct": round(volatility_pct, 2),
            "volatility_level": volatility_level,
            "risk_level": risk_level,
            "position_suggestion": position_suggestion,
            "risk_reward_ratio": "1:2"
        }
    
    def generate_key_points(self, technical_indicators: Dict, 
                           sentiment_result: Dict) -> list:
        """
        生成关键提示点
        
        Args:
            technical_indicators: 技术指标
            sentiment_result: 情绪分析结果
            
        Returns:
            list: 关键提示列表
        """
        points = []
        
        # 技术面提示
        ma_alignment = technical_indicators.get('ma_alignment', 'mixed')
        if ma_alignment == 'bullish':
            points.append("均线呈多头排列，短期趋势向好")
        elif ma_alignment == 'bearish':
            points.append("均线呈空头排列，短期趋势偏弱")
        
        rsi = technical_indicators.get('rsi', 50)
        if rsi > 70:
            points.append(f"RSI 处于超买区域 ({rsi:.1f})，注意回调风险")
        elif rsi < 30:
            points.append(f"RSI 处于超卖区域 ({rsi:.1f})，可能存在反弹机会")
        
        # 消息面提示
        sentiment_label = sentiment_result.get('sentiment_label', 'neutral')
        if sentiment_label == 'positive':
            points.append("消息面偏正面，市场情绪乐观")
        elif sentiment_label == 'negative':
            points.append("消息面偏负面，市场情绪谨慎")
        
        # 成交量提示
        volume_ratio = technical_indicators.get('volume_ratio', 1)
        if volume_ratio > 1.5:
            points.append(f"成交量放大 ({volume_ratio:.1f}x)，市场活跃度提升")
        elif volume_ratio < 0.5:
            points.append("成交量萎缩，市场观望情绪浓厚")
        
        # 通用风险提示
        points.append("注意大盘整体走势影响")
        
        if self.composite_score > 0:
            points.append("建议分批建仓，控制风险")
        else:
            points.append("建议谨慎操作，等待更好时机")
        
        return points

"""
配置文件 - 美股投资 Agent
"""

TWELVE_DATA_API_KEY = "85b9e20e7e4b4695a076ade8cead57a6"

# API 配置
FINNHUB_API_KEY = "d5d5bqpr01qvl80nqbj0d5d5bqpr01qvl80nqbjg"  # 用户需要在 https://finnhub.io/register 注册获取免费 API Key



# 技术分析参数
TECHNICAL_CONFIG = {
    "lookback_days": 90,          # 历史数据天数
    "rsi_period": 14,             # RSI 周期
    "macd_fast": 12,              # MACD 快线
    "macd_slow": 26,              # MACD 慢线
    "macd_signal": 9,             # MACD 信号线
    "bb_period": 20,              # 布林带周期
    "bb_std": 2,                  # 布林带标准差倍数
    "volume_ma_period": 20,       # 成交量均线周期
    "ma_periods": [5, 10, 20, 50], # 移动平均线周期
}

# 消息面分析参数
SENTIMENT_CONFIG = {
    "news_lookback_days": 7,      # 新闻回溯天数
    "min_news_count": 3,          # 最小新闻数量
    "use_finbert": True,          # 是否使用 FinBERT 模型
    "news_processing_limit": 20,  # 最多处理多少条新闻进行情绪分析
}

# 评分权重
SCORING_CONFIG = {
    "technical_weight": 0.6,      # 技术分析权重
    "sentiment_weight": 0.4,      # 情绪分析权重
}

# 信号阈值
SIGNAL_THRESHOLDS = {
    "strong_buy": 60,
    "buy": 30,
    "sell": -30,
    "strong_sell": -60,
}

# 风险管理参数
RISK_CONFIG = {
    "stop_loss_pct": 0.03,        # 默认止损百分比 3%
    "atr_period": 14,             # ATR 周期
    "atr_multiplier": 2.0,        # ATR 止损倍数
}

# 输出配置
OUTPUT_CONFIG = {
    "use_color": True,            # 是否使用彩色输出
    "save_json": True,            # 是否保存 JSON 报告
    "generate_chart": False,      # 是否生成图表（需要 matplotlib）
}

# 缓存配置
CACHE_CONFIG = {
    "enable_cache": True,
    "cache_dir": "cache",
    "cache_expire_hours": 1,      # 缓存过期时间（小时）
}

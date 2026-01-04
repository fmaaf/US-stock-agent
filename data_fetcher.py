"""
数据获取模块 - 使用 Twelve Data API (彻底解决 Yahoo 反爬问题)
"""

import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta
from config import FINNHUB_API_KEY, CACHE_CONFIG, TECHNICAL_CONFIG, SENTIMENT_CONFIG, TWELVE_DATA_API_KEY

class DataFetcher:
    """数据获取类"""
    
    def __init__(self):
        self.cache_dir = CACHE_CONFIG["cache_dir"]
        self.cache_enabled = CACHE_CONFIG["enable_cache"]
        self.cache_expire_hours = CACHE_CONFIG["cache_expire_hours"]
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_stock_data(self, symbol: str, days: int = None) -> pd.DataFrame:
        """
        使用 Twelve Data API 获取 K 线数据
        """
        if days is None:
            days = TECHNICAL_CONFIG["lookback_days"]
        
        # 统一大写
        symbol = symbol.upper()
        cache_file = os.path.join(self.cache_dir, f"{symbol}_stock.json")
        
        # 1. 检查缓存
        if self.cache_enabled and os.path.exists(cache_file):
            try:
                cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
                # 缩短缓存时间检查，确保数据新鲜，但如果有缓存且未过期则使用
                if datetime.now() - cache_time < timedelta(hours=self.cache_expire_hours):
                    print(f"[缓存] 从缓存加载 {symbol} 股票数据")
                    df = pd.read_json(cache_file)
                    if not isinstance(df.index, pd.DatetimeIndex):
                        df.index = pd.to_datetime(df.index)
                    return df
            except Exception:
                pass # 缓存出错直接忽略，去网络获取

        # 2. 网络获取 (Twelve Data)
        print(f"[数据] 正规 API 获取 {symbol} 数据 (Twelve Data)...")
        
        try:
            # 计算需要的数量 (outputsize)。Twelve Data 免费版一次最多 5000 条，足够了
            # 简单起见，直接请求最近的 500 条，覆盖中短期分析
            url = "https://api.twelvedata.com/time_series"
            params = {
                "symbol": symbol,
                "interval": "1day",
                "outputsize": 365, # 获取过去一年的数据
                "apikey": TWELVE_DATA_API_KEY,
                "order": "ASC" # 按日期升序
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if "code" in data and data["code"] == 429:
                 raise Exception("Twelve Data API 频率超限 (每分钟限制8次)，请稍等再试。")
            
            if "values" not in data:
                raise Exception(f"API 返回错误: {data.get('message', '未知错误')}")
            
            # 转换为 DataFrame
            df = pd.DataFrame(data["values"])
            
            # 数据清洗
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')
            
            # 转换列类型 (API返回的是字符串)
            cols = ['open', 'high', 'low', 'close', 'volume']
            for col in cols:
                df[col] = pd.to_numeric(df[col])
            
            # 重命名列以匹配你的技术分析模块 (首字母大写)
            df.columns = [c.capitalize() for c in df.columns]
            
            print(f"[成功] 获取到 {len(df)} 条K线数据")

            # 3. 保存缓存
            if self.cache_enabled:
                df.to_json(cache_file, date_format='iso')
                
            return df

        except Exception as e:
            raise Exception(f"获取股票数据失败: {str(e)}")

    def get_news(self, symbol: str, days: int = None) -> list:
        """获取股票相关新闻 (保持 Finnhub 不变)"""
        if days is None:
            days = SENTIMENT_CONFIG["news_lookback_days"]
        
        if not FINNHUB_API_KEY:
            return []
        
        cache_file = os.path.join(self.cache_dir, f"{symbol}_news.json")
        
        # 简单缓存检查
        if self.cache_enabled and os.path.exists(cache_file):
            try:
                cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
                if datetime.now() - cache_time < timedelta(hours=self.cache_expire_hours):
                    print(f"[缓存] 从缓存加载 {symbol} 新闻数据")
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except: pass
        
        try:
            print(f"[数据] 获取 {symbol} 新闻数据...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = "https://finnhub.io/api/v1/company-news"
            params = {
                "symbol": symbol,
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "token": FINNHUB_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                news_data = response.json()
                if self.cache_enabled:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(news_data, f, ensure_ascii=False, indent=2)
                return news_data
            return []
        
        except Exception:
            return []
    
    def get_company_info(self, symbol: str) -> dict:
        """获取公司基本信息 (使用 Twelve Data)"""
        try:
            url = "https://api.twelvedata.com/profile"
            params = {
                "symbol": symbol,
                "apikey": TWELVE_DATA_API_KEY
            }
            res = requests.get(url, params=params, timeout=10).json()
            
            if "symbol" not in res:
                return {"name": symbol, "sector": "N/A", "industry": "N/A", "market_cap": 0, "currency": "USD"}

            return {
                "name": res.get("name", symbol),
                "sector": res.get("sector", "N/A"),
                "industry": res.get("industry", "N/A"),
                # Twelve Data profile 不直接返回市值，暂设为0或需要额外接口
                "market_cap": 0, 
                "currency": res.get("currency", "USD"),
            }
        except Exception:
            return {"name": symbol, "sector": "N/A", "industry": "N/A", "market_cap": 0, "currency": "USD"}
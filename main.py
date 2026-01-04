#!/usr/bin/env python3
"""
美股投资 Agent 主程序
结合技术分析和消息面分析，提供中短期交易信号和建议
"""

import sys
import argparse
from data_fetcher import DataFetcher
from technical_analysis import TechnicalAnalyzer
from sentiment_analysis import SentimentAnalyzer
from signal_generator import SignalGenerator
from report_generator import ReportGenerator
from config import OUTPUT_CONFIG, SENTIMENT_CONFIG


class StockTradingAgent:
    """美股投资 Agent"""
    
    def __init__(self):
        """初始化 Agent"""
        self.data_fetcher = DataFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def analyze(self, symbol: str, use_finbert: bool = False) -> dict:
        """
        分析股票并生成报告
        
        Args:
            symbol: 股票代码
            use_finbert: 是否使用 FinBERT 模型
            
        Returns:
            dict: 分析结果
        """
        print(f"\n{'='*60}")
        print(f"开始分析股票: {symbol.upper()}")
        print(f"{'='*60}\n")
        
        # 1. 获取数据
        try:
            # 获取股票数据
            stock_data = self.data_fetcher.get_stock_data(symbol)
            
            # 获取公司信息
            company_info = self.data_fetcher.get_company_info(symbol)
            
            # 获取新闻数据
            news_data = self.data_fetcher.get_news(symbol)
            
        except Exception as e:
            print(f"\n[错误] 数据获取失败: {str(e)}")
            return None
        
        # 2. 技术分析
        print("[分析] 进行技术分析...")
        technical_analyzer = TechnicalAnalyzer(stock_data)
        technical_analyzer.calculate_all()
        
        technical_score = technical_analyzer.get_trend_score()
        price_info = technical_analyzer.get_price_change()
        
        # 3. 情绪分析
        print("[分析] 进行情绪分析...")
        sentiment_result = self.sentiment_analyzer.analyze_news(
            news_data, 
            use_finbert=use_finbert
        )
        
        sentiment_score = sentiment_result['sentiment_score']
        
        # 4. 生成交易信号
        print("[分析] 生成交易信号...")
        signal_gen = SignalGenerator(
            technical_score=technical_score,
            sentiment_score=sentiment_score,
            current_price=technical_analyzer.get_current_price(),
            atr=technical_analyzer.indicators.get('atr', 0)
        )
        
        signal_info = signal_gen.generate_signal()
        risk_metrics = signal_gen.calculate_risk_metrics()
        key_points = signal_gen.generate_key_points(
            technical_analyzer.indicators,
            sentiment_result
        )
        
        # 5. 生成报告
        print("[分析] 生成分析报告...")
        report_gen = ReportGenerator(symbol.upper(), company_info)
        
        # 终端输出
        terminal_report = report_gen.generate_terminal_report(
            price_info=price_info,
            technical_indicators=technical_analyzer.indicators,
            technical_signals=technical_analyzer.signals,
            sentiment_result=sentiment_result,
            signal_info=signal_info,
            risk_metrics=risk_metrics,
            key_points=key_points
        )
        
        print(terminal_report)
        
        # JSON 报告
        json_report = report_gen.generate_json_report(
            price_info=price_info,
            technical_indicators=technical_analyzer.indicators,
            technical_signals=technical_analyzer.signals,
            sentiment_result=sentiment_result,
            signal_info=signal_info,
            risk_metrics=risk_metrics,
            key_points=key_points
        )
        
        if OUTPUT_CONFIG["save_json"]:
            report_gen.save_json_report(json_report)
        
        return json_report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="美股投资 Agent - 基于技术分析和消息面的交易信号生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py AAPL              # 分析苹果公司股票
  python main.py TSLA --finbert    # 分析特斯拉股票，使用 FinBERT 模型
  python main.py MSFT GOOGL NVDA   # 批量分析多只股票
        """
    )
    
    parser.add_argument(
        'symbols',
        nargs='+',
        help='股票代码（可以输入多个）'
    )
    
    parser.add_argument(
        '--finbert',
        action='store_true',
        help='使用 FinBERT 模型进行情绪分析（需要安装 transformers 库）'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='禁用彩色输出'
    )
    
    args = parser.parse_args()
    
    # 更新配置
    if args.no_color:
        OUTPUT_CONFIG["use_color"] = False
    
    # 创建 Agent
    agent = StockTradingAgent()
    
    # 分析股票
    for symbol in args.symbols:
        try:
            agent.analyze(symbol.upper(), use_finbert=args.finbert)
        except KeyboardInterrupt:
            print("\n\n[提示] 用户中断程序")
            sys.exit(0)
        except Exception as e:
            print(f"\n[错误] 分析 {symbol} 时出错: {str(e)}")
            continue
        
        # 如果有多个股票，添加分隔
        if len(args.symbols) > 1 and symbol != args.symbols[-1]:
            print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()

"""
报告生成模块 - 生成分析报告
(已改进：打印完整新闻摘要，支持自动换行)
"""

import json
import textwrap  # <--- 新增：用于文本自动换行
from datetime import datetime
from typing import Dict
from config import OUTPUT_CONFIG

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, symbol: str, company_info: Dict):
        self.symbol = symbol
        self.company_info = company_info
        self.use_color = OUTPUT_CONFIG["use_color"]
    
    def _colorize(self, text: str, color: str) -> str:
        """为文本添加颜色"""
        if not self.use_color:
            return text
        
        colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "grey": "\033[90m", # 新增灰色
            "bold": "\033[1m",
            "reset": "\033[0m"
        }
        return f"{colors.get(color, '')}{text}{colors['reset']}"
    
    def generate_terminal_report(self, price_info: Dict, technical_indicators: Dict,
                                 technical_signals: Dict, sentiment_result: Dict,
                                 signal_info: Dict, risk_metrics: Dict,
                                 key_points: list) -> str:
        report = []
        
        # === 标题 ===
        report.append("\n" + "=" * 60)
        report.append(self._colorize("美股投资 Agent 分析报告", "bold"))
        report.append("=" * 60)
        
        # === 基本信息 ===
        report.append(f"\n【基本信息】")
        report.append(f"股票代码: {self._colorize(self.symbol, 'cyan')}")
        report.append(f"公司名称: {self.company_info.get('name', 'N/A')}")
        report.append(f"所属行业: {self.company_info.get('sector', 'N/A')} - {self.company_info.get('industry', 'N/A')}")
        report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # === 价格信息 ===
        current_price = price_info['current']
        change = price_info['change']
        change_pct = price_info['change_pct']
        change_color = "green" if change >= 0 else "red"
        change_symbol = "+" if change >= 0 else ""
        
        report.append(f"\n【价格信息】")
        report.append(f"当前价格: {self._colorize(f'${current_price:.2f}', 'bold')}")
        report.append(f"涨跌幅: {self._colorize(f'{change_symbol}{change:.2f} ({change_symbol}{change_pct:.2f}%)', change_color)}")
        
        # === 技术分析 ===
        report.append(f"\n【技术分析】")
        ma_alignment = technical_indicators.get('ma_alignment', 'mixed')
        ma_text = {"bullish": "上升趋势 ✓", "bearish": "下降趋势 ✗", "mixed": "震荡整理 ~"}
        ma_color = {"bullish": "green", "bearish": "red", "mixed": "yellow"}
        report.append(f"趋势判断: {self._colorize(ma_text[ma_alignment], ma_color[ma_alignment])}")
        
        rsi = technical_indicators.get('rsi', 50)
        rsi_signal = technical_signals.get('rsi', 'neutral')
        rsi_text = {"overbought": "超买", "oversold": "超卖", "neutral": "中性"}
        report.append(f"RSI(14): {rsi:.1f} ({rsi_text[rsi_signal]})")
        
        macd_signal = technical_signals.get('macd', 'none')
        macd_text = {"golden_cross": "金叉 ✓", "death_cross": "死叉 ✗", "none": "无明显信号"}
        macd_color = {"golden_cross": "green", "death_cross": "red", "none": "white"}
        report.append(f"MACD: {self._colorize(macd_text[macd_signal], macd_color[macd_signal])}")

        volume_ratio = technical_indicators.get('volume_ratio', 1)
        volume_signal = technical_signals.get('volume', 'normal')
        volume_text = {"high": "放量", "low": "缩量", "normal": "正常"}
        report.append(f"成交量: {volume_text[volume_signal]} ({volume_ratio:.1f}x)")
        
        # === 消息面分析 (完整版) ===
        report.append(f"\n【消息面分析】")
        total_news = sentiment_result.get('total_news', 0)
        
        if total_news > 0:
            report.append(f"新闻统计: 总计 {total_news} 条 | " + 
                          f"{self._colorize(str(sentiment_result['positive_count']) + ' 正面', 'green')} | " +
                          f"{self._colorize(str(sentiment_result['negative_count']) + ' 负面', 'red')}")
            
            sentiment_score = sentiment_result['sentiment_score']
            sentiment_label = sentiment_result['sentiment_label']
            sentiment_color = {"positive": "green", "negative": "red", "neutral": "yellow"}
            desc_map = {"positive": "情绪乐观", "negative": "情绪悲观", "neutral": "情绪平稳"}
            sentiment_desc = desc_map.get(sentiment_label, "中性")
            
            report.append(f"情绪总分: {self._colorize(f'{sentiment_score:+.2f}', sentiment_color[sentiment_label])} ({sentiment_desc})")
            
            # --- 打印详细新闻 ---
            news_list = sentiment_result.get('news_list', [])
            if news_list:
                # 筛选重要新闻（正面和负面），如果是中性新闻通常不打印全文以免刷屏
                pos_news = [n for n in news_list if n.get('sentiment') == 'positive'][:3]
                neg_news = [n for n in news_list if n.get('sentiment') == 'negative'][:3]
                
                def print_news_item(item, color_code):
                    """内部函数：漂亮地打印单条新闻"""
                    headline = item.get('headline', '无标题')
                    summary = item.get('summary', '').strip()
                    url = item.get('url', '')
                    time_str = item.get('datetime', '')

                    # 标题
                    report.append(f"\n  {self._colorize('● ' + headline, color_code)}")
                    report.append(f"    {self._colorize(time_str, 'grey')}")
                    
                    # 摘要（自动折行，缩进4格）
                    if summary and summary != headline:
                        wrapper = textwrap.TextWrapper(initial_indent='    ', subsequent_indent='    ', width=75)
                        report.append(self._colorize(wrapper.fill(summary), 'white'))
                    
                    # 链接
                    if url:
                         report.append(f"    {self._colorize('Link: ' + url, 'blue')}")

                if pos_news:
                    report.append(f"\n  {self._colorize('[主要利好详情]', 'green')}")
                    report.append(f"  {self._colorize('-' * 20, 'green')}")
                    for n in pos_news:
                        print_news_item(n, 'green')
                
                if neg_news:
                    report.append(f"\n  {self._colorize('[主要利空详情]', 'red')}")
                    report.append(f"  {self._colorize('-' * 20, 'red')}")
                    for n in neg_news:
                        print_news_item(n, 'red')
                        
        else:
            report.append(self._colorize("未获取到足够的新闻数据", "yellow"))
        
        # === 综合评分 ===
        report.append(f"\n【综合评分】")
        report.append(f"技术得分: {signal_info['technical_score']:+.1f}")
        report.append(f"情绪得分: {signal_info['sentiment_score']:+.1f}")
        composite_score_text = f"{signal_info['composite_score']:+.1f}"
        report.append(f"综合得分: {self._colorize(composite_score_text, signal_info['color'])}")
        
        # === 交易建议 ===
        report.append(f"\n【交易建议】")
        report.append(f"信号: {self._colorize(signal_info['signal'] + ' ' + signal_info['signal_emoji'], signal_info['color'])}")
        report.append(f"建议操作: {signal_info['action']}")
        report.append(f"止损位: ${risk_metrics['stop_loss']:.2f} (-{risk_metrics['stop_loss_pct']:.1f}%)")
        report.append(f"目标位: ${risk_metrics['target_price']:.2f} (+{risk_metrics['target_pct']:.1f}%)")
        
        # === 关键提示 ===
        report.append(f"\n【关键提示】")
        for i, point in enumerate(key_points, 1):
            report.append(f"  {i}. {point}")
        
        report.append(f"\n{self._colorize('【免责声明】本报告仅供参考。', 'yellow')}")
        report.append("=" * 60 + "\n")
        
        return "\n".join(report)

    def generate_json_report(self, price_info: Dict, technical_indicators: Dict,
                            technical_signals: Dict, sentiment_result: Dict,
                            signal_info: Dict, risk_metrics: Dict,
                            key_points: list) -> Dict:
        """生成 JSON 格式报告"""
        return {
            "metadata": {
                "symbol": self.symbol,
                "company_name": self.company_info.get('name', 'N/A'),
                "analysis_time": datetime.now().isoformat()
            },
            "price": price_info,
            "sentiment_analysis": sentiment_result, # 这里面现在包含 summary 了
            "trading_signal": signal_info,
            "risk_management": risk_metrics
        }
    
    def save_json_report(self, report_data: Dict, filename: str = None):
        """保存 JSON 报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/{self.symbol}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"\n[报告] JSON 报告已保存至: {filename}")
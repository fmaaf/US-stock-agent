"""
情绪分析模块 - 分析新闻情绪
(已修复：添加 SENTIMENT_CONFIG 导入)
"""

from datetime import datetime
from typing import List, Dict
import re
from config import SENTIMENT_CONFIG  

class SentimentAnalyzer:
    """情绪分析类"""
    
    def __init__(self):
        """初始化情绪分析器"""
        self.finbert_tokenizer = None
        self.finbert_model = None
        self.finbert_initialized = False 
        
        # 关键词词典
        self.positive_keywords = [
            'surge', 'soar', 'rally', 'gain', 'rise', 'jump', 'climb', 'advance',
            'profit', 'growth', 'strong', 'beat', 'exceed', 'outperform', 'bullish',
            'upgrade', 'positive', 'optimistic', 'success', 'breakthrough', 'innovation',
            'record', 'high', 'boost', 'momentum', 'recovery', 'expansion', 'acquisition',
            'deal', 'partnership', 'launch'
        ]
        
        self.negative_keywords = [
            'fall', 'drop', 'decline', 'plunge', 'tumble', 'crash', 'slump', 'sink',
            'loss', 'weak', 'miss', 'disappoint', 'underperform', 'bearish',
            'downgrade', 'negative', 'pessimistic', 'concern', 'risk', 'warning',
            'cut', 'reduce', 'layoff', 'lawsuit', 'investigation', 'scandal',
            'debt', 'default', 'bankruptcy', 'recession', 'slowdown', 'challenge'
        ]
    
    def load_finbert(self):
        """加载 FinBERT 模型"""
        if self.finbert_initialized:
            return True 
            
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            
            print("[模型] 尝试加载 FinBERT 模型...")
            model_name = "ProsusAI/finbert"
            self.finbert_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.finbert_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.finbert_model.eval()
            self.finbert_initialized = True
            print("[模型] FinBERT 模型加载成功")
            return True
        except ImportError:
            print("[警告] transformers 或 torch 库未安装，FinBERT 加载失败，将使用关键词方法。")
            return False
        except Exception as e:
            print(f"[警告] 加载 FinBERT 模型失败: {str(e)}，将使用关键词方法。")
            return False
    
    def analyze_with_finbert(self, text: str) -> Dict[str, float]:
        """使用 FinBERT 分析文本情绪"""
        if not self.finbert_initialized:
            return self.analyze_with_keywords(text)

        try:
            import torch
            inputs = self.finbert_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self.finbert_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            scores = predictions[0].tolist()
            return {
                "positive": scores[0],
                "negative": scores[1],
                "neutral": scores[2]
            }
        except Exception as e:
            print(f"[警告] FinBERT 分析失败: {str(e)}，回退到关键词方法。")
            return self.analyze_with_keywords(text)
    
    def analyze_with_keywords(self, text: str) -> Dict[str, float]:
        """使用关键词方法分析文本情绪"""
        text_lower = text.lower()
        
        positive_matches = sum(1 for keyword in self.positive_keywords if re.search(r'\b' + keyword + r'\b', text_lower))
        negative_matches = sum(1 for keyword in self.negative_keywords if re.search(r'\b' + keyword + r'\b', text_lower))
        
        total_matches = positive_matches + negative_matches
        
        if total_matches == 0:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
        
        positive_score = positive_matches / total_matches
        negative_score = negative_matches / total_matches
        neutral_score = 1.0 - positive_score - negative_score
        
        return {
            "positive": positive_score,
            "negative": negative_score,
            "neutral": max(0.0, neutral_score)
        }
    
    def analyze_news(self, news_list: List[dict], use_finbert: bool = False) -> Dict:
        """
        分析新闻列表的整体情绪
        
        Args:
            news_list: 新闻列表 (包含 headline, summary, datetime, url 等)
            use_finbert: 是否使用 FinBERT 模型
            
        Returns:
            dict: 情绪分析结果 (包含 news_list 详情用于打印)
        """
        # 1. 边界检查：如果没有新闻，直接返回默认空结构
        if not news_list:
            return {
                "total_news": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "sentiment_score": 0,
                "sentiment_label": "neutral",
                "news_list": []
            }
        
        # 2. 模型加载：如果指定使用 FinBERT 且未初始化，尝试加载
        if use_finbert and not self.finbert_initialized:
            self.load_finbert()
        
        # 3. 初始化计数器
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        analyzed_news_details = []
        
        # 4. 获取处理数量限制 (默认 20 条，防止 API 超时)
        limit = SENTIMENT_CONFIG.get('news_processing_limit', 20)
        
        # 5. 遍历新闻进行分析
        for news in news_list[:limit]: 
            headline = news.get('headline', '')
            summary = news.get('summary', '')
            
            # 拼接标题和摘要进行分析，内容更丰富
            text_to_analyze = f"{headline}. {summary}"
            
            if not text_to_analyze.strip():
                continue
            
            # 执行分析 (FinBERT 或 关键词)
            if use_finbert and self.finbert_initialized:
                sentiment = self.analyze_with_finbert(text_to_analyze)
            else:
                sentiment = self.analyze_with_keywords(text_to_analyze)
            
            # 确定情绪标签 (取最大概率)
            max_score = max(sentiment['positive'], sentiment['negative'], sentiment['neutral'])
            
            # 使用 0.5 作为阈值，让判断更严格
            if sentiment['positive'] == max_score and sentiment['positive'] > 0.5:
                label = 'positive'
                positive_count += 1
            elif sentiment['negative'] == max_score and sentiment['negative'] > 0.5:
                label = 'negative'
                negative_count += 1
            else:
                label = 'neutral'
                neutral_count += 1
            
            # === 关键点：将分析结果存入列表 ===
            analyzed_news_details.append({
                "headline": headline,
                "summary": summary,  # <--- 保留摘要，供 ReportGenerator 打印
                "datetime": datetime.fromtimestamp(news.get('datetime', 0)).strftime("%Y-%m-%d %H:%M"),
                "sentiment": label,
                "url": news.get('url', '')
            })
        
        # 6. 计算综合得分
        total_analyzed = len(analyzed_news_details)
        
        if total_analyzed == 0:
            sentiment_score = 0
        else:
            # 计算加权分 (-100 到 +100)
            sentiment_score = ((positive_count * 1.0 - negative_count * 1.0) / total_analyzed) * 100
        
        # 7. 确定整体情绪标签
        if sentiment_score > 25:
            sentiment_label = "positive"
        elif sentiment_score < -25:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        # 8. 返回完整结果
        return {
            "total_news": total_analyzed,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "news_list": analyzed_news_details  # 列表包含完整详情
        }
    
    # 这个方法在 report_generator.py 中已被替换，可以删除或保留但不再被 report_generator 调用
    def get_sentiment_description(self, score: float) -> str:
        """
        获取情绪描述
        """
        if score > 60:
            return "非常乐观"
        elif score > 20:
            return "偏乐观"
        elif score > -20:
            return "中性"
        elif score > -60:
            return "偏悲观"
        else:
            return "非常悲观"
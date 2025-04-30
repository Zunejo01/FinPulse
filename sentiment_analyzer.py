"""
FinPulse - Financial News Sentiment Analyzer
This module provides sentiment analysis functionality for financial news text,
with special handling for financial terminology and enhanced scoring for financial context.
"""

import re
import logging
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

FINANCIAL_TERMS = {
    # Positive terms
    'growth': 2.0,
    'profit': 2.0,
    'earnings': 1.5,
    'dividend': 1.7,
    'exceeded': 1.8,
    'beat': 1.8,
    'upgrade': 2.0,
    'outperform': 1.9,
    'bull': 1.5,
    'bullish': 1.8,
    'rally': 1.6,
    'gain': 1.5,
    'rise': 1.0,
    'boost': 1.5,
    'surge': 1.8,
    'upside': 1.7,
    'strong': 1.5,
    'robust': 1.6,
    
    # Negative terms
    'loss': -2.0,
    'losses': -2.0,
    'debt': -1.5,
    'decline': -1.5,
    'downgrade': -2.0,
    'underperform': -1.9,
    'bear': -1.5,
    'bearish': -1.8,
    'sell-off': -1.7,
    'drop': -1.5,
    'fall': -1.0,
    'plunge': -2.0,
    'crash': -2.5,
    'miss': -1.8,
    'bankruptcy': -2.5,
    'recession': -2.0,
    'inflation': -1.5,
    'disappointing': -1.8,
    'warning': -1.7,
    'risk': -1.5,
    'weakness': -1.7,
    'volatile': -1.3,
    'layoffs': -2.0,
    'lawsuit': -1.8
}


class SentimentAnalyzer:
    
    def __init__(self):
        self.ensure_nltk_resources()
        self.sid = SentimentIntensityAnalyzer()
        
        for term, score in FINANCIAL_TERMS.items():
            self.sid.lexicon[term] = score
    
    @staticmethod
    def ensure_nltk_resources():
        try:
            word_tokenize("Test sentence.")
        except LookupError:
            logger.info("Downloading NLTK resources...")
            nltk.download('punkt')
            nltk.download('vader_lexicon')
            nltk.download('stopwords')
            try:
                nltk.download('punkt_tab')
            except:
                pass
            logger.info("NLTK resources downloaded successfully.")
    
    @staticmethod
    def preprocess_text(text):
        if not text:
            return ""
            
        text = text.lower()
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        text = re.sub(r'[^\w\s$%.]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_keywords(self, text, max_keywords=10):
        if not text:
            return []
    
        tokens = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [w for w in tokens if w.lower() not in stop_words and len(w) > 2]
        
        word_freq = {}
        for token in filtered_tokens:
            word_freq[token] = word_freq.get(token, 0) + 1
            
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        
        return keywords
    
    def analyze_text(self, text):
        clean_text = self.preprocess_text(text)
        
        if not clean_text:
            return {
                'score': 0.0,
                'label': 'neutral',
                'breakdown': {
                    'positive': 0.0,
                    'negative': 0.0,
                    'neutral': 1.0
                },
                'keywords': []
            }
        
        scores = self.sid.polarity_scores(clean_text)
        
        if scores['compound'] >= 0.05:
            label = 'positive'
        elif scores['compound'] <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        
        keywords = self.extract_keywords(clean_text)
        return {
            'score': scores['compound'],
            'label': label,
            'breakdown': {
                'positive': scores['pos'],
                'negative': scores['neg'],
                'neutral': scores['neu']
            },
            'keywords': keywords
        }
    
    def analyze_news_item(self, news_item):
        headline = news_item.get('headline', '')
        summary = news_item.get('summary', '')
        text = f"{headline}. {summary}"
        sentiment = self.analyze_text(text)
        return {
            **news_item,
            'sentiment': sentiment
        }
    
    def analyze_news_batch(self, news_items):
        return [self.analyze_news_item(item) for item in news_items]
    
    def get_sentiment_summary(self, news_items):
        if not news_items:
            return {
                'count': 0,
                'avg_score': 0.0,
                'sentiment_distribution': {
                    'positive': 0.0,
                    'negative': 0.0,
                    'neutral': 0.0
                }
            }
        
        positive = sum(1 for item in news_items if item.get('sentiment', {}).get('label') == 'positive')
        negative = sum(1 for item in news_items if item.get('sentiment', {}).get('label') == 'negative')
        neutral = sum(1 for item in news_items if item.get('sentiment', {}).get('label') == 'neutral')
        
        total = len(news_items)

        pos_pct = (positive / total) * 100 if total else 0
        neg_pct = (negative / total) * 100 if total else 0
        neu_pct = (neutral / total) * 100 if total else 0
    
        avg_score = sum(item.get('sentiment', {}).get('score', 0) for item in news_items) / total if total else 0
        
        return {
            'count': total,
            'avg_score': avg_score,
            'sentiment_distribution': {
                'positive': {
                    'count': positive,
                    'percentage': pos_pct
                },
                'negative': {
                    'count': negative,
                    'percentage': neg_pct
                },
                'neutral': {
                    'count': neutral,
                    'percentage': neu_pct
                }
            }
        } 
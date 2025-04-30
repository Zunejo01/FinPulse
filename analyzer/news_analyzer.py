import re
import nltk
import logging
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

def ensure_nltk_resources():
    try:
        word_tokenize("Test sentence.")
    except LookupError:
        logger.info("Downloading NLTK resources...")
        nltk.download('punkt')
        nltk.download('vader_lexicon')
        nltk.download('stopwords')

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
    'disappointing': -1.8
}

def preprocess_text(text):
    """Clean and normalize text for sentiment analysis"""
    if not text:
        return ""
        
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'[^\w\s$%.]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_keywords(text, top_n=10):
    if not text:
        return []
    words = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.lower() not in stop_words and len(word) > 1]
    word_counts = {}
    for word in words:
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1

    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:top_n]]

def analyze_sentiment(news_item):
    sid = SentimentIntensityAnalyzer()
    for term, score in FINANCIAL_TERMS.items():
        sid.lexicon[term] = score

    text = preprocess_text(news_item.get('text', ''))
    
    if not text:
        headline = news_item.get('headline', '')
        summary = news_item.get('summary', '')
        text = preprocess_text(f"{headline}. {summary}")
    
    if not text:
        return {**news_item, 'sentiment': 'neutral', 'sentiment_score': 0.0, 'keywords': []}
    
    sentiment_scores = sid.polarity_scores(text)
    compound_score = sentiment_scores['compound']
    
    if compound_score >= 0.05:
        sentiment = 'positive'
    elif compound_score <= -0.05:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    keywords = extract_keywords(text)

    return {
        **news_item,
        'sentiment': sentiment,
        'sentiment_score': compound_score,
        'sentiment_breakdown': {
            'positive': sentiment_scores['pos'],
            'negative': sentiment_scores['neg'],
            'neutral': sentiment_scores['neu']
        },
        'keywords': keywords
    } 
import os
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def format_finnhub_date(date_obj=None):
    
    if date_obj is None:
        date_obj = datetime.now()
    return date_obj.strftime('%Y-%m-%d')

def calculate_date_range(days=7):
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return format_finnhub_date(start_date), format_finnhub_date(end_date)

def parse_finnhub_timestamp(timestamp):
   
    if not timestamp:
        return None
    
    try:
       
        return datetime.fromtimestamp(int(timestamp))
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing timestamp {timestamp}: {e}")
        return None

def format_news_data(news_items):
   
    if not news_items:
        return []
    
    formatted_news = []
    for item in news_items:
        if not item.get('headline') and not item.get('summary'):
            continue
        timestamp = item.get('datetime')
        if timestamp:
            item['formatted_date'] = parse_finnhub_timestamp(timestamp)
    
        headline = item.get('headline', '')
        summary = item.get('summary', '')
        item['text'] = f"{headline}. {summary}"
        
        formatted_news.append(item)
    
    return formatted_news

def filter_news_by_keywords(news_items, keywords):
    if not news_items or not keywords:
        return news_items
    
    filtered_news = []
    for item in news_items:
        text = item.get('text', '').lower()
        if not text:
            headline = item.get('headline', '').lower()
            summary = item.get('summary', '').lower()
            text = f"{headline}. {summary}"
        if any(keyword.lower() in text for keyword in keywords):
            filtered_news.append(item)
    
    return filtered_news

def group_news_by_symbol(news_items):
    if not news_items:
        return {}
    
    grouped_news = {}
    for item in news_items:
        related = item.get('related')
        if not related:
            continue
        symbols = [symbol.strip() for symbol in related.split(',')]
        
        for symbol in symbols:
            if symbol not in grouped_news:
                grouped_news[symbol] = []
            grouped_news[symbol].append(item)
    
    return grouped_news

def save_news_to_json(news_items, filename):
    if not news_items:
        logger.warning("No news items to save")
        return False
    
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        serializable_news = []
        for item in news_items:
            serializable_item = item.copy()
            if 'formatted_date' in serializable_item and isinstance(serializable_item['formatted_date'], datetime):
                serializable_item['formatted_date'] = serializable_item['formatted_date'].isoformat()
            serializable_news.append(serializable_item)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'count': len(serializable_news),
                'timestamp': datetime.now().isoformat(),
                'news': serializable_news
            }, f, indent=2)
        
        logger.info(f"Saved {len(news_items)} news items to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving news to {filename}: {e}")
        return False

def load_news_from_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data.get('news', []):
            if 'formatted_date' in item and isinstance(item['formatted_date'], str):
                try:
                    item['formatted_date'] = datetime.fromisoformat(item['formatted_date'])
                except ValueError:
                    pass
        
        logger.info(f"Loaded {len(data.get('news', []))} news items from {filename}")
        return data.get('news', [])
    except Exception as e:
        logger.error(f"Error loading news from {filename}: {e}")
        return [] 
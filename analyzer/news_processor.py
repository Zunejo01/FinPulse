"""Financial News Processor Module
This module handles the processing of financial news articles before sentiment analysis,
extracting key metrics and structured data.
"""

import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def extract_symbols(text):
    if not text:
        return []
        
    symbol_pattern = r'\$?([A-Z]{1,5})(?=\s|$|\.|,|\)|\(|\:|\;|\"|\')'
    matches = re.findall(symbol_pattern, text)
    common_words = {'A', 'I', 'FOR', 'AT', 'BE', 'CEO', 'CFO', 'CTO', 'THE', 'AND', 'OR', 'ON', 'IN', 'BY', 'IT', 'IS', 'TO', 'OF'}
    symbols = [match for match in matches if match not in common_words]
    
    return list(set(symbols))  # Remove duplicates

def extract_company_names(text, company_database=None):
    if not text or not company_database:
        return []
        
    companies = []
    for company, symbols in company_database.items():
        if company.lower() in text.lower():
            companies.append(company)
    
    return companies

def extract_metrics(text):
    if not text:
        return {}
        
    metrics = {}
    price_pattern = r'\$(\d+(?:\.\d{1,2})?)'
    price_matches = re.findall(price_pattern, text)
    if price_matches:
        metrics['prices'] = [float(price) for price in price_matches]
    
    percentage_pattern = r'(\d+(?:\.\d{1,2})?)%'
    percentage_matches = re.findall(percentage_pattern, text)
    if percentage_matches:
        metrics['percentages'] = [float(pct) for pct in percentage_matches]
    
    million_pattern = r'(\d+(?:\.\d{1,2})?)(?:\s+)(?:million|m\b)'
    million_matches = re.findall(million_pattern, text.lower())
    
    billion_pattern = r'(\d+(?:\.\d{1,2})?)(?:\s+)(?:billion|b\b)'
    billion_matches = re.findall(billion_pattern, text.lower())
    
    large_numbers = {}
    if million_matches:
        large_numbers['millions'] = [float(num) for num in million_matches]
    if billion_matches:
        large_numbers['billions'] = [float(num) for num in billion_matches]
    
    if large_numbers:
        metrics['large_numbers'] = large_numbers
    
    return metrics

def categorize_news(headline, content=None):
    text = (headline + " " + (content or "")).lower()
    categories = {
        'earnings': ['earnings', 'revenue', 'profit', 'quarter', 'quarterly', 'eps', 'beat', 'miss'],
        'merger_acquisition': ['merger', 'acquisition', 'acquire', 'takeover', 'bid', 'buyout', 'deal'],
        'product_launch': ['launch', 'unveil', 'announce', 'release', 'new product', 'new service'],
        'leadership': ['ceo', 'cfo', 'executive', 'board', 'appoint', 'resign', 'leadership'],
        'regulatory': ['sec', 'regulation', 'lawsuit', 'legal', 'compliance', 'investigation', 'fine'],
        'market_outlook': ['outlook', 'forecast', 'guidance', 'predict', 'expect', 'projection'],
        'economic_indicator': ['inflation', 'unemployment', 'gdp', 'growth', 'recession', 'fed', 'rate']
    }
    
    matches = {}
    for category, keywords in categories.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            matches[category] = score
    
    if matches:
        sorted_categories = sorted(matches.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, score in sorted_categories]
    
    return ['general']  # Default category

def process_news_article(article):
    if not article:
        return article
    
    headline = article.get('headline', '')
    summary = article.get('summary', '')
    content = headline + ". " + summary
    
    processed_article = article.copy()
    processed_article['extracted_data'] = {
        'symbols': extract_symbols(content),
        'metrics': extract_metrics(content),
        'categories': categorize_news(headline, summary)
    }
    if 'datetime' in article:
        try:
            timestamp = article['datetime']
            processed_article['formatted_date'] = datetime.fromtimestamp(timestamp).isoformat()
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to format datetime: {e}")
    
    return processed_article

def batch_process_news(articles):
    return [process_news_article(article) for article in articles] 
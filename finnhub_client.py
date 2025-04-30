"""FinPulse - Finnhub API Client
This module provides a client for the Finnhub API to fetch financial news and stock data.
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Optional, Union, Any

from utils.finnhub_utils import (
    format_finnhub_date,
    calculate_date_range,
    format_news_data
)
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinnhubClient:
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("Finnhub API key not provided. Set FINNHUB_API_KEY environment variable.")
        
        self.base_url = "https://finnhub.io/api/v1"
        self.session = requests.Session()
        self.rate_limit_remaining = 60  
        self.rate_limit_reset = time.time() + 60
    
    def _handle_rate_limiting(self):
        current_time = time.time()
        
        if current_time > self.rate_limit_reset:
            self.rate_limit_remaining = 60
            self.rate_limit_reset = current_time + 60
        
        if self.rate_limit_remaining <= 0:
            sleep_time = self.rate_limit_reset - current_time
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                self.rate_limit_remaining = 60
                self.rate_limit_reset = time.time() + 60
    
    def _make_request(self, endpoint, params=None):
        self._handle_rate_limiting()
        url = f"{self.base_url}/{endpoint}"
        headers = {"X-Finnhub-Token": self.api_key}
        try:
            response = self.session.get(url, headers=headers, params=params)
            self.rate_limit_remaining -= 1
            if 'X-Ratelimit-Remaining' in response.headers:
                self.rate_limit_remaining = int(response.headers['X-Ratelimit-Remaining'])
            if 'X-Ratelimit-Reset' in response.headers:
                self.rate_limit_reset = int(response.headers['X-Ratelimit-Reset'])
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.warning("Rate limit exceeded. Retrying after reset.")
                time.sleep(max(0, self.rate_limit_reset - time.time()))
                return self._make_request(endpoint, params)
            else:
                logger.error(f"HTTP error: {str(e)}")
                return {"error": str(e)}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {"error": str(e)}
    
    def get_company_news(self, symbol, from_date=None, to_date=None):
        if not from_date:
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Fetching news for {symbol} from {from_date} to {to_date}")
        
        params = {
            'symbol': symbol,
            'from': from_date,
            'to': to_date
        }
        
        return self._make_request('company-news', params)
    
    def get_market_news(self, category='general'):
        logger.info(f"Fetching market news for category: {category}")
        
        params = {
            'category': category
        }
        
        return self._make_request('news', params)
    
    def get_company_profile(self, symbol):
        logger.info(f"Fetching company profile for {symbol}")
        
        params = {
            'symbol': symbol
        }
        
        return self._make_request('stock/profile2', params)
    
    def get_stock_quote(self, symbol):
        logger.info(f"Fetching stock quote for {symbol}")
        
        params = {
            'symbol': symbol
        }
        
        return self._make_request('quote', params)
    
    def search_symbol(self, query):
        logger.info(f"Searching for symbol: {query}")
        
        params = {
            'q': query
        }
        
        return self._make_request('search', params)
    
    def get_earnings(self, symbol):
        logger.info(f"Fetching earnings data for {symbol}")
        
        params = {
            'symbol': symbol
        }
        
        return self._make_request('stock/earnings', params)
    
    def format_news_data(self, news_items):
        if not news_items or not isinstance(news_items, list):
            return []
        
        formatted_news = []
        
        for item in news_items:
            if not isinstance(item, dict):
                continue
                
            timestamp = item.get('datetime', 0)
            date_str = ""
            try:
                if timestamp:
                    date_obj = datetime.fromtimestamp(int(timestamp))
                    date_str = date_obj.strftime('%Y-%m-%d')
            except (ValueError, TypeError, OSError) as e:
                logger.warning(f"Error formatting date from timestamp {timestamp}: {e}")
                date_str = "Unknown date"
                
            formatted_item = {
                'headline': item.get('headline', 'No headline'),
                'summary': item.get('summary', ''),
                'url': item.get('url', ''),
                'source': item.get('source', 'Unknown'),
                'datetime': timestamp,
                'date': date_str,
                'related': item.get('related', ''),
                'image': item.get('image', ''),
                'category': item.get('category', 'general'),
                'id': item.get('id', '')
            }
            
            formatted_news.append(formatted_item)
        
        return formatted_news
    
    def save_news_data(self, news_items, filename):
        try:
            os.makedirs('data', exist_ok=True)
            filepath = os.path.join('data', filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(news_items, f, indent=2)
                
            logger.info(f"Saved {len(news_items)} news items to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving news data: {str(e)}")


if __name__ == "__main__":
    client = FinnhubClient()
    
    aapl_news = client.get_company_news('AAPL')
    formatted_news = client.format_news_data(aapl_news)
    
    client.save_news_data(formatted_news, 'aapl_news.json')
    
    profile = client.get_company_profile('AAPL')
    print(json.dumps(profile, indent=2))

    quote = client.get_stock_quote('AAPL')
    print(json.dumps(quote, indent=2))

    general_news = client.get_market_news()
    formatted_general_news = client.format_news_data(general_news)
    
    client.save_news_data(formatted_general_news, 'general_market_news.json')

    search_results = client.search_symbol('AAPL')
    print(json.dumps(search_results, indent=2))

    earnings = client.get_earnings('AAPL')
    print(json.dumps(earnings, indent=2)) 
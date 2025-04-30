import requests
import finnhub
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FinnhubService:
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = finnhub.Client(api_key=api_key)
        self.base_url = "https://finnhub.io/api/v1"
        self.request_limit = 60  
        self.requests_made = 0
        self.rate_limit_reset_time = time.time() + 60
    
    def _handle_rate_limiting(self):
        current_time = time.time()
        
        if current_time > self.rate_limit_reset_time:
            self.requests_made = 0
            self.rate_limit_reset_time = current_time + 60
        
        if self.requests_made >= self.request_limit:
            sleep_time = self.rate_limit_reset_time - current_time
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.requests_made = 0
                self.rate_limit_reset_time = time.time() + 60
        
        self.requests_made += 1
    
    def search_symbols(self, query):
        self._handle_rate_limiting()
        try:
            response = self.client.symbol_lookup(query)
            results = []
            if 'result' in response:
                results = [
                    {
                        'symbol': item.get('symbol', ''),
                        'description': item.get('description', ''),
                        'type': item.get('type', ''),
                        'primary_exchange': item.get('exchange', '')
                    }
                    for item in response['result']
                ]
            
            return results
        except Exception as e:
            logger.error(f"Error searching symbols: {str(e)}")
            return []
    
    def get_quote(self, symbol):
        self._handle_rate_limiting()
        try:
            quote = self.client.quote(symbol)
            quote['timestamp'] = int(time.time())
            quote['retrieved_at'] = datetime.now().isoformat()
            
            return quote
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {str(e)}")
            return None
    
    def get_company_profile(self, symbol):
        self._handle_rate_limiting()
        try:
            profile = self.client.company_profile2(symbol=symbol)
            return profile
        except Exception as e:
            logger.error(f"Error getting company profile for {symbol}: {str(e)}")
            return None
    
    def get_stock_candles(self, symbol, resolution, from_time, to_time):
        self._handle_rate_limiting()
        try:
            if isinstance(from_time, str):
                from_time = int(from_time)
            if isinstance(to_time, str):
                to_time = int(to_time)
                
            candles = self.client.stock_candles(symbol, resolution, from_time, to_time)

            if candles.get('s') == 'no_data':
                return {'s': 'no_data', 'error': 'No data available for the requested period'}
            
            formatted_candles = {
                'symbol': symbol,
                'resolution': resolution,
                'from': from_time,
                'to': to_time,
                'status': candles.get('s', ''),
                'candles': []
            }
            
            timestamps = candles.get('t', [])
            opens = candles.get('o', [])
            highs = candles.get('h', [])
            lows = candles.get('l', [])
            closes = candles.get('c', [])
            volumes = candles.get('v', [])
            
            for i in range(len(timestamps)):
                if i < len(opens) and i < len(highs) and i < len(lows) and i < len(closes) and i < len(volumes):
                    formatted_candles['candles'].append({
                        'timestamp': timestamps[i],
                        'datetime': datetime.fromtimestamp(timestamps[i]).isoformat(),
                        'open': opens[i],
                        'high': highs[i],
                        'low': lows[i],
                        'close': closes[i],
                        'volume': volumes[i]
                    })
            
            return formatted_candles
        except Exception as e:
            logger.error(f"Error getting candles for {symbol}: {str(e)}")
            return {'s': 'error', 'error': str(e)}
    
    def get_market_news(self, category, min_id=None, start_date=None, end_date=None):
        self._handle_rate_limiting()
        try:
            params = {'category': category}
            if start_date and end_date:
                try:
            
                    url = f"{self.base_url}/news"
                    headers = {'X-Finnhub-Token': self.api_key}
                    params.update({
                        'from': start_date,
                        'to': end_date
                    })
                    
                    response = requests.get(url, headers=headers, params=params)
                    if response.status_code == 200:
                        news = response.json()
                    else:
                        logger.error(f"Error getting news: {response.status_code} - {response.text}")
                        news = []
                except Exception as e:
                    logger.error(f"Error with date-based news request: {str(e)}")
                    news = self.client.general_news(category, min_id=min_id)
            else:
                news = self.client.general_news(category, min_id=min_id)
            formatted_news = []
            for article in news:
                formatted_news.append({
                    'id': article.get('id', ''),
                    'category': article.get('category', ''),
                    'datetime': article.get('datetime', 0),
                    'headline': article.get('headline', ''),
                    'image': article.get('image', ''),
                    'source': article.get('source', ''),
                    'summary': article.get('summary', ''),
                    'url': article.get('url', ''),
                    'related': article.get('related', '')
                })
            
            return formatted_news
        except Exception as e:
            logger.error(f"Error getting market news: {str(e)}")
            return []
    
    def get_company_news(self, symbol, start_date, end_date):
        self._handle_rate_limiting()
        try:
            news = self.client.company_news(symbol, _from=start_date, to=end_date)
            formatted_news = []
            for article in news:
                formatted_news.append({
                    'id': article.get('id', ''),
                    'category': article.get('category', ''),
                    'datetime': article.get('datetime', 0),
                    'headline': article.get('headline', ''),
                    'image': article.get('image', ''),
                    'source': article.get('source', ''),
                    'summary': article.get('summary', ''),
                    'url': article.get('url', ''),
                    'related': article.get('related', '')
                })
            
            return formatted_news
        except Exception as e:
            logger.error(f"Error getting company news for {symbol}: {str(e)}")
            return []
    
    def get_news_sentiment(self, symbol, start_date=None, end_date=None):
        try:
            news = self.get_company_news(symbol, start_date, end_date)
            self._handle_rate_limiting()
            finnhub_sentiment = None
            try:
                finnhub_sentiment = self.client.news_sentiment(symbol)
            except Exception as e:
                logger.warning(f"Could not get Finnhub sentiment for {symbol}: {str(e)}")
            article_count = len(news)
            sources = {}
            date_distribution = {}
            
            for article in news:
                source = article.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
                
                date = datetime.fromtimestamp(article.get('datetime', 0)).strftime('%Y-%m-%d')
                date_distribution[date] = date_distribution.get(date, 0) + 1
        
            sentiment_data = {
                'article_count': article_count,
                'source_distribution': sources,
                'date_distribution': date_distribution,
                'finnhub_sentiment': finnhub_sentiment,
                'period': {
                    'start': start_date,
                    'end': end_date
                }
            }
            
            return sentiment_data
        except Exception as e:
            logger.error(f"Error analyzing news sentiment for {symbol}: {str(e)}")
            return {
                'error': str(e),
                'article_count': 0
            } 
"""FinPulse - Financial News Sentiment Analyzer
Main application file that initializes the Finnhub client, processes financial news,
and analyzes sentiment.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import argparse

from finnhub_client import FinnhubClient
from utils.finnhub_utils import (
    format_finnhub_date,
    save_news_to_json,
    load_news_from_json,
    filter_news_by_keywords,
    group_news_by_symbol
)
from sentiment_analyzer import SentimentAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("finpulse.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FinPulseApp:
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "cache"):
        self.api_key = api_key or os.environ.get("FINNHUB_API_KEY")
        self.cache_dir = cache_dir
    
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        self.client = FinnhubClient(self.api_key)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.tracked_symbols = self._load_tracked_symbols()
        
        logger.info("FinPulse application initialized")
    
    def _load_tracked_symbols(self) -> List[str]:
        symbols_file = os.path.join(self.cache_dir, "tracked_symbols.json")
        
        try:
            if os.path.exists(symbols_file):
                with open(symbols_file, 'r') as f:
                    return json.load(f)
            else:
                default_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
                self._save_tracked_symbols(default_symbols)
                return default_symbols
        except Exception as e:
            logger.error(f"Error loading tracked symbols: {e}")
            return ["AAPL", "MSFT", "GOOGL"]
    
    def _save_tracked_symbols(self, symbols: List[str]) -> None:
        symbols_file = os.path.join(self.cache_dir, "tracked_symbols.json")
        
        try:
            with open(symbols_file, 'w') as f:
                json.dump(symbols, f)
        except Exception as e:
            logger.error(f"Error saving tracked symbols: {e}")
    
    def add_tracked_symbol(self, symbol: str) -> bool:
        symbol = symbol.upper()
        if symbol not in self.tracked_symbols:
            self.tracked_symbols.append(symbol)
            self._save_tracked_symbols(self.tracked_symbols)
            logger.info(f"Added {symbol} to tracked symbols")
            return True
        return False
    
    def remove_tracked_symbol(self, symbol: str) -> bool:
        symbol = symbol.upper()
        if symbol in self.tracked_symbols:
            self.tracked_symbols.remove(symbol)
            self._save_tracked_symbols(self.tracked_symbols)
            logger.info(f"Removed {symbol} from tracked symbols")
            return True
        return False
    
    def get_company_news_with_sentiment(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 50,
        use_cache: bool = True
    ) -> List[Dict]:
        cache_file = os.path.join(self.cache_dir, f"{symbol}_news.json")
        
        if use_cache and os.path.exists(cache_file):
            logger.info(f"Loading cached news for {symbol}")
            news_items = load_news_from_json(cache_file)
        else:
            logger.info(f"Fetching fresh news for {symbol}")
            news_items = self.client.get_company_news(symbol, from_date, to_date)
        
            if news_items:
                news_items = self.client.format_news_data(news_items)
                news_items = news_items[:limit]  # Apply limit after getting the news
                save_news_to_json(news_items, cache_file)
        
        if news_items:
            logger.info(f"Analyzing sentiment for {len(news_items)} news items")
            return self._add_sentiment_to_news(news_items)
        
        return []
    
    def get_market_news_with_sentiment(
        self,
        category: str = "general",
        limit: int = 50,
        use_cache: bool = True
    ) -> List[Dict]:
        cache_file = os.path.join(self.cache_dir, f"market_news_{category}.json")
        
        if use_cache and os.path.exists(cache_file):
            logger.info(f"Loading cached market news for {category}")
            news_items = load_news_from_json(cache_file)
        else:
            logger.info(f"Fetching fresh market news for {category}")
            news_items = self.client.get_market_news(category)
            
            if news_items:
                news_items = self.client.format_news_data(news_items)
                news_items = news_items[:limit]  # Apply limit after getting the news
                save_news_to_json(news_items, cache_file)
        
        if news_items:
            logger.info(f"Analyzing sentiment for {len(news_items)} market news items")
            return self._add_sentiment_to_news(news_items)
        
        return []
    
    def get_all_tracked_symbols_news(
        self,
        days: int = 7,
        limit_per_symbol: int = 20,
        use_cache: bool = True
    ) -> Dict[str, List[Dict]]:
        result = {}
        
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        for symbol in self.tracked_symbols:
            news = self.get_company_news_with_sentiment(
                symbol, 
                from_date=from_date,
                to_date=to_date,
                limit=limit_per_symbol,
                use_cache=use_cache
            )
            
            if news:
                result[symbol] = news
        
        return result
    
    def _add_sentiment_to_news(self, news_items: List[Dict]) -> List[Dict]:
        for item in news_items:
            # Combine headline and summary for better sentiment analysis
            text = f"{item.get('headline', '')} {item.get('summary', '')}"
            
            # Get sentiment score
            sentiment = self.sentiment_analyzer.analyze_text(text)
            
            # Add sentiment to news item
            item['sentiment'] = sentiment
        
        return news_items
    
    def get_sentiment_summary(self, identifier: str, news_items: List[Dict]) -> Dict:
        if not news_items:
            return {
                "identifier": identifier,
                "count": 0,
                "avg_score": 0.0,
                "sentiment_distribution": {
                    "positive": {"count": 0, "percentage": 0},
                    "negative": {"count": 0, "percentage": 0},
                    "neutral": {"count": 0, "percentage": 0}
                },
                "overall_sentiment": "neutral",
                "time_series": []
            }
        
        positive = sum(1 for item in news_items if item.get('sentiment', {}).get('label') == 'positive')
        negative = sum(1 for item in news_items if item.get('sentiment', {}).get('label') == 'negative')
        neutral = sum(1 for item in news_items if item.get('sentiment', {}).get('label') == 'neutral')
        
        total = len(news_items)
        pos_pct = (positive / total) * 100 if total else 0
        neg_pct = (negative / total) * 100 if total else 0
        neu_pct = (neutral / total) * 100 if total else 0
        
        avg_score = sum(item.get('sentiment', {}).get('score', 0) for item in news_items) / total if total else 0
        
        if avg_score >= 0.2:
            overall_sentiment = "positive"
        elif avg_score <= -0.2:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        date_sentiment = {}
        
        for item in news_items:
            date_str = None
            if 'formatted_date' in item and item['formatted_date']:
                if isinstance(item['formatted_date'], datetime):
                    date_str = item['formatted_date'].strftime('%Y-%m-%d')
                elif isinstance(item['formatted_date'], str):
                    try:
                        date_str = datetime.fromisoformat(item['formatted_date']).strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        if len(item['formatted_date']) >= 8:  
                            date_str = item['formatted_date']
            
            if not date_str and 'date' in item and item['date']:
                date_str = item['date']
            
            if not date_str and 'datetime' in item and item['datetime']:
                try:
                    if isinstance(item['datetime'], (int, float)):
                        date_obj = datetime.fromtimestamp(item['datetime'])
                        date_str = date_obj.strftime('%Y-%m-%d')
                except (ValueError, TypeError, OSError):
                    continue
            
            if date_str:
                if date_str not in date_sentiment:
                    date_sentiment[date_str] = {
                        'date': date_str,
                        'positive': 0,
                        'negative': 0,
                        'neutral': 0,
                        'avg_score': 0,
                        'count': 0
                    }
                
                sentiment_label = item.get('sentiment', {}).get('label', 'neutral')
                date_sentiment[date_str][sentiment_label] += 1
                date_sentiment[date_str]['count'] += 1
                date_sentiment[date_str]['avg_score'] += item.get('sentiment', {}).get('score', 0)
        
        for date_str in date_sentiment:
            if date_sentiment[date_str]['count'] > 0:
                date_sentiment[date_str]['avg_score'] /= date_sentiment[date_str]['count']
        
        time_series = sorted(date_sentiment.values(), key=lambda x: x['date'])
        
        return {
            "identifier": identifier,
            "count": total,
            "avg_score": avg_score,
            "sentiment_distribution": {
                "positive": {
                    "count": positive,
                    "percentage": pos_pct
                },
                "negative": {
                    "count": negative,
                    "percentage": neg_pct
                },
                "neutral": {
                    "count": neutral,
                    "percentage": neu_pct
                }
            },
            "overall_sentiment": overall_sentiment,
            "time_series": time_series
        }
    
    def get_symbol_sentiment_summary(self, symbol: str) -> Dict:
        news = self.get_company_news_with_sentiment(symbol)
        
        if not news:
            return {
                "symbol": symbol,
                "average_sentiment": 0,
                "sentiment_trend": "neutral",
                "news_count": 0
            }
        
        sentiment_scores = [item.get('sentiment', {}).get('score', 0) for item in news]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        if avg_sentiment > 0.2:
            trend = "positive"
        elif avg_sentiment < -0.2:
            trend = "negative"
        else:
            trend = "neutral"
        
        return {
            "symbol": symbol,
            "average_sentiment": round(avg_sentiment, 2),
            "sentiment_trend": trend,
            "news_count": len(news)
        }
    
    def get_all_tracked_symbols_sentiment(self) -> List[Dict]:
        return [self.get_symbol_sentiment_summary(symbol) for symbol in self.tracked_symbols]
    
    def run_dashboard(self):
       
        logger.info("Dashboard functionality not yet implemented")
        print("FinPulse Dashboard (console version)")
        print("=====================================")
        
        print(f"\nTracked Symbols: {', '.join(self.tracked_symbols)}")
    
        print("\nSymbol Sentiment:")
        for summary in self.get_all_tracked_symbols_sentiment():
            print(f"  {summary['symbol']}: {summary['sentiment_trend']} ({summary['average_sentiment']}) - {summary['news_count']} news items")
    
        print("\nRecent Market News:")
        market_news = self.get_market_news_with_sentiment(limit=5)
        for i, news in enumerate(market_news, 1):
            sentiment = news.get('sentiment', {})
            sentiment_label = sentiment.get('label', 'neutral')
            print(f"  {i}. {news['headline']} [{sentiment_label}]")
        
        print("\nUse command line arguments for more functionality.")

def main():
    parser = argparse.ArgumentParser(description="FinPulse - Financial News Sentiment Analyzer")
    
    parser.add_argument("--api-key", help="Finnhub API key (or set FINNHUB_API_KEY environment variable)")
    parser.add_argument("--symbol", help="Stock symbol to analyze")
    parser.add_argument("--add-symbol", help="Add symbol to tracked list")
    parser.add_argument("--remove-symbol", help="Remove symbol from tracked list")
    parser.add_argument("--list-symbols", action="store_true", help="List tracked symbols")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze")
    parser.add_argument("--no-cache", action="store_true", help="Don't use cached data")
    parser.add_argument("--limit", type=int, default=20, help="Limit number of news items per symbol")
    
    args = parser.parse_args()
    
    app = FinPulseApp(api_key=args.api_key)
    
    if args.add_symbol:
        app.add_tracked_symbol(args.add_symbol)
        print(f"Added {args.add_symbol} to tracked symbols")
    
    elif args.remove_symbol:
        app.remove_tracked_symbol(args.remove_symbol)
        print(f"Removed {args.remove_symbol} from tracked symbols")
    
    elif args.list_symbols:
        print(f"Tracked symbols: {', '.join(app.tracked_symbols)}")
    
    elif args.symbol:
        print(f"Analyzing news for {args.symbol}:")
        news = app.get_company_news_with_sentiment(
            args.symbol, 
            limit=args.limit,
            use_cache=not args.no_cache
        )
        
        summary = app.get_symbol_sentiment_summary(args.symbol)
        print(f"\nOverall sentiment: {summary['sentiment_trend']} ({summary['average_sentiment']})")
        
        print(f"\nTop news items ({len(news)}):")
        for i, item in enumerate(news[:10], 1):
            sentiment = item.get('sentiment', {})
            label = sentiment.get('label', 'neutral')
            score = sentiment.get('score', 0)
            print(f"{i}. [{label} {score:.2f}] {item['headline']}")
            print(f"   {item['summary'][:100]}..." if item.get('summary') else "   No summary available")
            print(f"   Source: {item.get('source', 'Unknown')} | Date: {item.get('date', 'Unknown')}")
            print()
    
    else:
        app.run_dashboard()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting FinPulse...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1) 
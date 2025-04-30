from flask import Flask, render_template, request, jsonify, send_file
import os
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import numpy as np
from PIL import Image

from finpulse_app import FinPulseApp
from sentiment_analyzer import SentimentAnalyzer
from finnhub_client import FinnhubClient

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

api_key = os.environ.get('FINNHUB_API_KEY')
if not api_key:
    logger.error("No Finnhub API key found. Set FINNHUB_API_KEY in your .env file.")
    raise ValueError("Finnhub API key is required")

finpulse = FinPulseApp(api_key=api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/company-news')
def company_news():
    symbol = request.args.get('symbol', '').upper()
    days = int(request.args.get('days', 7))
    limit = int(request.args.get('limit', 100))
    
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        news_with_sentiment = finpulse.get_company_news_with_sentiment(
            symbol=symbol,
            from_date=start_date.strftime('%Y-%m-%d'),
            to_date=end_date.strftime('%Y-%m-%d'),
            use_cache=True
        )
        
        news_with_sentiment = news_with_sentiment[:limit]
        
        sentiment_summary = finpulse.get_sentiment_summary(symbol, news_with_sentiment)
        
        response = {
            "symbol": symbol,
            "news_count": len(news_with_sentiment),
            "date_range": {
                "from": start_date.strftime('%Y-%m-%d'),
                "to": end_date.strftime('%Y-%m-%d')
            },
            "stats": sentiment_summary,
            "news": news_with_sentiment,
            "is_sample_data": False
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing request for {symbol}: {str(e)}")
        return jsonify({"error": f"Could not retrieve data for {symbol}: {str(e)}"}), 500

@app.route('/market-news')
def market_news():
    category = request.args.get('category', 'general')
    limit = int(request.args.get('limit', 100))
    
    try:
        news_with_sentiment = finpulse.get_market_news_with_sentiment(
            category=category,
            use_cache=True
        )
        
        news_with_sentiment = news_with_sentiment[:limit]
        
        sentiment_summary = finpulse.get_sentiment_summary(category, news_with_sentiment)
        
        response = {
            "category": category,
            "news_count": len(news_with_sentiment),
            "stats": sentiment_summary,
            "news": news_with_sentiment,
            "is_sample_data": False
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing request for market news ({category}): {str(e)}")
        return jsonify({"error": f"Could not retrieve market news: {str(e)}"}), 500

@app.route('/tracked-symbols')
def tracked_symbols():
    try:
        symbols = finpulse.get_tracked_symbols()
        return jsonify({"symbols": symbols})
    except Exception as e:
        logger.error(f"Error retrieving tracked symbols: {str(e)}")
        return jsonify({"error": f"Could not retrieve tracked symbols: {str(e)}"}), 500

@app.route('/add-symbol', methods=['POST'])
def add_symbol():
    data = request.get_json()
    symbol = data.get('symbol', '').upper()
    
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400
    
    try:
        finpulse.add_tracked_symbol(symbol)
        return jsonify({"success": True, "message": f"Added {symbol} to tracked symbols"})
    except Exception as e:
        logger.error(f"Error adding symbol {symbol}: {str(e)}")
        return jsonify({"error": f"Could not add symbol: {str(e)}"}), 500

@app.route('/remove-symbol', methods=['POST'])
def remove_symbol():
    data = request.get_json()
    symbol = data.get('symbol', '').upper()
    
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400
    
    try:
        finpulse.remove_tracked_symbol(symbol)
        return jsonify({"success": True, "message": f"Removed {symbol} from tracked symbols"})
    except Exception as e:
        logger.error(f"Error removing symbol {symbol}: {str(e)}")
        return jsonify({"error": f"Could not remove symbol: {str(e)}"}), 500

@app.route('/word-cloud')
def generate_word_cloud():
    symbol = request.args.get('symbol', '')
    category = request.args.get('category', '')
    days = int(request.args.get('days', 7))
    
    try:
        if symbol:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            news_items = finpulse.get_company_news_with_sentiment(
                symbol=symbol,
                from_date=start_date.strftime('%Y-%m-%d'),
                to_date=end_date.strftime('%Y-%m-%d'),
                use_cache=True
            )
            title = f"Word Cloud for {symbol} News"
        elif category:
            news_items = finpulse.get_market_news_with_sentiment(
                category=category,
                use_cache=True
            )
            title = f"Word Cloud for {category.capitalize()} Market News"
        else:
            return jsonify({"error": "Either symbol or category must be provided"}), 400
        
        if not news_items:
            return jsonify({"error": "No news data available"}), 404
        
        all_keywords = []
        for item in news_items:
            if 'sentiment' in item and 'keywords' in item['sentiment']:
                all_keywords.extend(item['sentiment']['keywords'])
            
            if 'headline' in item:
                headline_keywords = finpulse.sentiment_analyzer.extract_keywords(item['headline'], max_keywords=5)
                all_keywords.extend(headline_keywords)
        
        word_counts = Counter(all_keywords)
        
        stop_words = ['news', 'market', 'stock', 'stocks', 'report', 'reports', 'update', 'updates']
        for word in stop_words:
            if word in word_counts:
                del word_counts[word]
        
        if not word_counts:
            return jsonify({"error": "No significant keywords found"}), 404
            
        wordcloud = WordCloud(
            width=1000, 
            height=500, 
            background_color='white', 
            colormap='viridis',
            max_words=150,
            prefer_horizontal=0.9,
            scale=3,
            relative_scaling=0.6,
            min_font_size=8,
            max_font_size=150,
            contour_width=2, 
            contour_color='steelblue',
            random_state=42
        ).generate_from_frequencies(word_counts)
        
        img_bytes = io.BytesIO()
        wordcloud.to_image().save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        top_keywords = [{"word": word, "count": count} 
                       for word, count in word_counts.most_common(20)]
                       
        return send_file(
            img_bytes,
            mimetype='image/png',
            as_attachment=False,
            download_name='wordcloud.png'
        )
        
    except Exception as e:
        logger.error(f"Error generating word cloud: {str(e)}")
        return jsonify({"error": f"Could not generate word cloud: {str(e)}"}), 500

@app.route('/keywords')
def get_keywords():
    symbol = request.args.get('symbol', '')
    category = request.args.get('category', '')
    days = int(request.args.get('days', 7))
    
    try:
        if symbol:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            news_items = finpulse.get_company_news_with_sentiment(
                symbol=symbol,
                from_date=start_date.strftime('%Y-%m-%d'),
                to_date=end_date.strftime('%Y-%m-%d'),
                use_cache=True
            )
        elif category:
            news_items = finpulse.get_market_news_with_sentiment(
                category=category,
                use_cache=True
            )
        else:
            return jsonify({"error": "Either symbol or category must be provided"}), 400
        
        if not news_items:
            return jsonify({"error": "No news data available"}), 404
        
        all_keywords = []
        for item in news_items:
            if 'sentiment' in item and 'keywords' in item['sentiment']:
                all_keywords.extend(item['sentiment']['keywords'])
            
            if 'headline' in item:
                headline_keywords = finpulse.sentiment_analyzer.extract_keywords(item['headline'], max_keywords=5)
                all_keywords.extend(headline_keywords)
        
        word_counts = Counter(all_keywords)
        
        stop_words = ['news', 'market', 'stock', 'stocks', 'report', 'reports', 'update', 'updates']
        for word in stop_words:
            if word in word_counts:
                del word_counts[word]
        
        top_keywords = [{"word": word, "count": count} 
                       for word, count in word_counts.most_common(20)]
                       
        return jsonify({"keywords": top_keywords})
        
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        return jsonify({"error": f"Could not extract keywords: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
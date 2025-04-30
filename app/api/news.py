from flask import Blueprint, request, jsonify
from app.services.finnhub_service import FinnhubService
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.news_preference import NewsPreference
from app import db
import os
from datetime import datetime, timedelta

bp = Blueprint('news', __name__, url_prefix='/api/news')
finnhub_service = FinnhubService(api_key=os.environ.get('FINNHUB_API_KEY'))

@bp.route('/market', methods=['GET'])
def get_market_news():
    category = request.args.get('category', 'general')
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    if request.args.get('from'):
        try:
            start_date = datetime.strptime(request.args.get('from'), '%Y-%m-%d')
        except ValueError:
            pass
    
    if request.args.get('to'):
        try:
            end_date = datetime.strptime(request.args.get('to'), '%Y-%m-%d')
        except ValueError:
            pass
    
    news_items = finnhub_service.get_market_news(
        category,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    return jsonify({'news': news_items})

@bp.route('/company/<symbol>', methods=['GET'])
def get_company_news(symbol):
    if not symbol:
        return jsonify({'error': 'Company symbol is required'}), 400
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    if request.args.get('from'):
        try:
            start_date = datetime.strptime(request.args.get('from'), '%Y-%m-%d')
        except ValueError:
            pass
    
    if request.args.get('to'):
        try:
            end_date = datetime.strptime(request.args.get('to'), '%Y-%m-%d')
        except ValueError:
            pass
    
    news_items = finnhub_service.get_company_news(
        symbol,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    return jsonify({'news': news_items, 'symbol': symbol})

@bp.route('/sentiment/<symbol>', methods=['GET'])
def get_news_sentiment(symbol):
    if not symbol:
        return jsonify({'error': 'Company symbol is required'}), 400
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    if request.args.get('from'):
        try:
            start_date = datetime.strptime(request.args.get('from'), '%Y-%m-%d')
        except ValueError:
            pass
    
    if request.args.get('to'):
        try:
            end_date = datetime.strptime(request.args.get('to'), '%Y-%m-%d')
        except ValueError:
            pass
    
    sentiment = finnhub_service.get_news_sentiment(
        symbol,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    return jsonify({
        'symbol': symbol,
        'sentiment': sentiment
    })

@bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_news_preferences():
    current_user_id = get_jwt_identity()
    
    preferences = NewsPreference.query.filter_by(user_id=current_user_id).first()
    
    if not preferences:
        preferences = NewsPreference(
            user_id=current_user_id,
            followed_symbols=[],
            categories=['general', 'forex', 'crypto', 'merger'],
            keywords=[]
        )
        db.session.add(preferences)
        db.session.commit()
    
    return jsonify({
        'followed_symbols': preferences.followed_symbols,
        'categories': preferences.categories,
        'keywords': preferences.keywords
    })

@bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_news_preferences():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    preferences = NewsPreference.query.filter_by(user_id=current_user_id).first()
    
    if not preferences:
        preferences = NewsPreference(user_id=current_user_id)
        db.session.add(preferences)
    
    if 'followed_symbols' in data:
        preferences.followed_symbols = [symbol.upper() for symbol in data['followed_symbols']]
    
    if 'categories' in data:
        valid_categories = ['general', 'forex', 'crypto', 'merger', 'economic', 'ipo']
        preferences.categories = [cat for cat in data['categories'] if cat in valid_categories]
    
    if 'keywords' in data:
        preferences.keywords = data['keywords']
    
    db.session.commit()
    
    return jsonify({
        'message': 'News preferences updated successfully',
        'followed_symbols': preferences.followed_symbols,
        'categories': preferences.categories,
        'keywords': preferences.keywords
    })

@bp.route('/feed', methods=['GET'])
@jwt_required()
def get_personalized_news_feed():
    current_user_id = get_jwt_identity()
    
    preferences = NewsPreference.query.filter_by(user_id=current_user_id).first()
    
    if not preferences:
        preferences = NewsPreference(
            user_id=current_user_id,
            followed_symbols=[],
            categories=['general'],
            keywords=[]
        )
        db.session.add(preferences)
        db.session.commit()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    category_news = []
    for category in preferences.categories:
        news = finnhub_service.get_market_news(
            category,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        category_news.extend(news)

    symbol_news = []
    for symbol in preferences.followed_symbols:
        news = finnhub_service.get_company_news(
            symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        symbol_news.extend(news)
    
    all_news = category_news + symbol_news
    
    unique_news = {}
    for news_item in all_news:
        if news_item.get('id') and news_item['id'] not in unique_news:
            unique_news[news_item['id']] = news_item
    
    filtered_news = list(unique_news.values())
    if preferences.keywords:
        filtered_news = []
        for news_item in unique_news.values():
            headline = news_item.get('headline', '').lower()
            summary = news_item.get('summary', '').lower()
            
            for keyword in preferences.keywords:
                if keyword.lower() in headline or keyword.lower() in summary:
                    filtered_news.append(news_item)
                    break
    
    sorted_news = sorted(filtered_news, key=lambda x: x.get('datetime', 0), reverse=True)
    
    return jsonify({
        'news': sorted_news,
        'preferences': {
            'followed_symbols': preferences.followed_symbols,
            'categories': preferences.categories,
            'keywords': preferences.keywords
        }
    }) 
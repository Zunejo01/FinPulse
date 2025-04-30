from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.finnhub_service import FinnhubService
from app.models.stock_search_history import StockSearchHistory
from app import db
import os

bp = Blueprint('stocks', __name__, url_prefix='/api/stocks')
finnhub_service = FinnhubService(api_key=os.environ.get('FINNHUB_API_KEY'))

@bp.route('/search', methods=['GET'])
def search_stocks():
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    results = finnhub_service.search_symbols(query)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            from flask_jwt_extended import decode_token
            token = auth_header.split(' ')[1]
            user_id = decode_token(token)['sub']
            history = StockSearchHistory(
                user_id=user_id,
                query=query,
                result_count=len(results)
            )
            db.session.add(history)
            db.session.commit()
        except Exception:
            pass
    
    return jsonify({'results': results})

@bp.route('/quote/<symbol>', methods=['GET'])
def get_stock_quote(symbol):
    if not symbol:
        return jsonify({'error': 'Stock symbol is required'}), 400
    
    quote = finnhub_service.get_quote(symbol)
    if not quote:
        return jsonify({'error': 'Quote not found'}), 404
    
    company_profile = finnhub_service.get_company_profile(symbol)
    
    return jsonify({
        'symbol': symbol,
        'quote': quote,
        'company': company_profile or {}
    })

@bp.route('/news', methods=['GET'])
def get_market_news():
    category = request.args.get('category', 'general')
    min_id = request.args.get('min_id')
    
    news = finnhub_service.get_market_news(category, min_id=min_id)
    
    return jsonify({'news': news})

@bp.route('/<symbol>/news', methods=['GET'])
def get_company_news(symbol):
    if not symbol:
        return jsonify({'error': 'Stock symbol is required'}), 400
    
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    news = finnhub_service.get_company_news(
        symbol,
        start_date=request.args.get('from', start_date),
        end_date=request.args.get('to', end_date)
    )
    
    return jsonify({'news': news})

@bp.route('/<symbol>/candles', methods=['GET'])
def get_stock_candles(symbol):
    if not symbol:
        return jsonify({'error': 'Stock symbol is required'}), 400
    
    resolution = request.args.get('resolution', 'D')  # D for daily
    from_time = request.args.get('from')
    to_time = request.args.get('to')
    if not from_time or not to_time:
        from datetime import datetime, timedelta
        import time
        
        to_date = datetime.now()
        from_date = to_date - timedelta(days=30)
        
        to_time = int(time.mktime(to_date.timetuple()))
        from_time = int(time.mktime(from_date.timetuple()))
    
    candles = finnhub_service.get_stock_candles(
        symbol,
        resolution,
        from_time,
        to_time
    )
    
    return jsonify(candles)

@bp.route('/watchlist', methods=['GET'])
@jwt_required()
def get_watchlist():
    current_user_id = get_jwt_identity()
    from app.models.user import User
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    watchlist_items = []
    for item in user.watchlist:
        quote = finnhub_service.get_quote(item.symbol)
        watchlist_items.append({
            'id': item.id,
            'symbol': item.symbol,
            'added_at': item.created_at.isoformat(),
            'notes': item.notes,
            'quote': quote or {}
        })
    
    return jsonify({'watchlist': watchlist_items})

@bp.route('/watchlist', methods=['POST'])
@jwt_required()
def add_to_watchlist():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('symbol'):
        return jsonify({'error': 'Stock symbol is required'}), 400

    from app.models.user import User
    from app.models.watchlist import WatchlistItem
    
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    existing = WatchlistItem.query.filter_by(
        user_id=current_user_id, 
        symbol=data['symbol'].upper()
    ).first()
    
    if existing:
        return jsonify({'error': 'Stock already in watchlist'}), 400
    
    watchlist_item = WatchlistItem(
        user_id=current_user_id,
        symbol=data['symbol'].upper(),
        notes=data.get('notes', '')
    )
    
    db.session.add(watchlist_item)
    db.session.commit()
    
    return jsonify({
        'message': 'Stock added to watchlist',
        'id': watchlist_item.id
    }), 201

@bp.route('/watchlist/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_watchlist(item_id):
    current_user_id = get_jwt_identity()
    from app.models.watchlist import WatchlistItem
    
    watchlist_item = WatchlistItem.query.filter_by(
        id=item_id,
        user_id=current_user_id
    ).first()
    
    if not watchlist_item:
        return jsonify({'error': 'Watchlist item not found'}), 404
    
    db.session.delete(watchlist_item)
    db.session.commit()
    
    return jsonify({'message': 'Stock removed from watchlist'}), 200 
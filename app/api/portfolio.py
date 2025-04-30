from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.portfolio import Portfolio, Position
from app.services.finnhub_service import FinnhubService
from app import db
import os
from datetime import datetime

bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')
finnhub_service = FinnhubService(api_key=os.environ.get('FINNHUB_API_KEY'))

@bp.route('/', methods=['GET'])
@jwt_required()
def get_portfolios():
    current_user_id = get_jwt_identity()
    
    portfolios = Portfolio.query.filter_by(user_id=current_user_id).all()
    
    portfolio_list = []
    for portfolio in portfolios:
        total_value = 0
        positions_data = []
        
        for position in portfolio.positions:
            quote = finnhub_service.get_quote(position.symbol)
            current_price = quote.get('c', 0) if quote else 0
            position_value = position.quantity * current_price
            total_value += position_value
            
            positions_data.append({
                'id': position.id,
                'symbol': position.symbol,
                'quantity': position.quantity,
                'average_price': position.average_price,
                'current_price': current_price,
                'value': position_value,
                'gain_loss': position_value - (position.average_price * position.quantity),
                'gain_loss_percent': ((current_price / position.average_price) - 1) * 100 if position.average_price > 0 else 0
            })
        
        portfolio_list.append({
            'id': portfolio.id,
            'name': portfolio.name,
            'description': portfolio.description,
            'created_at': portfolio.created_at.isoformat(),
            'total_value': total_value,
            'positions': positions_data
        })
    
    return jsonify({'portfolios': portfolio_list})

@bp.route('/', methods=['POST'])
@jwt_required()
def create_portfolio():
    """Create a new portfolio"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Portfolio name is required'}), 400
    
    portfolio = Portfolio(
        user_id=current_user_id,
        name=data['name'],
        description=data.get('description', '')
    )
    
    db.session.add(portfolio)
    db.session.commit()
    
    return jsonify({
        'id': portfolio.id,
        'name': portfolio.name,
        'message': 'Portfolio created successfully'
    }), 201

@bp.route('/<int:portfolio_id>', methods=['GET'])
@jwt_required()
def get_portfolio(portfolio_id):
    """Get a specific portfolio by ID"""
    current_user_id = get_jwt_identity()
    
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user_id
    ).first()
    
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    total_value = 0
    positions_data = []
    
    for position in portfolio.positions:
        quote = finnhub_service.get_quote(position.symbol)
        current_price = quote.get('c', 0) if quote else 0
        position_value = position.quantity * current_price
        total_value += position_value
        
        company = finnhub_service.get_company_profile(position.symbol)
        
        positions_data.append({
            'id': position.id,
            'symbol': position.symbol,
            'company_name': company.get('name') if company else '',
            'quantity': position.quantity,
            'average_price': position.average_price,
            'current_price': current_price,
            'value': position_value,
            'gain_loss': position_value - (position.average_price * position.quantity),
            'gain_loss_percent': ((current_price / position.average_price) - 1) * 100 if position.average_price > 0 else 0,
            'sector': company.get('finnhubIndustry') if company else '',
            'notes': position.notes
        })
    
    return jsonify({
        'id': portfolio.id,
        'name': portfolio.name,
        'description': portfolio.description,
        'created_at': portfolio.created_at.isoformat(),
        'total_value': total_value,
        'positions': positions_data
    })

@bp.route('/<int:portfolio_id>', methods=['PUT'])
@jwt_required()
def update_portfolio(portfolio_id):
    """Update portfolio details"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user_id
    ).first()
    
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    if data.get('name'):
        portfolio.name = data['name']
    
    if 'description' in data:
        portfolio.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Portfolio updated successfully',
        'id': portfolio.id,
        'name': portfolio.name,
        'description': portfolio.description
    })

@bp.route('/<int:portfolio_id>', methods=['DELETE'])
@jwt_required()
def delete_portfolio(portfolio_id):
    """Delete a portfolio"""
    current_user_id = get_jwt_identity()
    
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user_id
    ).first()
    
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    db.session.delete(portfolio)
    db.session.commit()
    
    return jsonify({'message': 'Portfolio deleted successfully'})

@bp.route('/<int:portfolio_id>/positions', methods=['POST'])
@jwt_required()
def add_position(portfolio_id):
    """Add a position to a portfolio"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ['symbol', 'quantity', 'average_price']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user_id
    ).first()
    
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    existing_position = Position.query.filter_by(
        portfolio_id=portfolio_id,
        symbol=data['symbol'].upper()
    ).first()
    
    if existing_position:
        total_cost = (existing_position.quantity * existing_position.average_price) + (data['quantity'] * data['average_price'])
        total_quantity = existing_position.quantity + data['quantity']
        
        existing_position.quantity = total_quantity
        existing_position.average_price = total_cost / total_quantity if total_quantity > 0 else 0
        
        if data.get('notes'):
            existing_position.notes = data['notes']
        
        position = existing_position
    else:
        position = Position(
            portfolio_id=portfolio_id,
            symbol=data['symbol'].upper(),
            quantity=data['quantity'],
            average_price=data['average_price'],
            notes=data.get('notes', '')
        )
        db.session.add(position)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Position added successfully',
        'id': position.id,
        'symbol': position.symbol,
        'quantity': position.quantity,
        'average_price': position.average_price
    }), 201

@bp.route('/<int:portfolio_id>/positions/<int:position_id>', methods=['PUT'])
@jwt_required()
def update_position(portfolio_id, position_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user_id
    ).first()
    
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    position = Position.query.filter_by(
        id=position_id,
        portfolio_id=portfolio_id
    ).first()
    
    if not position:
        return jsonify({'error': 'Position not found'}), 404
    if 'quantity' in data:
        position.quantity = data['quantity']
    
    if 'average_price' in data:
        position.average_price = data['average_price']
    
    if 'notes' in data:
        position.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Position updated successfully',
        'id': position.id,
        'symbol': position.symbol,
        'quantity': position.quantity,
        'average_price': position.average_price
    })

@bp.route('/<int:portfolio_id>/positions/<int:position_id>', methods=['DELETE'])
@jwt_required()
def delete_position(portfolio_id, position_id):
    current_user_id = get_jwt_identity()
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user_id
    ).first()
    
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404
    position = Position.query.filter_by(
        id=position_id,
        portfolio_id=portfolio_id
    ).first()
    
    if not position:
        return jsonify({'error': 'Position not found'}), 404
    
    db.session.delete(position)
    db.session.commit()
    
    return jsonify({'message': 'Position deleted successfully'})

@bp.route('/<int:portfolio_id>/analysis', methods=['GET'])
@jwt_required()
def get_portfolio_analysis(portfolio_id):
    current_user_id = get_jwt_identity()
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user_id
    ).first()
    
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404
    total_value = 0
    total_cost = 0
    sector_allocation = {}
    positions_data = []
    
    for position in portfolio.positions:
        quote = finnhub_service.get_quote(position.symbol)
        company = finnhub_service.get_company_profile(position.symbol)
        
        current_price = quote.get('c', 0) if quote else 0
        position_value = position.quantity * current_price
        position_cost = position.quantity * position.average_price
        
        total_value += position_value
        total_cost += position_cost
        
        sector = company.get('finnhubIndustry', 'Unknown') if company else 'Unknown'
        if sector in sector_allocation:
            sector_allocation[sector] += position_value
        else:
            sector_allocation[sector] = position_value
        
        positions_data.append({
            'symbol': position.symbol,
            'quantity': position.quantity,
            'value': position_value,
            'cost': position_cost,
            'gain_loss': position_value - position_cost,
            'return_percent': ((position_value / position_cost) - 1) * 100 if position_cost > 0 else 0
        })
    
    performance = {
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain_loss': total_value - total_cost,
        'total_return_percent': ((total_value / total_cost) - 1) * 100 if total_cost > 0 else 0
    }
    
    sector_percentages = {sector: (value / total_value) * 100 for sector, value in sector_allocation.items()} if total_value > 0 else {}
    
    return jsonify({
        'portfolio_id': portfolio_id,
        'portfolio_name': portfolio.name,
        'performance': performance,
        'sector_allocation': sector_percentages,
        'positions': positions_data
    }) 
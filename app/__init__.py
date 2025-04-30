import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()

def create_app(test_config=None):
   
    app = Flask(__name__, instance_relative_config=True)
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
            SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///finpulse.db'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret'),
            JWT_ACCESS_TOKEN_EXPIRES=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)),
        )
    else:
        app.config.from_mapping(test_config)
    
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    from app.api import auth, stocks, portfolio, news
    app.register_blueprint(auth.bp)
    app.register_blueprint(stocks.bp)
    app.register_blueprint(portfolio.bp)
    app.register_blueprint(news.bp)
    
    from app import commands
    commands.init_app(app)
    
    @app.route('/')
    def index():
        return {
            'message': 'Welcome to FinPulse API',
            'version': '1.0.0'
        }
    
    return app 
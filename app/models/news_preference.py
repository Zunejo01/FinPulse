from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Text

class NewsPreference(db.Model):
    __tablename__ = 'news_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    _followed_symbols = db.Column('followed_symbols', db.Text, default='')
    _categories = db.Column('categories', db.Text, default='general')
    _keywords = db.Column('keywords', db.Text, default='')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def followed_symbols(self):
        """Get list of followed symbols"""
        if not self._followed_symbols:
            return []
        return self._followed_symbols.split(',')
    
    @followed_symbols.setter
    def followed_symbols(self, value):
        """Set list of followed symbols"""
        if isinstance(value, list):
            self._followed_symbols = ','.join(value)
        else:
            self._followed_symbols = ''
    
    @property
    def categories(self):
        """Get list of news categories"""
        if not self._categories:
            return ['general']
        return self._categories.split(',')
    
    @categories.setter
    def categories(self, value):
        """Set list of news categories"""
        if isinstance(value, list):
            self._categories = ','.join(value)
        else:
            self._categories = 'general'
    
    @property
    def keywords(self):
        """Get list of news keywords"""
        if not self._keywords:
            return []
        return self._keywords.split(',')
    
    @keywords.setter
    def keywords(self, value):
        """Set list of news keywords"""
        if isinstance(value, list):
            self._keywords = ','.join(value)
        else:
            self._keywords = ''
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'followed_symbols': self.followed_symbols,
            'categories': self.categories,
            'keywords': self.keywords,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<NewsPreference for user_id={self.user_id}>" 
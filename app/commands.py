import click
from flask.cli import with_appcontext
from app import db
from werkzeug.security import generate_password_hash
from app.models.user import User
from app.models.news_preference import NewsPreference

def init_app(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)

@click.command('init-db')
@with_appcontext
def init_db_command():
    db.create_all()
    click.echo('Initialized the database.')

@click.command('create-admin')
@click.option('--username', prompt=True, help='Admin username')
@click.option('--email', prompt=True, help='Admin email')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
@with_appcontext
def create_admin_command(username, email, password):
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        click.echo(f'User {username} already exists.')
        return
    
    admin = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        first_name='Admin',
        last_name='User'
    )
    
    db.session.add(admin)
    
    preferences = NewsPreference(user_id=admin.id)
    preferences.categories = ['general', 'forex', 'crypto', 'merger']
    db.session.add(preferences)
    
    db.session.commit()
    click.echo(f'Created admin user {username}.')

@click.command('seed-demo-data')
@with_appcontext
def seed_demo_data_command():
    from app.models.portfolio import Portfolio, Position
    from app.models.watchlist import WatchlistItem
    
    demo_user = User.query.filter_by(username='demo').first()
    if not demo_user:
        demo_user = User(
            username='demo',
            email='demo@example.com',
            password_hash=generate_password_hash('password'),
            first_name='Demo',
            last_name='User'
        )
        db.session.add(demo_user)
        db.session.flush()
    
    portfolio = Portfolio(
        user_id=demo_user.id,
        name='Demo Portfolio',
        description='Sample portfolio with tech stocks'
    )
    db.session.add(portfolio)
    db.session.flush()
    
    positions = [
        Position(portfolio_id=portfolio.id, symbol='AAPL', quantity=10, average_price=150.0),
        Position(portfolio_id=portfolio.id, symbol='MSFT', quantity=5, average_price=250.0),
        Position(portfolio_id=portfolio.id, symbol='GOOGL', quantity=2, average_price=2500.0),
        Position(portfolio_id=portfolio.id, symbol='AMZN', quantity=3, average_price=3200.0),
        Position(portfolio_id=portfolio.id, symbol='TSLA', quantity=8, average_price=700.0),
    ]
    db.session.add_all(positions)
    
    watchlist_items = [
        WatchlistItem(user_id=demo_user.id, symbol='NVDA'),
        WatchlistItem(user_id=demo_user.id, symbol='AMD'),
        WatchlistItem(user_id=demo_user.id, symbol='INTC'),
        WatchlistItem(user_id=demo_user.id, symbol='FB'),
        WatchlistItem(user_id=demo_user.id, symbol='NFLX'),
    ]
    db.session.add_all(watchlist_items)
    
    news_pref = NewsPreference.query.filter_by(user_id=demo_user.id).first()
    if not news_pref:
        news_pref = NewsPreference(user_id=demo_user.id)
        db.session.add(news_pref)
    
    news_pref.followed_symbols = ['AAPL', 'MSFT', 'GOOGL']
    news_pref.categories = ['general', 'merger', 'ipo']
    news_pref.keywords = ['earnings', 'dividend', 'growth']
    
    db.session.commit()
    click.echo('Seeded demo data successfully.')
    
    init_app.cli.add_command(seed_demo_data_command) 
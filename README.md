# FinPulse: Financial News Sentiment Analyzer

A web application that analyzes the sentiment of financial news articles to help investors make more informed decisions.

## Features

- Real-time financial news analysis
- Sentiment scoring for company-specific and general market news
- Interactive data visualizations (bar charts, pie charts, time series)
- Keyword extraction and word cloud generation
- News filtering by sentiment (positive, neutral, negative)
- Caching system to minimize API calls

## Technologies Used

- **Frontend**:
  - HTML/CSS
  - JavaScript with Plotly.js for data visualization
  - Font Awesome for icons

- **Backend**:
  - Python (3.9+)
  - Flask web framework
  - NLTK for natural language processing and sentiment analysis
  - WordCloud for keyword visualization

- **Data Sources**:
  - Finnhub API for financial news and market data

- **Storage**:
  - File-based caching system with JSON files

- **Development Tools**:
  - Flask debug server
  - Python dotenv for environment variable management

## Getting Started

### Prerequisites

- Python 3.9+
- Finnhub API key

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/finpulse.git
cd finpulse
```

2. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
cp .env.example .env
```
Edit the `.env` file with your Finnhub API key.

5. Start the application
```bash
python app.py
```

The application will be available at http://127.0.0.1:5000

## Configuration

FinPulse uses environment variables for configuration:
- `FINNHUB_API_KEY`: Your Finnhub API key (required)
- `FLASK_ENV`: Set to "development" or "production"

### API Keys
You'll need to register for a [Finnhub](https://finnhub.io/) API key for financial market data

## Project Structure
```
finpulse/
├── app.py                # Flask application and routes
├── finpulse_app.py       # Main application logic
├── finnhub_client.py     # Client for Finnhub API
├── sentiment_analyzer.py # Sentiment analysis engine
├── static/               # Static assets (CSS, JavaScript)
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript files
├── templates/            # HTML templates
├── utils/                # Utility functions
├── cache/                # Cached data (generated at runtime)
├── .env                  # Environment variables (not in repo)
└── requirements.txt      # Python dependencies
```

## License

This project is licensed under the MIT License.

## Acknowledgments

- [Finnhub](https://finnhub.io/) for financial data API
- [Flask](https://flask.palletsprojects.com/) web framework
- [NLTK](https://www.nltk.org/) for natural language processing
- [Plotly](https://plotly.com/javascript/) for interactive visualizations 
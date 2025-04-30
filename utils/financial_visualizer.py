import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

def create_sentiment_pie_chart(positive, neutral, negative):
    
    labels = ['Positive', 'Neutral', 'Negative']
    values = [positive, neutral, negative]
    colors = ['#4CAF50', '#9E9E9E', '#F44336']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=colors
    )])
    
    fig.update_layout(
        title='Sentiment Distribution',
        height=500
    )
    
    return fig.to_html(full_html=False)

def create_sentiment_time_series(news_items):
    dates = []
    scores = []
    
    for item in news_items:
        if 'datetime' in item and 'sentiment_score' in item:
            date = datetime.fromtimestamp(item['datetime'])
            dates.append(date)
            scores.append(item['sentiment_score'])
    
   
    date_scores = sorted(zip(dates, scores), key=lambda x: x[0])
    dates = [item[0] for item in date_scores]
    scores = [item[1] for item in date_scores]
    
    df = pd.DataFrame({
        'date': dates,
        'score': scores
    })
    
    window_size = min(7, len(df)) if len(df) > 0 else 1
    df['rolling_avg'] = df['score'].rolling(window=window_size, min_periods=1).mean()
    
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['score'],
            mode='markers',
            name='Sentiment Score',
            marker=dict(
                color=df['score'],
                colorscale='RdYlGn',
                cmin=-1,
                cmax=1,
                size=8
            )
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['rolling_avg'],
            mode='lines',
            name='7-day Average',
            line=dict(color='rgba(0, 0, 255, 0.7)', width=3)
        )
    )
    fig.add_shape(
        type="line",
        x0=min(dates) if dates else datetime.now() - timedelta(days=7),
        y0=0,
        x1=max(dates) if dates else datetime.now(),
        y1=0,
        line=dict(color="gray", width=1, dash="dash")
    )
    fig.update_layout(
        title='Sentiment Trend Over Time',
        xaxis_title='Date',
        yaxis_title='Sentiment Score',
        yaxis=dict(range=[-1.1, 1.1]),
        height=500,
        hovermode='closest'
    )
    return fig.to_html(full_html=False)

def create_source_distribution(news_items):

    source_counts = {}
    for item in news_items:
        source = item.get('source', 'Unknown')
        if source in source_counts:
            source_counts[source] += 1
        else:
            source_counts[source] = 1
    
    sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
    top_sources = sources[:10]
    
    fig = go.Figure(data=[
        go.Bar(
            x=[s[0] for s in top_sources],
            y=[s[1] for s in top_sources],
            marker_color='royalblue'
        )
    ])
    
    fig.update_layout(
        title='Top News Sources',
        xaxis_title='Source',
        yaxis_title='Number of Articles',
        height=400
    )
    
    return fig.to_html(full_html=False)

def create_keyword_frequency_chart(news_items, top_n=15):
    all_keywords = []
    for item in news_items:
        keywords = item.get('keywords', [])
        all_keywords.extend(keywords)
    
    keyword_counts = {}
    for keyword in all_keywords:
        if keyword in keyword_counts:
            keyword_counts[keyword] += 1
        else:
            keyword_counts[keyword] = 1
    
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    top_keywords = sorted_keywords[:top_n]
    
    fig = go.Figure(data=[
        go.Bar(
            y=[k[0] for k in top_keywords],
            x=[k[1] for k in top_keywords],
            orientation='h',
            marker_color='lightseagreen'
        )
    ])
    
    fig.update_layout(
        title=f'Top {top_n} Keywords',
        xaxis_title='Frequency',
        yaxis_title='Keyword',
        height=600
    )
    return fig.to_html(full_html=False)

def create_stock_price_chart(stock_data, sentiment_data=None):

    fig = make_subplots(
        rows=2, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3]
    )
    
    fig.add_trace(
        go.Scatter(
            x=stock_data['dates'],
            y=stock_data['prices'],
            mode='lines',
            name='Stock Price',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=stock_data['dates'],
            y=stock_data['volumes'],
            name='Volume',
            marker=dict(color='lightblue')
        ),
        row=2, col=1
    )
    if sentiment_data:
        sentiment_colors = []
        for score in sentiment_data['scores']:
            if score > 0.05:
               
                sentiment_colors.append('rgba(0, 255, 0, 0.5)')
            elif score < -0.05:
               
                sentiment_colors.append('rgba(255, 0, 0, 0.5)')
            else:
               
                sentiment_colors.append('rgba(128, 128, 128, 0.5)')
        
      
        fig.add_trace(
            go.Scatter(
                x=sentiment_data['dates'],
                y=[None] * len(sentiment_data['dates']), 
                mode='markers',
                name='News Sentiment',
                marker=dict(
                    symbol='diamond',
                    size=10,
                    color=sentiment_colors
                ),
                hovertext=sentiment_data['titles'],
                hoverinfo='text+x'
            ),
            row=1, col=1
        )
    
   
    fig.update_layout(
        title='Stock Price with Trading Volume',
        height=700,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        hovermode='x unified'
    )
    
   
    fig.update_yaxes(title_text='Price', row=1, col=1)
    fig.update_yaxes(title_text='Volume', row=2, col=1)
    fig.update_xaxes(title_text='Date', row=2, col=1)
    
   
    return fig.to_html(full_html=False) 
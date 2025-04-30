document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const companySearchBox = document.getElementById('company-search');
    const marketSearchBox = document.getElementById('market-search');
    const symbolInput = document.getElementById('symbol-input');
    const timeframeSelect = document.getElementById('timeframe-select');
    const categorySelect = document.getElementById('category-select');
    const marketCountSelect = document.getElementById('market-count-select');
    const companyButton = document.getElementById('company-button');
    const marketButton = document.getElementById('market-button');
    const loadingIndicator = document.getElementById('loading');
    const searchTabs = document.querySelectorAll('.search-tabs li');
    const overviewText = document.getElementById('overview-text');
    const newsContainer = document.getElementById('news-list');
    
    // Chart containers
    const sentimentOverviewChart = document.getElementById('sentiment-overview-chart');
    const sentimentPieChart = document.getElementById('sentiment-pie-chart');
    const timeSeriesChart = document.getElementById('time-series-chart');
    
    // Results storage
    let currentResults = null;
    let currentMode = 'company'; // 'company' or 'market'
    
    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            
            // Remove active class from all buttons and panes
            tabBtns.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Add active class to current button and pane
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Preview click handlers
    const previewPlaceholders = document.querySelectorAll('.preview-placeholder');
    previewPlaceholders.forEach(placeholder => {
        placeholder.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            
            // Activate the tab
            tabBtns.forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.tab === tabId) {
                    btn.classList.add('active');
                }
            });
            
            tabPanes.forEach(pane => {
                pane.classList.remove('active');
                if (pane.id === tabId) {
                    pane.classList.add('active');
                }
            });
        });
    });
    
    // Search tabs switching
    searchTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            searchTabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to current tab
            this.classList.add('active');
            
            // Show/hide search boxes
            const tabId = this.dataset.tab;
            currentMode = tabId;
            
            if (tabId === 'company') {
                companySearchBox.classList.remove('hidden');
                marketSearchBox.classList.add('hidden');
            } else {
                companySearchBox.classList.add('hidden');
                marketSearchBox.classList.remove('hidden');
            }
        });
    });
    
    // News filtering
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            
            // Remove active class from all buttons
            filterBtns.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to current button
            this.classList.add('active');
            
            // Filter the news
            if (currentResults) {
                displayNews(currentResults, filter);
            }
        });
    });
    
    // Company analysis button click
    companyButton.addEventListener('click', function() {
        const symbol = symbolInput.value.trim().toUpperCase();
        if (!symbol) {
            showError('Please enter a stock symbol');
            return;
        }
        
        const days = timeframeSelect.value;
        analyzeCompanyNews(symbol, days);
    });
    
    // Also analyze on enter key in symbol input
    symbolInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const symbol = symbolInput.value.trim().toUpperCase();
            if (!symbol) {
                alert('Please enter a stock symbol');
                return;
            }
            
            const days = timeframeSelect.value;
            analyzeCompanyNews(symbol, days);
        }
    });
    
    // Market analysis button click
    marketButton.addEventListener('click', function() {
        const category = categorySelect.value;
        const limit = marketCountSelect.value;
        analyzeMarketNews(category, limit);
    });
    
    // Analyze company news
    function analyzeCompanyNews(symbol, days) {
        showLoading();
        
        fetch(`/company-news?symbol=${symbol}&days=${days}&limit=100`)
            .then(response => response.json())
            .then(data => {
                hideLoading();
                
                if (data.error) {
                    showDashboardError(data.error);
                    return;
                }
                
                currentResults = data;
                currentMode = 'company';
                
                // Update overview header
                updateOverviewHeader(symbol, data.is_sample_data);
                
                // Update sentiment cards
                updateSentimentCards(data.stats);
                
                // Generate visualizations
                generateCharts(data);
                
                // Display news
                const activeFilter = document.querySelector('.filter-btn.active').dataset.filter;
                displayNews(data, activeFilter);
                
                // Switch to overview tab
                document.querySelector('.tab-btn[data-tab="overview"]').click();
            })
            .catch(error => {
                hideLoading();
                showDashboardError('Error analyzing company news: ' + error.message);
            });
    }
    
    // Analyze market news
    function analyzeMarketNews(category, limit) {
        showLoading();
        
        fetch(`/market-news?category=${category}&limit=${limit}`)
            .then(response => response.json())
            .then(data => {
                hideLoading();
                
                if (data.error) {
                    showDashboardError(data.error);
                    return;
                }
                
                currentResults = data;
                currentMode = 'market';
                
                // Update overview header
                updateOverviewHeader(category, data.is_sample_data);
                
                // Update sentiment cards
                updateSentimentCards(data.stats);
                
                // Generate visualizations
                generateCharts(data);
                
                // Display news
                const activeFilter = document.querySelector('.filter-btn.active').dataset.filter;
                displayNews(data, activeFilter);
                
                // Switch to overview tab
                document.querySelector('.tab-btn[data-tab="overview"]').click();
            })
            .catch(error => {
                hideLoading();
                showDashboardError('Error analyzing market news: ' + error.message);
            });
    }
    
    // Update overview header
    function updateOverviewHeader(query, isSampleData) {
        let headerText = '';
        let descriptionText = '';
        
        if (!currentResults) {
            overviewText.innerHTML = `
                <h2>FinPulse Financial News Sentiment Analysis</h2>
                <p>Enter a stock symbol or select a market category to analyze financial news sentiment.</p>
            `;
            return;
        }
        
        const count = currentResults.news_count || (currentResults.news ? currentResults.news.length : 0);
        
        if (currentMode === 'company') {
            headerText = `Sentiment Analysis for ${query}`;
            descriptionText = `Based on ${count} news articles over the selected time period.`;
            
            // Add date range if available
            if (currentResults.date_range) {
                const from = currentResults.date_range.from;
                const to = currentResults.date_range.to;
                descriptionText += ` (${from} to ${to})`;
            }
        } else {
            const categoryName = {
                'general': 'General Market',
                'forex': 'Forex Market',
                'crypto': 'Cryptocurrency Market',
                'merger': 'Merger & Acquisition'
            }[query] || query;
            
            headerText = `${categoryName} News Sentiment Analysis`;
            descriptionText = `Based on ${count} recent news articles.`;
        }
        
        // Add overall sentiment indicator if available
        if (currentResults.stats && currentResults.stats.overall_sentiment) {
            const sentiment = currentResults.stats.overall_sentiment;
            const score = currentResults.stats.avg_score !== undefined ? 
                currentResults.stats.avg_score.toFixed(2) : '0.00';
            
            headerText += ` <span class="sentiment-indicator ${sentiment}">${sentiment} (${score})</span>`;
        }
        
        // Add sample data warning if applicable
        if (isSampleData) {
            descriptionText += ' <span class="sample-warning">(Using sample data - please check your Finnhub API key)</span>';
        }
        
        overviewText.innerHTML = `
            <h2>${headerText}</h2>
            <p>${descriptionText}</p>
        `;
    }
    
    // Update sentiment cards
    function updateSentimentCards(stats) {
        if (!stats || typeof stats !== 'object') {
            console.error('Invalid stats object:', stats);
            return;
        }
        
        // Extract distribution data safely
        const distribution = stats.sentiment_distribution || {};
        const positive = distribution.positive ? distribution.positive.count || 0 : 0;
        const negative = distribution.negative ? distribution.negative.count || 0 : 0;
        const neutral = distribution.neutral ? distribution.neutral.count || 0 : 0;
        
        // Calculate percentages
        const total = positive + negative + neutral;
        const positivePercent = total > 0 ? Math.round((positive / total) * 100) : 0;
        const negativePercent = total > 0 ? Math.round((negative / total) * 100) : 0;
        const neutralPercent = total > 0 ? Math.round((neutral / total) * 100) : 0;
        
        // Update UI
        document.querySelector('#positive-card .percentage').textContent = `${positivePercent}%`;
        document.querySelector('#negative-card .percentage').textContent = `${negativePercent}%`;
        document.querySelector('#neutral-card .percentage').textContent = `${neutralPercent}%`;
        
        // Overall sentiment score - handle safely
        const scoreElement = document.querySelector('#score-card .percentage');
        const score = typeof stats.avg_score === 'number' ? stats.avg_score : 0;
        
        // Format score with two decimal places
        scoreElement.textContent = score.toFixed(2);
        
        // Add color based on score
        if (score >= 0.05) {
            scoreElement.classList.add('positive-score');
            scoreElement.classList.remove('negative-score', 'neutral-score');
        } else if (score <= -0.05) {
            scoreElement.classList.add('negative-score');
            scoreElement.classList.remove('positive-score', 'neutral-score');
        } else {
            scoreElement.classList.add('neutral-score');
            scoreElement.classList.remove('positive-score', 'negative-score');
        }
    }
    
    // Generate charts
    function generateCharts(data) {
        generateSentimentOverviewChart(data.stats);
        generateSentimentPieChart(data.stats);
        generateTimeSeriesChart(data.news);
        generateWordCloud();
    }
    
    // Generate sentiment overview chart
    function generateSentimentOverviewChart(stats) {
        if (!stats || typeof stats !== 'object') {
            console.error('Invalid stats object for overview chart:', stats);
            return;
        }
        
        // Extract distribution data safely
        const distribution = stats.sentiment_distribution || {};
        const positive = distribution.positive ? distribution.positive.count || 0 : 0;
        const negative = distribution.negative ? distribution.negative.count || 0 : 0;
        const neutral = distribution.neutral ? distribution.neutral.count || 0 : 0;
        
        const data = [{
            x: ['Positive', 'Neutral', 'Negative'],
            y: [positive, neutral, negative],
            type: 'bar',
            marker: {
                color: ['#4CAF50', '#FFC107', '#F44336']
            }
        }];
        
        const layout = {
            title: 'Sentiment Distribution',
            height: 300,
            margin: {t: 50, r: 20, l: 40, b: 40}
        };
        
        Plotly.newPlot(sentimentOverviewChart, data, layout);
    }
    
    // Generate sentiment pie chart
    function generateSentimentPieChart(stats) {
        if (!stats || typeof stats !== 'object') {
            console.error('Invalid stats object for pie chart:', stats);
            return;
        }
        
        // Extract distribution data safely
        const distribution = stats.sentiment_distribution || {};
        const positive = distribution.positive ? distribution.positive.count || 0 : 0;
        const negative = distribution.negative ? distribution.negative.count || 0 : 0;
        const neutral = distribution.neutral ? distribution.neutral.count || 0 : 0;
        
        const data = [{
            values: [positive, neutral, negative],
            labels: ['Positive', 'Neutral', 'Negative'],
            type: 'pie',
            marker: {
                colors: ['#4CAF50', '#FFC107', '#F44336']
            }
        }];
        
        const layout = {
            title: 'Sentiment Distribution',
            height: 400
        };
        
        Plotly.newPlot(sentimentPieChart, data, layout);
    }
    
    // Generate time series chart
    function generateTimeSeriesChart(news) {
        if (!news || !Array.isArray(news) || news.length === 0) {
            console.error('Invalid news data for time series chart');
            return;
        }
        
        // Check if we have time_series data from the API
        if (currentResults && currentResults.stats && currentResults.stats.time_series) {
            // Use pre-calculated time series data from the API
            const timeSeriesData = currentResults.stats.time_series;
            
            // Prepare data for visualization
            const dates = timeSeriesData.map(item => item.date);
            const positiveData = timeSeriesData.map(item => item.positive);
            const neutralData = timeSeriesData.map(item => item.neutral);
            const negativeData = timeSeriesData.map(item => item.negative);
            const avgScores = timeSeriesData.map(item => item.avg_score);
            
            const data = [
                {
                    x: dates,
                    y: positiveData,
                    name: 'Positive',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: {color: '#4CAF50'}
                },
                {
                    x: dates,
                    y: neutralData,
                    name: 'Neutral',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: {color: '#FFC107'}
                },
                {
                    x: dates,
                    y: negativeData,
                    name: 'Negative',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: {color: '#F44336'}
                },
                {
                    x: dates,
                    y: avgScores,
                    name: 'Average Score',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: {color: '#2196F3'},
                    yaxis: 'y2'
                }
            ];
            
            const layout = {
                title: 'Sentiment Over Time',
                height: 400,
                yaxis: {
                    title: 'Number of Articles'
                },
                yaxis2: {
                    title: 'Average Score',
                    overlaying: 'y',
                    side: 'right',
                    range: [-1, 1]
                },
                legend: {
                    x: 0,
                    y: 1.2,
                    orientation: 'h'
                }
            };
            
            Plotly.newPlot(timeSeriesChart, data, layout);
            return;
        }
        
        // If no pre-calculated data, calculate from news items
        // Sort news by datetime
        const sortedNews = [...news].sort((a, b) => {
            const dateA = a.datetime || 0;
            const dateB = b.datetime || 0;
            return dateA - dateB;
        });
        
        // Group by day
        const days = {};
        
        sortedNews.forEach(item => {
            if (!item.datetime) return;
            
            const date = new Date(item.datetime * 1000);
            const day = date.toISOString().split('T')[0];
            
            if (!days[day]) {
                days[day] = {
                    positive: 0,
                    neutral: 0,
                    negative: 0,
                    total: 0,
                    score_sum: 0
                };
            }
            
            const sentiment = item.sentiment || {};
            const label = sentiment.label || 'neutral';
            
            days[day][label]++;
            days[day].total++;
            days[day].score_sum += sentiment.score || 0;
        });
        
        // Prepare data for chart
        const dayLabels = Object.keys(days).sort();
        const positiveData = [];
        const neutralData = [];
        const negativeData = [];
        const avgScores = [];
        
        dayLabels.forEach(day => {
            const dayStats = days[day];
            positiveData.push(dayStats.positive);
            neutralData.push(dayStats.neutral);
            negativeData.push(dayStats.negative);
            avgScores.push(dayStats.total > 0 ? dayStats.score_sum / dayStats.total : 0);
        });
        
        const data = [
            {
                x: dayLabels,
                y: positiveData,
                name: 'Positive',
                type: 'scatter',
                mode: 'lines+markers',
                line: {color: '#4CAF50'}
            },
            {
                x: dayLabels,
                y: neutralData,
                name: 'Neutral',
                type: 'scatter',
                mode: 'lines+markers',
                line: {color: '#FFC107'}
            },
            {
                x: dayLabels,
                y: negativeData,
                name: 'Negative',
                type: 'scatter',
                mode: 'lines+markers',
                line: {color: '#F44336'}
            },
            {
                x: dayLabels,
                y: avgScores,
                name: 'Average Score',
                type: 'scatter',
                mode: 'lines+markers',
                line: {color: '#2196F3'},
                yaxis: 'y2'
            }
        ];
        
        const layout = {
            title: 'Sentiment Over Time',
            height: 400,
            yaxis: {
                title: 'Number of Articles'
            },
            yaxis2: {
                title: 'Average Score',
                overlaying: 'y',
                side: 'right',
                range: [-1, 1]
            },
            legend: {
                x: 0,
                y: 1.2,
                orientation: 'h'
            }
        };
        
        Plotly.newPlot(timeSeriesChart, data, layout);
    }
    
    // Generate word cloud
    function generateWordCloud() {
        // Clear previous word cloud if any
        const wordcloudImage = document.getElementById('wordcloud-image');
        const commonWordsList = document.getElementById('common-words-list');
        
        if (!currentResults) {
            wordcloudImage.src = '';
            wordcloudImage.alt = 'No data available';
            commonWordsList.innerHTML = '<p class="no-data">No data available</p>';
            return;
        }
        
        // Show loading state
        wordcloudImage.classList.remove('loaded', 'error');
        wordcloudImage.src = '';
        wordcloudImage.alt = 'Loading word cloud...';
        commonWordsList.innerHTML = '<p class="loading">Analyzing keywords and generating word cloud...</p>';
        
        // Build the URL with parameters based on current mode
        let wordCloudUrl = '/word-cloud?';
        let keywordsUrl = '/keywords?';
        
        if (currentMode === 'company') {
            const symbol = currentResults.symbol;
            const days = currentResults.date_range ? 
                Math.ceil((new Date(currentResults.date_range.to) - new Date(currentResults.date_range.from)) / (1000 * 60 * 60 * 24)) : 7;
                
            wordCloudUrl += `symbol=${symbol}&days=${days}`;
            keywordsUrl += `symbol=${symbol}&days=${days}`;
        } else {
            const category = currentResults.category;
            wordCloudUrl += `category=${category}`;
            keywordsUrl += `category=${category}`;
        }
        
        // Generate a unique cache-busting parameter to prevent browser caching
        const cacheBuster = new Date().getTime();
        wordCloudUrl += `&_=${cacheBuster}`;
        
        // Set the image source to the word cloud endpoint
        wordcloudImage.src = wordCloudUrl;
        wordcloudImage.alt = currentMode === 'company' ? 
            `Word Cloud for ${currentResults.symbol} News` : 
            `Word Cloud for ${currentResults.category} Market News`;
            
        // Add loading animation
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'word-cloud-loading';
        loadingOverlay.innerHTML = '<div class="spinner"></div><p>Generating visualization...</p>';
        
        const container = document.querySelector('.wordcloud-container');
        container.appendChild(loadingOverlay);
            
        // Fetch the top keywords
        fetch(keywordsUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    commonWordsList.innerHTML = `<p class="error">${data.error}</p>`;
                    return;
                }
                
                if (!data.keywords || data.keywords.length === 0) {
                    commonWordsList.innerHTML = '<p class="no-data">No significant keywords found</p>';
                    return;
                }
                
                // Create keyword list with scaled font sizes
                const keywords = data.keywords;
                const maxCount = keywords[0].count;
                const minCount = keywords[keywords.length - 1].count;
                const fontRange = [1, 2.5]; // min and max em sizes
                
                let html = '<ul class="keyword-list">';
                
                keywords.forEach((keyword, index) => {
                    // Calculate font size based on count (linear scaling)
                    const scaleFactor = maxCount === minCount ? 
                        1 : (keyword.count - minCount) / (maxCount - minCount);
                    const fontSize = fontRange[0] + scaleFactor * (fontRange[1] - fontRange[0]);
                    
                    html += `
                        <li style="font-size: ${fontSize}em;">
                            <span class="keyword-text">${keyword.word}</span>
                            <span class="keyword-count">${keyword.count}</span>
                        </li>
                    `;
                });
                
                html += '</ul>';
                commonWordsList.innerHTML = html;
            })
            .catch(error => {
                commonWordsList.innerHTML = `<p class="error">Error loading keywords: ${error.message}</p>`;
            });
            
        // Handle image loading events
        wordcloudImage.onload = function() {
            // Remove loading overlay once image is loaded
            container.removeChild(loadingOverlay);
            wordcloudImage.classList.add('loaded');
            
            // Add a click handler to open the image in a larger view
            wordcloudImage.onclick = function() {
                const modal = document.createElement('div');
                modal.className = 'modal';
                modal.innerHTML = `
                    <div class="modal-content">
                        <span class="close-modal">&times;</span>
                        <img src="${wordCloudUrl}" alt="Word Cloud (Full Size)" class="modal-image">
                    </div>
                `;
                document.body.appendChild(modal);
                
                // Handle close button
                modal.querySelector('.close-modal').onclick = function() {
                    document.body.removeChild(modal);
                };
                
                // Close on click outside
                modal.onclick = function(e) {
                    if (e.target === modal) {
                        document.body.removeChild(modal);
                    }
                };
            };
        };
            
        // Handle image loading errors
        wordcloudImage.onerror = function() {
            // Remove loading overlay on error
            if (container.contains(loadingOverlay)) {
                container.removeChild(loadingOverlay);
            }
            
            wordcloudImage.alt = 'Error loading word cloud';
            wordcloudImage.classList.add('error');
            
            // Add error message to image container
            const errorMsg = document.createElement('p');
            errorMsg.className = 'error-message';
            errorMsg.textContent = 'Failed to load word cloud. Please try again.';
            container.appendChild(errorMsg);
        };
    }
    
    // Display news
    function displayNews(data, filter) {
        if (!data || !data.news || !Array.isArray(data.news)) {
            newsContainer.innerHTML = '<p class="no-news">No news data available</p>';
            return;
        }
        
        let newsList = data.news;
        
        // Apply filter
        if (filter !== 'all') {
            newsList = newsList.filter(item => {
                const sentiment = item.sentiment || {};
                return sentiment.label === filter;
            });
        }
        
        // If no news items match the filter
        if (newsList.length === 0) {
            newsContainer.innerHTML = `<p class="no-news">No ${filter} news found</p>`;
            return;
        }
        
        // Sort news by datetime (newest first)
        newsList.sort((a, b) => (b.datetime || 0) - (a.datetime || 0));
        
        // Build HTML
        let html = '';
        
        newsList.forEach(item => {
            const sentiment = item.sentiment || {};
            const sentimentLabel = sentiment.label || 'neutral';
            const sentimentScore = sentiment.score !== undefined ? sentiment.score.toFixed(2) : '0.00';
            const dateObj = item.datetime ? new Date(item.datetime * 1000) : null;
            const formattedDate = dateObj ? dateObj.toLocaleDateString() : 'Unknown date';
            const keywords = sentiment.keywords || [];
            
            html += `
                <div class="news-item ${sentimentLabel}">
                    <div class="news-sentiment">
                        <span class="sentiment-label ${sentimentLabel}">${sentimentLabel}</span>
                        <span class="sentiment-score">${sentimentScore}</span>
                    </div>
                    <div class="news-content">
                        <h3 class="news-headline">${item.headline || 'No headline'}</h3>
                        <p class="news-summary">${item.summary || 'No summary available'}</p>
                        <div class="news-meta">
                            <span class="news-source">${item.source || 'Unknown source'}</span>
                            <span class="news-date">${formattedDate}</span>
                        </div>
                        ${keywords.length > 0 ? `
                        <div class="news-keywords">
                            <span>Keywords: </span>
                            ${keywords.map(keyword => `<span class="keyword">${keyword}</span>`).join('')}
                        </div>
                        ` : ''}
                        ${item.url ? `<a href="${item.url}" target="_blank" class="news-link">Read full article</a>` : ''}
                    </div>
                </div>
            `;
        });
        
        // Update container
        newsContainer.innerHTML = html;
    }
    
    // Show loading indicator
    function showLoading() {
        loadingIndicator.style.display = 'flex';
    }
    
    // Hide loading indicator
    function hideLoading() {
        loadingIndicator.style.display = 'none';
    }
    
    // Show error
    function showError(message) {
        alert('Error: ' + message);
    }
    
    // Show error message on dashboard
    function showDashboardError(message) {
        // First show the general error
        showError(message);
        
        // Then update the overview section with the error
        overviewText.innerHTML = `
            <h2>Error</h2>
            <p class="error-message">${message}</p>
            <p>Please try again or check your configuration.</p>
        `;
        
        // Reset sentiment cards
        document.querySelector('#positive-card .percentage').textContent = '-';
        document.querySelector('#negative-card .percentage').textContent = '-';
        document.querySelector('#neutral-card .percentage').textContent = '-';
        document.querySelector('#score-card .percentage').textContent = '-';
        
        // Clear charts
        Plotly.purge(sentimentOverviewChart);
        Plotly.purge(sentimentPieChart);
        Plotly.purge(timeSeriesChart);
        
        // Clear news
        newsContainer.innerHTML = `<p class="no-news error-message">${message}</p>`;
    }
    
    // Check if we have a demo message in the URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('demo')) {
        analyzeCompanyNews('AAPL', 7);
    }
}); 
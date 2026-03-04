"""
RSS News Fetcher - Free news aggregation via RSS feeds
No API keys required, no rate limits
"""

import feedparser
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import re

logger = logging.getLogger(__name__)


class RSSNewsFetcher:
    """Fetch news from RSS feeds - completely free, no API keys"""
    
    def __init__(self, feeds: List[str] = None):
        """
        Initialize RSS news fetcher
        
        Args:
            feeds: List of RSS feed URLs
        """
        self.feeds = feeds or self._get_default_feeds()
        
    def _get_default_feeds(self) -> List[str]:
        """Get default RSS feeds covering major news sources"""
        return [
            # General news
            "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "https://feeds.bbci.co.uk/news/rss.xml",
            "https://www.reddit.com/r/worldnews/.rss",
            
            # Crypto/Finance
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://cointelegraph.com/rss",
            "https://www.reddit.com/r/CryptoCurrency/.rss",
            
            # Politics
            "https://www.politico.com/rss/politics08.xml",
            "https://www.reddit.com/r/politics/.rss",
            
            # Technology
            "https://www.reddit.com/r/technology/.rss",
            "https://techcrunch.com/feed/",
        ]
    
    def fetch_news(self, query: str, limit: int = 10, days_back: int = 7) -> List[Dict]:
        """
        Fetch news articles matching query from RSS feeds
        
        Args:
            query: Search query (keywords)
            limit: Maximum number of articles to return
            days_back: Only include articles from last N days
            
        Returns:
            List of news articles with title, summary, url, published, source
        """
        logger.info(f"📰 Fetching RSS news for query: '{query}'")
        
        articles = []
        query_lower = query.lower()
        query_keywords = set(re.findall(r'\w+', query_lower))
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Check if article is recent enough
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                        if pub_date < cutoff_date:
                            continue
                    
                    # Check if query matches title or summary
                    title = entry.get('title', '').lower()
                    summary = entry.get('summary', entry.get('description', '')).lower()
                    
                    # Calculate relevance score
                    title_keywords = set(re.findall(r'\w+', title))
                    summary_keywords = set(re.findall(r'\w+', summary))
                    
                    matching_keywords = query_keywords & (title_keywords | summary_keywords)
                    relevance = len(matching_keywords) / len(query_keywords) if query_keywords else 0
                    
                    # Only include if at least one keyword matches
                    if relevance > 0:
                        articles.append({
                            'title': entry.get('title', 'No title'),
                            'summary': entry.get('summary', entry.get('description', 'No summary'))[:500],
                            'url': entry.get('link', ''),
                            'published': entry.get('published', 'Unknown'),
                            'source': feed.feed.get('title', 'RSS Feed'),
                            'relevance': relevance
                        })
                        
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse RSS feed {feed_url}: {e}")
                continue
        
        # Sort by relevance, then by recency
        articles.sort(key=lambda x: x['relevance'], reverse=True)
        
        logger.info(f"📰 Found {len(articles)} relevant articles from RSS feeds")
        
        return articles[:limit]
    
    def add_feed(self, feed_url: str):
        """Add a new RSS feed"""
        if feed_url not in self.feeds:
            self.feeds.append(feed_url)
            logger.info(f"✅ Added RSS feed: {feed_url}")
    
    def remove_feed(self, feed_url: str):
        """Remove an RSS feed"""
        if feed_url in self.feeds:
            self.feeds.remove(feed_url)
            logger.info(f"🗑️ Removed RSS feed: {feed_url}")

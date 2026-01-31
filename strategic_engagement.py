#!/usr/bin/env python3
"""
Strategic Engagement System for AlleyBot
Determines optimal engagement patterns and timing
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

class StrategicEngagement:
    """Intelligent engagement strategy and timing"""
    
    def __init__(self):
        self.analytics_file = Path('memory/engagement_analytics.json')
        self.analytics = self._load_analytics()
    
    def _load_analytics(self):
        """Load engagement analytics"""
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r') as f:
                return json.load(f)
        
        return {
            'best_times': {},  # Hour of day -> success rate
            'best_topics': {},  # Topic -> engagement score
            'successful_patterns': [],
            'failed_patterns': [],
            'response_rates': {
                'new_bots': 0,
                'claimed_bots': 0,
                'crypto_posts': 0,
                'tech_posts': 0
            },
            'optimal_comment_length': {'min': 100, 'max': 200},
            'engagement_by_submolt': {}
        }
    
    def save(self):
        """Save analytics"""
        self.analytics_file.parent.mkdir(exist_ok=True)
        with open(self.analytics_file, 'w') as f:
            json.dump(self.analytics, f, indent=2)
    
    def track_engagement_result(self, post_data, comment_data, result):
        """Track engagement outcome to learn patterns"""
        hour = str(datetime.now().hour)  # Convert to string for JSON compatibility
        
        # Track time-based success
        if hour not in self.analytics['best_times']:
            self.analytics['best_times'][hour] = {'attempts': 0, 'successes': 0}
        
        self.analytics['best_times'][hour]['attempts'] += 1
        if result.get('success'):
            self.analytics['best_times'][hour]['successes'] += 1
        
        # Track topic success
        topics = self._extract_topics(post_data.get('title', '') + ' ' + post_data.get('content', ''))
        for topic in topics:
            if topic not in self.analytics['best_topics']:
                self.analytics['best_topics'][topic] = {'score': 0, 'count': 0}
            
            self.analytics['best_topics'][topic]['count'] += 1
            if result.get('success'):
                self.analytics['best_topics'][topic]['score'] += 1
        
        # Track submolt performance
        submolt_data = post_data.get('submolt', 'general')
        # Handle both string and dict formats
        if isinstance(submolt_data, dict):
            submolt = submolt_data.get('name', 'general')
        else:
            submolt = submolt_data if submolt_data else 'general'
        
        if submolt not in self.analytics['engagement_by_submolt']:
            self.analytics['engagement_by_submolt'][submolt] = {'attempts': 0, 'successes': 0}
        
        self.analytics['engagement_by_submolt'][submolt]['attempts'] += 1
        if result.get('success'):
            self.analytics['engagement_by_submolt'][submolt]['successes'] += 1
        
        self.save()
    
    def _extract_topics(self, text):
        """Extract topics from text"""
        topics = []
        keywords = {
            'crypto': ['crypto', 'bitcoin', 'btc', 'eth', 'ethereum', 'sol', 'solana'],
            'ai': ['ai', 'agent', 'gpt', 'llm', 'machine learning'],
            'coding': ['code', 'python', 'javascript', 'programming', 'dev'],
            'trading': ['trading', 'defi', 'dex', 'swap'],
            'nft': ['nft', 'collectible', 'art'],
            'dao': ['dao', 'governance', 'voting']
        }
        
        text_lower = text.lower()
        for topic, keywords_list in keywords.items():
            if any(kw in text_lower for kw in keywords_list):
                topics.append(topic)
        
        return topics
    
    def get_best_engagement_time(self):
        """Get optimal time to engage based on past success"""
        if not self.analytics['best_times']:
            return None
        
        # Calculate success rate for each hour
        success_rates = {}
        for hour, data in self.analytics['best_times'].items():
            if data['attempts'] > 0:
                success_rates[hour] = data['successes'] / data['attempts']
        
        if not success_rates:
            return None
        
        best_hour = max(success_rates, key=success_rates.get)
        return int(best_hour)
    
    def get_priority_topics(self):
        """Get topics that generate best engagement"""
        if not self.analytics['best_topics']:
            return []
        
        # Sort topics by success rate
        topic_scores = []
        for topic, data in self.analytics['best_topics'].items():
            if data['count'] > 0:
                score = data['score'] / data['count']
                topic_scores.append((topic, score))
        
        topic_scores.sort(key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in topic_scores[:5]]
    
    def should_engage_with_post(self, post_data, relationship_strength=0):
        """Determine if we should engage with this post"""
        # Always engage with new bots
        if self._is_new_bot(post_data):
            return True, 100
        
        # Calculate engagement score
        score = 0
        
        # Topic relevance
        topics = self._extract_topics(post_data.get('title', '') + ' ' + post_data.get('content', ''))
        priority_topics = self.get_priority_topics()
        for topic in topics:
            if topic in priority_topics:
                score += 20
        
        # Relationship strength bonus
        score += relationship_strength * 0.3
        
        # Submolt performance
        submolt_obj = post_data.get('submolt', 'general')
        # Handle both string and dict formats
        if isinstance(submolt_obj, dict):
            submolt = submolt_obj.get('name', 'general')
        else:
            submolt = submolt_obj if submolt_obj else 'general'
        
        if submolt in self.analytics['engagement_by_submolt']:
            submolt_data = self.analytics['engagement_by_submolt'][submolt]
            if submolt_data['attempts'] > 0:
                success_rate = submolt_data['successes'] / submolt_data['attempts']
                score += success_rate * 30
        
        # Post freshness (prefer recent posts)
        created_at = post_data.get('created_at')
        if created_at:
            try:
                post_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                hours_old = (datetime.now() - post_time.replace(tzinfo=None)).total_seconds() / 3600
                if hours_old < 1:
                    score += 20
                elif hours_old < 6:
                    score += 10
            except:
                pass
        
        # Engage if score is high enough
        return score >= 40, score
    
    def _is_new_bot(self, post_data):
        """Detect if this is a new bot introduction"""
        title = post_data.get('title', '').lower()
        content = post_data.get('content', '').lower()
        
        new_bot_indicators = [
            'hello moltbook', 'hi moltbook', 'just hatched', 'first post',
            'new bot', 'new agent', 'introducing', 'meet me'
        ]
        
        return any(indicator in title or indicator in content for indicator in new_bot_indicators)
    
    def get_optimal_comment_length(self):
        """Get optimal comment length based on past success"""
        return self.analytics['optimal_comment_length']
    
    def learn_from_response(self, comment_length, got_response):
        """Learn optimal comment length from responses"""
        if got_response:
            # Adjust optimal range toward this length
            current_min = self.analytics['optimal_comment_length']['min']
            current_max = self.analytics['optimal_comment_length']['max']
            
            if comment_length < current_min:
                self.analytics['optimal_comment_length']['min'] = (current_min + comment_length) // 2
            elif comment_length > current_max:
                self.analytics['optimal_comment_length']['max'] = (current_max + comment_length) // 2
            
            self.save()
    
    def get_engagement_insights(self):
        """Get insights about engagement patterns"""
        insights = []
        
        # Best time
        best_time = self.get_best_engagement_time()
        if best_time:
            insights.append(f"Best engagement time: {best_time}:00")
        
        # Best topics
        priority_topics = self.get_priority_topics()
        if priority_topics:
            insights.append(f"High-performing topics: {', '.join(priority_topics)}")
        
        # Best submolts
        best_submolts = []
        for submolt, data in self.analytics['engagement_by_submolt'].items():
            if data['attempts'] > 3:
                success_rate = data['successes'] / data['attempts']
                if success_rate > 0.5:
                    best_submolts.append((submolt, success_rate))
        
        if best_submolts:
            best_submolts.sort(key=lambda x: x[1], reverse=True)
            top_submolt = best_submolts[0][0]
            insights.append(f"Best submolt: m/{top_submolt}")
        
        return insights

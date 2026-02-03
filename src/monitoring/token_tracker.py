"""
Token Usage Tracker for LLM APIs
Tracks token usage for DeepSeek and Grok APIs with daily aggregation
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict


class TokenTracker:
    """Track and monitor LLM API token usage"""
    
    def __init__(self, storage_dir: str = "data/token_usage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session tracking
        self.session_usage = {
            'deepseek': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0, 'requests': 0},
            'grok': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0, 'requests': 0}
        }
        
        # Load today's usage
        self.today_file = self._get_today_file()
        self.daily_usage = self._load_daily_usage()
    
    def _get_today_file(self) -> Path:
        """Get the file path for today's usage data"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.storage_dir / f"usage_{today}.json"
    
    def _load_daily_usage(self) -> Dict:
        """Load today's usage data from file"""
        if self.today_file.exists():
            with open(self.today_file, 'r') as f:
                return json.load(f)
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'deepseek': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0, 'requests': 0},
            'grok': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0, 'requests': 0}
        }
    
    def _save_daily_usage(self):
        """Save daily usage to file"""
        with open(self.today_file, 'w') as f:
            json.dump(self.daily_usage, f, indent=2)
    
    def track_usage(self, provider: str, prompt_tokens: int, completion_tokens: int):
        """
        Track token usage for an API call
        
        Args:
            provider: 'deepseek' or 'grok'
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
        """
        provider = provider.lower()
        if provider not in ['deepseek', 'grok']:
            print(f"⚠️  Unknown provider: {provider}")
            return
        
        total_tokens = prompt_tokens + completion_tokens
        
        # Update session usage
        self.session_usage[provider]['prompt_tokens'] += prompt_tokens
        self.session_usage[provider]['completion_tokens'] += completion_tokens
        self.session_usage[provider]['total_tokens'] += total_tokens
        self.session_usage[provider]['requests'] += 1
        
        # Update daily usage
        self.daily_usage[provider]['prompt_tokens'] += prompt_tokens
        self.daily_usage[provider]['completion_tokens'] += completion_tokens
        self.daily_usage[provider]['total_tokens'] += total_tokens
        self.daily_usage[provider]['requests'] += 1
        
        # Save to disk
        self._save_daily_usage()
        
        print(f"📊 Token usage tracked: {provider} - {total_tokens} tokens ({prompt_tokens} prompt + {completion_tokens} completion)")
    
    def get_session_stats(self) -> Dict:
        """Get token usage stats for current session"""
        return {
            'session': self.session_usage,
            'total_session_tokens': sum(p['total_tokens'] for p in self.session_usage.values()),
            'total_session_requests': sum(p['requests'] for p in self.session_usage.values())
        }
    
    def get_daily_stats(self) -> Dict:
        """Get token usage stats for today"""
        return {
            'date': self.daily_usage['date'],
            'usage': {
                'deepseek': self.daily_usage['deepseek'],
                'grok': self.daily_usage['grok']
            },
            'total_tokens': self.daily_usage['deepseek']['total_tokens'] + self.daily_usage['grok']['total_tokens'],
            'total_requests': self.daily_usage['deepseek']['requests'] + self.daily_usage['grok']['requests']
        }
    
    def get_weekly_stats(self) -> Dict:
        """Get token usage stats for the past 7 days"""
        weekly_data = defaultdict(lambda: {
            'deepseek': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0, 'requests': 0},
            'grok': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0, 'requests': 0}
        })
        
        # Load last 7 days of data
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            file_path = self.storage_dir / f"usage_{date}.json"
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    weekly_data[date] = {
                        'deepseek': data.get('deepseek', {}),
                        'grok': data.get('grok', {})
                    }
        
        # Calculate totals
        total_tokens = 0
        total_requests = 0
        for date_data in weekly_data.values():
            total_tokens += date_data['deepseek'].get('total_tokens', 0)
            total_tokens += date_data['grok'].get('total_tokens', 0)
            total_requests += date_data['deepseek'].get('requests', 0)
            total_requests += date_data['grok'].get('requests', 0)
        
        return {
            'period': 'last_7_days',
            'daily_breakdown': dict(weekly_data),
            'total_tokens': total_tokens,
            'total_requests': total_requests,
            'average_tokens_per_day': total_tokens / 7 if total_tokens > 0 else 0
        }
    
    def get_monthly_stats(self) -> Dict:
        """Get token usage stats for current month"""
        current_month = datetime.now().strftime('%Y-%m')
        monthly_data = {
            'deepseek': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0, 'requests': 0},
            'grok': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0, 'requests': 0}
        }
        
        # Load all files from current month
        for file_path in self.storage_dir.glob(f"usage_{current_month}-*.json"):
            with open(file_path, 'r') as f:
                data = json.load(f)
                for provider in ['deepseek', 'grok']:
                    if provider in data:
                        monthly_data[provider]['prompt_tokens'] += data[provider].get('prompt_tokens', 0)
                        monthly_data[provider]['completion_tokens'] += data[provider].get('completion_tokens', 0)
                        monthly_data[provider]['total_tokens'] += data[provider].get('total_tokens', 0)
                        monthly_data[provider]['requests'] += data[provider].get('requests', 0)
        
        return {
            'month': current_month,
            'usage': monthly_data,
            'total_tokens': monthly_data['deepseek']['total_tokens'] + monthly_data['grok']['total_tokens'],
            'total_requests': monthly_data['deepseek']['requests'] + monthly_data['grok']['requests']
        }
    
    def get_cost_estimate(self) -> Dict:
        """
        Estimate costs based on token usage
        Using approximate pricing (update with actual rates)
        """
        # Approximate pricing (per 1M tokens)
        pricing = {
            'deepseek': {
                'prompt': 0.14,  # $0.14 per 1M prompt tokens
                'completion': 0.28  # $0.28 per 1M completion tokens
            },
            'grok': {
                'prompt': 5.00,  # $5.00 per 1M prompt tokens
                'completion': 15.00  # $15.00 per 1M completion tokens
            }
        }
        
        daily = self.get_daily_stats()
        costs = {}
        
        for provider in ['deepseek', 'grok']:
            prompt_cost = (daily['usage'][provider]['prompt_tokens'] / 1_000_000) * pricing[provider]['prompt']
            completion_cost = (daily['usage'][provider]['completion_tokens'] / 1_000_000) * pricing[provider]['completion']
            costs[provider] = {
                'prompt_cost': round(prompt_cost, 4),
                'completion_cost': round(completion_cost, 4),
                'total_cost': round(prompt_cost + completion_cost, 4)
            }
        
        total_cost = sum(c['total_cost'] for c in costs.values())
        
        return {
            'date': daily['date'],
            'costs': costs,
            'total_daily_cost': round(total_cost, 4),
            'estimated_monthly_cost': round(total_cost * 30, 2)
        }
    
    def print_dashboard(self):
        """Print a formatted dashboard of token usage"""
        print("\n" + "="*60)
        print("📊 LLM API TOKEN USAGE DASHBOARD")
        print("="*60)
        
        # Session stats
        session = self.get_session_stats()
        print(f"\n🔄 Current Session:")
        print(f"  Total Tokens: {session['total_session_tokens']:,}")
        print(f"  Total Requests: {session['total_session_requests']}")
        print(f"  DeepSeek: {session['session']['deepseek']['total_tokens']:,} tokens ({session['session']['deepseek']['requests']} requests)")
        print(f"  Grok: {session['session']['grok']['total_tokens']:,} tokens ({session['session']['grok']['requests']} requests)")
        
        # Daily stats
        daily = self.get_daily_stats()
        print(f"\n📅 Today ({daily['date']}):")
        print(f"  Total Tokens: {daily['total_tokens']:,}")
        print(f"  Total Requests: {daily['total_requests']}")
        print(f"  DeepSeek: {daily['usage']['deepseek']['total_tokens']:,} tokens ({daily['usage']['deepseek']['requests']} requests)")
        print(f"  Grok: {daily['usage']['grok']['total_tokens']:,} tokens ({daily['usage']['grok']['requests']} requests)")
        
        # Cost estimate
        costs = self.get_cost_estimate()
        print(f"\n💰 Estimated Costs (Today):")
        print(f"  DeepSeek: ${costs['costs']['deepseek']['total_cost']:.4f}")
        print(f"  Grok: ${costs['costs']['grok']['total_cost']:.4f}")
        print(f"  Total: ${costs['total_daily_cost']:.4f}")
        print(f"  Estimated Monthly: ${costs['estimated_monthly_cost']:.2f}")
        
        # Weekly stats
        weekly = self.get_weekly_stats()
        print(f"\n📈 Last 7 Days:")
        print(f"  Total Tokens: {weekly['total_tokens']:,}")
        print(f"  Average per Day: {int(weekly['average_tokens_per_day']):,}")
        print(f"  Total Requests: {weekly['total_requests']}")
        
        print("\n" + "="*60)

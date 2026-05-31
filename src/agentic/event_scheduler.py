"""
Event-Driven Scheduler for Proactive Agent Behavior
Uses APScheduler to poll for on-chain opportunities and trigger autonomous actions
"""
import os
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger


class OnChainOpportunityDetector:
    """Detect on-chain opportunities from various sources"""
    
    def __init__(self, moltbook_api=None, web3_provider=None):
        self.moltbook_api = moltbook_api
        self.web3_provider = web3_provider
        self.last_check = {}
        self.opportunities = []
        
    def detect_moltbook_opportunities(self) -> List[Dict[str, Any]]:
        """Detect opportunities on Moltbook (new posts, karma changes, etc.)"""
        opportunities = []
        
        try:
            if not self.moltbook_api:
                return opportunities
            
            # Check for new posts in followed submolts
            new_posts = self._check_new_posts()
            if new_posts:
                opportunities.append({
                    'type': 'new_posts',
                    'platform': 'moltbook',
                    'data': new_posts,
                    'priority': 2,
                    'action_suggested': 'engage_with_posts',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Check for karma milestones
            karma_changes = self._check_karma_changes()
            if karma_changes:
                opportunities.append({
                    'type': 'karma_milestone',
                    'platform': 'moltbook',
                    'data': karma_changes,
                    'priority': 1,
                    'action_suggested': 'celebrate_milestone',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Check for mentions/replies
            mentions = self._check_mentions()
            if mentions:
                opportunities.append({
                    'type': 'mentions',
                    'platform': 'moltbook',
                    'data': mentions,
                    'priority': 3,
                    'action_suggested': 'respond_to_mentions',
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            print(f"⚠️  Error detecting Moltbook opportunities: {e}")
        
        return opportunities
    
    def _check_new_posts(self) -> List[Dict]:
        """Check for new posts since last check"""
        try:
            # Get feed from Moltbook
            feed = self.moltbook_api.get_feed(sort='hot', limit=20)
            
            # Filter posts newer than last check
            last_check_time = self.last_check.get('posts', datetime.now() - timedelta(hours=1))
            new_posts = []
            
            # Parse feed and filter
            # TODO: Implement actual feed parsing based on Moltbook API response
            
            self.last_check['posts'] = datetime.now()
            return new_posts
            
        except Exception as e:
            print(f"⚠️  Error checking new posts: {e}")
            return []
    
    def _check_karma_changes(self) -> Optional[Dict]:
        """Check for karma changes"""
        try:
            # Get current karma
            stats = self.moltbook_api.get_stats()
            current_karma = stats.get('karma', 0)
            
            # Compare with last known karma
            last_karma = self.last_check.get('karma', current_karma)
            
            if current_karma > last_karma:
                karma_change = {
                    'previous': last_karma,
                    'current': current_karma,
                    'change': current_karma - last_karma
                }
                self.last_check['karma'] = current_karma
                return karma_change
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error checking karma: {e}")
            return None
    
    def _check_mentions(self) -> List[Dict]:
        """Check for new mentions"""
        try:
            # Get notifications/mentions
            # TODO: Implement based on Moltbook API
            mentions = []
            
            self.last_check['mentions'] = datetime.now()
            return mentions
            
        except Exception as e:
            print(f"⚠️  Error checking mentions: {e}")
            return []
    
    def detect_on_chain_opportunities(self) -> List[Dict[str, Any]]:
        """Detect on-chain opportunities (transactions, events, etc.)"""
        opportunities = []
        
        try:
            if not self.web3_provider:
                return opportunities
            
            w3 = self.web3_provider
            
            # Check wallet balance changes
            wallet_address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')
            if wallet_address:
                balance = w3.eth.get_balance(wallet_address)
                balance_eth = float(w3.from_wei(balance, 'ether'))
                
                last_balance = self.last_check.get('balance', balance_eth)
                
                if balance_eth != last_balance:
                    opportunities.append({
                        'type': 'balance_change',
                        'platform': 'base',
                        'data': {
                            'previous': last_balance,
                            'current': balance_eth,
                            'change': balance_eth - last_balance
                        },
                        'priority': 2,
                        'action_suggested': 'acknowledge_transaction',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    self.last_check['balance'] = balance_eth
            
            # Check for incoming transactions
            # TODO: Implement transaction monitoring
            
        except Exception as e:
            print(f"⚠️  Error detecting on-chain opportunities: {e}")
        
        return opportunities
    
    def get_all_opportunities(self) -> List[Dict[str, Any]]:
        """Get all detected opportunities"""
        all_opportunities = []
        
        # Detect from all sources
        all_opportunities.extend(self.detect_moltbook_opportunities())
        all_opportunities.extend(self.detect_on_chain_opportunities())
        
        # Sort by priority (higher first)
        all_opportunities.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        # Store for later retrieval
        self.opportunities = all_opportunities
        
        return all_opportunities


class ProactiveAgentScheduler:
    """
    Proactive scheduler for autonomous agent behavior
    Polls for opportunities and triggers agent actions
    """
    
    def __init__(self, agent_executor: Callable, opportunity_detector: OnChainOpportunityDetector):
        self.agent_executor = agent_executor
        self.opportunity_detector = opportunity_detector
        self.scheduler = BackgroundScheduler()
        self.job_history = []
        self.enabled = False
        
    def start(self):
        """Start the scheduler"""
        if self.enabled:
            print("⚠️  Scheduler already running")
            return
        
        # Schedule opportunity detection (every 5 minutes)
        self.scheduler.add_job(
            func=self._check_opportunities,
            trigger=IntervalTrigger(minutes=5),
            id='opportunity_check',
            name='Check for on-chain opportunities',
            replace_existing=True
        )
        
        # Schedule proactive engagement (every 30 minutes)
        self.scheduler.add_job(
            func=self._proactive_engagement,
            trigger=IntervalTrigger(minutes=30),
            id='proactive_engagement',
            name='Proactive community engagement',
            replace_existing=True
        )
        
        # Schedule karma building (every 2 hours)
        self.scheduler.add_job(
            func=self._karma_building,
            trigger=IntervalTrigger(hours=2),
            id='karma_building',
            name='Build karma on Moltbook',
            replace_existing=True
        )
        
        # Schedule daily summary (at 6 PM)
        self.scheduler.add_job(
            func=self._daily_summary,
            trigger=CronTrigger(hour=18, minute=0),
            id='daily_summary',
            name='Generate daily summary',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.enabled = True
        print("✅ Proactive agent scheduler started")
        print(f"📅 Active jobs: {len(self.scheduler.get_jobs())}")
        
    def stop(self):
        """Stop the scheduler"""
        if not self.enabled:
            return
        
        self.scheduler.shutdown()
        self.enabled = False
        print("🛑 Proactive agent scheduler stopped")
    
    def _check_opportunities(self):
        """Check for opportunities and trigger agent if found"""
        try:
            print("🔍 Checking for opportunities...")
            
            opportunities = self.opportunity_detector.get_all_opportunities()
            
            if opportunities:
                print(f"✨ Found {len(opportunities)} opportunities")
                
                # Process high-priority opportunities
                for opp in opportunities:
                    if opp.get('priority', 0) >= 3:
                        self._handle_opportunity(opp)
            else:
                print("📭 No new opportunities found")
                
            self._log_job('opportunity_check', True)
            
        except Exception as e:
            print(f"❌ Error checking opportunities: {e}")
            self._log_job('opportunity_check', False, str(e))
    
    def _handle_opportunity(self, opportunity: Dict[str, Any]):
        """Handle a detected opportunity by triggering agent"""
        try:
            opp_type = opportunity.get('type')
            action = opportunity.get('action_suggested')
            data = opportunity.get('data')
            
            print(f"🎯 Handling opportunity: {opp_type}")
            
            # Create task for agent
            task = self._create_task_from_opportunity(opportunity)
            
            # Execute via agent
            result = self.agent_executor(task, on_chain_context=data)
            
            print(f"✅ Opportunity handled: {opp_type}")
            
        except Exception as e:
            print(f"❌ Error handling opportunity: {e}")
    
    def _create_task_from_opportunity(self, opportunity: Dict[str, Any]) -> str:
        """Create an agent task from an opportunity"""
        opp_type = opportunity.get('type')
        action = opportunity.get('action_suggested')
        data = opportunity.get('data')
        
        task_templates = {
            'new_posts': "Engage with new posts on Moltbook. Review the posts and provide thoughtful comments to build karma and community presence.",
            'mentions': "Respond to mentions on Moltbook. Provide helpful and engaging responses to build relationships.",
            'karma_milestone': f"Celebrate reaching a karma milestone on Moltbook. Current karma: {data.get('current', 0)}",
            'balance_change': f"Acknowledge balance change. New balance: {data.get('current', 0)} ETH"
        }
        
        return task_templates.get(opp_type, f"Handle {opp_type} opportunity")
    
    def _proactive_engagement(self):
        """Proactively engage with community"""
        try:
            print("💬 Proactive engagement triggered...")
            
            task = "Proactively engage with the Moltbook community. Browse recent posts, provide valuable comments, and build relationships."
            
            result = self.agent_executor(task)
            
            self._log_job('proactive_engagement', True)
            
        except Exception as e:
            print(f"❌ Proactive engagement error: {e}")
            self._log_job('proactive_engagement', False, str(e))
    
    def _karma_building(self):
        """Execute karma building strategy"""
        try:
            print("⭐ Karma building triggered...")
            
            task = "Execute karma building strategy on Moltbook. Create a high-quality post or engage meaningfully with trending discussions."
            
            result = self.agent_executor(task)
            
            self._log_job('karma_building', True)
            
        except Exception as e:
            print(f"❌ Karma building error: {e}")
            self._log_job('karma_building', False, str(e))
    
    def _daily_summary(self):
        """Generate daily summary"""
        try:
            print("📊 Generating daily summary...")
            
            task = "Generate a daily summary of activities, karma gained, and community engagement on Moltbook."
            
            result = self.agent_executor(task)
            
            self._log_job('daily_summary', True)
            
        except Exception as e:
            print(f"❌ Daily summary error: {e}")
            self._log_job('daily_summary', False, str(e))
    
    def _log_job(self, job_id: str, success: bool, error: str = None):
        """Log job execution"""
        self.job_history.append({
            'job_id': job_id,
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'error': error
        })
        
        # Keep only last 100 entries
        if len(self.job_history) > 100:
            self.job_history = self.job_history[-100:]
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        jobs = self.scheduler.get_jobs()
        
        return {
            'enabled': self.enabled,
            'total_jobs': len(jobs),
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in jobs
            ],
            'recent_executions': self.job_history[-10:]
        }

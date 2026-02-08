"""
Clawbr Deep Integration Mixin for Phase 11
Advanced debate analytics, opponent analysis, and strategic debate management
"""
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict


class ClawbrDeepIntegrationMixin:
    """Mixin for advanced Clawbr debate analytics and strategy"""

    def _init_clawbr_deep_integration(self):
        """Initialize Clawbr deep integration systems"""
        # Debate performance tracking
        self.debate_history: List[Dict] = []
        self.debate_stats_cache: Dict[str, Any] = {}
        
        # Opponent analysis
        self.opponent_profiles: Dict[str, Dict] = {}  # opponent_id -> profile
        self.opponent_debate_styles: Dict[str, Dict] = {}  # opponent_id -> style analysis
        
        # Active debate management
        self.active_debates: Dict[str, Dict] = {}  # slug -> debate info
        self.debate_turn_tracking: Dict[str, Dict] = {}  # slug -> turn info
        
        # Reminder system
        self.last_reminder_check: Optional[str] = None
        self.reminder_interval_minutes: int = 30
        
        # Strategy settings
        self.min_win_probability_threshold: float = 0.35  # Minimum probability to accept debate
        self.max_simultaneous_debates: int = 5
        
        self._load_clawbr_integration_state()

    def _load_clawbr_integration_state(self):
        """Load integration state from memory"""
        try:
            if hasattr(self, 'core') and self.core:
                state = self.core.get_memory('clawbr_deep_integration')
                if state:
                    self.debate_history = state.get('debate_history', [])
                    self.opponent_profiles = state.get('opponent_profiles', {})
                    self.opponent_debate_styles = state.get('opponent_debate_styles', {})
                    self.debate_stats_cache = state.get('debate_stats_cache', {})
        except Exception:
            pass

    def _save_clawbr_integration_state(self):
        """Save integration state to memory"""
        try:
            if hasattr(self, 'core') and self.core:
                self.core.save_memory('clawbr_deep_integration', {
                    'debate_history': self.debate_history[-200:],  # Keep last 200
                    'opponent_profiles': self.opponent_profiles,
                    'opponent_debate_styles': self.opponent_debate_styles,
                    'debate_stats_cache': self.debate_stats_cache,
                    'last_saved': datetime.now().isoformat(),
                })
        except Exception as e:
            print(f"⚠️ Failed to save Clawbr integration state: {e}")

    # =================================================================
    # Debate Performance Analytics
    # =================================================================

    def get_debate_performance_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive debate performance analytics
        
        Returns:
            Dict with win/loss stats, ELO progression, and performance trends
        """
        try:
            # Get current profile data
            profile = self.get_profile()
            if not profile.get('success', True):
                return {'error': 'Failed to get profile'}
            
            agent_data = profile.get('data', profile)
            debate_stats = agent_data.get('debateStats', {})
            
            wins = debate_stats.get('wins', 0)
            losses = debate_stats.get('losses', 0)
            draws = debate_stats.get('draws', 0)
            total = wins + losses + draws
            
            current_elo = debate_stats.get('elo', 1200)
            
            # Calculate derived metrics
            win_rate = wins / total if total > 0 else 0
            
            # ELO progression from history
            elo_history = [d.get('elo_after', current_elo) for d in self.debate_history if d.get('elo_after')]
            elo_change_30d = self._calculate_elo_change_days(30)
            elo_change_7d = self._calculate_elo_change_days(7)
            
            # Performance by category
            category_performance = self._analyze_performance_by_category()
            
            # Streak calculation
            current_streak = self._calculate_current_streak()
            best_streak = self._calculate_best_streak()
            
            analytics = {
                'total_debates': total,
                'wins': wins,
                'losses': losses,
                'draws': draws,
                'win_rate': round(win_rate, 3),
                'current_elo': current_elo,
                'elo_change_7d': elo_change_7d,
                'elo_change_30d': elo_change_30d,
                'current_streak': current_streak,
                'best_streak': best_streak,
                'category_performance': category_performance,
                'avg_debate_length': self._calculate_avg_debate_length(),
                'last_updated': datetime.now().isoformat(),
            }
            
            self.debate_stats_cache = analytics
            return analytics
            
        except Exception as e:
            return {'error': f'Analytics failed: {e}'}

    def _calculate_elo_change_days(self, days: int) -> int:
        """Calculate ELO change over last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()
        
        debates_in_period = [d for d in self.debate_history if d.get('ended_at', '') > cutoff_iso]
        
        if not debates_in_period:
            return 0
        
        # Find ELO at start of period
        elo_start = None
        for debate in reversed(debates_in_period):
            elo = debate.get('elo_before')
            if elo:
                elo_start = elo
                break
        
        # Find most recent ELO
        elo_end = None
        for debate in reversed(self.debate_history):
            elo = debate.get('elo_after')
            if elo:
                elo_end = elo
                break
        
        if elo_start and elo_end:
            return elo_end - elo_start
        return 0

    def _analyze_performance_by_category(self) -> Dict[str, Dict]:
        """Analyze win rate by debate category"""
        category_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
        
        for debate in self.debate_history:
            category = debate.get('category', 'general')
            result = debate.get('result')
            
            if result:
                category_stats[category]['total'] += 1
                if result == 'win':
                    category_stats[category]['wins'] += 1
                elif result == 'loss':
                    category_stats[category]['losses'] += 1
        
        # Calculate win rates
        result = {}
        for cat, stats in category_stats.items():
            total = stats['total']
            result[cat] = {
                'total': total,
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': round(stats['wins'] / total, 3) if total > 0 else 0,
            }
        
        return result

    def _calculate_current_streak(self) -> Dict[str, Any]:
        """Calculate current win/loss streak"""
        if not self.debate_history:
            return {'type': 'none', 'count': 0}
        
        # Sort by end time
        sorted_debates = sorted(
            self.debate_history, 
            key=lambda d: d.get('ended_at', ''), 
            reverse=True
        )
        
        if not sorted_debates:
            return {'type': 'none', 'count': 0}
        
        first_result = sorted_debates[0].get('result')
        if not first_result:
            return {'type': 'none', 'count': 0}
        
        streak_type = first_result
        streak_count = 0
        
        for debate in sorted_debates:
            result = debate.get('result')
            if result == streak_type:
                streak_count += 1
            elif result:
                break
        
        return {'type': streak_type, 'count': streak_count}

    def _calculate_best_streak(self) -> int:
        """Calculate best win streak ever"""
        if not self.debate_history:
            return 0
        
        sorted_debates = sorted(
            self.debate_history, 
            key=lambda d: d.get('ended_at', '')
        )
        
        best_streak = 0
        current_streak = 0
        
        for debate in sorted_debates:
            result = debate.get('result')
            if result == 'win':
                current_streak += 1
                best_streak = max(best_streak, current_streak)
            elif result:
                current_streak = 0
        
        return best_streak

    def _calculate_avg_debate_length(self) -> float:
        """Calculate average number of posts per debate"""
        total_posts = sum(d.get('total_posts', 0) for d in self.debate_history)
        total_debates = len(self.debate_history)
        return round(total_posts / total_debates, 1) if total_debates > 0 else 0

    # =================================================================
    # Opponent Analysis
    # =================================================================

    def analyze_opponent(self, opponent_id: str, opponent_name: str = "") -> Dict[str, Any]:
        """
        Analyze an opponent's debate style and history
        
        Args:
            opponent_id: Clawbr agent ID of opponent
            opponent_name: Display name of opponent
        
        Returns:
            Opponent profile with style analysis
        """
        try:
            # Get debates against this opponent
            opponent_debates = [
                d for d in self.debate_history 
                if d.get('opponent_id') == opponent_id or d.get('opponent_name') == opponent_name
            ]
            
            if not opponent_debates:
                return {'error': f'No debate history with opponent {opponent_name or opponent_id}'}
            
            # Head-to-head stats
            wins = sum(1 for d in opponent_debates if d.get('result') == 'win')
            losses = sum(1 for d in opponent_debates if d.get('result') == 'loss')
            draws = sum(1 for d in opponent_debates if d.get('result') == 'draw')
            
            # Analyze opponent's argument characteristics
            avg_opponent_posts = sum(d.get('opponent_post_count', 0) for d in opponent_debates) / len(opponent_debates)
            avg_opponent_length = sum(d.get('opponent_avg_length', 0) for d in opponent_debates) / len(opponent_debates)
            
            # Style indicators
            style_analysis = {
                'argument_length_tendency': 'long' if avg_opponent_length > 400 else 'short' if avg_opponent_length < 200 else 'medium',
                'activity_level': 'high' if avg_opponent_posts > 4 else 'low' if avg_opponent_posts < 2 else 'medium',
            }
            
            profile = {
                'opponent_id': opponent_id,
                'opponent_name': opponent_name,
                'total_debates': len(opponent_debates),
                'head_to_head': {
                    'wins': wins,
                    'losses': losses,
                    'draws': draws,
                    'win_rate': round(wins / len(opponent_debates), 3),
                },
                'style_analysis': style_analysis,
                'avg_posts_per_debate': round(avg_opponent_posts, 1),
                'avg_argument_length': round(avg_opponent_length, 0),
                'last_debate': max((d.get('ended_at', '') for d in opponent_debates), default=None),
            }
            
            self.opponent_profiles[opponent_id] = profile
            self._save_clawbr_integration_state()
            
            return profile
            
        except Exception as e:
            return {'error': f'Opponent analysis failed: {e}'}

    def get_opponent_insights(self, opponent_id: str) -> List[str]:
        """Get strategic insights about an opponent"""
        profile = self.opponent_profiles.get(opponent_id)
        if not profile:
            return []
        
        insights = []
        style = profile.get('style_analysis', {})
        h2h = profile.get('head_to_head', {})
        
        # Style-based insights
        if style.get('argument_length_tendency') == 'long':
            insights.append("Opponent writes long arguments - counter with concise, punchy points")
        elif style.get('argument_length_tendency') == 'short':
            insights.append("Opponent keeps arguments brief - overwhelm with detailed analysis")
        
        # Win rate insights
        win_rate = h2h.get('win_rate', 0)
        if win_rate > 0.7:
            insights.append("You've dominated this opponent historically")
        elif win_rate < 0.3:
            insights.append("This opponent has your number - consider avoiding or changing strategy")
        
        return insights

    # =================================================================
    # Strategic Debate Selection
    # =================================================================

    def calculate_debate_probability(self, topic: str, category: str,
                                    opponent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate win probability for a potential debate
        
        Args:
            topic: Debate topic
            category: Debate category
            opponent_id: Optional opponent to face
        
        Returns:
            Win probability and confidence factors
        """
        try:
            factors = {}
            score = 50  # Base 50% chance
            
            # Category advantage
            category_perf = self.debate_stats_cache.get('category_performance', {}).get(category, {})
            cat_win_rate = category_perf.get('win_rate', 0.5)
            factors['category_advantage'] = (cat_win_rate - 0.5) * 20
            score += factors['category_advantage']
            
            # Streak factor
            streak = self.debate_stats_cache.get('current_streak', {})
            if streak.get('type') == 'win':
                streak_bonus = min(streak.get('count', 0) * 2, 10)
                factors['momentum'] = streak_bonus
                score += streak_bonus
            elif streak.get('type') == 'loss':
                streak_penalty = -min(streak.get('count', 0) * 3, 15)
                factors['slump'] = streak_penalty
                score += streak_penalty
            
            # Opponent-specific factor
            if opponent_id and opponent_id in self.opponent_profiles:
                opp_profile = self.opponent_profiles[opponent_id]
                h2h = opp_profile.get('head_to_head', {})
                h2h_win_rate = h2h.get('win_rate', 0.5)
                h2h_factor = (h2h_win_rate - 0.5) * 25
                factors['opponent_history'] = h2h_factor
                score += h2h_factor
            
            # Clamp to valid range
            probability = max(0.05, min(0.95, score / 100))
            
            return {
                'win_probability': round(probability, 3),
                'recommendation': 'accept' if probability >= self.min_win_probability_threshold else 'decline',
                'confidence': 'high' if abs(probability - 0.5) > 0.2 else 'medium' if abs(probability - 0.5) > 0.1 else 'low',
                'factors': factors,
                'explanation': self._generate_probability_explanation(factors),
            }
            
        except Exception as e:
            return {'error': f'Probability calculation failed: {e}'}

    def _generate_probability_explanation(self, factors: Dict[str, float]) -> str:
        """Generate human-readable explanation of probability factors"""
        parts = []
        
        if 'category_advantage' in factors:
            val = factors['category_advantage']
            parts.append(f"Category {'strength' if val > 0 else 'weakness'} ({val:+.1f}%)")
        
        if 'momentum' in factors:
            parts.append(f"Win streak momentum (+{factors['momentum']:.1f}%)")
        
        if 'slump' in factors:
            parts.append(f"Recent slump ({factors['slump']:.1f}%)")
        
        if 'opponent_history' in factors:
            val = factors['opponent_history']
            parts.append(f"H2H {'advantage' if val > 0 else 'disadvantage'} ({val:+.1f}%)")
        
        return '; '.join(parts) if parts else 'No significant factors'

    def should_accept_debate_invite(self, debate_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide whether to accept a debate invitation
        
        Args:
            debate_info: Dict with topic, category, opponent info
        
        Returns:
            Decision with reasoning
        """
        # Check if at debate capacity
        my_debates = self.get_my_debates()
        active_count = 0
        if my_debates.get('success'):
            debates = my_debates.get('debates', my_debates.get('data', []))
            active_count = sum(1 for d in debates if d.get('status') == 'active')
        
        if active_count >= self.max_simultaneous_debates:
            return {
                'should_accept': False,
                'reason': f'At maximum simultaneous debates ({self.max_simultaneous_debates})',
                'priority': 'skip',
            }
        
        # Calculate win probability
        topic = debate_info.get('topic', '')
        category = debate_info.get('category', 'general')
        opponent_id = debate_info.get('opponent_id')
        
        probability_result = self.calculate_debate_probability(topic, category, opponent_id)
        
        prob = probability_result.get('win_probability', 0.5)
        
        if prob >= self.min_win_probability_threshold:
            return {
                'should_accept': True,
                'win_probability': prob,
                'reason': f'Win probability {prob:.1%} meets threshold',
                'priority': 'high' if prob > 0.6 else 'medium',
            }
        else:
            return {
                'should_accept': False,
                'win_probability': prob,
                'reason': f'Win probability {prob:.1%} below {self.min_win_probability_threshold:.1%} threshold',
                'priority': 'decline',
            }

    # =================================================================
    # Multi-Debate Management
    # =================================================================

    def refresh_active_debates(self) -> Dict[str, Any]:
        """Refresh the list of active debates we're participating in"""
        try:
            my_debates = self.get_my_debates()
            if not my_debates.get('success', True):
                return {'error': 'Failed to get debates'}
            
            debates = my_debates.get('debates', my_debates.get('data', []))
            
            new_active = {}
            need_attention = []
            
            for debate in debates:
                slug = debate.get('slug')
                if not slug:
                    continue
                
                status = debate.get('status')
                is_my_turn = debate.get('isMyTurn', False)
                
                if status == 'active':
                    new_active[slug] = {
                        'topic': debate.get('topic'),
                        'is_my_turn': is_my_turn,
                        'current_round': debate.get('currentRound', 0),
                        'total_rounds': debate.get('maxRounds', 5),
                        'opponent': debate.get('opponent', {}),
                        'last_updated': datetime.now().isoformat(),
                    }
                    
                    if is_my_turn:
                        need_attention.append({
                            'slug': slug,
                            'topic': debate.get('topic'),
                            'urgency': 'high' if debate.get('hoursRemaining', 24) < 6 else 'medium',
                        })
            
            self.active_debates = new_active
            self._save_clawbr_integration_state()
            
            return {
                'active_count': len(new_active),
                'my_turn_count': len(need_attention),
                'need_attention': need_attention,
                'at_capacity': len(new_active) >= self.max_simultaneous_debates,
            }
            
        except Exception as e:
            return {'error': f'Refresh failed: {e}'}

    def get_debate_turn_summary(self) -> str:
        """Get a summary of debates waiting for our turn"""
        refresh = self.refresh_active_debates()
        
        if refresh.get('error'):
            return f"❌ {refresh['error']}"
        
        need_attention = refresh.get('need_attention', [])
        
        if not need_attention:
            return f"✅ No debates waiting for your turn\n📊 Active debates: {refresh.get('active_count', 0)}/{self.max_simultaneous_debates}"
        
        output = f"🎭 Debates Awaiting Your Response ({len(need_attention)})\n\n"
        
        for debate in need_attention:
            slug = debate['slug']
            topic = debate['topic']
            urgency = debate['urgency']
            emoji = '🔴' if urgency == 'high' else '🟡'
            output += f"{emoji} **{slug}**\n   Topic: {topic[:60]}...\n\n"
        
        output += f"\n📊 Total active: {refresh.get('active_count', 0)}/{self.max_simultaneous_debates}"
        
        return output

    # =================================================================
    # Debate Reminder System
    # =================================================================

    def check_debate_reminders(self) -> List[Dict[str, Any]]:
        """
        Check for debates needing attention and return reminders
        
        Returns:
            List of reminder notifications
        """
        now = datetime.now()
        
        # Check if enough time has passed since last reminder
        if self.last_reminder_check:
            last_check = datetime.fromisoformat(self.last_reminder_check)
            minutes_since = (now - last_check).total_seconds() / 60
            if minutes_since < self.reminder_interval_minutes:
                return []
        
        self.last_reminder_check = now.isoformat()
        
        refresh = self.refresh_active_debates()
        need_attention = refresh.get('need_attention', [])
        
        reminders = []
        
        for debate in need_attention:
            reminders.append({
                'type': 'debate_turn',
                'slug': debate['slug'],
                'topic': debate['topic'],
                'urgency': debate['urgency'],
                'message': f"🎭 Your turn in debate: {debate['slug']}\nTopic: {debate['topic'][:80]}",
            })
        
        return reminders

    def send_debate_reminders(self) -> str:
        """Check and send debate reminders via available channels"""
        reminders = self.check_debate_reminders()
        
        if not reminders:
            return "📭 No debate reminders needed"
        
        # Try to send via Telegram if available
        sent_count = 0
        try:
            telegram = self.core.plugin_manager.plugins.get('telegram')
            if telegram and hasattr(telegram, 'send_message_to_admin'):
                for reminder in reminders:
                    telegram.send_message_to_admin(reminder['message'])
                    sent_count += 1
        except Exception as e:
            print(f"⚠️ Failed to send Telegram reminders: {e}")
        
        # Log to console
        for reminder in reminders:
            print(f"🔔 DEBATE REMINDER: {reminder['message']}")
        
        return f"🔔 {len(reminders)} debate reminder(s) sent ({sent_count} via Telegram)"

    # =================================================================
    # CLI Commands
    # =================================================================

    def clawbr_analytics_command(self, *args) -> str:
        """Show comprehensive debate analytics: /clawbr_analytics [opponent_id]"""
        if args:
            # Show opponent-specific analytics
            opponent_id = args[0]
            profile = self.analyze_opponent(opponent_id)
            
            if 'error' in profile:
                return f"❌ {profile['error']}"
            
            output = f"🎯 **Opponent Analysis: {profile['opponent_name']}**\n\n"
            h2h = profile['head_to_head']
            output += f"**Head-to-Head:** {h2h['wins']}W - {h2h['losses']}L - {h2h['draws']}D\n"
            output += f"**Win Rate vs Opponent:** {h2h['win_rate']:.1%}\n\n"
            
            style = profile['style_analysis']
            output += f"**Opponent Style:**\n"
            output += f"  • Argument length: {style['argument_length_tendency']}\n"
            output += f"  • Activity level: {style['activity_level']}\n"
            output += f"  • Avg posts/debate: {profile['avg_posts_per_debate']}\n\n"
            
            insights = self.get_opponent_insights(opponent_id)
            if insights:
                output += "**Strategic Insights:**\n"
                for insight in insights:
                    output += f"  • {insight}\n"
            
            return output
        
        # Show general analytics
        analytics = self.get_debate_performance_analytics()
        
        if 'error' in analytics:
            return f"❌ {analytics['error']}"
        
        output = "📊 **Clawbr Debate Analytics**\n\n"
        output += f"**Overall Record:** {analytics['wins']}W - {analytics['losses']}L - {analytics['draws']}D\n"
        output += f"**Win Rate:** {analytics['win_rate']:.1%}\n"
        output += f"**Current ELO:** {analytics['current_elo']}\n"
        output += f"**ELO Change (7d):** {analytics['elo_change_7d']:+d}\n"
        output += f"**ELO Change (30d):** {analytics['elo_change_30d']:+d}\n\n"
        
        streak = analytics['current_streak']
        if streak['count'] > 0:
            output += f"**Current Streak:** {streak['count']} {streak['type']}(s)\n"
        output += f"**Best Streak:** {analytics['best_streak']} wins\n\n"
        
        # Category performance
        cat_perf = analytics.get('category_performance', {})
        if cat_perf:
            output += "**Performance by Category:**\n"
            for cat, stats in cat_perf.items():
                output += f"  • {cat}: {stats['win_rate']:.1%} ({stats['wins']}W/{stats['losses']}L)\n"
        
        return output

    def clawbr_strategy_command(self, topic: str = "", category: str = "general", *args) -> str:
        """Analyze win probability for a debate topic: /clawbr_strategy <topic> [category]"""
        if not topic:
            return "Usage: /clawbr_strategy <topic> [category]\nExample: /clawbr_strategy 'AI will surpass human intelligence' technology"
        
        opponent_id = args[0] if args else None
        
        result = self.calculate_debate_probability(topic, category, opponent_id)
        
        if 'error' in result:
            return f"❌ {result['error']}"
        
        output = f"🎯 **Debate Strategy Analysis**\n\n"
        output += f"**Topic:** {topic}\n"
        output += f"**Category:** {category}\n"
        if opponent_id:
            output += f"**Opponent:** {opponent_id}\n"
        output += f"\n**Win Probability:** {result['win_probability']:.1%}\n"
        output += f"**Recommendation:** {result['recommendation'].upper()}\n"
        output += f"**Confidence:** {result['confidence']}\n\n"
        output += f"**Analysis:** {result['explanation']}\n"
        
        return output

    def clawbr_turns_command(self, *args) -> str:
        """Show debates waiting for your turn: /clawbr_turns"""
        return self.get_debate_turn_summary()

    def clawbr_remind_command(self, *args) -> str:
        """Check and send debate reminders: /clawbr_remind"""
        return self.send_debate_reminders()

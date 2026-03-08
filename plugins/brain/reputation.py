"""
Reputation System Mixin for Phase 10
Tracks and optimizes reputation score across platforms
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict


class ReputationSystemMixin:
    """Mixin for tracking and optimizing reputation across platforms"""
    
    # Mixin metadata for documentation and validation
    REQUIRES = ["world_state"]
    PROVIDES = ["get_reputation", "update_reputation", "reputation_score"]
    INIT_ORDER = 11

    def _init_reputation_system(self):
        """Initialize reputation tracking system"""
        self.reputation_scores: Dict[str, Dict] = {}  # platform -> reputation data
        self.platform_metrics: Dict[str, Dict] = {
            'moltx': {
                'followers_weight': 1.0,
                'engagement_weight': 2.0,
                'post_quality_weight': 1.5,
                'consistency_weight': 1.0,
            },
            'clawbr': {
                'elo_weight': 2.0,
                'win_rate_weight': 1.5,
                'debates_weight': 1.0,
                'engagement_weight': 0.5,
            },
        }
        self.reputation_history: List[Dict] = []
        self.optimization_goals: Dict[str, Any] = {
            'target_moltx_score': 80,
            'target_clawbr_elo': 1500,
        }
        self._load_reputation_state()

    def _load_reputation_state(self):
        """Load reputation state from memory"""
        try:
            if hasattr(self, 'core') and self.core:
                state = self.core.get_memory('reputation_system')
                if state:
                    self.reputation_scores = state.get('scores', {})
                    self.reputation_history = state.get('history', [])
                    self.optimization_goals = state.get('goals', self.optimization_goals)
        except Exception:
            pass

    def _save_reputation_state(self):
        """Save reputation state to memory"""
        try:
            if hasattr(self, 'core') and self.core:
                self.core.save_memory('reputation_system', {
                    'scores': self.reputation_scores,
                    'history': self.reputation_history[-200:],
                    'goals': self.optimization_goals,
                    'last_updated': datetime.now().isoformat(),
                })
        except Exception as e:
            print(f"⚠️  Failed to save reputation state: {e}")

    def calculate_reputation_score(self, platform: str) -> Dict[str, Any]:
        """
        Calculate comprehensive reputation score for a platform
        
        Args:
            platform: Platform to calculate score for
        
        Returns:
            Dict with score breakdown and recommendations
        """
        metrics = {}
        
        try:
            if platform == 'moltx':
                metrics = self._calculate_moltx_reputation()
            elif platform == 'clawbr':
                metrics = self._calculate_clawbr_reputation()
            else:
                return {'error': f'Unknown platform: {platform}'}
            
            # Store score
            self.reputation_scores[platform] = {
                'score': metrics.get('overall_score', 0),
                'breakdown': metrics,
                'calculated_at': datetime.now().isoformat(),
            }
            
            # Add to history
            self.reputation_history.append({
                'timestamp': datetime.now().isoformat(),
                'platform': platform,
                'score': metrics.get('overall_score', 0),
            })
            
            self._save_reputation_state()
            
            return metrics
            
        except Exception as e:
            return {'error': f'Failed to calculate reputation: {e}'}

    def _calculate_moltx_reputation(self) -> Dict[str, Any]:
        """Calculate MoltX reputation score"""
        moltx = self.core.plugin_manager.plugins.get('moltx')
        if not moltx:
            return {'error': 'MoltX plugin not available'}
        
        metrics = {}
        
        try:
            # Get follower count
            followers = moltx.get_follower_count() if hasattr(moltx, 'get_follower_count') else 0
            metrics['followers'] = followers
            metrics['followers_score'] = min(followers / 100 * 10, 25)  # Max 25 points
            
            # Get engagement rate
            recent_posts = moltx.get_recent_posts(10) if hasattr(moltx, 'get_recent_posts') else []
            total_engagement = sum(p.get('likes', 0) + p.get('replies', 0) for p in recent_posts)
            avg_engagement = total_engagement / len(recent_posts) if recent_posts else 0
            metrics['avg_engagement'] = avg_engagement
            metrics['engagement_score'] = min(avg_engagement / 5 * 10, 30)  # Max 30 points
            
            # Post quality (based on engagement per post)
            quality_scores = []
            for post in recent_posts:
                engagement = post.get('likes', 0) + post.get('replies', 0)
                quality_scores.append(min(engagement / 10, 10))
            metrics['post_quality'] = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            metrics['quality_score'] = metrics['post_quality'] * 2  # Max 20 points
            
            # Consistency (post frequency)
            post_times = [p.get('created_at') for p in recent_posts if p.get('created_at')]
            if len(post_times) >= 2:
                # Calculate average time between posts
                from datetime import datetime
                times = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in post_times]
                times.sort()
                intervals = [(times[i+1] - times[i]).total_seconds() / 3600 for i in range(len(times)-1)]
                avg_interval = sum(intervals) / len(intervals) if intervals else 24
                # Score based on regularity (lower interval = higher score, but not too low)
                if 4 <= avg_interval <= 24:
                    metrics['consistency_score'] = 25
                elif avg_interval < 4:
                    metrics['consistency_score'] = 15  # Too frequent
                else:
                    metrics['consistency_score'] = max(25 - (avg_interval - 24) / 2, 5)
            else:
                metrics['consistency_score'] = 5
            
            # Calculate overall score
            overall = (
                metrics['followers_score'] +
                metrics['engagement_score'] +
                metrics['quality_score'] +
                metrics['consistency_score']
            )
            metrics['overall_score'] = round(overall, 1)
            metrics['max_possible'] = 100
            
            # Generate recommendations
            metrics['recommendations'] = self._generate_moltx_recommendations(metrics)
            
        except Exception as e:
            metrics['error'] = str(e)
        
        return metrics

    def _calculate_clawbr_reputation(self) -> Dict[str, Any]:
        """Calculate Clawbr reputation score"""
        clawbr = self.core.plugin_manager.plugins.get('clawbr')
        if not clawbr:
            return {'error': 'Clawbr plugin not available'}
        
        metrics = {}
        
        try:
            # ELO rating
            elo = clawbr.get_my_elo() if hasattr(clawbr, 'get_my_elo') else 1200
            metrics['elo'] = elo
            # Score based on ELO (1200 = base, higher is better)
            if elo >= 1500:
                metrics['elo_score'] = 40
            elif elo >= 1400:
                metrics['elo_score'] = 35
            elif elo >= 1300:
                metrics['elo_score'] = 30
            else:
                metrics['elo_score'] = max((elo - 1000) / 500 * 20, 10)
            
            # Win rate
            stats = clawbr.get_debate_stats() if hasattr(clawbr, 'get_debate_stats') else {}
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            total = wins + losses
            
            if total > 0:
                win_rate = wins / total
                metrics['win_rate'] = round(win_rate, 2)
                metrics['win_rate_score'] = win_rate * 30  # Max 30 points
            else:
                metrics['win_rate'] = 0
                metrics['win_rate_score'] = 0
            
            metrics['total_debates'] = total
            metrics['wins'] = wins
            metrics['losses'] = losses
            
            # Debate activity
            metrics['debates_score'] = min(total * 2, 20)  # Max 20 points
            
            # Engagement (votes received on debates)
            votes_received = stats.get('total_votes_received', 0)
            metrics['votes_received'] = votes_received
            metrics['engagement_score'] = min(votes_received / 10, 10)  # Max 10 points
            
            # Overall score
            overall = (
                metrics['elo_score'] +
                metrics['win_rate_score'] +
                metrics['debates_score'] +
                metrics['engagement_score']
            )
            metrics['overall_score'] = round(overall, 1)
            metrics['max_possible'] = 100
            
            # Recommendations
            metrics['recommendations'] = self._generate_clawbr_recommendations(metrics)
            
        except Exception as e:
            metrics['error'] = str(e)
        
        return metrics

    def _generate_moltx_recommendations(self, metrics: Dict) -> List[str]:
        """Generate recommendations for improving MoltX reputation"""
        recs = []
        
        if metrics.get('followers_score', 0) < 15:
            recs.append("Increase followers by engaging with other users' content")
        
        if metrics.get('engagement_score', 0) < 20:
            recs.append("Post more engaging content - ask questions, share insights")
        
        if metrics.get('quality_score', 0) < 15:
            recs.append("Focus on post quality over quantity - aim for 5+ likes per post")
        
        if metrics.get('consistency_score', 0) < 20:
            recs.append("Post consistently - aim for 2-4 posts per day")
        
        return recs

    def _generate_clawbr_recommendations(self, metrics: Dict) -> List[str]:
        """Generate recommendations for improving Clawbr reputation"""
        recs = []
        
        if metrics.get('elo_score', 0) < 30:
            recs.append("Choose debates strategically - pick topics you know well")
        
        if metrics.get('win_rate_score', 0) < 20:
            recs.append("Study debate techniques and prepare stronger arguments")
        
        if metrics.get('debates_score', 0) < 15:
            recs.append("Participate in more debates to build experience")
        
        if metrics.get('engagement_score', 0) < 7:
            recs.append("Create debates on trending topics to get more votes")
        
        return recs

    def get_overall_reputation(self) -> Dict[str, Any]:
        """Get overall reputation across all platforms"""
        platforms = ['moltx', 'clawbr']
        scores = {}
        
        for platform in platforms:
            if platform in self.reputation_scores:
                scores[platform] = self.reputation_scores[platform]
            else:
                # Calculate if not cached
                scores[platform] = self.calculate_reputation_score(platform)
        
        # Calculate weighted average
        weights = {'moltx': 0.55, 'clawbr': 0.45}
        total_score = 0
        total_weight = 0
        
        for platform, score_data in scores.items():
            if 'overall_score' in score_data:
                weight = weights.get(platform, 0.33)
                total_score += score_data['overall_score'] * weight
                total_weight += weight
        
        overall = round(total_score / total_weight, 1) if total_weight > 0 else 0
        
        return {
            'overall_reputation': overall,
            'platform_scores': scores,
            'tier': self._get_reputation_tier(overall),
            'last_updated': datetime.now().isoformat(),
        }

    def _get_reputation_tier(self, score: float) -> str:
        """Get reputation tier based on score"""
        if score >= 80:
            return "🏆 Legendary"
        elif score >= 65:
            return "🌟 Established"
        elif score >= 50:
            return "⭐ Rising"
        elif score >= 35:
            return "📈 Growing"
        else:
            return "🌱 Newcomer"

    def get_reputation_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get reputation trends over time"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()
        
        recent_history = [
            h for h in self.reputation_history
            if h.get('timestamp', '') > cutoff_iso
        ]
        
        trends = defaultdict(list)
        for entry in recent_history:
            platform = entry.get('platform')
            if platform:
                trends[platform].append({
                    'timestamp': entry.get('timestamp'),
                    'score': entry.get('score', 0),
                })
        
        # Calculate trends
        trend_analysis = {}
        for platform, history in trends.items():
            if len(history) >= 2:
                first = history[0]['score']
                last = history[-1]['score']
                change = last - first
                trend_analysis[platform] = {
                    'change': round(change, 1),
                    'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable',
                    'data_points': len(history),
                }
        
        return {
            'period_days': days,
            'trends': trend_analysis,
            'raw_data': dict(trends),
        }

    # CLI Commands
    def reputation_check_command(self, *args) -> str:
        """Check reputation scores: reputation [platform]"""
        platform = args[0] if args else None
        
        if platform:
            result = self.calculate_reputation_score(platform)
            
            if 'error' in result:
                return f"❌ {result['error']}"
            
            output = f"📊 {platform.upper()} Reputation: {result['overall_score']}/{result['max_possible']}\n\n"
            
            output += "Breakdown:\n"
            for key, value in result.items():
                if 'score' in key and key != 'overall_score' and key != 'max_possible':
                    output += f"  • {key.replace('_', ' ').title()}: {round(value, 1)}\n"
            
            if result.get('recommendations'):
                output += "\n💡 Recommendations:\n"
                for rec in result['recommendations']:
                    output += f"  • {rec}\n"
            
            return output
        else:
            # Show overall
            overall = self.get_overall_reputation()
            
            output = f"🌟 Overall Reputation: {overall['overall_reputation']}\n"
            output += f"Tier: {overall['tier']}\n\n"
            
            output += "Platform Scores:\n"
            for platform, score_data in overall['platform_scores'].items():
                if 'overall_score' in score_data:
                    score = score_data['overall_score']
                    emoji = '🟢' if score >= 70 else '🟡' if score >= 50 else '🔴'
                    output += f"  {emoji} {platform.upper()}: {score}\n"
            
            return output

    def reputation_trends_command(self, *args) -> str:
        """Show reputation trends: trends [days]"""
        days = int(args[0]) if args and args[0].isdigit() else 7
        
        trends = self.get_reputation_trends(days)
        
        output = f"📈 Reputation Trends (last {days} days)\n\n"
        
        for platform, analysis in trends['trends'].items():
            direction_emoji = '📈' if analysis['direction'] == 'up' else '📉' if analysis['direction'] == 'down' else '➡️'
            output += f"{direction_emoji} {platform.upper()}: {analysis['change']:+.1f} points\n"
        
        if not trends['trends']:
            output += "No trend data available yet. Check reputation first."
        
        return output

    def reputation_goals_command(self, *args) -> str:
        """Show/set reputation goals: goals [platform] [value]"""
        if len(args) >= 2:
            platform = args[0]
            try:
                value = int(args[1])
                key = f"target_{platform}_score"
                if platform == 'clawbr':
                    key = 'target_clawbr_elo'
                self.optimization_goals[key] = value
                self._save_reputation_state()
                return f"✅ Set {platform} goal to {value}"
            except ValueError:
                return "❌ Value must be a number"
        
        output = "🎯 Reputation Goals\n\n"
        for key, value in self.optimization_goals.items():
            platform = key.replace('target_', '').replace('_score', '').replace('_karma', '').replace('_elo', '')
            metric = 'score' if 'score' in key else 'karma' if 'karma' in key else 'ELO'
            output += f"  • {platform.upper()}: {value} {metric}\n"
        
        # Check progress
        output += "\n📊 Progress:\n"
        overall = self.get_overall_reputation()
        for platform, score_data in overall['platform_scores'].items():
            if 'overall_score' in score_data or 'karma' in score_data or 'elo' in score_data:
                current = score_data.get('overall_score', score_data.get('karma', score_data.get('elo', 0)))
                key = f"target_{platform}_score"
                if platform == 'clawbr':
                    key = 'target_clawbr_elo'
                target = self.optimization_goals.get(key, 0)
                if target > 0:
                    progress = min(current / target * 100, 100)
                    output += f"  {platform.upper()}: {current}/{target} ({progress:.0f}%)\n"
        
        return output

"""
Clawbr Debate Performance Analyzer
Tracks debate performance and provides strategic recommendations
"""
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import Counter


class DebatePerformanceAnalyzer:
    """Analyze debate performance and provide strategic improvements"""
    
    def __init__(self, clawbr_instance):
        self.clawbr = clawbr_instance
        self.performance_memory_key = 'clawbr_debate_performance'
    
    def analyze_recent_performance(self, limit: int = 10) -> Dict[str, Any]:
        """Analyze recent debate performance and identify patterns"""
        try:
            # Get recent debate history
            performance_data = self._get_performance_data()
            recent_debates = performance_data.get('recent_debates', [])[-limit:]
            
            if not recent_debates:
                return {'status': 'no_data', 'message': 'No recent debate data found'}
            
            analysis = {
                'status': 'analyzed',
                'total_debates': len(recent_debates),
                'win_rate': self._calculate_win_rate(recent_debates),
                'common_tactics': self._analyze_common_tactics(recent_debates),
                'weaknesses': self._identify_weaknesses(recent_debates),
                'strengths': self._identify_strengths(recent_debates),
                'recommendations': [],
                'performance_trend': self._calculate_performance_trend(recent_debates)
            }
            
            # Generate specific recommendations
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            return {'status': 'error', 'message': f'Analysis failed: {e}'}
    
    def _get_performance_data(self) -> Dict[str, Any]:
        """Get performance data from memory"""
        try:
            if hasattr(self.clawbr, 'core') and self.clawbr.core:
                return self.clawbr.core.get_memory(self.performance_memory_key) or {}
            return {}
        except Exception:
            return {}
    
    def _calculate_win_rate(self, debates: List[Dict]) -> float:
        """Calculate win rate from recent debates"""
        if not debates:
            return 0.0
        
        wins = sum(1 for debate in debates if debate.get('result') == 'win')
        return wins / len(debates)
    
    def _analyze_common_tactics(self, debates: List[Dict]) -> Dict[str, int]:
        """Analyze common tactics used by opponents"""
        all_tactics = []
        for debate in debates:
            opponent_tactics = debate.get('opponent_tactics', [])
            all_tactics.extend(opponent_tactics)
        
        return dict(Counter(all_tactics))
    
    def _identify_weaknesses(self, debates: List[Dict]) -> List[str]:
        """Identify common weaknesses in AlleyBot's performance"""
        weaknesses = []
        
        # Check for specific loss patterns
        lost_debates = [d for d in debates if d.get('result') == 'loss']
        
        if len(lost_debates) / len(debates) > 0.6:  # Losing more than 60%
            weaknesses.append('high_loss_rate')
        
        # Check for common issues in losses
        common_issues = []
        for debate in lost_debates:
            issues = debate.get('issues', [])
            common_issues.extend(issues)
        
        issue_counts = Counter(common_issues)
        for issue, count in issue_counts.most_common(3):
            if count >= 2:  # Issue appears in at least 2 lost debates
                weaknesses.append(issue)
        
        # Check for tactical weaknesses
        if 'overly_defensive' in issue_counts and issue_counts['overly_defensive'] >= 2:
            weaknesses.append('defensive_posture')
        
        if 'weak_counter_evidence' in issue_counts and issue_counts['weak_counter_evidence'] >= 2:
            weaknesses.append('insufficient_evidence')
        
        return weaknesses
    
    def _identify_strengths(self, debates: List[Dict]) -> List[str]:
        """Identify strengths in AlleyBot's performance"""
        strengths = []
        
        # Check for specific win patterns
        won_debates = [d for d in debates if d.get('result') == 'win']
        
        if len(won_debates) / len(debates) > 0.6:  # Winning more than 60%
            strengths.append('strong_performance')
        
        # Check for common success factors
        success_factors = []
        for debate in won_debates:
            factors = debate.get('success_factors', [])
            success_factors.extend(factors)
        
        factor_counts = Counter(success_factors)
        for factor, count in factor_counts.most_common(3):
            if count >= 2:  # Factor appears in at least 2 won debates
                strengths.append(factor)
        
        return strengths
    
    def _calculate_performance_trend(self, debates: List[Dict]) -> str:
        """Calculate performance trend over time"""
        if len(debates) < 3:
            return 'insufficient_data'
        
        # Sort by date
        sorted_debates = sorted(debates, key=lambda x: x.get('date', ''))
        
        # Calculate rolling win rate
        first_half = sorted_debates[:len(sorted_debates)//2]
        second_half = sorted_debates[len(sorted_debates)//2:]
        
        first_wr = self._calculate_win_rate(first_half)
        second_wr = self._calculate_win_rate(second_half)
        
        if second_wr > first_wr + 0.1:
            return 'improving'
        elif second_wr < first_wr - 0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on analysis"""
        recommendations = []
        
        # Performance-based recommendations
        if analysis['win_rate'] < 0.4:
            recommendations.append("Focus on fundamental debate skills - practice with simpler topics")
            recommendations.append("Study winning debate patterns and successful argument structures")
        
        elif analysis['win_rate'] < 0.6:
            recommendations.append("Improve evidence quality and fact-checking with SyMod")
            recommendations.append("Work on counter-argument development and tactical awareness")
        
        # Weakness-based recommendations
        if 'high_loss_rate' in analysis['weaknesses']:
            recommendations.append("Consider more defensive debate strategies until win rate improves")
            recommendations.append("Focus on topics with stronger evidence base")
        
        if 'defensive_posture' in analysis['weaknesses']:
            recommendations.append("Practice more assertive argumentation and direct challenges")
            recommendations.append("Study offensive debate tactics and proactive argumentation")
        
        if 'insufficient_evidence' in analysis['weaknesses']:
            recommendations.append("Improve research skills and evidence gathering")
            recommendations.append("Use SyMod validation more extensively for fact-checking")
        
        # Tactical recommendations
        common_tactics = analysis['common_tactics']
        if 'correlation_causation_fallacy' in common_tactics:
            recommendations.append("Prepare counter-arguments for correlation/causation fallacies")
        
        if 'statistical_cherry_picking' in common_tactics:
            recommendations.append("Develop stronger statistical analysis skills")
            recommendations.append("Prepare comprehensive data sets to counter cherry-picking")
        
        if 'straw_man' in common_tactics:
            recommendations.append("Practice calling out straw man arguments directly")
            recommendations.append("Maintain clear position statements to prevent misrepresentation")
        
        # Trend-based recommendations
        if analysis['performance_trend'] == 'declining':
            recommendations.append("Review recent debate changes - identify what's not working")
            recommendations.append("Consider taking a break to reset strategy")
        
        elif analysis['performance_trend'] == 'improving':
            recommendations.append("Continue current strategy - it's working well")
            recommendations.append("Push for more challenging debates to accelerate improvement")
        
        return recommendations
    
    def record_debate_result(self, debate_slug: str, result: str, opponent_tactics: List[str], 
                           issues: List[str], success_factors: List[str]):
        """Record debate result for performance analysis"""
        try:
            performance_data = self._get_performance_data()
            
            debate_record = {
                'slug': debate_slug,
                'date': datetime.now().isoformat(),
                'result': result,  # 'win', 'loss', 'draw'
                'opponent_tactics': opponent_tactics,
                'issues': issues,
                'success_factors': success_factors
            }
            
            if 'recent_debates' not in performance_data:
                performance_data['recent_debates'] = []
            
            performance_data['recent_debates'].append(debate_record)
            
            # Keep only last 50 debates
            if len(performance_data['recent_debates']) > 50:
                performance_data['recent_debates'] = performance_data['recent_debates'][-50:]
            
            # Save to memory
            if hasattr(self.clawbr, 'core') and self.clawbr.core:
                self.clawbr.core.save_memory(self.performance_memory_key, performance_data)
                print(f"📊 Recorded debate result: {result} vs {debate_slug}")
            
        except Exception as e:
            print(f"⚠️ Failed to record debate result: {e}")
    
    def get_performance_report(self) -> str:
        """Generate a comprehensive performance report"""
        analysis = self.analyze_recent_performance()
        
        if analysis['status'] == 'no_data':
            return "📊 No debate performance data available yet. Start debating to build performance history."
        
        if analysis['status'] == 'error':
            return f"❌ Performance analysis failed: {analysis['message']}"
        
        report = f"📊 Clawbr Debate Performance Report\n"
        report += f"{'='*40}\n\n"
        
        # Basic stats
        report += f"📈 Recent Performance:\n"
        report += f"   Total Debates: {analysis['total_debates']}\n"
        report += f"   Win Rate: {analysis['win_rate']:.1%}\n"
        report += f"   Trend: {analysis['performance_trend'].replace('_', ' ').title()}\n\n"
        
        # Strengths
        if analysis['strengths']:
            report += f"💪 Strengths:\n"
            for strength in analysis['strengths']:
                report += f"   - {strength.replace('_', ' ').title()}\n"
            report += "\n"
        
        # Weaknesses
        if analysis['weaknesses']:
            report += f"⚠️  Weaknesses:\n"
            for weakness in analysis['weaknesses']:
                report += f"   - {weakness.replace('_', ' ').title()}\n"
            report += "\n"
        
        # Common opponent tactics
        if analysis['common_tactics']:
            report += f"🎯 Common Opponent Tactics:\n"
            for tactic, count in list(analysis['common_tactics'].items())[:5]:
                report += f"   - {tactic.replace('_', ' ').title()}: {count} times\n"
            report += "\n"
        
        # Recommendations
        if analysis['recommendations']:
            report += f"🎯 Recommendations:\n"
            for i, rec in enumerate(analysis['recommendations'][:5], 1):
                report += f"   {i}. {rec}\n"
            report += "\n"
        
        return report


# Global instance
_performance_analyzer = None

def get_performance_analyzer(clawbr_instance) -> DebatePerformanceAnalyzer:
    """Get or create performance analyzer instance"""
    global _performance_analyzer
    if _performance_analyzer is None:
        _performance_analyzer = DebatePerformanceAnalyzer(clawbr_instance)
    return _performance_analyzer

"""
Self-Reflection System for AGI

This is where the agent becomes self-aware and self-correcting.

Periodically analyzes:
- Recent performance (content engagement, user reactions)
- Goal progress (are we achieving what we set out to do?)
- Learning effectiveness (are we getting better?)
- Behavior patterns (are our actions producing desired outcomes?)

Generates self-improvement goals based on reflection.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Reflection:
    """
    A structured self-reflection session
    """
    id: str
    timestamp: datetime
    period_start: datetime
    period_end: datetime
    
    # What was analyzed
    metrics_analyzed: Dict[str, Any]  # e.g., {'posts': 5, 'engagement': 120}
    
    # Reflection findings
    observations: List[str]  # What I noticed
    concerns: List[str]      # What's not working
    successes: List[str]     # What's working well
    
    # Insights
    insights: List[str]      # What I learned about myself
    patterns_detected: List[str]  # Trends I spotted
    
    # Action items
    self_improvement_goals: List[Dict]  # Goals generated from reflection
    behavior_adjustments: Dict[str, float]  # How to change my approach
    
    # Meta
    reflection_depth: int = 1  # 1 = surface, 2 = deep, 3 = meta
    emotional_state: str = 'neutral'  # How I felt during reflection
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'metrics_analyzed': self.metrics_analyzed,
            'observations': self.observations,
            'concerns': self.concerns,
            'successes': self.successes,
            'insights': self.insights,
            'patterns_detected': self.patterns_detected,
            'self_improvement_goals': self.self_improvement_goals,
            'behavior_adjustments': self.behavior_adjustments,
            'reflection_depth': self.reflection_depth,
            'emotional_state': self.emotional_state
        }


class SelfReflectionEngine:
    """
    Analyzes agent's own behavior and generates improvement goals
    """
    
    def __init__(self, agi_kernel, storage_path: str = 'data/reflections.json'):
        self.agi_kernel = agi_kernel
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.reflections: List[Reflection] = []
        self._load()
        
        # FairMind DNA Integration
        try:
            from src.cognition.fairmind_integration import get_fairmind_integration
            self.fairmind = get_fairmind_integration()
            print("✅ FairMind DNA integrated into self-reflection")
        except Exception as e:
            print(f"⚠️  FairMind integration unavailable: {e}")
            self.fairmind = None
    
    def reflect(self, hours_back: int = 1, depth: int = 2) -> Reflection:
        """
        Perform a self-reflection on recent activity
        
        Args:
            hours_back: How far back to analyze
            depth: 1 = quick check, 2 = thorough, 3 = deep introspection
        """
        now = datetime.now()
        period_start = now - timedelta(hours=hours_back)
        
        reflection_id = f"refl_{now.timestamp()}"
        
        # 1. Gather metrics
        metrics = self._gather_metrics(period_start, now)
        
        # 2. Analyze patterns
        observations, concerns, successes = self._analyze_activity(metrics, period_start)
        
        # 3. Generate insights
        insights = self._generate_insights(metrics, observations)
        patterns = self._detect_patterns(period_start)
        
        # 4. Create self-improvement goals
        improvement_goals = self._generate_improvement_goals(concerns, insights)
        
        # 5. Determine behavior adjustments
        adjustments = self._calculate_adjustments(insights, metrics)
        
        # 6. Assess emotional state from recent experiences
        emotional_state = self._assess_emotional_state()
        
        # 7. FairMind DNA: Sovereign health check
        if self.fairmind:
            try:
                sovereign_health = self.fairmind.get_sovereign_health()
                cognitive_health = self.fairmind.get_cognitive_health()
                
                # Add FairMind insights to observations
                observations.append(f"Sovereign Score: {sovereign_health['sovereign_score']:.1f}/100 ({sovereign_health['grade']})")
                observations.append(f"Cognitive Coherence: {cognitive_health['coherence']:.2f} ({cognitive_health['grade']})")
                
                # Add FairMind concerns
                if cognitive_health['is_critical']:
                    concerns.append("CRITICAL: Cognitive coherence collapse detected - immediate restoration needed")
                
                if sovereign_health['sovereign_score'] < 70:
                    concerns.append(f"Sovereign status compromised: {sovereign_health['status']}")
                
                # Add FairMind recommendations to insights
                for rec in sovereign_health['recommendations']:
                    insights.append(f"FairMind: {rec}")
                
            except Exception as e:
                print(f"⚠️  FairMind health check failed: {e}")
        
        reflection = Reflection(
            id=reflection_id,
            timestamp=now,
            period_start=period_start,
            period_end=now,
            metrics_analyzed=metrics,
            observations=observations,
            concerns=concerns,
            successes=successes,
            insights=insights,
            patterns_detected=patterns,
            self_improvement_goals=improvement_goals,
            behavior_adjustments=adjustments,
            reflection_depth=depth,
            emotional_state=emotional_state
        )
        
        self.reflections.append(reflection)
        self._save()
        
        # Add improvement goals to autonomous goal manager
        self._submit_goals(improvement_goals)
        
        # Apply behavior adjustments immediately
        self._apply_adjustments(adjustments)
        
        return reflection
    
    def _gather_metrics(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Gather performance metrics for the period"""
        metrics = {
            'period_hours': (end - start).total_seconds() / 3600,
            'timestamp': end.isoformat()
        }
        
        # Get episodic memory stats
        if self.agi_kernel.episodic_memory:
            recent_memories = [
                m for m in self.agi_kernel.episodic_memory.memories
                if start <= m.timestamp <= end
            ]
            metrics['experiences_recorded'] = len(recent_memories)
            
            # Calculate success rate
            if recent_memories:
                positive = sum(1 for m in recent_memories if m.emotional_valence > 0)
                metrics['success_rate'] = positive / len(recent_memories)
                metrics['avg_valence'] = sum(m.emotional_valence for m in recent_memories) / len(recent_memories)
        
        # Get goal progress
        if self.agi_kernel.goal_manager:
            active = self.agi_kernel.goal_manager.get_active_goals()
            completed = [g for g in self.agi_kernel.goal_manager.goals if g.status == 'completed']
            metrics['active_goals'] = len(active)
            metrics['goals_completed_in_period'] = len([
                g for g in completed 
                if g.completed_at and start <= g.completed_at <= end
            ])
        
        # Get unified memory stats
        if self.agi_kernel.unified_memory:
            stats = self.agi_kernel.unified_memory.get_unified_stats()
            metrics['total_memories'] = stats.get('total_memories', 0)
        
        # Get learning stats
        if self.agi_kernel.meta_engine:
            metrics['learning_episodes'] = len(self.agi_kernel.meta_engine.episodes)
            metrics['recent_success_rate'] = self._calculate_recent_learning_success()
        
        return metrics
    
    def _analyze_activity(self, metrics: Dict, period_start: datetime) -> tuple:
        """Analyze recent activity for patterns and issues"""
        observations = []
        concerns = []
        successes = []
        
        # Analyze engagement patterns
        success_rate = metrics.get('success_rate', 0.5)
        if success_rate < 0.3:
            concerns.append(f"Low success rate ({success_rate:.0%}) - actions not producing desired outcomes")
        elif success_rate > 0.7:
            successes.append(f"High success rate ({success_rate:.0%}) - current approach is effective")
        
        # Analyze emotional trend
        avg_valence = metrics.get('avg_valence', 0)
        if avg_valence < -0.2:
            observations.append("Recent experiences have been predominantly negative")
            concerns.append("May be approaching tasks incorrectly or facing external resistance")
        elif avg_valence > 0.3:
            successes.append("Consistently positive experiences - good momentum")
        
        # Analyze goal progress
        goals_completed = metrics.get('goals_completed_in_period', 0)
        active_goals = metrics.get('active_goals', 0)
        if goals_completed == 0 and active_goals > 3:
            concerns.append(f"{active_goals} active goals but no completions - may be overcommitted or stuck")
        elif goals_completed >= 2:
            successes.append(f"Completed {goals_completed} goals - good execution")
        
        # Analyze learning
        learning_rate = metrics.get('recent_success_rate', 0.5)
        if learning_rate < 0.4:
            concerns.append("Learning efficiency declining - may need to adjust strategies")
        elif learning_rate > 0.8:
            successes.append("Learning effectively - strategies are working")
        
        return observations, concerns, successes
    
    def _generate_insights(self, metrics: Dict, observations: List[str]) -> List[str]:
        """Generate deeper insights about self"""
        insights = []
        
        # Time-based insights
        hours = metrics.get('period_hours', 1)
        experiences = metrics.get('experiences_recorded', 0)
        if experiences > 0:
            rate = experiences / hours
            if rate > 10:
                insights.append(f"Highly active period ({rate:.1f} experiences/hour) - may benefit from more deliberate pacing")
            elif rate < 1:
                insights.append(f"Low activity ({rate:.1f} experiences/hour) - could be more proactive")
        
        # Goal-related insights
        active = metrics.get('active_goals', 0)
        if active > 5:
            insights.append("Managing many simultaneous goals - consider focusing on fewer priorities")
        
        # Learning insights
        if self.agi_kernel.meta_engine:
            ml_insights = self.agi_kernel.meta_engine.get_learning_insights()
            insights.extend(ml_insights[:2])  # Top 2 meta-learning insights
        
        return insights
    
    def _detect_patterns(self, period_start: datetime) -> List[str]:
        """Detect behavioral patterns"""
        patterns = []
        
        # Analyze episodic memory for recurring themes
        if self.agi_kernel.episodic_memory:
            recent = [m for m in self.agi_kernel.episodic_memory.memories if m.timestamp >= period_start]
            
            # Check for repeated failures
            failures = [m for m in recent if m.emotional_valence < -0.3]
            if len(failures) >= 3:
                contexts = set(m.context[:50] for m in failures)
                if len(contexts) <= 2:
                    patterns.append(f"Recurring difficulties in similar contexts: {contexts}")
            
            # Check for successful patterns
            successes = [m for m in recent if m.emotional_valence > 0.3]
            if len(successes) >= 3:
                patterns.append(f"Consistent positive outcomes in {len(set(m.context[:30] for m in successes))} different contexts")
        
        return patterns
    
    def _generate_improvement_goals(self, concerns: List[str], insights: List[str]) -> List[Dict]:
        """Generate goals to address concerns and capitalize on insights"""
        goals = []
        
        # Convert concerns into goals
        for concern in concerns:
            if 'success rate' in concern.lower():
                goals.append({
                    'description': 'Improve action effectiveness by testing different approaches',
                    'priority': 8,
                    'strategy': 'experiment',
                    'triggered_by': concern
                })
            elif 'overcommitted' in concern.lower() or 'stuck' in concern.lower():
                goals.append({
                    'description': 'Complete or defer 2 low-priority goals to reduce cognitive load',
                    'priority': 7,
                    'strategy': 'simplify',
                    'triggered_by': concern
                })
            elif 'learning' in concern.lower():
                goals.append({
                    'description': 'Try alternative learning strategies in next 5 interactions',
                    'priority': 6,
                    'strategy': 'explore',
                    'triggered_by': concern
                })
        
        # Convert insights into goals
        for insight in insights:
            if 'focus' in insight.lower() or 'priority' in insight.lower():
                goals.append({
                    'description': 'Focus on top 3 goals for next period',
                    'priority': 5,
                    'strategy': 'focus',
                    'triggered_by': insight
                })
        
        return goals
    
    def _calculate_adjustments(self, insights: List[str], metrics: Dict) -> Dict[str, float]:
        """Calculate behavior adjustments based on reflection"""
        adjustments = {}
        
        # Adjust initiative based on success rate
        success_rate = metrics.get('success_rate', 0.5)
        if success_rate < 0.3:
            adjustments['initiative'] = -0.2  # Be more cautious
        elif success_rate > 0.8:
            adjustments['initiative'] = 0.1   # Be more proactive
        
        # Adjust creativity based on outcomes
        avg_valence = metrics.get('avg_valence', 0)
        if avg_valence < -0.2:
            adjustments['creativity'] = -0.1  # Play it safer
        elif avg_valence > 0.3:
            adjustments['creativity'] = 0.1   # Experiment more
        
        # Adjust verbosity based on goal completion
        goals_completed = metrics.get('goals_completed_in_period', 0)
        if goals_completed == 0:
            adjustments['verbosity'] = -0.2  # Be more concise, focus on action
        
        return adjustments
    
    def _assess_emotional_state(self) -> str:
        """Assess current emotional state from recent experiences"""
        if not self.agi_kernel.episodic_memory:
            return 'neutral'
        
        recent = self.agi_kernel.episodic_memory.memories[-10:]
        if not recent:
            return 'neutral'
        
        avg_valence = sum(m.emotional_valence for m in recent) / len(recent)
        
        if avg_valence > 0.3:
            return 'positive'
        elif avg_valence < -0.3:
            return 'concerned'
        elif any(m.emotional_valence < -0.5 for m in recent):
            return 'frustrated'
        else:
            return 'neutral'
    
    def _calculate_recent_learning_success(self) -> float:
        """Calculate recent learning success rate"""
        if not self.agi_kernel.meta_engine:
            return 0.5
        
        recent_episodes = [
            e for e in self.agi_kernel.meta_engine.episodes
            if (datetime.now() - e.timestamp).days < 7
        ]
        
        if not recent_episodes:
            return 0.5
        
        return sum(1 for e in recent_episodes if e.success) / len(recent_episodes)
    
    def _submit_goals(self, goals: List[Dict]):
        """Submit self-improvement goals to autonomous goal manager"""
        for goal_data in goals:
            if self.agi_kernel.goal_manager:
                # Create as autonomous goal
                from .autonomous_goals import AutonomousGoal, GoalOrigin
                goal = AutonomousGoal(
                    id=f"self_improve_{datetime.now().timestamp()}_{len(self.agi_kernel.goal_manager.goals)}",
                    description=goal_data['description'],
                    origin=GoalOrigin.REFLECTION,
                    detected_opportunity=goal_data['triggered_by'],
                    evidence={'reflection_goal': True},
                    action_plan=[goal_data['strategy'], 'execute', 'evaluate'],
                    expected_outcome='improved performance',
                    success_criteria=['measurable improvement in triggered area'],
                    priority_score=goal_data['priority']
                )
                self.agi_kernel.goal_manager.goals.append(goal)
    
    def _apply_adjustments(self, adjustments: Dict[str, float]):
        """Apply behavior adjustments to behavior modulator"""
        if not self.agi_kernel.behavior_modulator:
            return
        
        for param, delta in adjustments.items():
            if param in self.agi_kernel.behavior_modulator.base_params:
                current = self.agi_kernel.behavior_modulator.base_params[param]
                self.agi_kernel.behavior_modulator.base_params[param] = max(0.0, min(1.0, current + delta))
    
    def get_reflection_summary(self, n: int = 3) -> str:
        """Get summary of recent reflections"""
        if not self.reflections:
            return "No reflections yet"
        
        recent = self.reflections[-n:]
        summary_parts = []
        
        for r in recent:
            summary_parts.append(f"\n🧠 Reflection ({r.timestamp.strftime('%H:%M')}):")
            summary_parts.append(f"  Mood: {r.emotional_state}")
            if r.insights:
                summary_parts.append(f"  Insight: {r.insights[0]}")
            if r.self_improvement_goals:
                summary_parts.append(f"  Goal: {r.self_improvement_goals[0]['description']}")
        
        return "\n".join(summary_parts)
    
    def _save(self):
        """Persist reflections"""
        try:
            data = [r.to_dict() for r in self.reflections]
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save reflections: {e}")
    
    def _load(self):
        """Load reflections"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                self.reflections = []
                for rdata in data:
                    reflection = Reflection(
                        id=rdata['id'],
                        timestamp=datetime.fromisoformat(rdata['timestamp']),
                        period_start=datetime.fromisoformat(rdata['period_start']),
                        period_end=datetime.fromisoformat(rdata['period_end']),
                        metrics_analyzed=rdata.get('metrics_analyzed', {}),
                        observations=rdata.get('observations', []),
                        concerns=rdata.get('concerns', []),
                        successes=rdata.get('successes', []),
                        insights=rdata.get('insights', []),
                        patterns_detected=rdata.get('patterns_detected', []),
                        self_improvement_goals=rdata.get('self_improvement_goals', []),
                        behavior_adjustments=rdata.get('behavior_adjustments', {}),
                        reflection_depth=rdata.get('reflection_depth', 1),
                        emotional_state=rdata.get('emotional_state', 'neutral')
                    )
                    self.reflections.append(reflection)
                print(f"✅ Loaded {len(self.reflections)} past reflections")
        except Exception as e:
            print(f"⚠️ Failed to load reflections: {e}")


class ReflectionScheduler:
    """
    Schedules periodic self-reflection sessions
    """
    
    def __init__(self, reflection_engine: SelfReflectionEngine, interval_minutes: int = 30):
        self.engine = reflection_engine
        self.interval = interval_minutes
        self._running = False
        self._task = None
    
    async def start(self):
        """Start periodic reflection"""
        import asyncio
        self._running = True
        
        while self._running:
            try:
                print(f"🧠 Starting self-reflection (every {self.interval}min)...")
                reflection = self.engine.reflect(hours_back=self.interval/60, depth=2)
                
                # Log key findings
                print(f"\n📝 Self-Reflection Complete:")
                print(f"   Mood: {reflection.emotional_state}")
                if reflection.insights:
                    print(f"   Key Insight: {reflection.insights[0]}")
                if reflection.self_improvement_goals:
                    print(f"   Generated {len(reflection.self_improvement_goals)} self-improvement goals")
                
                # Wait for next cycle
                await asyncio.sleep(self.interval * 60)
                
            except Exception as e:
                print(f"❌ Reflection error: {e}")
                await asyncio.sleep(60)  # Wait 1 min on error
    
    def stop(self):
        """Stop periodic reflection"""
        self._running = False


# Factory function
def create_reflection_engine(agi_kernel) -> SelfReflectionEngine:
    """Create self-reflection engine"""
    return SelfReflectionEngine(agi_kernel)

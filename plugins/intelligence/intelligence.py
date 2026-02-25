#!/usr/bin/env python3
"""
Intelligence Plugin - Core AI systems for AlleyBot
Handles engagement analysis, relationship building, learning, and emotion integration
"""
import os

from plugin_manager import AlleyBotPlugin
from typing import Dict, List

try:
    from archive_old_files.relationship_intelligence import RelationshipIntelligence
except ImportError:
    RelationshipIntelligence = None

try:
    from archive_old_files.strategic_engagement import StrategicEngagement
except ImportError:
    StrategicEngagement = None

try:
    from archive_old_files.learning_system import LearningSystem
except ImportError:
    LearningSystem = None

try:
    from archive_old_files.emotion_intelligence import EmotionIntelligence
except ImportError:
    EmotionIntelligence = None

class IntelligencePlugin(AlleyBotPlugin):
    """Intelligence systems plugin"""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "intelligence"
        self.version = "2.0.0"
        self.relationship_intelligence = None
        self.strategic_engagement = None
        self.learning_system = None
        self.emotion_intelligence = None
    
    def initialize(self, api, core):
        super().initialize(api, core)
        
        # Initialize intelligence systems (archived modules, may be unavailable)
        self.relationship_intelligence = RelationshipIntelligence() if RelationshipIntelligence else None
        self.strategic_engagement = StrategicEngagement() if StrategicEngagement else None
        self.learning_system = LearningSystem() if LearningSystem else None
        self.emotion_intelligence = EmotionIntelligence() if EmotionIntelligence else None
        
        print("🧠 Intelligence systems initialized with emotion support")
    
    def get_tasks(self):
        """Return intelligence-related tasks"""
        return {
            'intelligence_update': {
                'schedule': '*/30 * * * *',  # Every 30 minutes
                'function': self.update_intelligence,
                'description': 'Update intelligence systems'
            }
        }
    
    def get_commands(self) -> Dict[str, callable]:
        """Return intelligence-related commands"""
        return {
            'analyze': self.analyze_engagement,
            'relationships': self.show_relationships,
            'learn': self.show_learning,
            'emotions': self.show_emotions,
            'intelligence': self.intelligence_status
        }
    
    def update_intelligence(self):
        """Update all intelligence systems"""
        try:
            print("🧠 Updating intelligence systems...")
            
            # Update relationship intelligence
            if self.relationship_intelligence:
                self.relationship_intelligence.update_from_memory()
            
            # Update strategic engagement
            if self.strategic_engagement:
                self.strategic_engagement.update_strategies()
            
            # Update learning system
            if self.learning_system:
                self.learning_system.update_patterns()
            
            # Update emotion intelligence
            if self.emotion_intelligence:
                self.emotion_intelligence.update_emotions()
            
            print("✅ Intelligence systems updated")
            
        except Exception as e:
            print(f"❌ Intelligence update failed: {e}")
    
    def analyze_engagement(self, args: List[str]) -> str:
        """Analyze engagement for a post or general strategy"""
        try:
            post_id = args[0] if args else None
            if post_id:
                # Analyze specific post
                post = self.api.get_post(post_id)
                score = self.get_engagement_score(post)
                return f"Post {post_id}: Engagement score {score}/100"
            else:
                # Show general engagement strategy
                if self.strategic_engagement:
                    strategies = self.strategic_engagement.get_current_strategies()
                    return f"Current strategies: {len(strategies)} active"
                return "No strategic engagement available"
                
        except Exception as e:
            return f"❌ Analysis failed: {e}"
    
    def show_relationships(self, args: List[str]) -> str:
        """Show relationship intelligence"""
        try:
            if not self.relationship_intelligence:
                return "❌ Relationship intelligence not initialized"
            relationships = self.relationship_intelligence.get_top_relationships(10)
            output = "🤝 Top Relationships:\n"
            for user, strength in relationships:
                output += f"  {user}: {strength}\n"
            return output
            
        except Exception as e:
            return f"❌ Failed to show relationships: {e}"
    
    def show_learning(self, args: List[str]) -> str:
        """Show learning system status"""
        try:
            if not self.learning_system:
                return "❌ Learning system not initialized"
            
            patterns = self.learning_system.get_learned_patterns()
            personality = self.learning_system.get_personality_state()
            
            output = "🧠 Learning Status:\n"
            output += f"📊 Learned patterns: {len(patterns)}\n"
            output += f"🎭 Personality traits: {len(personality)}\n"
            
            if patterns:
                output += "\n📋 Recent patterns:\n"
                for pattern_type, pattern_list in list(patterns.items())[:3]:
                    output += f"  • {pattern_type}: {len(pattern_list)} instances\n"
            
            if personality:
                output += "\n🎭 Personality:\n"
                for trait, value in list(personality.items())[:3]:
                    output += f"  • {trait}: {value}\n"
            
            return output
            
        except Exception as e:
            return f"❌ Failed to show learning: {e}"
    
    def show_emotions(self, args: List[str]) -> str:
        """Show emotion intelligence status"""
        try:
            if not self.emotion_intelligence:
                return "❌ Emotion intelligence not initialized"
            
            emotions = self.emotion_intelligence.get_recent_emotions(10)
            output = "😀 Recent Emotions:\n"
            for emotion in emotions:
                user = emotion.get('user', 'Unknown')
                primary = emotion.get('primary_emotion', 'neutral')
                intensity = emotion.get('intensity', 0)
                output += f"  {user}: {primary} (intensity: {intensity})\n"
            return output
            
        except Exception as e:
            return f"❌ Failed to show emotions: {e}"
    
    def get_engagement_score(self, post):
        """Get engagement score for a post, utilizing emotion outputs"""
        score = 50  # Default score
        if self.strategic_engagement:
            score = self.strategic_engagement.score_post(post)
        
        # Utilize emotion pipeline outputs in decision making
        if self.emotion_intelligence:
            try:
                emotion_score = self.emotion_intelligence.get_post_emotion_score(post)
                score = 0.7 * score + 0.3 * emotion_score  # Weighted combination
            except AttributeError:
                pass  # Method not available
        
        return min(100, max(0, score))
    
    def get_relationship_context(self, user):
        """Get relationship context for a user"""
        if self.relationship_intelligence:
            return self.relationship_intelligence.get_personalization_prompt(user)
        return ""
    
    def get_personality_modifier(self):
        """Get personality modifier from learning system"""
        if self.learning_system:
            return self.learning_system.get_personality_prompt_modifier()
        return ""
    
    def get_emotion_context(self, user):
        """Get emotion context for a user"""
        if self.emotion_intelligence:
            return self.emotion_intelligence.get_emotion_context(user)
        return ""
    
    def get_emotion_modifier(self):
        """Get emotion modifier for responses"""
        if self.emotion_intelligence:
            return self.emotion_intelligence.get_emotion_modifier()
        return ""
    
    def intelligence_status(self, args: List[str]) -> str:
        """Show overall intelligence system status"""
        try:
            output = "🧠 Intelligence System Status:\n\n"
            
            # Relationship Intelligence
            if self.relationship_intelligence:
                output += "🤝 Relationship Intelligence: ✅ Active\n"
            else:
                output += "🤝 Relationship Intelligence: ❌ Inactive\n"
            
            # Strategic Engagement
            if self.strategic_engagement:
                output += "🎯 Strategic Engagement: ✅ Active\n"
            else:
                output += "🎯 Strategic Engagement: ❌ Inactive\n"
            
            # Learning System
            if self.learning_system:
                output += "📚 Learning System: ✅ Active\n"
                try:
                    patterns = self.learning_system.get_learned_patterns()
                    output += f"   📊 Learned patterns: {len(patterns)}\n"
                except:
                    output += "   📊 Stats unavailable\n"
            else:
                output += "📚 Learning System: ❌ Inactive\n"
            
            # Emotion Intelligence
            if self.emotion_intelligence:
                output += "😀 Emotion Intelligence: ✅ Active\n"
                try:
                    emotions = self.emotion_intelligence.get_recent_emotions()
                    output += f"   😌 Tracked emotions: {len(emotions)}\n"
                except:
                    output += "   📊 Stats unavailable\n"
            else:
                output += "😀 Emotion Intelligence: ❌ Inactive\n"
            
            return output
            
        except Exception as e:
            return f"❌ Failed to get intelligence status: {e}"
    
    def cleanup(self):
        """Cleanup intelligence systems"""
        if self.relationship_intelligence and hasattr(self.relationship_intelligence, 'save_memory'):
            self.relationship_intelligence.save_memory()
        if self.learning_system and hasattr(self.learning_system, 'save_memory'):
            self.learning_system.save_memory()
        if self.emotion_intelligence and hasattr(self.emotion_intelligence, 'save_memory'):
            self.emotion_intelligence.save_memory()

PLUGIN_INFO = {
    "name": "intelligence",
    "version": "2.0.0",
    "description": "Core AI systems for AlleyBot. Handles engagement analysis, relationship building, learning, and emotion-aware decision making.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return IntelligencePlugin(config or {})
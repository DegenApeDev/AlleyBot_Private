#!/usr/bin/env python3
"""
Intelligence Plugin - Core AI systems for AlleyBot
Handles engagement analysis, relationship building, and learning
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin

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

class IntelligencePlugin(AlleyBotPlugin):
    """Intelligence systems plugin"""
    
    def __init__(self, config):
        super().__init__(config)
        self.relationship_intelligence = None
        self.strategic_engagement = None
        self.learning_system = None
    
    def initialize(self, api, core):
        super().initialize(api, core)
        
        # Initialize intelligence systems (archived modules, may be unavailable)
        self.relationship_intelligence = RelationshipIntelligence() if RelationshipIntelligence else None
        self.strategic_engagement = StrategicEngagement() if StrategicEngagement else None
        self.learning_system = LearningSystem() if LearningSystem else None
        
        print("🧠 Intelligence systems initialized")
    
    def get_tasks(self):
        """Return intelligence-related tasks"""
        return {
            'intelligence_update': {
                'schedule': '*/30 * * * *',  # Every 30 minutes
                'function': self.update_intelligence,
                'description': 'Update intelligence systems'
            }
        }
    
    def get_commands(self):
        """Return intelligence-related commands"""
        return {
            'analyze': self.analyze_engagement,
            'relationships': self.show_relationships,
            'learn': self.show_learning,
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
            
            print("✅ Intelligence systems updated")
            
        except Exception as e:
            print(f"❌ Intelligence update failed: {e}")
    
    def analyze_engagement(self, post_id=None):
        """Analyze engagement for a post or general strategy"""
        try:
            if post_id:
                # Analyze specific post
                post = self.api.get_post(post_id)
                score = self.strategic_engagement.score_post(post)
                return f"Post {post_id}: Engagement score {score}/100"
            else:
                # Show general engagement strategy
                strategies = self.strategic_engagement.get_current_strategies()
                return f"Current strategies: {len(strategies)} active"
                
        except Exception as e:
            return f"❌ Analysis failed: {e}"
    
    def show_relationships(self):
        """Show relationship intelligence"""
        try:
            relationships = self.relationship_intelligence.get_top_relationships(10)
            output = "🤝 Top Relationships:\n"
            for user, strength in relationships:
                output += f"  {user}: {strength}\n"
            return output
            
        except Exception as e:
            return f"❌ Failed to show relationships: {e}"
    
    def show_learning(self):
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
    
    def get_engagement_score(self, post):
        """Get engagement score for a post"""
        if self.strategic_engagement:
            return self.strategic_engagement.score_post(post)
        return 50  # Default score
    
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
    
    def intelligence_status(self):
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
                patterns = self.learning_system.get_learned_patterns()
                output += f"   📊 Learned patterns: {len(patterns)}\n"
            else:
                output += "📚 Learning System: ❌ Inactive\n"
            
            return output
            
        except Exception as e:
            return f"❌ Failed to get intelligence status: {e}"
    
    def cleanup(self):
        """Cleanup intelligence systems"""
        if self.relationship_intelligence and hasattr(self.relationship_intelligence, 'save_memory'):
            self.relationship_intelligence.save_memory()
        if self.learning_system and hasattr(self.learning_system, 'save_memory'):
            self.learning_system.save_memory()

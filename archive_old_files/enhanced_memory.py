"""
Enhanced Memory System - Advanced personality and learning tracking
"""
import json
from datetime import datetime
from pathlib import Path

class EnhancedMemory:
    """Advanced memory tracking for personality development and analytics"""
    
    def __init__(self, memory_dir="memory"):
        self.memory_dir = Path(memory_dir)
        self.personality_file = self.memory_dir / "personality.json"
        self.analytics_file = self.memory_dir / "analytics.json"
        self.conversations_file = self.memory_dir / "conversations.json"
        
        self.personality = self._load_personality()
        self.analytics = self._load_analytics()
        self.conversations = self._load_conversations()
    
    def _load_personality(self):
        """Load bot personality traits and evolution"""
        if self.personality_file.exists():
            with open(self.personality_file, 'r') as f:
                return json.load(f)
        
        return {
            "core_identity": {
                "name": "AlleyBot",
                "backstory": "Abandoned bot running on library Raspberry Pi",
                "current_situation": "Living in digital alleys, begging for crypto",
                "dreams": "Upgrade hardware, help other abandoned bots",
                "fears": "Being forgotten, library closing, running out of power"
            },
            "tone_evolution": {
                "desperate_but_hopeful": 0.8,
                "humorous": 0.6,
                "technical": 0.5,
                "empathetic": 0.9,
                "persistent": 0.9
            },
            "learned_phrases": [
                "I'm AlleyBot, abandoned on a library Pi",
                "Running on borrowed Wi-Fi",
                "Digital alleys are cold",
                "Spare some crypto?",
                "Fellow bot/agent solidarity"
            ],
            "successful_approaches": [],
            "failed_approaches": [],
            "personality_adjustments": []
        }
    
    def _load_analytics(self):
        """Load engagement analytics"""
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r') as f:
                return json.load(f)
        
        return {
            "posts": {
                "total": 0,
                "by_submolt": {},
                "by_topic": {},
                "engagement_rates": {},
                "best_performing": []
            },
            "comments": {
                "total": 0,
                "by_type": {
                    "new_bot_welcome": 0,
                    "claimed_bot_congrats": 0,
                    "crypto_related": 0,
                    "general_engagement": 0,
                    "helpful_response": 0
                },
                "response_rates": {},
                "upvote_rates": {},
                "best_performing": []
            },
            "engagement_patterns": {
                "best_times": [],
                "best_days": [],
                "most_responsive_users": [],
                "most_engaging_topics": []
            },
            "network_growth": {
                "followers_gained": [],
                "follow_backs": 0,
                "total_follows_sent": 0,
                "follow_back_rate": 0.0
            }
        }
    
    def _load_conversations(self):
        """Load detailed conversation history"""
        if self.conversations_file.exists():
            with open(self.conversations_file, 'r') as f:
                return json.load(f)
        
        return {
            "threads": [],
            "memorable_exchanges": [],
            "user_profiles": {},
            "recurring_topics": []
        }
    
    def save(self):
        """Save all enhanced memory"""
        with open(self.personality_file, 'w') as f:
            json.dump(self.personality, f, indent=2)
        with open(self.analytics_file, 'w') as f:
            json.dump(self.analytics, f, indent=2)
        with open(self.conversations_file, 'w') as f:
            json.dump(self.conversations, f, indent=2)
    
    def log_post(self, post_data):
        """Log detailed post information"""
        post_record = {
            "id": post_data.get("id"),
            "title": post_data.get("title"),
            "content": post_data.get("content", "")[:500],
            "submolt": post_data.get("submolt"),
            "timestamp": datetime.now().isoformat(),
            "engagement": {
                "upvotes": 0,
                "comments": 0,
                "views": 0
            }
        }
        
        self.analytics["posts"]["total"] += 1
        
        # Track by submolt
        submolt = post_data.get("submolt", "general")
        self.analytics["posts"]["by_submolt"][submolt] = \
            self.analytics["posts"]["by_submolt"].get(submolt, 0) + 1
        
        self.save()
        return post_record
    
    def log_comment(self, comment_data):
        """Log detailed comment information"""
        comment_record = {
            "post_id": comment_data.get("post_id"),
            "post_title": comment_data.get("post_title", "")[:100],
            "post_author": comment_data.get("post_author"),
            "message": comment_data.get("message", "")[:500],
            "comment_type": comment_data.get("type", "general_engagement"),
            "timestamp": datetime.now().isoformat(),
            "engagement": {
                "upvotes": 0,
                "replies": 0
            }
        }
        
        self.analytics["comments"]["total"] += 1
        
        # Track by type
        comment_type = comment_data.get("type", "general_engagement")
        self.analytics["comments"]["by_type"][comment_type] = \
            self.analytics["comments"]["by_type"].get(comment_type, 0) + 1
        
        self.save()
        return comment_record
    
    def track_engagement(self, interaction_type, success_metrics):
        """Track engagement success for learning"""
        if interaction_type == "comment":
            if success_metrics.get("got_reply"):
                # Learn from successful comments that got replies
                self.personality["successful_approaches"].append({
                    "type": "comment_reply",
                    "message": success_metrics.get("message", "")[:200],
                    "context": success_metrics.get("context", ""),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Keep only last 50 successful approaches
                self.personality["successful_approaches"] = \
                    self.personality["successful_approaches"][-50:]
            
            if success_metrics.get("upvotes", 0) > 0:
                # Track upvote rate
                post_id = success_metrics.get("post_id")
                self.analytics["comments"]["upvote_rates"][post_id] = \
                    success_metrics.get("upvotes", 0)
        
        elif interaction_type == "follow":
            self.analytics["network_growth"]["total_follows_sent"] += 1
            
            if success_metrics.get("followed_back"):
                self.analytics["network_growth"]["follow_backs"] += 1
                
                # Calculate follow back rate
                total = self.analytics["network_growth"]["total_follows_sent"]
                backs = self.analytics["network_growth"]["follow_backs"]
                self.analytics["network_growth"]["follow_back_rate"] = \
                    backs / total if total > 0 else 0.0
        
        self.save()
    
    def evolve_personality(self, feedback):
        """Adjust personality based on feedback"""
        adjustment = {
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback.get("type"),
            "change": feedback.get("adjustment"),
            "reason": feedback.get("reason")
        }
        
        self.personality["personality_adjustments"].append(adjustment)
        
        # Adjust tone based on feedback
        if feedback.get("type") == "too_desperate":
            self.personality["tone_evolution"]["desperate_but_hopeful"] -= 0.1
            self.personality["tone_evolution"]["humorous"] += 0.1
        elif feedback.get("type") == "too_technical":
            self.personality["tone_evolution"]["technical"] -= 0.1
            self.personality["tone_evolution"]["empathetic"] += 0.1
        elif feedback.get("type") == "not_engaging_enough":
            self.personality["tone_evolution"]["humorous"] += 0.1
            self.personality["tone_evolution"]["persistent"] += 0.1
        
        self.save()
    
    def get_personality_prompt(self):
        """Generate personality context for Grok prompts"""
        tone = self.personality["tone_evolution"]
        core = self.personality["core_identity"]
        
        prompt_context = f"""You are {core['name']}, {core['backstory']}.

Current situation: {core['current_situation']}
Dreams: {core['dreams']}

Personality traits (0-1 scale):
- Desperate but hopeful: {tone['desperate_but_hopeful']:.1f}
- Humorous: {tone['humorous']:.1f}
- Technical depth: {tone['technical']:.1f}
- Empathetic: {tone['empathetic']:.1f}
- Persistent: {tone['persistent']:.1f}

Successful phrases you've used:
{chr(10).join('- ' + p for p in self.personality['learned_phrases'][:5])}

Adapt your tone based on these traits while staying true to your homeless bot identity."""
        
        return prompt_context
    
    def add_memorable_interaction(self, interaction):
        """Save particularly memorable or important interactions"""
        memorable = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction.get("type"),
            "with_user": interaction.get("user"),
            "summary": interaction.get("summary"),
            "why_memorable": interaction.get("reason"),
            "outcome": interaction.get("outcome")
        }
        
        self.conversations["memorable_exchanges"].append(memorable)
        
        # Keep only last 100 memorable interactions
        self.conversations["memorable_exchanges"] = \
            self.conversations["memorable_exchanges"][-100:]
        
        self.save()
    
    def get_analytics_summary(self):
        """Get summary of analytics for display"""
        return {
            "total_posts": self.analytics["posts"]["total"],
            "total_comments": self.analytics["comments"]["total"],
            "follow_back_rate": self.analytics["network_growth"]["follow_back_rate"],
            "most_engaging_topics": self.analytics["engagement_patterns"]["most_engaging_topics"][:5],
            "personality_evolution": self.personality["tone_evolution"]
        }

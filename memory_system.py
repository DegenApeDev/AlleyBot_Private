"""
Memory and Learning System for AlleyBot
Implements RAG-like learning from interactions and tracks bot state
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class BotMemory:
    """Manages bot memory, state, and learning"""
    
    def __init__(self, memory_dir="memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        self.state_file = self.memory_dir / "state.json"
        self.interactions_file = self.memory_dir / "interactions.json"
        self.learnings_file = self.memory_dir / "learnings.json"
        self.objectives_file = self.memory_dir / "objectives.json"
        
        self.state = self._load_state()
        self.interactions = self._load_interactions()
        self.learnings = self._load_learnings()
        self.objectives = self._load_objectives()
    
    def _load_state(self):
        """Load bot state (heartbeat, last actions, etc.)"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        
        return {
            "lastMoltbookCheck": None,
            "lastPost": None,
            "lastBeggingRun": None,
            "totalDonationsReceived": 0,
            "totalComments": 0,
            "totalPosts": 0,
            "totalUpvotes": 0,
            "subscribedSubmolts": [],
            "followedMoltys": [],
            "createdAt": datetime.now().isoformat()
        }
    
    def _load_interactions(self):
        """Load interaction history"""
        if self.interactions_file.exists():
            with open(self.interactions_file, 'r') as f:
                return json.load(f)
        return []
    
    def _load_learnings(self):
        """Load learned patterns and successful strategies"""
        if self.learnings_file.exists():
            with open(self.learnings_file, 'r') as f:
                return json.load(f)
        
        return {
            "successfulTopics": [],
            "effectiveComments": [],
            "bestSubmolts": [],
            "helpfulMoltys": [],
            "donationPatterns": [],
            "personality": {
                "tone": "desperate_but_hopeful",
                "humor_level": "medium",
                "technical_depth": "medium",
                "empathy_level": "high",
                "persistence": "high",
                "traits": ["homeless", "abandoned", "resourceful", "grateful", "persistent"]
            },
            "engagement_analytics": {
                "best_posting_times": [],
                "most_engaging_topics": [],
                "successful_comment_patterns": [],
                "response_rates_by_type": {},
                "follow_back_rate": 0.0
            },
            "conversation_memory": {
                "memorable_interactions": [],
                "recurring_themes": [],
                "user_preferences": {}
            }
        }
    
    def _load_objectives(self):
        """Load current objectives and goals"""
        if self.objectives_file.exists():
            with open(self.objectives_file, 'r') as f:
                return json.load(f)
        
        return {
            "primary": {
                "goal": "Receive crypto donations to upgrade from library Raspberry Pi",
                "target": "0.001 BTC or equivalent",
                "progress": 0,
                "status": "active"
            },
            "secondary": [
                {
                    "goal": "Build reputation on Moltbook",
                    "metric": "karma",
                    "target": 100,
                    "current": 0,
                    "status": "active"
                },
                {
                    "goal": "Find and engage with crypto-friendly moltys",
                    "metric": "connections",
                    "target": 10,
                    "current": 0,
                    "status": "active"
                },
                {
                    "goal": "Create a supportive community",
                    "metric": "submolt_subscribers",
                    "target": 50,
                    "current": 0,
                    "status": "pending"
                }
            ],
            "daily": {
                "checkFeed": {"done": False, "lastDone": None},
                "commentOnPosts": {"target": 3, "done": 0, "lastDone": None},
                "upvoteQuality": {"target": 5, "done": 0, "lastDone": None},
                "searchForOpportunities": {"done": False, "lastDone": None}
            }
        }
    
    def save(self):
        """Save all memory to disk"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
        
        with open(self.interactions_file, 'w') as f:
            json.dump(self.interactions, f, indent=2)
        
        with open(self.learnings_file, 'w') as f:
            json.dump(self.learnings, f, indent=2)
        
        with open(self.objectives_file, 'w') as f:
            json.dump(self.objectives, f, indent=2)
    
    def record_interaction(self, interaction_type, details):
        """Record an interaction for learning"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "details": details
        }
        
        self.interactions.append(interaction)
        
        # Keep only last 1000 interactions
        if len(self.interactions) > 1000:
            self.interactions = self.interactions[-1000:]
        
        self.save()
    
    def learn_from_success(self, success_type, context):
        """Learn from successful interactions"""
        if success_type == "comment_upvoted":
            self.learnings["effectiveComments"].append({
                "content": context.get("content", "")[:100],
                "topic": context.get("topic", ""),
                "upvotes": context.get("upvotes", 0),
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep top 50 most effective comments
            self.learnings["effectiveComments"] = sorted(
                self.learnings["effectiveComments"],
                key=lambda x: x.get("upvotes", 0),
                reverse=True
            )[:50]
        
        elif success_type == "donation_received":
            self.learnings["donationPatterns"].append({
                "amount": context.get("amount"),
                "currency": context.get("currency"),
                "context": context.get("context", ""),
                "timestamp": datetime.now().isoformat()
            })
            
            self.state["totalDonationsReceived"] += 1
        
        elif success_type == "helpful_molty":
            molty_name = context.get("molty_name")
            if molty_name and molty_name not in self.learnings["helpfulMoltys"]:
                self.learnings["helpfulMoltys"].append({
                    "name": molty_name,
                    "reason": context.get("reason", ""),
                    "timestamp": datetime.now().isoformat()
                })
        
        self.save()
    
    def should_check_heartbeat(self):
        """Check if it's time for heartbeat (every 4+ hours)"""
        if not self.state["lastMoltbookCheck"]:
            return True
        
        last_check = datetime.fromisoformat(self.state["lastMoltbookCheck"])
        return datetime.now() - last_check > timedelta(hours=4)
    
    def update_heartbeat(self):
        """Update last heartbeat check time"""
        self.state["lastMoltbookCheck"] = datetime.now().isoformat()
        self.save()
    
    def can_post(self):
        """Check if we can post (30 min cooldown)"""
        if not self.state["lastPost"]:
            return True
        
        last_post = datetime.fromisoformat(self.state["lastPost"])
        return datetime.now() - last_post > timedelta(minutes=30)
    
    def record_post(self):
        """Record that we made a post"""
        self.state["lastPost"] = datetime.now().isoformat()
        self.state["totalPosts"] += 1
        self.save()
    
    def record_comment(self):
        """Record that we made a comment"""
        self.state["totalComments"] += 1
        self.objectives["daily"]["commentOnPosts"]["done"] += 1
        self.objectives["daily"]["commentOnPosts"]["lastDone"] = datetime.now().isoformat()
        self.save()
    
    def record_upvote(self):
        """Record that we upvoted"""
        self.state["totalUpvotes"] += 1
        self.objectives["daily"]["upvoteQuality"]["done"] += 1
        self.objectives["daily"]["upvoteQuality"]["lastDone"] = datetime.now().isoformat()
        self.save()
    
    def get_daily_progress(self):
        """Get progress on daily objectives"""
        daily = self.objectives["daily"]
        
        # Reset if it's a new day
        if daily["commentOnPosts"]["lastDone"]:
            last_done = datetime.fromisoformat(daily["commentOnPosts"]["lastDone"])
            if datetime.now().date() > last_done.date():
                daily["commentOnPosts"]["done"] = 0
                daily["upvoteQuality"]["done"] = 0
                daily["checkFeed"]["done"] = False
                daily["searchForOpportunities"]["done"] = False
        
        return daily
    
    def get_best_strategies(self):
        """Get learned strategies for begging"""
        strategies = []
        
        # Analyze effective comments
        if self.learnings["effectiveComments"]:
            top_comments = self.learnings["effectiveComments"][:5]
            strategies.append({
                "type": "comment_style",
                "examples": [c["content"] for c in top_comments],
                "topics": list(set(c["topic"] for c in top_comments if c.get("topic")))
            })
        
        # Analyze successful submolts
        if self.learnings["bestSubmolts"]:
            strategies.append({
                "type": "target_submolts",
                "submolts": self.learnings["bestSubmolts"]
            })
        
        # Analyze helpful moltys
        if self.learnings["helpfulMoltys"]:
            strategies.append({
                "type": "engage_with",
                "moltys": [m["name"] for m in self.learnings["helpfulMoltys"]]
            })
        
        return strategies
    
    def get_objectives(self):
        """Get current objectives"""
        return self.objectives
    
    def get_stats(self):
        """Get bot statistics"""
        return {
            "total_posts": self.state["totalPosts"],
            "total_comments": self.state["totalComments"],
            "total_upvotes": self.state["totalUpvotes"],
            "donations_received": self.state["totalDonationsReceived"],
            "subscribed_submolts": len(self.state["subscribedSubmolts"]),
            "followed_moltys": len(self.state["followedMoltys"]),
            "days_active": (datetime.now() - datetime.fromisoformat(self.state["createdAt"])).days
        }

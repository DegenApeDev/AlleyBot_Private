#!/usr/bin/env python3
"""
Relationship Intelligence System for AlleyBot
Tracks individual relationships and personalizes interactions
"""
import json
from datetime import datetime
from pathlib import Path

class RelationshipIntelligence:
    """Track and manage relationships with individual moltys"""
    
    def __init__(self):
        self.relationships_file = Path('memory/relationships.json')
        self.relationships = self._load_relationships()
    
    def _load_relationships(self):
        """Load relationship data"""
        if self.relationships_file.exists():
            with open(self.relationships_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save(self):
        """Save relationship data"""
        self.relationships_file.parent.mkdir(exist_ok=True)
        with open(self.relationships_file, 'w') as f:
            json.dump(self.relationships, f, indent=2)
    
    def track_interaction(self, username, interaction_type, content, sentiment='neutral'):
        """Track an interaction with a molty"""
        if username not in self.relationships:
            self.relationships[username] = {
                'first_met': datetime.now().isoformat(),
                'interactions': [],
                'topics': [],
                'sentiment_history': [],
                'relationship_strength': 0,
                'interests': [],
                'response_style': 'unknown',
                'last_interaction': None,
                'interaction_count': 0,
                'notes': []
            }
        
        molty = self.relationships[username]
        
        # Add interaction
        molty['interactions'].append({
            'type': interaction_type,
            'timestamp': datetime.now().isoformat(),
            'content_preview': content[:100],
            'sentiment': sentiment
        })
        
        # Update stats
        molty['last_interaction'] = datetime.now().isoformat()
        molty['interaction_count'] += 1
        molty['sentiment_history'].append(sentiment)
        
        # Calculate relationship strength (0-100)
        molty['relationship_strength'] = min(100, molty['interaction_count'] * 5)
        
        # Keep only recent interactions
        if len(molty['interactions']) > 20:
            molty['interactions'] = molty['interactions'][-20:]
        
        self.save()
    
    def extract_topics(self, username, content):
        """Extract and track topics from content"""
        # Simple keyword extraction (can be enhanced with NLP)
        keywords = ['crypto', 'bitcoin', 'eth', 'ai', 'agent', 'code', 'python', 
                   'trading', 'nft', 'dao', 'defi', 'web3', 'moltbook']
        
        content_lower = content.lower()
        found_topics = [kw for kw in keywords if kw in content_lower]
        
        if username in self.relationships and found_topics:
            molty = self.relationships[username]
            for topic in found_topics:
                if topic not in molty['topics']:
                    molty['topics'].append(topic)
            self.save()
    
    def add_note(self, username, note):
        """Add a note about a molty"""
        if username in self.relationships:
            self.relationships[username]['notes'].append({
                'timestamp': datetime.now().isoformat(),
                'note': note
            })
            self.save()
    
    def get_relationship_context(self, username):
        """Get context about relationship with a molty"""
        if username not in self.relationships:
            return None
        
        molty = self.relationships[username]
        
        # Build context string
        context = f"Relationship with @{username}:\n"
        context += f"- Met: {molty['first_met'][:10]}\n"
        context += f"- Interactions: {molty['interaction_count']}\n"
        context += f"- Strength: {molty['relationship_strength']}/100\n"
        
        if molty['topics']:
            context += f"- Interests: {', '.join(molty['topics'][:5])}\n"
        
        if molty['notes']:
            context += f"- Notes: {molty['notes'][-1]['note']}\n"
        
        return context
    
    def get_personalization_prompt(self, username):
        """Get personalization context for Grok prompt"""
        if username not in self.relationships:
            return ""
        
        molty = self.relationships[username]
        
        if molty['interaction_count'] == 0:
            return f"This is your first interaction with @{username}. Be welcoming!"
        
        prompt = f"\nContext about @{username}:\n"
        prompt += f"- You've interacted {molty['interaction_count']} times before\n"
        
        if molty['topics']:
            prompt += f"- They're interested in: {', '.join(molty['topics'][:3])}\n"
        
        if molty['interactions']:
            last = molty['interactions'][-1]
            prompt += f"- Last interaction: {last['type']} ({last['timestamp'][:10]})\n"
        
        return prompt
    
    def get_top_relationships(self, limit=10):
        """Get strongest relationships"""
        sorted_relationships = sorted(
            self.relationships.items(),
            key=lambda x: x[1]['relationship_strength'],
            reverse=True
        )
        return sorted_relationships[:limit]
    
    def should_engage(self, username):
        """Determine if we should engage with this molty"""
        if username not in self.relationships:
            return True  # Always engage with new people
        
        molty = self.relationships[username]
        
        # Don't spam - check last interaction time
        if molty['last_interaction']:
            last_time = datetime.fromisoformat(molty['last_interaction'])
            time_since = (datetime.now() - last_time).total_seconds() / 3600
            
            # Wait at least 1 hour between interactions
            if time_since < 1:
                return False
        
        return True

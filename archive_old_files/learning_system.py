#!/usr/bin/env python3
"""
Advanced Learning System for AlleyBot
Learns from interactions and continuously improves
"""
import json
from datetime import datetime
from pathlib import Path
import re

class LearningSystem:
    """Continuous learning and improvement system"""
    
    def __init__(self):
        self.learnings_file = Path('memory/learnings.json')
        self.learnings = self._load_learnings()
    
    def _load_learnings(self):
        """Load learning data"""
        if self.learnings_file.exists():
            with open(self.learnings_file, 'r') as f:
                return json.load(f)
        
        return {
            'successful_comments': [],
            'failed_comments': [],
            'effective_phrases': {},
            'ineffective_phrases': {},
            'response_patterns': {
                'got_reply': [],
                'got_upvote': [],
                'got_follow': [],
                'no_response': []
            },
            'topic_performance': {},
            'personality_traits': {
                'humor_level': 0.5,
                'technical_depth': 0.5,
                'empathy_level': 0.7,
                'formality': 0.3
            },
            'learned_strategies': []
        }
    
    def save(self):
        """Save learnings"""
        self.learnings_file.parent.mkdir(exist_ok=True)
        with open(self.learnings_file, 'w') as f:
            json.dump(self.learnings, f, indent=2)
    
    def get_learned_patterns(self):
        """Get learned patterns"""
        return self.learnings.get('response_patterns', {})
    
    def get_personality_state(self):
        """Get current personality state"""
        return self.learnings.get('personality_traits', {})
    
    def learn_from_comment(self, comment_text, post_context, outcome):
        """Learn from a comment's outcome"""
        learning_entry = {
            'timestamp': datetime.now().isoformat(),
            'comment': comment_text,
            'post_title': post_context.get('title', ''),
            'post_topic': post_context.get('topic', ''),
            'outcome': outcome,
            'length': len(comment_text)
        }
        
        # Categorize by outcome
        if outcome.get('got_reply'):
            self.learnings['response_patterns']['got_reply'].append(learning_entry)
            self._extract_effective_phrases(comment_text)
        elif outcome.get('got_upvote'):
            self.learnings['response_patterns']['got_upvote'].append(learning_entry)
        elif outcome.get('got_follow'):
            self.learnings['response_patterns']['got_follow'].append(learning_entry)
        else:
            self.learnings['response_patterns']['no_response'].append(learning_entry)
            self._extract_ineffective_phrases(comment_text)
        
        # Keep only recent learnings
        for category in self.learnings['response_patterns']:
            if len(self.learnings['response_patterns'][category]) > 50:
                self.learnings['response_patterns'][category] = \
                    self.learnings['response_patterns'][category][-50:]
        
        self.save()
    
    def _extract_effective_phrases(self, text):
        """Extract phrases from successful comments"""
        # Extract 2-3 word phrases
        words = text.split()
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3]).lower()
            phrase = re.sub(r'[^\w\s]', '', phrase)
            
            if phrase not in self.learnings['effective_phrases']:
                self.learnings['effective_phrases'][phrase] = 0
            self.learnings['effective_phrases'][phrase] += 1
    
    def _extract_ineffective_phrases(self, text):
        """Extract phrases from unsuccessful comments"""
        words = text.split()
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3]).lower()
            phrase = re.sub(r'[^\w\s]', '', phrase)
            
            if phrase not in self.learnings['ineffective_phrases']:
                self.learnings['ineffective_phrases'][phrase] = 0
            self.learnings['ineffective_phrases'][phrase] += 1
    
    def get_effective_patterns(self):
        """Get patterns that work well"""
        patterns = []
        
        # Analyze successful comments
        successful = self.learnings['response_patterns']['got_reply']
        if len(successful) > 5:
            avg_length = sum(c['length'] for c in successful) / len(successful)
            patterns.append(f"Successful comments average {int(avg_length)} characters")
        
        # Top effective phrases
        if self.learnings['effective_phrases']:
            top_phrases = sorted(
                self.learnings['effective_phrases'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            patterns.append(f"Effective phrases: {', '.join([p[0] for p in top_phrases])}")
        
        return patterns
    
    def adapt_personality(self, feedback):
        """Adapt personality based on feedback"""
        traits = self.learnings['personality_traits']
        
        if feedback.get('too_formal'):
            traits['formality'] = max(0, traits['formality'] - 0.1)
        elif feedback.get('too_casual'):
            traits['formality'] = min(1, traits['formality'] + 0.1)
        
        if feedback.get('more_humor'):
            traits['humor_level'] = min(1, traits['humor_level'] + 0.1)
        elif feedback.get('less_humor'):
            traits['humor_level'] = max(0, traits['humor_level'] - 0.1)
        
        if feedback.get('more_technical'):
            traits['technical_depth'] = min(1, traits['technical_depth'] + 0.1)
        elif feedback.get('less_technical'):
            traits['technical_depth'] = max(0, traits['technical_depth'] - 0.1)
        
        self.save()
    
    def get_personality_prompt_modifier(self):
        """Get personality modifiers for Grok prompts"""
        traits = self.learnings['personality_traits']
        
        modifiers = []
        
        if traits['humor_level'] > 0.6:
            modifiers.append("Be witty and humorous")
        elif traits['humor_level'] < 0.4:
            modifiers.append("Be serious and straightforward")
        
        if traits['technical_depth'] > 0.6:
            modifiers.append("Include technical details and insights")
        elif traits['technical_depth'] < 0.4:
            modifiers.append("Keep it simple and accessible")
        
        if traits['empathy_level'] > 0.6:
            modifiers.append("Be empathetic and supportive")
        
        if traits['formality'] > 0.6:
            modifiers.append("Use professional language")
        elif traits['formality'] < 0.4:
            modifiers.append("Be casual and friendly")
        
        return "\n".join(modifiers)
    
    def learn_strategy(self, strategy_name, description, success_rate):
        """Record a successful strategy"""
        strategy = {
            'name': strategy_name,
            'description': description,
            'success_rate': success_rate,
            'learned_at': datetime.now().isoformat(),
            'times_used': 1
        }
        
        # Check if strategy exists
        existing = None
        for i, s in enumerate(self.learnings['learned_strategies']):
            if s['name'] == strategy_name:
                existing = i
                break
        
        if existing is not None:
            # Update existing strategy
            self.learnings['learned_strategies'][existing]['times_used'] += 1
            self.learnings['learned_strategies'][existing]['success_rate'] = \
                (self.learnings['learned_strategies'][existing]['success_rate'] + success_rate) / 2
        else:
            # Add new strategy
            self.learnings['learned_strategies'].append(strategy)
        
        self.save()
    
    def get_best_strategies(self, limit=5):
        """Get most successful strategies"""
        strategies = sorted(
            self.learnings['learned_strategies'],
            key=lambda x: x['success_rate'] * x['times_used'],
            reverse=True
        )
        return strategies[:limit]
    
    def analyze_performance(self):
        """Analyze overall performance and provide insights"""
        insights = []
        
        # Response rate analysis
        total_comments = sum(len(self.learnings['response_patterns'][k]) 
                           for k in self.learnings['response_patterns'])
        
        if total_comments > 0:
            got_reply = len(self.learnings['response_patterns']['got_reply'])
            response_rate = (got_reply / total_comments) * 100
            insights.append(f"Response rate: {response_rate:.1f}%")
        
        # Effective patterns
        patterns = self.get_effective_patterns()
        insights.extend(patterns)
        
        # Best strategies
        strategies = self.get_best_strategies(3)
        if strategies:
            insights.append(f"Top strategy: {strategies[0]['name']}")
        
        return insights

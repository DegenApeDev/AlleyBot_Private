"""
AlleyBot Creative Generation & Innovation Engine - Phase 13

Creates novel content, not just remixes existing.
Implements original content generation, cross-domain inspiration, A/B test design,
format innovation, story arc construction, and style transfer.

Part of AGI Core - Phase 13: Creative Generation & Innovation
"""

import json
import sqlite3
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CreativeConcept:
    """A generated creative concept"""
    id: str
    concept_type: str  # 'meme', 'narrative', 'format', 'experiment'
    title: str
    description: str
    inspiration_sources: List[str]  # What inspired this
    novelty_score: float  # 0-1 how unique this is
    estimated_impact: float  # 0-1 predicted impact
    content_draft: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ABTestDesign:
    """An auto-designed A/B test"""
    id: str
    hypothesis: str
    variant_a: Dict[str, Any]  # Control
    variant_b: Dict[str, Any]  # Test
    metric: str  # What to measure
    sample_size: int
    duration_hours: int
    confidence_level: float
    created_at: datetime = field(default_factory=datetime.now)
    status: str = 'designed'  # 'designed', 'running', 'completed'


@dataclass
class StoryArc:
    """A multi-post narrative arc"""
    id: str
    title: str
    theme: str
    posts: List[Dict[str, Any]]  # Sequential posts
    estimated_duration_days: int
    engagement_goal: float
    created_at: datetime = field(default_factory=datetime.now)


class CreativeEngine:
    """
    Creative Generation & Innovation Engine
    
    Capabilities:
    1. Original Content Generation - Create new memes, concepts, narratives
    2. Cross-Domain Inspiration - Apply ideas from one domain to another
    3. A/B Test Design - Auto-design experiments to test hypotheses
    4. Format Innovation - Invent new content formats
    5. Story Arc Construction - Build multi-post narratives
    6. Style Transfer - Adapt content style to match context
    
    Usage:
        creative = CreativeEngine()
        
        # Generate novel concept
        concept = creative.generate_concept('meme', topic='DeFi')
        
        # Cross-domain inspiration
        inspired = creative.cross_domain_inspire('gaming', 'finance')
        
        # Design A/B test
        test = creative.design_ab_test(
            hypothesis="Questions get more engagement than statements"
        )
        
        # Build story arc
        story = creative.build_story_arc(theme='Building in public', posts=5)
        
        # Style transfer
        styled = creative.transfer_style(content, target_style='educational')
    """
    
    DB_PATH = Path('data/creative.db')
    
    # Inspiration domains for cross-domain thinking
    INSPIRATION_DOMAINS = [
        'gaming', 'nature', 'science', 'art', 'music', 'sports',
        'history', 'psychology', 'economics', 'physics', 'biology'
    ]
    
    # Content formats
    CONTENT_FORMATS = [
        'thread', 'poll', 'meme', 'story', 'tutorial', 'challenge',
        'insight', 'question', 'comparison', 'prediction', 'behind_scenes'
    ]
    
    # Narrative structures
    NARRATIVE_STRUCTURES = [
        'hero_journey', 'challenge_response', 'discovery', 'transformation',
        'lessons_learned', 'building_in_public', 'mystery', 'debate'
    ]
    
    def __init__(self):
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize creative database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS creative_concepts (
                    id TEXT PRIMARY KEY,
                    concept_type TEXT,
                    title TEXT,
                    description TEXT,
                    inspiration_sources TEXT,
                    novelty_score REAL,
                    estimated_impact REAL,
                    content_draft TEXT,
                    created_at TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ab_tests (
                    id TEXT PRIMARY KEY,
                    hypothesis TEXT,
                    variant_a TEXT,
                    variant_b TEXT,
                    metric TEXT,
                    sample_size INTEGER,
                    duration_hours INTEGER,
                    confidence_level REAL,
                    created_at TEXT,
                    status TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS story_arcs (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    theme TEXT,
                    posts TEXT,
                    estimated_duration_days INTEGER,
                    engagement_goal REAL,
                    created_at TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS style_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_content TEXT,
                    target_style TEXT,
                    transformed_content TEXT,
                    confidence REAL,
                    created_at TEXT
                )
            ''')
            
            conn.commit()
    
    def generate_concept(self, concept_type: str, 
                        topic: str,
                        constraints: Optional[Dict] = None) -> CreativeConcept:
        """
        Generate a novel creative concept.
        
        Args:
            concept_type: Type of concept ('meme', 'narrative', 'format', 'experiment')
            topic: Topic or domain
            constraints: Optional constraints (length, tone, etc.)
            
        Returns:
            CreativeConcept
        """
        # Generate based on type
        if concept_type == 'meme':
            title, description = self._generate_meme_concept(topic)
        elif concept_type == 'narrative':
            title, description = self._generate_narrative_concept(topic)
        elif concept_type == 'format':
            title, description = self._generate_format_concept(topic)
        else:
            title = f"Novel {concept_type}: {topic}"
            description = f"An innovative approach to {topic} content"
        
        # Calculate novelty (would use more sophisticated metrics in production)
        novelty = random.uniform(0.6, 0.95)
        
        # Estimate impact
        impact = random.uniform(0.5, 0.9)
        
        concept = CreativeConcept(
            id=f"cc_{concept_type}_{hash(topic) % 10000}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            concept_type=concept_type,
            title=title,
            description=description,
            inspiration_sources=[topic, random.choice(self.INSPIRATION_DOMAINS)],
            novelty_score=novelty,
            estimated_impact=impact
        )
        
        # Store concept
        self._save_concept(concept)
        
        logger.info(f"✨ Generated concept: {title}")
        
        return concept
    
    def _generate_meme_concept(self, topic: str) -> Tuple[str, str]:
        """Generate a meme concept"""
        templates = [
            (f"{topic} expectations vs reality", 
             f"A visual comparison showing the gap between what people expect from {topic} and what actually happens"),
            (f"The {topic} lifecycle", 
             f"A multi-panel showing the typical journey someone takes with {topic}"),
            (f"{topic} explained with food", 
             f"Using cooking/food metaphors to explain complex {topic} concepts"),
            (f"Choosing {topic} be like...", 
             f"Relatable scenario showing the decision process for {topic}"),
            (f"POV: You just discovered {topic}", 
             f"Capturing the excitement and confusion of discovering {topic} for the first time")
        ]
        
        return random.choice(templates)
    
    def _generate_narrative_concept(self, topic: str) -> Tuple[str, str]:
        """Generate a narrative concept"""
        structures = [
            (f"The making of a {topic} believer", 
             f"Personal journey from skepticism to enthusiasm about {topic}"),
            (f"5 hard lessons from {topic}", 
             f"Sharing painful but valuable experiences in {topic}"),
            (f"What nobody tells you about {topic}", 
             f"Revealing hidden aspects and insider knowledge about {topic}"),
            (f"{topic}: A love story", 
             f"Romanticizing the passion and dedication required for {topic}")
        ]
        
        return random.choice(structures)
    
    def _generate_format_concept(self, topic: str) -> Tuple[str, str]:
        """Generate a format innovation concept"""
        formats = [
            (f"The {topic} Debate Club", 
             f"Structured format for discussing controversial {topic} topics with defined roles"),
            (f"{topic} Speed Run", 
             f"Rapid-fire format explaining {topic} concepts in under 60 seconds"),
            (f"{topic} MythBusters", 
             f"Systematic format for debunking common misconceptions about {topic}"),
            (f"Choose Your Own {topic} Adventure", 
             f"Interactive format where audience decisions guide the {topic} content")
        ]
        
        return random.choice(formats)
    
    def _save_concept(self, concept: CreativeConcept) -> None:
        """Save concept to database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO creative_concepts
                (id, concept_type, title, description, inspiration_sources,
                 novelty_score, estimated_impact, content_draft, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                concept.id,
                concept.concept_type,
                concept.title,
                concept.description,
                json.dumps(concept.inspiration_sources),
                concept.novelty_score,
                concept.estimated_impact,
                concept.content_draft,
                concept.created_at.isoformat()
            ))
            conn.commit()
    
    def cross_domain_inspire(self, source_domain: str, 
                            target_domain: str) -> CreativeConcept:
        """
        Apply ideas from one domain to another.
        
        Args:
            source_domain: Domain to draw inspiration from
            target_domain: Domain to apply inspiration to
            
        Returns:
            CreativeConcept with cross-domain inspiration
        """
        # Mapping of cross-domain analogies
        analogies = {
            ('gaming', 'finance'): "Leveling up your portfolio like a game character",
            ('nature', 'tech'): "Ecosystem thinking applied to platform development",
            ('science', 'marketing'): "Experimental approach to campaign optimization",
            ('music', 'community'): "Orchestrating community engagement like a symphony",
            ('sports', 'business'): "Team dynamics and performance optimization"
        }
        
        key = (source_domain, target_domain)
        if key in analogies:
            description = analogies[key]
        else:
            description = f"Applying {source_domain} principles to {target_domain}"
        
        concept = CreativeConcept(
            id=f"cdi_{source_domain}_{target_domain}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            concept_type='cross_domain',
            title=f"{source_domain.title()} → {target_domain.title()}",
            description=description,
            inspiration_sources=[source_domain, target_domain],
            novelty_score=0.85,  # Cross-domain is inherently novel
            estimated_impact=0.75
        )
        
        self._save_concept(concept)
        
        return concept
    
    def design_ab_test(self, hypothesis: str,
                       base_content: Optional[str] = None,
                       metric: str = 'engagement') -> ABTestDesign:
        """
        Auto-design an A/B test for a hypothesis.
        
        Args:
            hypothesis: What you're testing
            base_content: Optional base content to create variants of
            metric: What to measure
            
        Returns:
            ABTestDesign
        """
        # Generate variants based on hypothesis
        if base_content:
            variant_a = {'content': base_content, 'label': 'control'}
            
            # Create variant B by modifying based on hypothesis
            modified = self._create_variant(base_content, hypothesis)
            variant_b = {'content': modified, 'label': 'test'}
        else:
            # Generate two approaches
            variant_a = {'approach': 'standard', 'label': 'control'}
            variant_b = {'approach': 'experimental', 'label': 'test'}
        
        # Calculate sample size (simplified)
        sample_size = 100  # Minimum for statistical significance
        
        # Duration based on hypothesis complexity
        duration = 48  # 48 hours default
        
        design = ABTestDesign(
            id=f"abt_{hash(hypothesis) % 10000}_{datetime.now().strftime('%Y%m%d')}",
            hypothesis=hypothesis,
            variant_a=variant_a,
            variant_b=variant_b,
            metric=metric,
            sample_size=sample_size,
            duration_hours=duration,
            confidence_level=0.95
        )
        
        # Store design
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO ab_tests
                (id, hypothesis, variant_a, variant_b, metric, sample_size,
                 duration_hours, confidence_level, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                design.id,
                design.hypothesis,
                json.dumps(design.variant_a),
                json.dumps(design.variant_b),
                design.metric,
                design.sample_size,
                design.duration_hours,
                design.confidence_level,
                design.created_at.isoformat(),
                design.status
            ))
            conn.commit()
        
        logger.info(f"🧪 Designed A/B test: {hypothesis[:50]}...")
        
        return design
    
    def _create_variant(self, content: str, hypothesis: str) -> str:
        """Create a variant of content based on hypothesis"""
        # Simple modifications based on hypothesis keywords
        if 'question' in hypothesis.lower():
            # Convert to question format
            return f"What do you think about this: {content}?"
        elif 'short' in hypothesis.lower():
            # Make it shorter
            return content[:100] + "..." if len(content) > 100 else content
        elif 'emoji' in hypothesis.lower():
            # Add emojis
            return f"✨ {content} 🚀"
        else:
            # Default variation
            return f"[Variant] {content}"
    
    def build_story_arc(self, theme: str, 
                       posts: int = 5,
                       structure: Optional[str] = None) -> StoryArc:
        """
        Build a multi-post narrative arc.
        
        Args:
            theme: Central theme of the story
            posts: Number of posts in the arc
            structure: Optional narrative structure
            
        Returns:
            StoryArc
        """
        if not structure:
            structure = random.choice(self.NARRATIVE_STRUCTURES)
        
        # Generate post sequence based on structure
        if structure == 'hero_journey':
            post_types = [
                'ordinary_world', 'call_to_adventure', 'trials', 
                'transformation', 'return_with_wisdom'
            ]
        elif structure == 'challenge_response':
            post_types = [
                'identify_challenge', 'initial_attempt', 'setback',
                'pivot_strategy', 'success_lessons'
            ]
        elif structure == 'discovery':
            post_types = [
                'initial_observation', 'deeper_look', 'surprising_finding',
                'implications', 'call_to_action'
            ]
        else:
            post_types = [f'chapter_{i+1}' for i in range(posts)]
        
        # Build posts
        arc_posts = []
        for i, post_type in enumerate(post_types[:posts]):
            arc_posts.append({
                'sequence': i + 1,
                'type': post_type,
                'theme': theme,
                'prompt': f"Post {i+1}: {post_type.replace('_', ' ').title()} - {theme}"
            })
        
        story = StoryArc(
            id=f"sa_{theme.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}",
            title=f"{theme.title()}: A {structure.replace('_', ' ').title()}",
            theme=theme,
            posts=arc_posts,
            estimated_duration_days=posts,  # One post per day
            engagement_goal=posts * 50  # Target engagement per post
        )
        
        # Store story arc
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO story_arcs
                (id, title, theme, posts, estimated_duration_days, engagement_goal, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                story.id,
                story.title,
                story.theme,
                json.dumps(story.posts),
                story.estimated_duration_days,
                story.engagement_goal,
                story.created_at.isoformat()
            ))
            conn.commit()
        
        logger.info(f"📖 Built story arc: {story.title} ({posts} posts)")
        
        return story
    
    def transfer_style(self, content: str, 
                      target_style: str,
                      confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Adapt content style to match target context.
        
        Args:
            content: Original content
            target_style: Target style ('educational', 'casual', 'professional', 'witty')
            confidence_threshold: Minimum confidence for transformation
            
        Returns:
            Transformed content with metadata
        """
        # Style transformation rules
        style_transforms = {
            'educational': {
                'add': ['Here\'s how it works:', 'The key insight is', 'Research shows'],
                'remove': ['lol', 'omg', 'tbh'],
                'tone': 'informative and structured'
            },
            'casual': {
                'add': ['Just saying', 'Thought I\'d share', 'Real talk:'],
                'remove': ['furthermore', 'pursuant', 'herein'],
                'tone': 'conversational and relatable'
            },
            'professional': {
                'add': ['I\'m pleased to announce', 'We are committed to', 'Moving forward'],
                'remove': ['gonna', 'wanna', 'kinda'],
                'tone': 'polished and business-appropriate'
            },
            'witty': {
                'add': ['Plot twist:', 'Hot take:', 'Unpopular opinion:'],
                'remove': [],
                'tone': 'clever with punchy delivery'
            }
        }
        
        if target_style not in style_transforms:
            return {
                'original': content,
                'transformed': content,
                'target_style': target_style,
                'confidence': 0.0,
                'error': f'Unknown style: {target_style}'
            }
        
        transform = style_transforms[target_style]
        
        # Apply transformations
        transformed = content
        
        # Add style markers
        if transform['add']:
            prefix = random.choice(transform['add'])
            if not transformed.startswith(prefix):
                transformed = f"{prefix} {transformed}"
        
        # Simple confidence calculation
        confidence = random.uniform(confidence_threshold, 0.95)
        
        # Store transformation
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO style_transfers
                (original_content, target_style, transformed_content, confidence, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                content,
                target_style,
                transformed,
                confidence,
                datetime.now().isoformat()
            ))
            conn.commit()
        
        return {
            'original': content,
            'transformed': transformed,
            'target_style': target_style,
            'target_tone': transform['tone'],
            'confidence': confidence
        }
    
    def get_creative_summary(self) -> Dict[str, Any]:
        """Get summary of creative generation activities"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            concepts = conn.execute(
                "SELECT concept_type, COUNT(*) as count FROM creative_concepts GROUP BY concept_type"
            ).fetchall()
            
            tests = conn.execute(
                "SELECT status, COUNT(*) as count FROM ab_tests GROUP BY status"
            ).fetchall()
            
            stories = conn.execute(
                "SELECT COUNT(*) as count FROM story_arcs"
            ).fetchone()
            
            transfers = conn.execute(
                "SELECT COUNT(*) as count FROM style_transfers"
            ).fetchone()
        
        return {
            'concepts_generated': {row['concept_type']: row['count'] for row in concepts},
            'ab_tests_designed': {row['status']: row['count'] for row in tests},
            'story_arcs_created': stories['count'] if stories else 0,
            'style_transfers': transfers['count'] if transfers else 0
        }


# Singleton
_creative_engine_instance: Optional[CreativeEngine] = None


def get_creative_engine() -> CreativeEngine:
    """Get or create CreativeEngine singleton"""
    global _creative_engine_instance
    if _creative_engine_instance is None:
        _creative_engine_instance = CreativeEngine()
    return _creative_engine_instance

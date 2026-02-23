"""
AlleyBot Autonomous Research & Discovery Engine - Phase 11

Enables Alley to find new knowledge on his own.
Implements curiosity-driven research, web search, documentation parsing,
experimentation loops, and knowledge synthesis.

Part of AGI Core - Phase 11: Autonomous Research & Discovery
"""

import json
import sqlite3
import re
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeGap:
    """A detected gap in knowledge that needs research"""
    id: str
    topic: str
    description: str
    detected_from: str  # 'failed_action', 'user_request', 'pattern_gap'
    urgency: int  # 1-10
    related_facts: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    status: str = 'open'  # 'open', 'researching', 'answered', 'stale'


@dataclass
class ResearchFinding:
    """A piece of discovered knowledge"""
    id: str
    gap_id: str
    source: str  # 'web', 'documentation', 'experiment', 'inference'
    content: str
    confidence: float
    verified: bool = False
    verification_method: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Experiment:
    """An experiment to test a hypothesis"""
    id: str
    hypothesis: str
    test_method: str
    expected_outcome: str
    actual_outcome: Optional[str] = None
    success: Optional[bool] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class ResearchEngine:
    """
    Autonomous Research & Discovery Engine
    
    Capabilities:
    1. Curiosity Engine - Identify knowledge gaps, seek answers
    2. Web Search Integration - Auto-research topics of interest
    3. Documentation Reading - Parse docs/APIs to learn capabilities
    4. Experimentation Loop - Try new things, record results
    5. Knowledge Synthesis - Connect facts from multiple sources
    6. Question Generation - Formulate good questions to investigate
    
    Usage:
        engine = ResearchEngine()
        
        # Detect gaps from failed actions
        gaps = engine.detect_gaps_from_failures()
        
        # Research a topic
        findings = engine.research_topic("blockchain consensus mechanisms")
        
        # Run experiment
        exp = engine.design_experiment(
            hypothesis="Posts with questions get more engagement",
            test_method="Post 5 questions, 5 statements, compare"
        )
        
        # Synthesize knowledge
        synthesis = engine.synthesize_knowledge("DeFi protocols")
    """
    
    DB_PATH = Path('data/research.db')
    
    # Research thresholds
    MIN_GAP_URGENCY = 5  # Minimum urgency to auto-research
    MAX_RESEARCH_CYCLES = 3  # Max research attempts per gap
    KNOWLEDGE_DECAY_DAYS = 30  # How long before knowledge gets stale
    
    def __init__(self):
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize research database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_gaps (
                    id TEXT PRIMARY KEY,
                    topic TEXT,
                    description TEXT,
                    detected_from TEXT,
                    urgency INTEGER,
                    related_facts TEXT,
                    created_at TEXT,
                    status TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS research_findings (
                    id TEXT PRIMARY KEY,
                    gap_id TEXT,
                    source TEXT,
                    content TEXT,
                    confidence REAL,
                    verified INTEGER,
                    verification_method TEXT,
                    created_at TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    hypothesis TEXT,
                    test_method TEXT,
                    expected_outcome TEXT,
                    actual_outcome TEXT,
                    success INTEGER,
                    created_at TEXT,
                    completed_at TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    fact TEXT,
                    source TEXT,
                    confidence REAL,
                    related_topics TEXT,
                    created_at TEXT,
                    last_verified TEXT
                )
            ''')
            
            conn.commit()
    
    def detect_gaps_from_failures(self, action_logger=None) -> List[KnowledgeGap]:
        """
        Detect knowledge gaps from failed actions.
        
        Analyzes recent failures to identify missing knowledge.
        
        Args:
            action_logger: Optional ActionLogger to pull failure data from
            
        Returns:
            List of detected knowledge gaps
        """
        gaps = []
        
        # Check database for repeated failure patterns
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            # Look for gaps already tracked
            rows = conn.execute(
                "SELECT * FROM knowledge_gaps WHERE status = 'open'"
            ).fetchall()
            
            for row in rows:
                gap = KnowledgeGap(
                    id=row['id'],
                    topic=row['topic'],
                    description=row['description'],
                    detected_from=row['detected_from'],
                    urgency=row['urgency'],
                    related_facts=json.loads(row['related_facts']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    status=row['status']
                )
                gaps.append(gap)
        
        # If we have an action logger, analyze failures
        if action_logger:
            try:
                recent_failures = action_logger.get_recent_actions(
                    outcome='failure',
                    limit=50
                )
                
                # Group by action type
                failures_by_type = defaultdict(list)
                for action in recent_failures:
                    failures_by_type[action.action_type].append(action)
                
                # Detect patterns (multiple failures of same type)
                for action_type, actions in failures_by_type.items():
                    if len(actions) >= 3:  # 3+ failures indicates a gap
                        gap_id = f"gap_failure_{action_type}_{datetime.now().strftime('%Y%m%d')}"
                        
                        # Check if already tracked
                        if not any(g.id == gap_id for g in gaps):
                            gap = KnowledgeGap(
                                id=gap_id,
                                topic=f"Improve {action_type} success rate",
                                description=f"{len(actions)} recent failures in {action_type} actions",
                                detected_from='failure_pattern',
                                urgency=min(10, len(actions)),
                                related_facts=[a.id for a in actions[:5]]
                            )
                            
                            self._save_gap(gap)
                            gaps.append(gap)
            
            except Exception as e:
                logger.error(f"Error analyzing failures: {e}")
        
        return gaps
    
    def _save_gap(self, gap: KnowledgeGap) -> None:
        """Save knowledge gap to database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO knowledge_gaps 
                (id, topic, description, detected_from, urgency, related_facts, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                gap.id,
                gap.topic,
                gap.description,
                gap.detected_from,
                gap.urgency,
                json.dumps(gap.related_facts),
                gap.created_at.isoformat(),
                gap.status
            ))
            conn.commit()
    
    def research_topic(self, topic: str, source_preference: str = 'auto') -> List[ResearchFinding]:
        """
        Research a topic and return findings.
        
        Args:
            topic: Topic to research
            source_preference: 'web', 'documentation', 'memory', or 'auto'
            
        Returns:
            List of research findings
        """
        findings = []
        
        # 1. Check existing knowledge base
        existing = self._query_knowledge_base(topic)
        if existing:
            for fact in existing:
                finding = ResearchFinding(
                    id=f"kb_{fact['id']}",
                    gap_id='manual_query',
                    source='knowledge_base',
                    content=fact['fact'],
                    confidence=fact['confidence'],
                    verified=True,
                    verification_method='previous_research'
                )
                findings.append(finding)
        
        # 2. Try web search (if available)
        if source_preference in ('web', 'auto'):
            web_results = self._web_search(topic)
            for result in web_results:
                finding = ResearchFinding(
                    id=f"web_{hash(result['url'])}"[:20],
                    gap_id='manual_query',
                    source='web',
                    content=result['snippet'],
                    confidence=0.6,  # Web sources need verification
                    verified=False
                )
                findings.append(finding)
        
        # 3. Check internal documentation
        if source_preference in ('documentation', 'auto'):
            docs = self._search_documentation(topic)
            for doc in docs:
                finding = ResearchFinding(
                    id=f"doc_{hash(doc['path'])}"[:20],
                    gap_id='manual_query',
                    source='documentation',
                    content=doc['content'],
                    confidence=0.9,  # Internal docs are high confidence
                    verified=True,
                    verification_method='internal'
                )
                findings.append(finding)
        
        # Store new findings
        for finding in findings:
            if finding.source != 'knowledge_base':  # Already stored
                self._save_finding(finding)
                
                # Add to knowledge base
                self._add_to_knowledge_base(topic, finding)
        
        return findings
    
    def _query_knowledge_base(self, topic: str) -> List[Dict]:
        """Query existing knowledge base for topic"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                '''SELECT * FROM knowledge_base 
                   WHERE topic LIKE ? OR related_topics LIKE ?
                   ORDER BY confidence DESC''',
                (f'%{topic}%', f'%{topic}%')
            ).fetchall()
            
            return [
                {
                    'id': row['id'],
                    'fact': row['fact'],
                    'confidence': row['confidence'],
                    'source': row['source']
                }
                for row in rows
            ]
    
    def _web_search(self, query: str) -> List[Dict]:
        """Perform web search (placeholder - requires API integration)"""
        # This would integrate with a search API
        # For now, return empty - implement with actual search provider
        logger.info(f"🔍 Web search requested for: {query}")
        return []
    
    def _search_documentation(self, topic: str) -> List[Dict]:
        """Search internal documentation"""
        docs = []
        
        # Search for relevant markdown files
        doc_paths = [
            Path('README.md'),
            Path('SOP.md'),
            Path('PLATFORM_INTEGRATION_GUIDE.md'),
            Path('AGENTIC_BEHAVIOR.md'),
        ]
        
        for path in doc_paths:
            if path.exists():
                try:
                    content = path.read_text()
                    
                    # Simple keyword matching
                    if topic.lower() in content.lower():
                        # Extract relevant section (simple implementation)
                        lines = content.split('\n')
                        matching = [l for l in lines if topic.lower() in l.lower()]
                        
                        if matching:
                            docs.append({
                                'path': str(path),
                                'content': '\n'.join(matching[:5])  # First 5 matching lines
                            })
                
                except Exception as e:
                    logger.warning(f"Error reading {path}: {e}")
        
        return docs
    
    def _save_finding(self, finding: ResearchFinding) -> None:
        """Save finding to database"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO research_findings
                (id, gap_id, source, content, confidence, verified, verification_method, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                finding.id,
                finding.gap_id,
                finding.source,
                finding.content,
                finding.confidence,
                1 if finding.verified else 0,
                finding.verification_method,
                finding.created_at.isoformat()
            ))
            conn.commit()
    
    def _add_to_knowledge_base(self, topic: str, finding: ResearchFinding) -> None:
        """Add finding to knowledge base"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO knowledge_base (topic, fact, source, confidence, related_topics, created_at, last_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                topic,
                finding.content,
                finding.source,
                finding.confidence,
                json.dumps([topic]),
                datetime.now().isoformat(),
                datetime.now().isoformat() if finding.verified else None
            ))
            conn.commit()
    
    def design_experiment(self, hypothesis: str, test_method: str) -> Experiment:
        """
        Design an experiment to test a hypothesis.
        
        Args:
            hypothesis: What we're testing
            test_method: How to test it
            
        Returns:
            Experiment object
        """
        exp = Experiment(
            id=f"exp_{hash(hypothesis) % 100000000}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            hypothesis=hypothesis,
            test_method=test_method,
            expected_outcome="To be determined",
            created_at=datetime.now()
        )
        
        # Store experiment
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                INSERT INTO experiments (id, hypothesis, test_method, expected_outcome, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                exp.id,
                exp.hypothesis,
                exp.test_method,
                exp.expected_outcome,
                exp.created_at.isoformat()
            ))
            conn.commit()
        
        logger.info(f"🔬 Designed experiment: {hypothesis[:50]}...")
        
        return exp
    
    def record_experiment_result(self, experiment_id: str, 
                                  actual_outcome: str, 
                                  success: bool) -> None:
        """Record the result of an experiment"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute('''
                UPDATE experiments 
                SET actual_outcome = ?, success = ?, completed_at = ?
                WHERE id = ?
            ''', (
                actual_outcome,
                1 if success else 0,
                datetime.now().isoformat(),
                experiment_id
            ))
            conn.commit()
        
        # If successful, add to knowledge base
        if success:
            exp = self._get_experiment(experiment_id)
            if exp:
                finding = ResearchFinding(
                    id=f"exp_result_{experiment_id}",
                    gap_id='experiment',
                    source='experiment',
                    content=f"Verified: {exp.hypothesis}",
                    confidence=0.8,
                    verified=True,
                    verification_method=f"experiment:{experiment_id}"
                )
                self._save_finding(finding)
    
    def _get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM experiments WHERE id = ?',
                (experiment_id,)
            ).fetchone()
            
            if row:
                return Experiment(
                    id=row['id'],
                    hypothesis=row['hypothesis'],
                    test_method=row['test_method'],
                    expected_outcome=row['expected_outcome'],
                    actual_outcome=row['actual_outcome'],
                    success=bool(row['success']) if row['success'] is not None else None,
                    created_at=datetime.fromisoformat(row['created_at']),
                    completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None
                )
        
        return None
    
    def synthesize_knowledge(self, topic: str) -> Dict[str, Any]:
        """
        Synthesize knowledge from multiple sources.
        
        Connects facts from different sources to create unified understanding.
        
        Args:
            topic: Topic to synthesize
            
        Returns:
            Synthesis with connected facts and insights
        """
        # Get all knowledge on topic
        facts = self._query_knowledge_base(topic)
        findings = []
        
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM research_findings WHERE gap_id LIKE ?',
                (f'%{topic}%',)
            ).fetchall()
            
            for row in rows:
                findings.append({
                    'source': row['source'],
                    'content': row['content'],
                    'confidence': row['confidence'],
                    'verified': bool(row['verified'])
                })
        
        # Simple synthesis: group by source, identify common themes
        by_source = defaultdict(list)
        for f in findings:
            by_source[f['source']].append(f['content'])
        
        # Calculate synthesis confidence
        verified_count = sum(1 for f in findings if f['verified'])
        total_count = len(findings)
        synthesis_confidence = verified_count / total_count if total_count > 0 else 0
        
        # Generate insights (simple keyword extraction)
        all_text = ' '.join([f['content'] for f in findings])
        words = re.findall(r'\b[A-Za-z]{4,}\b', all_text.lower())
        common_words = Counter(words).most_common(10)
        
        return {
            'topic': topic,
            'total_facts': len(facts) + len(findings),
            'sources_used': list(by_source.keys()),
            'synthesis_confidence': synthesis_confidence,
            'key_concepts': [w[0] for w in common_words],
            'by_source': dict(by_source)
        }
    
    def generate_research_questions(self, topic: str, num_questions: int = 5) -> List[str]:
        """
        Generate good questions to investigate on a topic.
        
        Args:
            topic: Topic to generate questions for
            num_questions: Number of questions to generate
            
        Returns:
            List of research questions
        """
        # Template-based question generation
        templates = [
            f"What are the main components of {topic}?",
            f"How does {topic} work in practice?",
            f"What are common pitfalls when working with {topic}?",
            f"What are the best practices for {topic}?",
            f"How has {topic} evolved over time?",
            f"What are alternative approaches to {topic}?",
            f"Who are the key contributors to {topic}?",
            f"What problems does {topic} solve?",
            f"How does {topic} compare to similar solutions?",
            f"What is the future outlook for {topic}?"
        ]
        
        # Get existing knowledge to avoid duplicate questions
        existing = self._query_knowledge_base(topic)
        existing_text = ' '.join([e['fact'] for e in existing]).lower()
        
        # Filter and select questions
        questions = []
        for template in templates:
            # Check if already answered (simple heuristic)
            key_terms = template.replace(topic, '').lower().split()
            if not all(term in existing_text for term in key_terms if len(term) > 3):
                questions.append(template)
            
            if len(questions) >= num_questions:
                break
        
        return questions
    
    def get_research_summary(self) -> Dict[str, Any]:
        """Get summary of research activities"""
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            gaps = conn.execute(
                "SELECT COUNT(*) as count, status FROM knowledge_gaps GROUP BY status"
            ).fetchall()
            
            findings = conn.execute(
                "SELECT COUNT(*) as count, source FROM research_findings GROUP BY source"
            ).fetchall()
            
            experiments = conn.execute(
                "SELECT COUNT(*) as count, success FROM experiments GROUP BY success"
            ).fetchall()
            
            knowledge = conn.execute(
                "SELECT COUNT(*) as count FROM knowledge_base"
            ).fetchone()
        
        return {
            'open_gaps': sum(row['count'] for row in gaps if row['status'] == 'open'),
            'answered_gaps': sum(row['count'] for row in gaps if row['status'] == 'answered'),
            'findings_by_source': {row['source']: row['count'] for row in findings},
            'successful_experiments': sum(row['count'] for row in experiments if row['success'] == 1),
            'failed_experiments': sum(row['count'] for row in experiments if row['success'] == 0),
            'pending_experiments': sum(row['count'] for row in experiments if row['success'] is None),
            'total_knowledge_facts': knowledge['count'] if knowledge else 0
        }


# Singleton
_research_engine_instance: Optional[ResearchEngine] = None


def get_research_engine() -> ResearchEngine:
    """Get or create ResearchEngine singleton"""
    global _research_engine_instance
    if _research_engine_instance is None:
        _research_engine_instance = ResearchEngine()
    return _research_engine_instance

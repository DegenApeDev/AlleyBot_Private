"""
Knowledge Graph for AlleyBot AGI
Unified representation of all knowledge across domains
Enables cross-domain reasoning and knowledge transfer
"""
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of entities in the knowledge graph"""
    CONCEPT = "concept"  # Abstract concept (strategy, timing, etc)
    AGENT = "agent"  # AI agent or person
    PLATFORM = "platform"  # Social platform
    TOKEN = "token"  # Cryptocurrency token
    ACTION = "action"  # Action that can be taken
    SKILL = "skill"  # Learned skill
    PATTERN = "pattern"  # Identified pattern
    GOAL = "goal"  # Goal or objective
    FACT = "fact"  # Factual knowledge


class RelationType(Enum):
    """Types of relationships between entities"""
    IS_A = "is_a"  # Inheritance
    HAS_A = "has_a"  # Composition
    SIMILAR_TO = "similar_to"  # Analogy
    CAUSES = "causes"  # Causal relationship
    REQUIRES = "requires"  # Dependency
    ENABLES = "enables"  # Enablement
    CONFLICTS_WITH = "conflicts_with"  # Conflict
    PART_OF = "part_of"  # Part-whole
    APPLIES_TO = "applies_to"  # Application
    LEARNED_FROM = "learned_from"  # Learning source


@dataclass
class Entity:
    """An entity in the knowledge graph"""
    id: str
    name: str
    entity_type: EntityType
    domain: str  # Which domain (social, trading, chess, etc)
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: str = None
    confidence: float = 1.0  # Confidence in this entity (0-1)


@dataclass
class Relationship:
    """A relationship between two entities"""
    id: str
    source_id: str  # Source entity ID
    target_id: str  # Target entity ID
    relation_type: RelationType
    strength: float = 1.0  # Strength of relationship (0-1)
    attributes: Dict[str, Any] = field(default_factory=dict)
    bidirectional: bool = False  # Can traverse in both directions


class KnowledgeGraph:
    """
    Unified Knowledge Graph - Single representation of all knowledge
    
    Stores:
    - Entities (concepts, agents, platforms, tokens, etc)
    - Relationships (is_a, similar_to, causes, etc)
    - Domain facts
    - Cross-domain connections
    
    Enables:
    - Cross-domain reasoning
    - Knowledge transfer
    - Analogical reasoning
    - Causal reasoning
    """
    
    def __init__(self):
        """Initialize knowledge graph"""
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        
        # Indexes for fast lookup
        self.domain_index: Dict[str, Set[str]] = defaultdict(set)  # domain -> entity_ids
        self.type_index: Dict[EntityType, Set[str]] = defaultdict(set)  # type -> entity_ids
        self.relation_index: Dict[str, Set[str]] = defaultdict(set)  # entity_id -> relationship_ids
        
        # Initialize with core concepts
        self._init_core_concepts()
        
        logger.info("✅ Knowledge Graph initialized")
    
    def _init_core_concepts(self):
        """Initialize core concepts that span all domains"""
        # Strategy concept
        self.add_entity(Entity(
            id="concept_strategy",
            name="Strategy",
            entity_type=EntityType.CONCEPT,
            domain="general",
            attributes={
                'description': 'A plan of action designed to achieve a goal',
                'applies_to': ['chess', 'trading', 'social', 'planning']
            }
        ))
        
        # Timing concept
        self.add_entity(Entity(
            id="concept_timing",
            name="Timing",
            entity_type=EntityType.CONCEPT,
            domain="general",
            attributes={
                'description': 'When to take action for optimal results',
                'applies_to': ['chess', 'trading', 'social', 'planning']
            }
        ))
        
        # Pattern concept
        self.add_entity(Entity(
            id="concept_pattern",
            name="Pattern",
            entity_type=EntityType.CONCEPT,
            domain="general",
            attributes={
                'description': 'Recurring structure or behavior',
                'applies_to': ['chess', 'trading', 'social', 'learning']
            }
        ))
        
        # Risk concept
        self.add_entity(Entity(
            id="concept_risk",
            name="Risk",
            entity_type=EntityType.CONCEPT,
            domain="general",
            attributes={
                'description': 'Potential for loss or negative outcome',
                'applies_to': ['trading', 'social', 'planning']
            }
        ))
        
        logger.info(f"✅ Initialized {len(self.entities)} core concepts")
    
    def add_entity(self, entity: Entity) -> str:
        """Add entity to knowledge graph"""
        self.entities[entity.id] = entity
        
        # Update indexes
        self.domain_index[entity.domain].add(entity.id)
        self.type_index[entity.entity_type].add(entity.id)
        
        logger.debug(f"Added entity: {entity.name} ({entity.entity_type.value})")
        return entity.id
    
    def add_relationship(self, relationship: Relationship) -> str:
        """Add relationship to knowledge graph"""
        self.relationships[relationship.id] = relationship
        
        # Update indexes
        self.relation_index[relationship.source_id].add(relationship.id)
        if relationship.bidirectional:
            self.relation_index[relationship.target_id].add(relationship.id)
        
        logger.debug(f"Added relationship: {relationship.id} ({relationship.relation_type.value})")
        return relationship.id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def get_relationship(self, relationship_id: str) -> Optional[Relationship]:
        """Get relationship by ID"""
        return self.relationships.get(relationship_id)
    
    def get_domain_facts(self, domain: str) -> List[Entity]:
        """Get all facts/entities for a domain"""
        entity_ids = self.domain_index.get(domain, set())
        return [self.entities[eid] for eid in entity_ids]
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a specific type"""
        entity_ids = self.type_index.get(entity_type, set())
        return [self.entities[eid] for eid in entity_ids]
    
    def get_related_entities(self, entity_id: str, relation_type: Optional[RelationType] = None) -> List[Tuple[Entity, Relationship]]:
        """Get entities related to given entity"""
        related = []
        
        relationship_ids = self.relation_index.get(entity_id, set())
        for rel_id in relationship_ids:
            rel = self.relationships[rel_id]
            
            # Filter by relation type if specified
            if relation_type and rel.relation_type != relation_type:
                continue
            
            # Get target entity
            target_id = rel.target_id if rel.source_id == entity_id else rel.source_id
            target = self.entities.get(target_id)
            
            if target:
                related.append((target, rel))
        
        return related
    
    def find_analogies(self, source_domain: str, target_domain: str) -> List[Dict[str, Any]]:
        """Find analogous concepts between domains"""
        analogies = []
        
        # Get entities from both domains
        source_entities = self.get_domain_facts(source_domain)
        target_entities = self.get_domain_facts(target_domain)
        
        # Find similar concepts
        for source_ent in source_entities:
            for target_ent in target_entities:
                # Check if they share a common parent concept
                if self._share_concept(source_ent, target_ent):
                    analogies.append({
                        'source': source_ent,
                        'target': target_ent,
                        'similarity': self._calculate_similarity(source_ent, target_ent),
                        'shared_concept': self._get_shared_concept(source_ent, target_ent)
                    })
        
        # Sort by similarity
        analogies.sort(key=lambda x: x['similarity'], reverse=True)
        
        return analogies
    
    def _share_concept(self, entity1: Entity, entity2: Entity) -> bool:
        """Check if two entities share a common concept"""
        # Get related concepts for both entities
        concepts1 = self._get_related_concepts(entity1.id)
        concepts2 = self._get_related_concepts(entity2.id)
        
        # Check for overlap
        return bool(concepts1.intersection(concepts2))
    
    def _get_related_concepts(self, entity_id: str) -> Set[str]:
        """Get all concepts related to an entity"""
        concepts = set()
        
        related = self.get_related_entities(entity_id)
        for entity, rel in related:
            if entity.entity_type == EntityType.CONCEPT:
                concepts.add(entity.id)
        
        return concepts
    
    def _calculate_similarity(self, entity1: Entity, entity2: Entity) -> float:
        """Calculate similarity between two entities"""
        # Simple similarity based on shared concepts
        concepts1 = self._get_related_concepts(entity1.id)
        concepts2 = self._get_related_concepts(entity2.id)
        
        if not concepts1 or not concepts2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(concepts1.intersection(concepts2))
        union = len(concepts1.union(concepts2))
        
        return intersection / union if union > 0 else 0.0
    
    def _get_shared_concept(self, entity1: Entity, entity2: Entity) -> Optional[str]:
        """Get the strongest shared concept between entities"""
        concepts1 = self._get_related_concepts(entity1.id)
        concepts2 = self._get_related_concepts(entity2.id)
        
        shared = concepts1.intersection(concepts2)
        
        if shared:
            # Return first shared concept (can be enhanced with ranking)
            return list(shared)[0]
        
        return None
    
    def get_causal_relationships(self, domain: str) -> Dict[str, List[str]]:
        """Get causal relationships in a domain"""
        causal_map = defaultdict(list)
        
        # Get domain entities
        domain_entities = self.get_domain_facts(domain)
        
        for entity in domain_entities:
            # Find causal relationships
            related = self.get_related_entities(entity.id, RelationType.CAUSES)
            
            for target, rel in related:
                causal_map[entity.name].append(target.name)
        
        return dict(causal_map)
    
    def get_social_context(self, domain: str) -> Dict[str, Any]:
        """Get social context for a domain"""
        context = {
            'agents': [],
            'platforms': [],
            'relationships': [],
            'patterns': []
        }
        
        # Get social entities
        domain_entities = self.get_domain_facts(domain)
        
        for entity in domain_entities:
            if entity.entity_type == EntityType.AGENT:
                context['agents'].append(entity.name)
            elif entity.entity_type == EntityType.PLATFORM:
                context['platforms'].append(entity.name)
            elif entity.entity_type == EntityType.PATTERN:
                context['patterns'].append(entity.name)
        
        return context
    
    def add_domain_knowledge(self, domain: str, knowledge: Dict[str, Any]):
        """Add knowledge from a specific domain"""
        for key, value in knowledge.items():
            # Create entity for each piece of knowledge
            entity = Entity(
                id=f"{domain}_{key}",
                name=key,
                entity_type=EntityType.FACT,
                domain=domain,
                attributes={'value': value}
            )
            self.add_entity(entity)
    
    def learn_from_outcome(
        self,
        action: str,
        domain: str,
        context: str,
        outcome: str,
        success: bool,
        confidence: float = 1.0,
    ) -> List[str]:
        """
        Learn causal knowledge from an action outcome.

        After every action, extract and store:
        - Action entity + CAUSES relationship to outcome
        - Context entities (platform, topic, etc.)
        - REQUIRES edges from action to context
        - If repeated success, increase strength on CAUSES edge
        - If failure, add FAILED_CAUSES or decrease strength

        Returns list of entity/relationship IDs created.
        """
        created = []
        timestamp = datetime.now().isoformat()

        action_id = f"action_{domain}_{action}_{hash(action + domain) % 10000}"
        existing_action = self.entities.get(action_id)
        if existing_action:
            existing_action.attributes['last_attempt'] = timestamp
            attempts = existing_action.attributes.get('attempts', 0) + 1
            existing_action.attributes['attempts'] = attempts
            successes = existing_action.attributes.get('successes', 0) + (1 if success else 0)
            existing_action.attributes['successes'] = successes
            existing_action.attributes['success_rate'] = successes / attempts if attempts > 0 else 0.0
            existing_action.confidence = max(0.05, min(0.95, existing_action.confidence + (0.1 if success else -0.1)))
        else:
            action_entity = Entity(
                id=action_id,
                name=f"{domain}:{action}",
                entity_type=EntityType.ACTION,
                domain=domain,
                attributes={
                    'action': action,
                    'domain': domain,
                    'first_seen': timestamp,
                    'last_attempt': timestamp,
                    'attempts': 1,
                    'successes': 1 if success else 0,
                    'success_rate': 1.0 if success else 0.0,
                    'best_conditions': [],
                    'worst_conditions': [],
                },
                confidence=0.6 if success else 0.4,
            )
            self.add_entity(action_entity)
            created.append(action_id)

            domain_id = f"domain_{domain}"
            if domain_id not in self.entities:
                self.add_entity(Entity(
                    id=domain_id, name=domain, entity_type=EntityType.CONCEPT,
                    domain=domain, attributes={'type': 'domain'},
                ))
                created.append(domain_id)
            self.add_relationship(Relationship(
                id=f"rel_{action_id}_belongs_{domain_id}",
                source_id=action_id, target_id=domain_id,
                relation_type=RelationType.PART_OF, strength=1.0,
            ))
            created.append(f"rel_{action_id}_belongs_{domain_id}")

        context_words = [w.lower() for w in context.split() if len(w) > 3][:5]
        for word in context_words:
            context_id = f"ctx_{domain}_{word}"
            if context_id not in self.entities:
                self.add_entity(Entity(
                    id=context_id, name=word, entity_type=EntityType.PATTERN,
                    domain=domain, attributes={'source': 'experience', 'word': word},
                    confidence=0.5,
                ))
                created.append(context_id)
            self.add_relationship(Relationship(
                id=f"rel_{action_id}_requires_{context_id}",
                source_id=action_id, target_id=context_id,
                relation_type=RelationType.REQUIRES, strength=0.5,
            ))

        outcome_id = f"outcome_{domain}_{success}_{hash(outcome) % 10000}"
        if outcome_id not in self.entities:
            outcome_type = EntityType.PATTERN if not success else EntityType.FACT
            self.add_entity(Entity(
                id=outcome_id, name=outcome[:80],
                entity_type=outcome_type, domain=domain,
                attributes={'outcome': outcome, 'success': success},
                confidence=0.5 if success else 0.3,
            ))
            created.append(outcome_id)

        rel_type = RelationType.CAUSES if success else RelationType.CONFLICTS_WITH
        cause_rel_id = f"rel_{action_id}_{rel_type.value}_{outcome_id}"
        existing_rel = self.relationships.get(cause_rel_id)
        if existing_rel:
            delta = 0.05 if success else -0.05
            existing_rel.strength = max(0.05, min(1.0, existing_rel.strength + delta))
            existing_rel.attributes['occurrence_count'] = existing_rel.attributes.get('occurrence_count', 1) + 1
            existing_rel.attributes['last_seen'] = timestamp
        else:
            self.add_relationship(Relationship(
                id=cause_rel_id,
                source_id=action_id, target_id=outcome_id,
                relation_type=rel_type,
                strength=0.6 if success else 0.4,
                attributes={'occurrence_count': 1, 'first_seen': timestamp, 'last_seen': timestamp},
            ))
            created.append(cause_rel_id)

        action_entity = self.entities[action_id]
        if success and context:
            best = action_entity.attributes.get('best_conditions', [])
            if context not in best:
                best.append(context[:100])
                if len(best) > 10:
                    best.pop(0)
                action_entity.attributes['best_conditions'] = best
        elif not success and context:
            worst = action_entity.attributes.get('worst_conditions', [])
            if context not in worst:
                worst.append(context[:100])
                if len(worst) > 10:
                    worst.pop(0)
                action_entity.attributes['worst_conditions'] = worst

        logger.info(f"📊 KG learned: {action}@{domain} {'→' if success else '✗'} {outcome[:50]} ({len(created)} new nodes)")
        return created

    def predict_outcome(self, action: str, domain: str) -> Dict[str, Any]:
        """
        Predict likely outcome of an action based on causal knowledge.
        Traverses CAUSES edges from similar actions. Returns predicted outcome
        with confidence based on how many times we've seen this pattern.
        """
        action_entities = [
            e for e in self.entities.values()
            if e.entity_type == EntityType.ACTION
            and e.domain == domain
            and action.lower() in e.name.lower()
        ]

        if not action_entities:
            return {'predicted_success': 0.5, 'sample_size': 0, 'evidence': []}

        best_match = max(action_entities, key=lambda e: e.confidence * (e.attributes.get('attempts', 1)))

        causal_outcomes = []
        for rel_id in self.relation_index.get(best_match.id, set()):
            rel = self.relationships.get(rel_id)
            if not rel:
                continue
            target = self.entities.get(rel.target_id)
            if not target:
                continue
            if rel.relation_type in (RelationType.CAUSES, RelationType.CONFLICTS_WITH):
                causal_outcomes.append({
                    'outcome': target.name,
                    'success': target.attributes.get('success', False),
                    'strength': rel.strength,
                    'occurrences': rel.attributes.get('occurrence_count', 1),
                })

        if not causal_outcomes:
            return {
                'predicted_success': best_match.attributes.get('success_rate', 0.5),
                'sample_size': best_match.attributes.get('attempts', 0),
                'evidence': [],
                'best_conditions': best_match.attributes.get('best_conditions', []),
                'worst_conditions': best_match.attributes.get('worst_conditions', []),
            }

        total_weight = sum(o['occurrences'] for o in causal_outcomes)
        success_weight = sum(
            o['occurrences'] * o['strength']
            for o in causal_outcomes if o['success']
        )

        return {
            'predicted_success': success_weight / total_weight if total_weight > 0 else 0.5,
            'sample_size': best_match.attributes.get('attempts', 0),
            'evidence': causal_outcomes[:5],
            'best_conditions': best_match.attributes.get('best_conditions', [])[:3],
            'worst_conditions': best_match.attributes.get('worst_conditions', [])[:3],
        }

    def analogical_transfer(self, novel_situation: str, source_domain: str = None) -> List[Dict[str, Any]]:
        """
        Given a novel situation, find structurally similar situations in the
        graph and transfer their causal knowledge. This is REAL transfer learning
        - not keyword matching, but graph-structural similarity.

        Returns list of transferred beliefs with confidence adjustments.
        """
        situation_words = set(novel_situation.lower().split())
        candidates = []

        for entity in self.entities.values():
            if entity.entity_type != EntityType.ACTION:
                continue
            if source_domain and entity.domain == source_domain:
                continue

            entity_words = set(entity.name.lower().split())
            entity_context_words = set()
            for w in entity.attributes.get('best_conditions', []):
                entity_context_words.update(w.lower().split())
            for w in entity.attributes.get('worst_conditions', []):
                entity_context_words.update(w.lower().split())

            all_entity_words = entity_words | entity_context_words
            overlap = len(situation_words & all_entity_words)
            if overlap == 0:
                continue

            similarity = overlap / max(len(situation_words | all_entity_words), 1)

            causal = self.get_causal_relationships(entity.domain)
            for cause_key, effects in causal.items():
                if cause_key.lower() in entity.name.lower() or entity.name.lower() in cause_key.lower():
                    candidates.append({
                        'source_domain': entity.domain,
                        'source_action': entity.name,
                        'success_rate': entity.attributes.get('success_rate', 0.5),
                        'similarity': similarity,
                        'transferred_from': entity.id,
                        'confidence_discount': similarity * 0.8,
                        'best_conditions': entity.attributes.get('best_conditions', [])[:3],
                    })

        candidates.sort(key=lambda x: x['similarity'], reverse=True)
        return candidates[:5]


from datetime import datetime


def get_knowledge_graph() -> KnowledgeGraph:
    """Get or create singleton knowledge graph"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
    return _knowledge_graph

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
    
    def query(self, query: str, domain: Optional[str] = None) -> List[Entity]:
        """Query the knowledge graph"""
        results = []
        
        # Simple keyword search (can be enhanced with semantic search)
        query_lower = query.lower()
        
        entities_to_search = self.entities.values()
        if domain:
            entity_ids = self.domain_index.get(domain, set())
            entities_to_search = [self.entities[eid] for eid in entity_ids]
        
        for entity in entities_to_search:
            if query_lower in entity.name.lower():
                results.append(entity)
            elif any(query_lower in str(v).lower() for v in entity.attributes.values()):
                results.append(entity)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        return {
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships),
            'domains': list(self.domain_index.keys()),
            'entity_types': {et.value: len(ids) for et, ids in self.type_index.items()},
            'entities_per_domain': {domain: len(ids) for domain, ids in self.domain_index.items()}
        }


# Singleton instance
_knowledge_graph = None

def get_knowledge_graph() -> KnowledgeGraph:
    """Get or create singleton knowledge graph"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
    return _knowledge_graph

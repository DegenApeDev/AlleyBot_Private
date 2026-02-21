"""
Recursive Strategy Engine - Phase 3 Upgrade for AlleyBot AGI

Implements the recursive AGI flow with:
- 7-phase strategic loop (Phase 1-7)
- Root Cause Analysis (RCA) for recursive correction
- Phase 8: Synergy Audit with cryptographic validation
- Memory Registry integration
- Self-Correction mechanisms
- A2A Tier 3 outsourcing

Replaces sequential logic with recursive AGI flow per directive.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable, Tuple
from pathlib import Path
import json

from lib.synergy_gate import (
    get_synergy_gate, 
    SyModValidationResult, 
    RCAType,
    ValidationQuote
)

logger = logging.getLogger(__name__)


class PhaseStatus(Enum):
    """Status of each phase in the recursive loop"""
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    RECURSING = auto()


@dataclass
class PhaseResult:
    """Result from executing a phase"""
    phase_name: str
    status: PhaseStatus
    output: Any = None
    confidence: float = 0.0
    recursion_depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RecursiveTask:
    """A task being processed through the recursive loop"""
    task_id: str
    task_type: str
    inputs: Dict[str, Any]
    
    # Phase tracking
    phase_results: List[PhaseResult] = field(default_factory=list)
    current_phase: int = 1
    
    # Recursive tracking
    recursion_depth: int = 0
    max_recursion_depth: int = 5
    
    # LTM references
    similar_tasks: List[str] = field(default_factory=list)
    relevant_memories: List[str] = field(default_factory=list)
    
    # Status
    status: str = "pending"  # pending, running, completed, failed
    final_output: Any = None
    validation_quote: Optional[ValidationQuote] = None
    lesson_learned: str = ""


class Phase1Understanding:
    """
    Phase 1: Understanding
    Query LTM for similar past tasks before proceeding
    """
    
    def __init__(self, memory_system=None):
        self.memory = memory_system
    
    async def execute(self, task: RecursiveTask) -> PhaseResult:
        """
        Query LTM for similar tasks and extract patterns
        """
        logger.info(f"[Phase 1] Understanding task: {task.task_id}")
        
        # Query LTM for similar tasks
        similar = await self._query_ltm(task)
        task.similar_tasks = similar
        
        # Extract common patterns
        patterns = self._extract_patterns(similar)
        
        # Build understanding context
        understanding = {
            'task_type': task.task_type,
            'similar_tasks_found': len(similar),
            'patterns': patterns,
            'novelty_score': self._calculate_novelty(task, similar)
        }
        
        confidence = 0.9 if similar else 0.6  # Lower confidence if no similar tasks
        
        return PhaseResult(
            phase_name="Phase 1: Understanding",
            status=PhaseStatus.COMPLETED,
            output=understanding,
            confidence=confidence,
            metadata={'similar_tasks': similar}
        )
    
    async def _query_ltm(self, task: RecursiveTask) -> List[str]:
        """Query long-term memory for similar tasks"""
        # Would integrate with actual memory system
        # For now, return empty (would query vector DB in production)
        return []
    
    def _extract_patterns(self, similar_tasks: List[str]) -> List[str]:
        """Extract common success patterns from similar tasks"""
        return []
    
    def _calculate_novelty(self, task: RecursiveTask, similar: List[str]) -> float:
        """Calculate how novel this task is (0 = common, 1 = completely new)"""
        if not similar:
            return 1.0
        return max(0.0, 1.0 - (len(similar) * 0.1))


class Phase2Contextualizing:
    """
    Phase 2: Contextualizing
    Load relevant memories and build context
    """
    
    def __init__(self, memory_system=None):
        self.memory = memory_system
    
    async def execute(self, task: RecursiveTask, phase1_result: PhaseResult) -> PhaseResult:
        """
        Load relevant memories based on understanding
        """
        logger.info(f"[Phase 2] Contextualizing task: {task.task_id}")
        
        # Load memories related to task type
        memories = await self._load_relevant_memories(task, phase1_result)
        task.relevant_memories = memories
        
        # Build comprehensive context
        context = {
            'task_inputs': task.inputs,
            'understanding': phase1_result.output,
            'relevant_memories': memories,
            'current_world_state': await self._get_world_state(),
            'recent_outcomes': await self._get_recent_outcomes(task.task_type)
        }
        
        confidence = 0.85 if memories else 0.7
        
        return PhaseResult(
            phase_name="Phase 2: Contextualizing",
            status=PhaseStatus.COMPLETED,
            output=context,
            confidence=confidence,
            metadata={'memories_loaded': len(memories)}
        )
    
    async def _load_relevant_memories(self, task: RecursiveTask, understanding: PhaseResult) -> List[str]:
        """Load memories relevant to this task"""
        return []
    
    async def _get_world_state(self) -> Dict:
        """Get current world state"""
        return {}
    
    async def _get_recent_outcomes(self, task_type: str) -> List[Dict]:
        """Get recent outcomes for similar tasks"""
        return []


class Phase3Strategizing:
    """
    Phase 3: Strategizing - RECURSIVE CORE
    Generate approaches and validate through Synergy Gate
    """
    
    def __init__(self):
        self.synergy_gate = get_synergy_gate(threshold=0.85)
    
    async def execute(self, task: RecursiveTask, context: Dict) -> PhaseResult:
        """
        Generate strategy with recursive validation
        """
        logger.info(f"[Phase 3] Strategizing task: {task.task_id} (depth={task.recursion_depth})")
        
        # Generate strategy hypotheses
        strategies = self._generate_strategies(context)
        
        # Validate each through Synergy Gate
        valid_strategies = []
        for strategy in strategies:
            validation_data = {
                'content': str(strategy),
                'recursion_depth': task.recursion_depth,
                'urgency': 1.0
            }
            
            result = self.synergy_gate.validate_thought(
                validation_data,
                action_type=task.task_type,
                is_high_stakes=True
            )
            
            can_exec, reason = result.can_execute(0.85)
            
            if can_exec:
                valid_strategies.append({
                    'strategy': strategy,
                    'validation': result,
                    'confidence': result.confidence
                })
            else:
                logger.warning(f"[Phase 3] Strategy rejected: {reason}")
        
        if not valid_strategies:
            # No valid strategies - trigger RCA
            logger.error(f"[Phase 3] No valid strategies - triggering RCA")
            return PhaseResult(
                phase_name="Phase 3: Strategizing",
                status=PhaseStatus.FAILED,
                output=None,
                confidence=0.0,
                recursion_depth=task.recursion_depth,
                metadata={'rca_required': True, 'reason': 'No valid strategies'}
            )
        
        # Select best strategy
        best = max(valid_strategies, key=lambda x: x['confidence'])
        
        return PhaseResult(
            phase_name="Phase 3: Strategizing",
            status=PhaseStatus.COMPLETED,
            output=best['strategy'],
            confidence=best['confidence'],
            recursion_depth=task.recursion_depth,
            metadata={
                'strategies_generated': len(strategies),
                'strategies_valid': len(valid_strategies),
                'validation_result': best['validation']
            }
        )
    
    def _generate_strategies(self, context: Dict) -> List[Dict]:
        """Generate strategy hypotheses"""
        # In production, this would use LLM to generate approaches
        return [{'approach': 'standard', 'params': {}}]


class Phase4ConfidenceCheck:
    """
    Phase 4: Confidence Check
    If Low → RCA; If High → proceed
    """
    
    def __init__(self):
        self.synergy_gate = get_synergy_gate()
    
    async def execute(self, task: RecursiveTask, phase3_result: PhaseResult) -> PhaseResult:
        """
        Check confidence and decide: proceed or RCA
        """
        logger.info(f"[Phase 4] Confidence Check for task: {task.task_id}")
        
        confidence = phase3_result.confidence
        
        if confidence >= 0.85:
            return PhaseResult(
                phase_name="Phase 4: Confidence Check",
                status=PhaseStatus.COMPLETED,
                output={'decision': 'PROCEED', 'confidence': confidence},
                confidence=confidence,
                recursion_depth=task.recursion_depth
            )
        else:
            # Low confidence - perform RCA
            rca_type = self.synergy_gate.perform_rca(
                phase3_result.metadata.get('validation_result')
            )
            
            return PhaseResult(
                phase_name="Phase 4: Confidence Check",
                status=PhaseStatus.RECURSING,  # Signal to recurse
                output={
                    'decision': 'RCA',
                    'confidence': confidence,
                    'rca_type': rca_type
                },
                confidence=confidence,
                recursion_depth=task.recursion_depth,
                metadata={'rca_type': rca_type}
            )


class Phase5Execution:
    """
    Phase 5: Execution
    Execute the validated strategy
    """
    
    async def execute(self, task: RecursiveTask, strategy: Dict) -> PhaseResult:
        """
        Execute the strategy
        """
        logger.info(f"[Phase 5] Executing task: {task.task_id}")
        
        try:
            # Execute based on task type
            result = await self._execute_strategy(task, strategy)
            
            return PhaseResult(
                phase_name="Phase 5: Execution",
                status=PhaseStatus.COMPLETED,
                output=result,
                confidence=0.95,
                recursion_depth=task.recursion_depth
            )
        except Exception as e:
            logger.error(f"[Phase 5] Execution failed: {e}")
            return PhaseResult(
                phase_name="Phase 5: Execution",
                status=PhaseStatus.FAILED,
                output={'error': str(e)},
                confidence=0.0,
                recursion_depth=task.recursion_depth
            )
    
    async def _execute_strategy(self, task: RecursiveTask, strategy: Dict) -> Any:
        """Execute the strategy - override in subclasses"""
        return {'status': 'executed', 'strategy': strategy}


class Phase6Output:
    """
    Phase 6: Output
    Generate and format output
    """
    
    async def execute(self, task: RecursiveTask, execution_result: PhaseResult) -> PhaseResult:
        """
        Format the output
        """
        logger.info(f"[Phase 6] Generating output for task: {task.task_id}")
        
        output = {
            'task_id': task.task_id,
            'result': execution_result.output,
            'execution_confidence': execution_result.confidence,
            'phases_completed': len(task.phase_results) + 1
        }
        
        return PhaseResult(
            phase_name="Phase 6: Output",
            status=PhaseStatus.COMPLETED,
            output=output,
            confidence=execution_result.confidence,
            recursion_depth=task.recursion_depth
        )


class Phase7Outcome:
    """
    Phase 7: Success/Failure Determination
    """
    
    async def execute(self, task: RecursiveTask, output_result: PhaseResult) -> PhaseResult:
        """
        Determine final outcome
        """
        logger.info(f"[Phase 7] Outcome for task: {task.task_id}")
        
        success = output_result.status == PhaseStatus.COMPLETED and output_result.confidence > 0.5
        
        outcome = {
            'success': success,
            'output': output_result.output,
            'total_recursion_depth': task.recursion_depth,
            'phases': [r.phase_name for r in task.phase_results]
        }
        
        return PhaseResult(
            phase_name="Phase 7: Outcome",
            status=PhaseStatus.COMPLETED,
            output=outcome,
            confidence=1.0 if success else 0.0,
            recursion_depth=task.recursion_depth
        )


class Phase8SynergyAudit:
    """
    Phase 8: Synergy Audit
    Final gate before completion - cryptographic validation
    """
    
    def __init__(self):
        self.synergy_gate = get_synergy_gate()
        self.code_version = self._get_code_version()
    
    async def execute(self, task: RecursiveTask, outcome_result: PhaseResult) -> PhaseResult:
        """
        Perform final Synergy Audit and generate validation quote
        """
        logger.info(f"[Phase 8] Synergy Audit for task: {task.task_id}")
        
        # Generate validation quote
        quote = self.synergy_gate.generate_validation_quote(
            task_id=task.task_id,
            code_version=self.code_version,
            inputs=task.inputs,
            outputs=outcome_result.output,
            symod_result=task.phase_results[-1].metadata.get('validation_result') if task.phase_results else None
        )
        
        task.validation_quote = quote
        
        # Log for ERC-8004 submission
        logger.info(f"[Phase 8] Validation Quote: {quote.generate_hash()}")
        
        audit_result = {
            'validation_quote_hash': quote.generate_hash(),
            'attestation': quote.attestation_signature,
            'registry_ready': True
        }
        
        return PhaseResult(
            phase_name="Phase 8: Synergy Audit",
            status=PhaseStatus.COMPLETED,
            output=audit_result,
            confidence=1.0,
            recursion_depth=task.recursion_depth,
            metadata={'quote': quote}
        )
    
    def _get_code_version(self) -> str:
        """Get current code version hash"""
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  capture_output=True, text=True)
            return result.stdout.strip() or "unknown"
        except:
            return "unknown"


class RootCauseAnalysis:
    """
    Root Cause Analysis (RCA) Handler
    """
    
    def __init__(self):
        self.synergy_gate = get_synergy_gate()
        self.web_search_available = False
        self.refactor_available = True
        self.a2a_available = False
    
    async def handle(self, task: RecursiveTask, rca_type: RCAType) -> PhaseResult:
        """
        Handle RCA based on type
        """
        logger.info(f"[RCA] Handling type {rca_type.value} for task: {task.task_id}")
        
        if rca_type == RCAType.MISSING_DATA:
            return await self._handle_missing_data(task)
        elif rca_type == RCAType.LOGIC_ERROR:
            return await self._handle_logic_error(task)
        elif rca_type == RCAType.RESOURCE_CONSTRAINT:
            return await self._handle_resource_constraint(task)
        else:
            return await self._handle_unknown(task)
    
    async def _handle_missing_data(self, task: RecursiveTask) -> PhaseResult:
        """Trigger Autonomous Web Search for missing data"""
        logger.info(f"[RCA] Triggering Autonomous Web Search")
        
        # Would trigger web search here
        # For now, simulate data acquisition
        
        return PhaseResult(
            phase_name="RCA: Autonomous Web Search",
            status=PhaseStatus.COMPLETED,
            output={'data_acquired': True, 'source': 'web_search'},
            confidence=0.7,
            recursion_depth=task.recursion_depth + 1
        )
    
    async def _handle_logic_error(self, task: RecursiveTask) -> PhaseResult:
        """Trigger Self Code Refactor for logic error"""
        logger.info(f"[RCA] Triggering Self Code Refactor")
        
        # Would trigger code refactoring here
        
        return PhaseResult(
            phase_name="RCA: Self Code Refactor",
            status=PhaseStatus.COMPLETED,
            output={'refactored': True, 'changes': []},
            confidence=0.8,
            recursion_depth=task.recursion_depth + 1
        )
    
    async def _handle_resource_constraint(self, task: RecursiveTask) -> PhaseResult:
        """Escalate to Tier 3 via A2A"""
        logger.info(f"[RCA] Escalating to Tier 3 via A2A")
        
        return PhaseResult(
            phase_name="RCA: A2A Tier 3 Escalation",
            status=PhaseStatus.COMPLETED,
            output={'outsourced': True, 'tier': 3},
            confidence=0.9,
            recursion_depth=task.recursion_depth + 1
        )
    
    async def _handle_unknown(self, task: RecursiveTask) -> PhaseResult:
        """Handle unknown RCA type"""
        return PhaseResult(
            phase_name="RCA: Unknown",
            status=PhaseStatus.FAILED,
            output={'error': 'Unknown RCA type'},
            confidence=0.0,
            recursion_depth=task.recursion_depth + 1
        )


class RecursiveStrategyEngine:
    """
    Main Recursive Strategy Engine
    Orchestrates all 8 phases with recursive loops
    """
    
    def __init__(self, memory_system=None):
        self.memory_system = memory_system
        
        # Phase handlers
        self.phase1 = Phase1Understanding(memory_system)
        self.phase2 = Phase2Contextualizing(memory_system)
        self.phase3 = Phase3Strategizing()
        self.phase4 = Phase4ConfidenceCheck()
        self.phase5 = Phase5Execution()
        self.phase6 = Phase6Output()
        self.phase7 = Phase7Outcome()
        self.phase8 = Phase8SynergyAudit()
        
        # RCA handler
        self.rca_handler = RootCauseAnalysis()
        
        # Task registry
        self.tasks: Dict[str, RecursiveTask] = {}
        
        logger.info("🔄 Recursive Strategy Engine initialized (Tier 2 Cryptographic Trust)")
    
    async def run_task(self, task_type: str, inputs: Dict[str, Any], 
                      task_id: Optional[str] = None) -> RecursiveTask:
        """
        Run a task through the full 8-phase recursive loop
        """
        task = RecursiveTask(
            task_id=task_id or self._generate_task_id(),
            task_type=task_type,
            inputs=inputs,
            status="running"
        )
        
        self.tasks[task.task_id] = task
        
        try:
            # Execute recursive loop
            await self._execute_recursive_loop(task)
            
            # Store lesson learned
            await self._store_lesson_learned(task)
            
            task.status = "completed"
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            task.status = "failed"
        
        return task
    
    async def _execute_recursive_loop(self, task: RecursiveTask):
        """Execute the full 8-phase loop with recursion handling"""
        
        while task.current_phase <= 8 and task.recursion_depth <= task.max_recursion_depth:
            
            if task.current_phase == 1:
                result = await self.phase1.execute(task)
                task.phase_results.append(result)
                task.current_phase = 2
                
            elif task.current_phase == 2:
                result = await self.phase2.execute(task, task.phase_results[0].output)
                task.phase_results.append(result)
                task.current_phase = 3
                
            elif task.current_phase == 3:
                result = await self.phase3.execute(task, task.phase_results[1].output)
                task.phase_results.append(result)
                
                if result.status == PhaseStatus.FAILED:
                    # Trigger RCA and recurse
                    await self._handle_recursion(task, RCAType.LOGIC_ERROR)
                    continue
                
                task.current_phase = 4
                
            elif task.current_phase == 4:
                result = await self.phase4.execute(task, task.phase_results[2])
                task.phase_results.append(result)
                
                if result.status == PhaseStatus.RECURSING:
                    # RCA triggered
                    rca_type = result.metadata.get('rca_type')
                    await self._handle_recursion(task, rca_type)
                    continue
                
                task.current_phase = 5
                
            elif task.current_phase == 5:
                strategy = task.phase_results[2].output
                result = await self.phase5.execute(task, strategy)
                task.phase_results.append(result)
                task.current_phase = 6
                
            elif task.current_phase == 6:
                result = await self.phase6.execute(task, task.phase_results[4])
                task.phase_results.append(result)
                task.current_phase = 7
                
            elif task.current_phase == 7:
                result = await self.phase7.execute(task, task.phase_results[5])
                task.phase_results.append(result)
                task.current_phase = 8
                
            elif task.current_phase == 8:
                result = await self.phase8.execute(task, task.phase_results[6])
                task.phase_results.append(result)
                
                # Final check - if audit fails, recurse
                if result.status == PhaseStatus.FAILED:
                    await self._handle_recursion(task, RCAType.LOGIC_ERROR)
                    continue
                
                task.current_phase = 9  # Done
                break
    
    async def _handle_recursion(self, task: RecursiveTask, rca_type: RCAType):
        """Handle recursive loop back to Phase 3"""
        
        task.recursion_depth += 1
        
        if task.recursion_depth > task.max_recursion_depth:
            raise RecursionError(f"Max recursion depth exceeded for task {task.task_id}")
        
        logger.warning(f"🔄 Recursion triggered for task {task.task_id}: {rca_type.value} (depth={task.recursion_depth})")
        
        # Handle RCA
        rca_result = await self.rca_handler.handle(task, rca_type)
        task.phase_results.append(rca_result)
        
        # Reset to Phase 3 for re-strategizing
        task.current_phase = 3
    
    async def _store_lesson_learned(self, task: RecursiveTask):
        """Store lesson learned from task completion"""
        
        # Extract lesson
        lesson = self._extract_lesson(task)
        task.lesson_learned = lesson
        
        # Store in LTM (would integrate with memory system)
        logger.info(f"🎓 Lesson learned stored for task {task.task_id}: {lesson[:100]}...")
    
    def _extract_lesson(self, task: RecursiveTask) -> str:
        """Extract lesson from completed task"""
        success = task.phase_results[-2].output.get('success', False) if len(task.phase_results) > 6 else False
        
        if success:
            return f"Task type '{task.task_type}' succeeded with strategy from recursion depth {task.recursion_depth}"
        else:
            return f"Task type '{task.task_type}' failed - review Phase 3 strategy generation"
    
    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        import uuid
        return f"task_{uuid.uuid4().hex[:8]}"
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a task"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            'task_id': task_id,
            'status': task.status,
            'current_phase': task.current_phase,
            'recursion_depth': task.recursion_depth,
            'phases_completed': len(task.phase_results),
            'final_output': task.final_output,
            'validation_quote': task.validation_quote.generate_hash() if task.validation_quote else None
        }


# Convenience function for quick execution
def run_recursive_task(task_type: str, inputs: Dict[str, Any]) -> RecursiveTask:
    """
    Convenience function to run a task through the recursive engine
    """
    import asyncio
    
    engine = RecursiveStrategyEngine()
    return asyncio.run(engine.run_task(task_type, inputs))

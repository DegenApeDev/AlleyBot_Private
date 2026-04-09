"""
Cross-Plugin Orchestrator - Complex multi-plugin workflow execution

Enables AlleyBot to execute sophisticated workflows that span multiple plugins,
with automatic dependency resolution, error handling, and intelligent failover.

Part of Sovereignty Enhancement - Phase 2: Cross-Plugin Orchestration
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Status of workflow execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some steps succeeded, some failed


@dataclass
class WorkflowStep:
    """A single step in a multi-plugin workflow"""
    step_id: str
    plugin: str
    action: str
    params: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)  # Step IDs this depends on
    fallback_plugins: List[str] = field(default_factory=list)  # Alternative plugins if primary fails
    required: bool = True  # If False, workflow continues even if this fails
    timeout_seconds: int = 30
    
    # Execution state
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Workflow:
    """A complete multi-plugin workflow"""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    created_at: datetime = field(default_factory=datetime.now)
    
    # Execution state
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """Get steps that are ready to execute (dependencies satisfied)"""
        ready = []
        for step in self.steps:
            if step.status != WorkflowStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_satisfied = all(
                dep_id in self.completed_steps 
                for dep_id in step.depends_on
            )
            
            if deps_satisfied:
                ready.append(step)
        
        return ready


class CrossPluginOrchestrator:
    """
    Orchestrates complex workflows across multiple plugins.
    
    Features:
    - Dependency resolution (Step B waits for Step A)
    - Automatic failover (If Plugin A fails, try Plugin B)
    - Parallel execution (Independent steps run concurrently)
    - Error recovery (Continue workflow even if non-critical steps fail)
    - Result passing (Output of Step A becomes input to Step B)
    """
    
    # Platform alternatives for failover
    PLATFORM_ALTERNATIVES = {
        'moltx': ['moltbook', 'moltchan', 'telegram'],
        'moltbook': ['moltx', 'moltchan'],
        'moltchan': ['moltx', 'moltbook'],
        'solana_trading': ['base_trading', 'avax_trading'],
        'base_trading': ['solana_trading', 'avax_trading'],
        'clawbr': ['moltx', 'telegram'],
    }
    
    def __init__(self, agi_kernel):
        self.agi = agi_kernel
        self.active_workflows: Dict[str, Workflow] = {}
        logger.info("🔄 Cross-Plugin Orchestrator initialized")
    
    async def execute_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """
        Execute a complete workflow with dependency resolution.
        
        Returns:
            {
                'success': bool,
                'workflow_id': str,
                'completed_steps': int,
                'failed_steps': int,
                'results': Dict[str, Any],
                'errors': List[str]
            }
        """
        logger.info(f"🚀 Starting workflow: {workflow.name}")
        
        workflow.status = WorkflowStatus.IN_PROGRESS
        self.active_workflows[workflow.workflow_id] = workflow
        
        results = {}
        errors = []
        
        # Execute steps in dependency order
        while True:
            ready_steps = workflow.get_ready_steps()
            
            if not ready_steps:
                # No more steps ready - check if we're done
                pending_steps = [s for s in workflow.steps if s.status == WorkflowStatus.PENDING]
                if not pending_steps:
                    break  # All steps processed
                else:
                    # Deadlock - some steps can't execute due to failed dependencies
                    logger.warning(f"⚠️ Workflow deadlock: {len(pending_steps)} steps blocked")
                    for step in pending_steps:
                        step.status = WorkflowStatus.FAILED
                        step.error = "Dependency failed"
                        workflow.failed_steps.append(step.step_id)
                    break
            
            # Execute ready steps (can be parallel if independent)
            step_results = await self._execute_steps_parallel(workflow, ready_steps, results)
            
            for step_id, result in step_results.items():
                if result['success']:
                    workflow.completed_steps.append(step_id)
                    results[step_id] = result
                else:
                    workflow.failed_steps.append(step_id)
                    errors.append(f"{step_id}: {result.get('error', 'Unknown error')}")
        
        # Determine final workflow status
        if len(workflow.failed_steps) == 0:
            workflow.status = WorkflowStatus.COMPLETED
            success = True
        elif len(workflow.completed_steps) > 0:
            workflow.status = WorkflowStatus.PARTIAL
            success = False
        else:
            workflow.status = WorkflowStatus.FAILED
            success = False
        
        logger.info(f"✅ Workflow {workflow.name} finished: {len(workflow.completed_steps)} succeeded, {len(workflow.failed_steps)} failed")
        
        return {
            'success': success,
            'workflow_id': workflow.workflow_id,
            'completed_steps': len(workflow.completed_steps),
            'failed_steps': len(workflow.failed_steps),
            'results': results,
            'errors': errors
        }
    
    async def _execute_steps_parallel(
        self, 
        workflow: Workflow, 
        steps: List[WorkflowStep],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Execute multiple independent steps in parallel"""
        tasks = []
        step_map = {}
        
        for step in steps:
            task = self._execute_step(workflow, step, previous_results)
            tasks.append(task)
            step_map[id(task)] = step.step_id
        
        # Run all tasks concurrently
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results back to step IDs
        results = {}
        for task, result in zip(tasks, results_list):
            step_id = step_map[id(task)]
            if isinstance(result, Exception):
                results[step_id] = {'success': False, 'error': str(result)}
            else:
                results[step_id] = result
        
        return results
    
    async def _execute_step(
        self, 
        workflow: Workflow, 
        step: WorkflowStep,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step with failover support"""
        step.status = WorkflowStatus.IN_PROGRESS
        step.started_at = datetime.now()
        
        logger.info(f"  🔄 Executing step: {step.step_id} ({step.plugin}.{step.action})")
        
        # Inject results from dependencies
        params = self._inject_dependency_results(step, previous_results)
        
        # Try primary plugin
        result = await self._execute_action(step.plugin, step.action, params)
        
        # If failed and fallbacks available, try alternatives
        if not result['success'] and step.fallback_plugins:
            logger.warning(f"  ⚠️ Primary plugin {step.plugin} failed, trying fallbacks...")
            
            for fallback_plugin in step.fallback_plugins:
                logger.info(f"  🔄 Trying fallback: {fallback_plugin}")
                result = await self._execute_action(fallback_plugin, step.action, params)
                
                if result['success']:
                    logger.info(f"  ✅ Fallback {fallback_plugin} succeeded!")
                    result['used_fallback'] = fallback_plugin
                    break
        
        # Update step state
        step.completed_at = datetime.now()
        step.result = result
        
        if result['success']:
            step.status = WorkflowStatus.COMPLETED
        else:
            step.status = WorkflowStatus.FAILED
            step.error = result.get('error', 'Unknown error')
            
            # If step is required, mark as critical failure
            if step.required:
                logger.error(f"  ❌ Required step {step.step_id} failed: {step.error}")
        
        return result
    
    def _inject_dependency_results(
        self, 
        step: WorkflowStep, 
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Inject results from dependency steps into params"""
        params = step.params.copy()
        
        for dep_id in step.depends_on:
            if dep_id in previous_results:
                dep_result = previous_results[dep_id]
                # Add dependency output to params
                params[f'dep_{dep_id}_output'] = dep_result.get('data', dep_result)
        
        return params
    
    async def _execute_action(
        self, 
        plugin: str, 
        action: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an action through the action router"""
        try:
            # Use AGI Kernel's action router
            if not self.agi or not self.agi.action_router:
                return {'success': False, 'error': 'Action router not available'}
            
            # Build action envelope
            from .action_router import ActionEnvelope
            envelope = ActionEnvelope(
                plugin=plugin,
                action_type=action,
                params=params,
                context={'source': 'cross_plugin_orchestrator'}
            )
            
            # Execute through canonical typed contract
            result = await self.agi.action_router.route(envelope)
            
            return result
            
        except Exception as e:
            logger.error(f"Action execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_workflow(
        self, 
        name: str, 
        description: str, 
        steps: List[Dict[str, Any]]
    ) -> Workflow:
        """
        Create a workflow from a step definition.
        
        Args:
            name: Workflow name
            description: What this workflow does
            steps: List of step definitions
        
        Returns:
            Workflow object ready for execution
        """
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        workflow_steps = []
        for i, step_def in enumerate(steps):
            step = WorkflowStep(
                step_id=step_def.get('id', f"step_{i}"),
                plugin=step_def['plugin'],
                action=step_def['action'],
                params=step_def.get('params', {}),
                depends_on=step_def.get('depends_on', []),
                fallback_plugins=step_def.get('fallback_plugins', 
                    self.PLATFORM_ALTERNATIVES.get(step_def['plugin'], [])),
                required=step_def.get('required', True),
                timeout_seconds=step_def.get('timeout', 30)
            )
            workflow_steps.append(step)
        
        return Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            steps=workflow_steps
        )
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return None
        
        return {
            'workflow_id': workflow.workflow_id,
            'name': workflow.name,
            'status': workflow.status.value,
            'completed_steps': len(workflow.completed_steps),
            'failed_steps': len(workflow.failed_steps),
            'total_steps': len(workflow.steps),
            'current_step': workflow.current_step
        }


# Singleton instance
_orchestrator: Optional[CrossPluginOrchestrator] = None


def get_cross_plugin_orchestrator(agi_kernel) -> CrossPluginOrchestrator:
    """Get or create cross-plugin orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CrossPluginOrchestrator(agi_kernel)
    return _orchestrator


def create_cross_plugin_orchestrator(agi_kernel) -> CrossPluginOrchestrator:
    """Create cross-plugin orchestrator"""
    return CrossPluginOrchestrator(agi_kernel)

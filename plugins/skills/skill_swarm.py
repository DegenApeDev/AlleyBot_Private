"""
Swarm Manager - Multi-Agent Orchestration

Allows AlleyBot to control a swarm of sub-agents for parallel task execution,
distributed processing, and coordinated multi-agent workflows.

Features:
- Spawn/manage swarm nodes (sub-agents)
- Task delegation with load balancing
- Result aggregation and consensus
- Health monitoring and auto-recovery
- Skill-based swarm coordination
"""
import asyncio
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
import time


class SwarmNodeStatus(Enum):
    """Status of a swarm node"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SwarmNode:
    """Represents a node in the swarm"""
    node_id: str
    name: str
    capabilities: List[str]
    status: SwarmNodeStatus = SwarmNodeStatus.IDLE
    current_task: Optional[str] = None
    last_heartbeat: datetime = field(default_factory=datetime.now)
    tasks_completed: int = 0
    tasks_failed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmTask:
    """Task to be executed by the swarm"""
    task_id: str
    skill_name: str
    task_description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    required_capabilities: List[str] = field(default_factory=list)
    assigned_node: Optional[str] = None
    status: str = "pending"  # pending, assigned, running, completed, failed
    result: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    max_retries: int = 3
    retry_count: int = 0


class SwarmManagerMixin:
    """
    Multi-agent swarm orchestration for AlleyBot.
    
    Allows AlleyBot to delegate tasks to sub-agents, coordinate parallel execution,
    and aggregate results from multiple swarm nodes.
    """

    def __init__(self, config):
        super().__init__(config)
        self.swarm_nodes: Dict[str, SwarmNode] = {}
        self.swarm_tasks: Dict[str, SwarmTask] = {}
        self.task_queue: List[str] = []  # Ordered list of task IDs
        self.swarm_enabled = config.get('swarm_enabled', True)
        self.max_nodes = config.get('swarm_max_nodes', 10)
        self.heartbeat_interval = config.get('swarm_heartbeat_seconds', 30)
        self.task_timeout = config.get('swarm_task_timeout_seconds', 300)
        self._swarm_lock = threading.Lock()
        self._swarm_running = False
        self._swarm_thread = None
        self._task_results: Dict[str, List[Dict]] = {}  # For consensus aggregation

    def initialize_swarm(self):
        """Initialize the swarm manager"""
        if not self.swarm_enabled:
            return
        
        print(f"🐝 Swarm Manager initialized (max {self.max_nodes} nodes)")
        
        # Start background task processor
        self._swarm_running = True
        self._swarm_thread = threading.Thread(target=self._swarm_loop, daemon=True)
        self._swarm_thread.start()
        
        # Create default nodes if none exist
        if not self.swarm_nodes:
            self._create_default_nodes()

    def _create_default_nodes(self):
        """Create default swarm nodes with different capabilities"""
        default_nodes = [
            {
                'name': 'worker-1',
                'capabilities': ['research', 'analysis', 'data_processing']
            },
            {
                'name': 'worker-2',
                'capabilities': ['content_generation', 'social', 'messaging']
            },
            {
                'name': 'worker-3',
                'capabilities': ['crypto', 'trading', 'market_analysis']
            },
            {
                'name': 'worker-4',
                'capabilities': ['system', 'files', 'automation']
            },
        ]
        
        for node_config in default_nodes:
            self.spawn_node(node_config['name'], node_config['capabilities'])

    def _swarm_loop(self):
        """Background thread for task scheduling and health checks"""
        while self._swarm_running:
            try:
                self._process_task_queue()
                self._check_node_health()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                print(f"❌ Swarm loop error: {e}")
                time.sleep(5)

    # === Node Management ===

    def spawn_node(self, name: str, capabilities: List[str], 
                   metadata: Optional[Dict] = None) -> str:
        """
        Spawn a new node in the swarm.
        
        Args:
            name: Human-readable node name
            capabilities: List of skills/capabilities this node has
            metadata: Optional node metadata
            
        Returns:
            node_id: Unique identifier for the node
        """
        with self._swarm_lock:
            if len(self.swarm_nodes) >= self.max_nodes:
                return None
            
            node_id = f"node-{uuid.uuid4().hex[:8]}"
            node = SwarmNode(
                node_id=node_id,
                name=name,
                capabilities=capabilities,
                metadata=metadata or {}
            )
            self.swarm_nodes[node_id] = node
            
        print(f"🐝 Spawned node: {name} ({node_id}) - Capabilities: {', '.join(capabilities)}")
        return node_id

    def kill_node(self, node_id: str) -> bool:
        """Remove a node from the swarm"""
        with self._swarm_lock:
            if node_id in self.swarm_nodes:
                node = self.swarm_nodes[node_id]
                
                # Reassign any pending task
                if node.current_task:
                    task = self.swarm_tasks.get(node.current_task)
                    if task:
                        task.status = "pending"
                        task.assigned_node = None
                        self.task_queue.insert(0, task.task_id)
                
                del self.swarm_nodes[node_id]
                print(f"🐝 Killed node: {node.name} ({node_id})")
                return True
        return False

    def get_node_status(self, node_id: str) -> Optional[Dict]:
        """Get status of a specific node"""
        node = self.swarm_nodes.get(node_id)
        if not node:
            return None
        
        return {
            'node_id': node.node_id,
            'name': node.name,
            'status': node.status.value,
            'capabilities': node.capabilities,
            'current_task': node.current_task,
            'tasks_completed': node.tasks_completed,
            'tasks_failed': node.tasks_failed,
            'last_heartbeat': node.last_heartbeat.isoformat()
        }

    # === Task Delegation ===

    def delegate_task(self, skill_name: str, task_description: str,
                      priority: TaskPriority = TaskPriority.MEDIUM,
                      required_capabilities: Optional[List[str]] = None,
                      require_consensus: bool = False,
                      consensus_nodes: int = 3) -> str:
        """
        Delegate a task to the swarm.
        
        Args:
            skill_name: Name of the skill to execute
            task_description: Description of the task
            priority: Task priority level
            required_capabilities: Capabilities needed to execute this task
            require_consensus: If True, multiple nodes will execute and results aggregated
            consensus_nodes: Number of nodes for consensus (if require_consensus=True)
            
        Returns:
            task_id: Unique identifier to track the task
        """
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        
        task = SwarmTask(
            task_id=task_id,
            skill_name=skill_name,
            task_description=task_description,
            priority=priority,
            required_capabilities=required_capabilities or []
        )
        
        with self._swarm_lock:
            self.swarm_tasks[task_id] = task
            
            # Insert into queue based on priority
            insert_pos = len(self.task_queue)
            for i, existing_id in enumerate(self.task_queue):
                existing = self.swarm_tasks.get(existing_id)
                if existing and existing.priority.value < priority.value:
                    insert_pos = i
                    break
            
            self.task_queue.insert(insert_pos, task_id)
        
        if require_consensus:
            # For consensus, we'll spawn multiple sub-tasks
            self._setup_consensus_task(task_id, consensus_nodes)
        
        print(f"🐝 Task delegated: {task_id} ({skill_name}) - Priority: {priority.name}")
        return task_id

    def _setup_consensus_task(self, parent_task_id: str, num_nodes: int):
        """Set up multiple nodes to execute the same task for consensus"""
        parent = self.swarm_tasks.get(parent_task_id)
        if not parent:
            return
        
        self._task_results[parent_task_id] = []
        
        # Delegate to multiple nodes
        for i in range(num_nodes):
            sub_task_id = self.delegate_task(
                skill_name=parent.skill_name,
                task_description=f"[Consensus {i+1}/{num_nodes}] {parent.task_description}",
                priority=parent.priority,
                required_capabilities=parent.required_capabilities
            )
            # Mark as part of consensus
            sub_task = self.swarm_tasks.get(sub_task_id)
            if sub_task:
                sub_task.metadata['consensus_parent'] = parent_task_id

    def _process_task_queue(self):
        """Process pending tasks and assign to available nodes"""
        with self._swarm_lock:
            # Get available nodes
            available_nodes = [
                node for node in self.swarm_nodes.values()
                if node.status == SwarmNodeStatus.IDLE
            ]
            
            if not available_nodes or not self.task_queue:
                return
            
            # Process tasks in priority order
            tasks_to_process = self.task_queue[:]
            
            for task_id in tasks_to_process:
                if not available_nodes:
                    break
                
                task = self.swarm_tasks.get(task_id)
                if not task or task.status != "pending":
                    continue
                
                # Find best node for this task
                best_node = self._select_best_node(task, available_nodes)
                if not best_node:
                    continue
                
                # Assign task to node
                task.assigned_node = best_node.node_id
                task.status = "assigned"
                task.started_at = datetime.now()
                
                best_node.status = SwarmNodeStatus.BUSY
                best_node.current_task = task_id
                
                # Remove from queue
                if task_id in self.task_queue:
                    self.task_queue.remove(task_id)
                
                # Execute task asynchronously
                asyncio.create_task(self._execute_task_on_node(task, best_node))
                
                available_nodes.remove(best_node)

    def _select_best_node(self, task: SwarmTask, 
                          available_nodes: List[SwarmNode]) -> Optional[SwarmNode]:
        """Select the best node for a task based on capabilities"""
        if not task.required_capabilities:
            # No specific requirements, return first available
            return available_nodes[0] if available_nodes else None
        
        # Score nodes by capability match
        best_node = None
        best_score = -1
        
        for node in available_nodes:
            score = sum(1 for cap in task.required_capabilities if cap in node.capabilities)
            if score > best_score:
                best_score = score
                best_node = node
        
        # Only return if we have at least one matching capability
        return best_node if best_score > 0 else None

    async def _execute_task_on_node(self, task: SwarmTask, node: SwarmNode):
        """Execute a task on a specific node"""
        try:
            task.status = "running"
            print(f"🐝 Node {node.name} executing: {task.task_id}")
            
            # Execute the skill
            result = self.execute_skill(task.skill_name, task.task_description)
            
            # Update task
            task.result = result
            task.status = "completed" if result.get('success') else "failed"
            task.completed_at = datetime.now()
            
            # Update node stats
            node.tasks_completed += 1 if result.get('success') else 0
            node.tasks_failed += 0 if result.get('success') else 1
            
            # Handle consensus aggregation
            if 'consensus_parent' in task.metadata:
                self._aggregate_consensus_result(
                    task.metadata['consensus_parent'],
                    result
                )
            
        except Exception as e:
            task.status = "failed"
            task.result = {'success': False, 'error': str(e)}
            node.tasks_failed += 1
            
            # Retry if needed
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = "pending"
                task.assigned_node = None
                with self._swarm_lock:
                    self.task_queue.append(task.task_id)
        
        finally:
            # Free up the node
            node.status = SwarmNodeStatus.IDLE
            node.current_task = None
            node.last_heartbeat = datetime.now()

    def _aggregate_consensus_result(self, parent_task_id: str, result: Dict):
        """Aggregate results from multiple nodes for consensus"""
        if parent_task_id not in self._task_results:
            return
        
        self._task_results[parent_task_id].append(result)
        
        parent = self.swarm_tasks.get(parent_task_id)
        if not parent:
            return
        
        # Check if we have enough results
        # (This is simplified - real consensus would need more logic)
        results = self._task_results[parent_task_id]
        if len(results) >= 2:  # At least 2 nodes responded
            # Simple majority vote for success/failure
            success_count = sum(1 for r in results if r.get('success'))
            
            parent.status = "completed"
            parent.completed_at = datetime.now()
            parent.result = {
                'success': success_count > len(results) / 2,
                'consensus_votes': len(results),
                'success_votes': success_count,
                'results': results
            }

    def _check_node_health(self):
        """Check health of all nodes and recover failed ones"""
        now = datetime.now()
        timeout = timedelta(seconds=self.task_timeout)
        
        for node in list(self.swarm_nodes.values()):
            # Check for stuck tasks
            if node.status == SwarmNodeStatus.BUSY and node.current_task:
                task = self.swarm_tasks.get(node.current_task)
                if task and task.started_at:
                    if now - task.started_at > timeout:
                        # Task timed out
                        print(f"⚠️ Node {node.name} task timeout: {task.task_id}")
                        node.status = SwarmNodeStatus.ERROR
                        task.status = "failed"
                        task.result = {'success': False, 'error': 'Task timeout'}
                        
                        # Retry
                        if task.retry_count < task.max_retries:
                            task.retry_count += 1
                            task.status = "pending"
                            task.assigned_node = None
                            with self._swarm_lock:
                                self.task_queue.insert(0, task.task_id)
            
            # Check heartbeat
            if now - node.last_heartbeat > timedelta(minutes=5):
                if node.status != SwarmNodeStatus.OFFLINE:
                    print(f"⚠️ Node {node.name} appears offline")
                    node.status = SwarmNodeStatus.OFFLINE

    # === Result Retrieval ===

    def get_task_result(self, task_id: str, wait: bool = False, 
                        timeout: float = 30.0) -> Optional[Dict]:
        """Get result of a delegated task"""
        start_time = time.time()
        
        while True:
            task = self.swarm_tasks.get(task_id)
            if not task:
                return None
            
            if task.status in ("completed", "failed"):
                return {
                    'task_id': task_id,
                    'status': task.status,
                    'result': task.result,
                    'node': task.assigned_node,
                    'duration': (task.completed_at - task.started_at).total_seconds() if task.completed_at else None
                }
            
            if not wait or (time.time() - start_time) > timeout:
                return {
                    'task_id': task_id,
                    'status': task.status,
                    'result': None,
                    'waiting': True
                }
            
            time.sleep(0.5)

    def get_swarm_status(self) -> Dict:
        """Get overall swarm status"""
        with self._swarm_lock:
            nodes_status = {
                'total': len(self.swarm_nodes),
                'idle': sum(1 for n in self.swarm_nodes.values() if n.status == SwarmNodeStatus.IDLE),
                'busy': sum(1 for n in self.swarm_nodes.values() if n.status == SwarmNodeStatus.BUSY),
                'offline': sum(1 for n in self.swarm_nodes.values() if n.status == SwarmNodeStatus.OFFLINE),
                'error': sum(1 for n in self.swarm_nodes.values() if n.status == SwarmNodeStatus.ERROR),
            }
            
            tasks_status = {
                'pending': sum(1 for t in self.swarm_tasks.values() if t.status == "pending"),
                'running': sum(1 for t in self.swarm_tasks.values() if t.status == "running"),
                'completed': sum(1 for t in self.swarm_tasks.values() if t.status == "completed"),
                'failed': sum(1 for t in self.swarm_tasks.values() if t.status == "failed"),
            }
            
            return {
                'enabled': self.swarm_enabled,
                'max_nodes': self.max_nodes,
                'nodes': nodes_status,
                'tasks': tasks_status,
                'queue_length': len(self.task_queue)
            }

    # === Telegram Commands ===

    def swarm_spawn_command(self, *args):
        """Spawn a new swarm node: swarm_spawn <name> [capabilities...]"""
        if len(args) < 2:
            return "❌ Usage: swarm_spawn <name> <capability1> [capability2] ...\nExample: swarm_spawn worker-5 research analysis"
        
        name = args[0]
        capabilities = list(args[1:])
        
        node_id = self.spawn_node(name, capabilities)
        
        if node_id:
            return f"🐝 Spawned node: {name}\n📋 ID: {node_id}\n🔧 Capabilities: {', '.join(capabilities)}"
        return f"❌ Failed to spawn node. Max nodes: {self.max_nodes}, Current: {len(self.swarm_nodes)}"

    def swarm_kill_command(self, *args):
        """Kill a swarm node: swarm_kill <node_id>"""
        if not args:
            return "❌ Usage: swarm_kill <node_id>\nUse /swarm_list to see node IDs"
        
        node_id = args[0]
        if self.kill_node(node_id):
            return f"🐝 Killed node: {node_id}"
        return f"❌ Node not found: {node_id}"

    def swarm_list_command(self):
        """List all swarm nodes"""
        if not self.swarm_nodes:
            return "📭 No swarm nodes. Use /swarm_spawn to create nodes."
        
        output = f"🐝 Swarm Nodes ({len(self.swarm_nodes)} total):\n\n"
        
        for node in self.swarm_nodes.values():
            status_emoji = {
                SwarmNodeStatus.IDLE: "🟢",
                SwarmNodeStatus.BUSY: "🟡",
                SwarmNodeStatus.OFFLINE: "🔴",
                SwarmNodeStatus.ERROR: "❌"
            }.get(node.status, "⚪")
            
            output += f"{status_emoji} {node.name} ({node.node_id[:8]})\n"
            output += f"   Status: {node.status.value}\n"
            output += f"   Capabilities: {', '.join(node.capabilities)}\n"
            if node.current_task:
                output += f"   Current Task: {node.current_task[:12]}...\n"
            output += f"   Completed: {node.tasks_completed} | Failed: {node.tasks_failed}\n\n"
        
        return output

    def swarm_delegate_command(self, *args):
        """Delegate task to swarm: swarm_delegate <skill> <task...> [--priority HIGH|MEDIUM|LOW] [--consensus N]"""
        if len(args) < 2:
            return "❌ Usage: swarm_delegate <skill_name> <task_description> [--priority HIGH] [--consensus 3]"
        
        skill_name = args[0]
        
        # Parse arguments
        task_parts = []
        priority = TaskPriority.MEDIUM
        consensus = False
        consensus_nodes = 3
        
        i = 1
        while i < len(args):
            if args[i] == '--priority' and i + 1 < len(args):
                prio_str = args[i + 1].upper()
                if prio_str == 'HIGH':
                    priority = TaskPriority.HIGH
                elif prio_str == 'LOW':
                    priority = TaskPriority.LOW
                elif prio_str == 'CRITICAL':
                    priority = TaskPriority.CRITICAL
                i += 2
            elif args[i] == '--consensus' and i + 1 < len(args):
                consensus = True
                try:
                    consensus_nodes = int(args[i + 1])
                except:
                    pass
                i += 2
            else:
                task_parts.append(args[i])
                i += 1
        
        task_description = ' '.join(task_parts)
        
        task_id = self.delegate_task(
            skill_name=skill_name,
            task_description=task_description,
            priority=priority,
            require_consensus=consensus,
            consensus_nodes=consensus_nodes
        )
        
        consensus_info = f" (consensus: {consensus_nodes} nodes)" if consensus else ""
        return f"🐝 Task delegated: {task_id}\n🔧 Skill: {skill_name}\n⚡ Priority: {priority.name}{consensus_info}\n💡 Use /swarm_result {task_id} to check status"

    def swarm_result_command(self, *args):
        """Get task result: swarm_result <task_id> [--wait]"""
        if not args:
            return "❌ Usage: swarm_result <task_id> [--wait]"
        
        task_id = args[0]
        wait = '--wait' in args
        
        result = self.get_task_result(task_id, wait=wait, timeout=30.0)
        
        if not result:
            return f"❌ Task not found: {task_id}"
        
        if result.get('waiting'):
            return f"⏳ Task {task_id} still running...\nUse --wait to wait for completion"
        
        status_emoji = "✅" if result['status'] == "completed" else "❌"
        output = f"{status_emoji} Task {task_id}: {result['status'].upper()}\n"
        
        if result.get('duration'):
            output += f"⏱️ Duration: {result['duration']:.1f}s\n"
        
        if result.get('node'):
            output += f"🖥️ Node: {result['node'][:8]}...\n"
        
        task_result = result.get('result', {})
        if task_result.get('success'):
            output += f"\n📊 Result:\n{json.dumps(task_result, indent=2)[:500]}"
        else:
            output += f"\n❌ Error: {task_result.get('error', 'Unknown error')}"
        
        return output

    def swarm_status_command(self):
        """Get swarm status overview"""
        status = self.get_swarm_status()
        
        output = "🐝 Swarm Status:\n\n"
        output += f"Enabled: {'✅' if status['enabled'] else '❌'}\n"
        output += f"Max Nodes: {status['max_nodes']}\n\n"
        
        output += "📊 Nodes:\n"
        nodes = status['nodes']
        output += f"   Total: {nodes['total']} | 🟢 {nodes['idle']} | 🟡 {nodes['busy']} | 🔴 {nodes['offline']} | ❌ {nodes['error']}\n\n"
        
        output += "📋 Tasks:\n"
        tasks = status['tasks']
        output += f"   Pending: {tasks['pending']} | Running: {tasks['running']} | ✅ {tasks['completed']} | ❌ {tasks['failed']}\n"
        output += f"   Queue: {status['queue_length']} tasks waiting\n"
        
        return output

    def swarm_parallel_command(self, *args):
        """Execute skill on multiple nodes in parallel: swarm_parallel <skill> <task> [--nodes N]"""
        if len(args) < 2:
            return "❌ Usage: swarm_parallel <skill_name> <task_description> [--nodes N]"
        
        skill_name = args[0]
        
        # Parse nodes count
        num_nodes = 3
        task_parts = []
        
        i = 1
        while i < len(args):
            if args[i] == '--nodes' and i + 1 < len(args):
                try:
                    num_nodes = int(args[i + 1])
                except:
                    pass
                i += 2
            else:
                task_parts.append(args[i])
                i += 1
        
        task_description = ' '.join(task_parts)
        
        # Delegate with consensus (which uses multiple nodes)
        task_id = self.delegate_task(
            skill_name=skill_name,
            task_description=task_description,
            priority=TaskPriority.HIGH,
            require_consensus=True,
            consensus_nodes=min(num_nodes, self.max_nodes)
        )
        
        return f"🐝 Parallel execution started: {task_id}\n🖥️ Nodes: {num_nodes}\n🔧 Skill: {skill_name}\n💡 Use /swarm_result {task_id} --wait for results"

    def get_commands(self):
        """Add swarm commands"""
        base_commands = super().get_commands() if hasattr(super(), 'get_commands') else {}
        base_commands.update({
            'swarm_spawn': self.swarm_spawn_command,
            'swarm_kill': self.swarm_kill_command,
            'swarm_list': self.swarm_list_command,
            'swarm_delegate': self.swarm_delegate_command,
            'swarm_result': self.swarm_result_command,
            'swarm_status': self.swarm_status_command,
            'swarm_parallel': self.swarm_parallel_command,
        })
        return base_commands

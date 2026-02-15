"""
ERC-8004 Validation Registry & A2A Tier 3 Integration

Post-execution validation with:
1. Cryptographic hash generation (Task_ID, Code_Version_Hash, Execution_Timestamp)
2. Self-Signed Attestation (VPS-based)
3. Local memory registry for future ERC-8004 submissions
4. Auto-report POST request logic
5. A2A Tier 3 escalation for high-trust tasks
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class TrustTier(Enum):
    """Trust tiers for agent operations"""
    TIER_1 = 1  # Standard operations
    TIER_2 = 2  # Cryptographic trust (SyMod validated)
    TIER_3 = 3  # High trust - requires TEE or multi-sig


@dataclass
class ERC8004Attestation:
    """
    ERC-8004 compliant attestation structure
    Based on ERC-8004 Agent Identity & Attestation Standard
    """
    attestation_id: str
    agent_id: str
    agent_address: str  # On-chain agent identity
    task_id: str
    task_hash: str
    input_hash: str
    output_hash: str
    code_version_hash: str
    execution_timestamp: str
    symod_validation_hash: str
    
    # Signature components
    domain_separator: str = "ERC8004_V1"
    chain_id: int = 8453  # Base network
    
    # Attestation
    attestation_signature: str = ""
    tee_attestation: Optional[str] = None  # TEE enclave attestation if available
    
    # Metadata
    trust_tier: TrustTier = TrustTier.TIER_2
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_message_hash(self) -> str:
        """
        Create structured data hash for EIP-712 style signing
        """
        structured_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"}
                ],
                "AgentAttestation": [
                    {"name": "agentId", "type": "string"},
                    {"name": "taskHash", "type": "bytes32"},
                    {"name": "inputHash", "type": "bytes32"},
                    {"name": "outputHash", "type": "bytes32"},
                    {"name": "timestamp", "type": "uint256"},
                    {"name": "success", "type": "bool"}
                ]
            },
            "primaryType": "AgentAttestation",
            "domain": {
                "name": self.domain_separator,
                "version": "1",
                "chainId": self.chain_id
            },
            "message": {
                "agentId": self.agent_id,
                "taskHash": self.task_hash,
                "inputHash": self.input_hash,
                "outputHash": self.output_hash,
                "timestamp": int(datetime.fromisoformat(self.execution_timestamp).timestamp()),
                "success": self.success
            }
        }
        
        # Simplified - would use proper EIP-712 encoding in production
        data_str = json.dumps(structured_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def generate_full_hash(self) -> str:
        """Generate full attestation hash for registry submission"""
        data = f"{self.agent_id}:{self.task_hash}:{self.input_hash}:{self.output_hash}:{self.execution_timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class A2APeer:
    """
    A2A (Agent-to-Agent) peer definition for Tier 3 outsourcing
    """
    peer_id: str
    agent_address: str
    endpoint_url: str
    capabilities: List[str]
    trust_tier: TrustTier
    tee_verified: bool = False
    tee_attestation: Optional[str] = None
    reputation_score: float = 0.0
    last_successful_task: Optional[datetime] = None
    total_tasks_completed: int = 0
    success_rate: float = 0.0
    
    def is_eligible_for_tier3(self) -> bool:
        """Check if peer is eligible for Tier 3 tasks"""
        return (
            self.trust_tier == TrustTier.TIER_3 and
            self.tee_verified and
            self.reputation_score >= 0.8 and
            self.success_rate >= 0.9
        )


class ERC8004Registry:
    """
    ERC-8004 Validation Registry Manager
    
    Manages:
    - Local storage of attestations
    - Batch preparation for on-chain submission
    - Validation quote registry
    - Auto-report POST request preparation
    """
    
    def __init__(self, storage_path: str = "data/erc8004_registry.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Agent identity
        self.agent_id = "alleybot_v2"
        self.agent_address = self._load_agent_address()
        
        # Registry storage
        self.attestations: List[ERC8004Attestation] = []
        self.pending_submissions: List[ERC8004Attestation] = []
        
        # Registry endpoint (would be configured for actual registry)
        self.registry_endpoint = "https://registry.erc8004.io/api/v1/attestations"
        
        self._load_registry()
        
        logger.info(f"📝 ERC-8004 Registry initialized (agent={self.agent_address})")
    
    def _load_agent_address(self) -> str:
        """Load agent's on-chain identity from onchain plugin or env"""
        # Try to get from environment first
        import os
        wallet = os.getenv('BASE_WALLET_PUBLIC_ADDRESS') or os.getenv('BASE_WALLET')
        if wallet:
            return wallet
        
        # Fallback to placeholder (will be updated when onchain plugin loads)
        return "0xALLEYBOT00000000000000000000000000000000"
    
    def create_attestation(self,
                          task_id: str,
                          inputs: Dict[str, Any],
                          outputs: Dict[str, Any],
                          code_version: str,
                          symod_validation: Optional[Dict] = None,
                          success: bool = True) -> ERC8004Attestation:
        """
        Create a new ERC-8004 attestation for a completed task
        """
        # Generate hashes
        input_str = json.dumps(inputs, sort_keys=True)
        output_str = json.dumps(outputs, sort_keys=True)
        
        input_hash = hashlib.sha256(input_str.encode()).hexdigest()[:32]
        output_hash = hashlib.sha256(output_str.encode()).hexdigest()[:32]
        code_hash = hashlib.sha256(code_version.encode()).hexdigest()[:32]
        
        # Task hash combines inputs and outputs
        task_hash = hashlib.sha256(f"{input_hash}:{output_hash}".encode()).hexdigest()[:32]
        
        # SyMod validation hash
        symod_hash = ""
        if symod_validation:
            symod_str = json.dumps(symod_validation, sort_keys=True)
            symod_hash = hashlib.sha256(symod_str.encode()).hexdigest()[:32]
        
        attestation = ERC8004Attestation(
            attestation_id=f"attest_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_id[:8]}",
            agent_id=self.agent_id,
            agent_address=self.agent_address,
            task_id=task_id,
            task_hash=task_hash,
            input_hash=input_hash,
            output_hash=output_hash,
            code_version_hash=code_hash,
            execution_timestamp=datetime.now().isoformat(),
            symod_validation_hash=symod_hash,
            success=success,
            metadata={
                'input_keys': list(inputs.keys()),
                'output_keys': list(outputs.keys()),
                'has_symod': symod_validation is not None
            }
        )
        
        # Sign the attestation
        attestation.attestation_signature = self._sign_attestation(attestation)
        
        # Store locally
        self.attestations.append(attestation)
        self.pending_submissions.append(attestation)
        
        self._save_registry()
        
        logger.info(f"📝 Attestation created: {attestation.attestation_id} (success={success})")
        
        return attestation
    
    def _sign_attestation(self, attestation: ERC8004Attestation) -> str:
        """
        Create self-signed attestation
        In production: VPS-based secure enclave or hardware signing
        """
        message_hash = attestation.to_message_hash()
        
        # Simplified self-signing (production would use proper key management)
        # Format: VPS_ATTEST:agent_address:timestamp:message_hash
        signature_data = f"VPS_ATTEST:{self.agent_address}:{int(datetime.now().timestamp())}:{message_hash}"
        signature = hashlib.sha256(signature_data.encode()).hexdigest()
        
        return signature[:64]  # First 64 chars as signature
    
    def prepare_batch_submission(self, batch_size: int = 10) -> Dict[str, Any]:
        """
        Prepare a batch of attestations for on-chain submission
        Returns the POST request payload
        """
        batch = self.pending_submissions[:batch_size]
        
        if not batch:
            return {"error": "No pending attestations"}
        
        # Build batch structure
        batch_payload = {
            "agent_id": self.agent_id,
            "agent_address": self.agent_address,
            "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "count": len(batch),
            "attestations": []
        }
        
        for attestation in batch:
            batch_payload["attestations"].append({
                "attestation_id": attestation.attestation_id,
                "task_id": attestation.task_id,
                "task_hash": attestation.task_hash,
                "input_hash": attestation.input_hash,
                "output_hash": attestation.output_hash,
                "code_version_hash": attestation.code_version_hash,
                "execution_timestamp": attestation.execution_timestamp,
                "symod_validation_hash": attestation.symod_validation_hash,
                "attestation_signature": attestation.attestation_signature,
                "success": attestation.success
            })
        
        # Generate batch signature
        batch_str = json.dumps(batch_payload, sort_keys=True)
        batch_payload["batch_signature"] = hashlib.sha256(f"BATCH:{batch_str}".encode()).hexdigest()[:64]
        
        return batch_payload
    
    async def submit_to_registry(self, batch_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit attestations to ERC-8004 registry
        In production: actual HTTP POST to registry endpoint
        """
        logger.info(f"🌐 Submitting batch {batch_payload['batch_id']} to registry")
        
        # Simulate submission (production would make actual HTTP call)
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(self.registry_endpoint, json=batch_payload) as resp:
        #         return await resp.json()
        
        # Simulated success
        result = {
            "status": "submitted",
            "batch_id": batch_payload["batch_id"],
            "transaction_hash": f"0x{hashlib.sha256(batch_payload['batch_id'].encode()).hexdigest()[:40]}",
            "attestations_confirmed": batch_payload["count"]
        }
        
        # Remove submitted attestations from pending
        submitted_ids = {a["attestation_id"] for a in batch_payload["attestations"]}
        self.pending_submissions = [
            a for a in self.pending_submissions 
            if a.attestation_id not in submitted_ids
        ]
        
        self._save_registry()
        
        return result
    
    def get_attestation_by_task(self, task_id: str) -> Optional[ERC8004Attestation]:
        """Find attestation by task ID"""
        for att in self.attestations:
            if att.task_id == task_id:
                return att
        return None
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total = len(self.attestations)
        successful = sum(1 for a in self.attestations if a.success)
        pending = len(self.pending_submissions)
        
        return {
            "total_attestations": total,
            "successful": successful,
            "failed": total - successful,
            "pending_submission": pending,
            "agent_id": self.agent_id,
            "agent_address": self.agent_address
        }
    
    def _save_registry(self):
        """Persist registry to storage"""
        try:
            data = {
                "agent_id": self.agent_id,
                "agent_address": self.agent_address,
                "attestations": [
                    {
                        "attestation_id": a.attestation_id,
                        "task_id": a.task_id,
                        "task_hash": a.task_hash,
                        "input_hash": a.input_hash,
                        "output_hash": a.output_hash,
                        "code_version_hash": a.code_version_hash,
                        "execution_timestamp": a.execution_timestamp,
                        "symod_validation_hash": a.symod_validation_hash,
                        "attestation_signature": a.attestation_signature,
                        "success": a.success
                    }
                    for a in self.attestations
                ],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def _load_registry(self):
        """Load registry from storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct attestations
                for att_data in data.get("attestations", []):
                    att = ERC8004Attestation(
                        attestation_id=att_data["attestation_id"],
                        agent_id=data.get("agent_id", self.agent_id),
                        agent_address=data.get("agent_address", self.agent_address),
                        task_id=att_data["task_id"],
                        task_hash=att_data["task_hash"],
                        input_hash=att_data["input_hash"],
                        output_hash=att_data["output_hash"],
                        code_version_hash=att_data["code_version_hash"],
                        execution_timestamp=att_data["execution_timestamp"],
                        symod_validation_hash=att_data.get("symod_validation_hash", ""),
                        attestation_signature=att_data["attestation_signature"],
                        success=att_data["success"]
                    )
                    self.attestations.append(att)
                    self.pending_submissions.append(att)
                
                logger.info(f"✅ Loaded {len(self.attestations)} attestations from registry")
                
        except Exception as e:
            logger.warning(f"Could not load existing registry: {e}")


class A2ATier3Manager:
    """
    A2A (Agent-to-Agent) Tier 3 Outsourcing Manager
    
    Handles:
    - Peer discovery and verification
    - Task outsourcing to TEE-verified peers
    - Reputation tracking
    - Secure task handoff with cryptographic attestation
    """
    
    def __init__(self, registry: Optional[ERC8004Registry] = None):
        self.registry = registry or ERC8004Registry()
        
        # Known peers
        self.peers: Dict[str, A2APeer] = {}
        
        # Active outsourced tasks
        self.outsourced_tasks: Dict[str, Dict] = {}
        
        self._load_peers()
        
        logger.info("🤝 A2A Tier 3 Manager initialized")
    
    def _load_peers(self):
        """Load known peers from configuration"""
        # In production: load from secure peer registry
        # For now, empty
        pass
    
    def register_peer(self, peer: A2APeer):
        """Register a trusted peer"""
        self.peers[peer.peer_id] = peer
        logger.info(f"🔌 Peer registered: {peer.peer_id} (tee={peer.tee_verified})")
    
    def find_eligible_peers(self, capability: str) -> List[A2APeer]:
        """Find peers eligible for Tier 3 tasks with given capability"""
        eligible = []
        
        for peer in self.peers.values():
            if peer.is_eligible_for_tier3() and capability in peer.capabilities:
                eligible.append(peer)
        
        # Sort by reputation score
        eligible.sort(key=lambda p: p.reputation_score, reverse=True)
        
        return eligible
    
    async def outsource_task(self, 
                            task_id: str,
                            task_data: Dict[str, Any],
                            required_capability: str,
                            timeout_seconds: int = 300) -> Dict[str, Any]:
        """
        Outsource a task to a Tier 3 peer
        
        Returns result with attestation from peer
        """
        logger.info(f"🤝 Outsourcing task {task_id} to Tier 3 peer")
        
        # Find eligible peers
        peers = self.find_eligible_peers(required_capability)
        
        if not peers:
            return {
                "success": False,
                "error": "No eligible Tier 3 peers available",
                "task_id": task_id
            }
        
        # Select best peer
        selected_peer = peers[0]
        
        # Create escrow attestation (binds task to peer)
        escrow = self._create_escrow_attestation(task_id, selected_peer, task_data)
        
        # Record outsourcing
        self.outsourced_tasks[task_id] = {
            "peer_id": selected_peer.peer_id,
            "escrow_attestation": escrow,
            "status": "outsourced",
            "outsource_time": datetime.now().isoformat()
        }
        
        # In production: make actual A2A protocol call
        # For now, simulate successful completion
        logger.info(f"📤 Task {task_id} outsourced to {selected_peer.peer_id}")
        
        # Simulate peer execution
        result = await self._simulate_peer_execution(task_id, task_data, selected_peer)
        
        # Record completion
        self.outsourced_tasks[task_id]["status"] = "completed"
        self.outsourced_tasks[task_id]["completion_time"] = datetime.now().isoformat()
        self.outsourced_tasks[task_id]["result"] = result
        
        # Update peer stats
        selected_peer.total_tasks_completed += 1
        selected_peer.last_successful_task = datetime.now()
        selected_peer.success_rate = (
            selected_peer.total_tasks_completed / 
            (selected_peer.total_tasks_completed + 1)  # Simplified
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "peer_id": selected_peer.peer_id,
            "result": result,
            "escrow_attestation": escrow
        }
    
    def _create_escrow_attestation(self, 
                                    task_id: str, 
                                    peer: A2APeer,
                                    task_data: Dict) -> str:
        """Create escrow attestation for task handoff"""
        data = f"ESCROW:{task_id}:{peer.agent_address}:{hashlib.sha256(str(task_data).encode()).hexdigest()[:16]}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    async def _simulate_peer_execution(self, 
                                       task_id: str, 
                                       task_data: Dict,
                                       peer: A2APeer) -> Dict:
        """Simulate peer execution (production: actual A2A call)"""
        import asyncio
        # Simulate delay
        await asyncio.sleep(0.1)
        
        return {
            "executed_by": peer.peer_id,
            "task_type": task_data.get("type", "unknown"),
            "output": {"status": "completed", "peer_processed": True}
        }
    
    def verify_peer_attestation(self, 
                                peer_id: str, 
                                attestation: str) -> bool:
        """Verify a peer's TEE attestation"""
        peer = self.peers.get(peer_id)
        if not peer:
            return False
        
        # In production: verify against TEE registry
        return peer.tee_verified


# Singleton instances
_erc_registry: Optional[ERC8004Registry] = None
_a2a_manager: Optional[A2ATier3Manager] = None


def get_erc8004_registry() -> ERC8004Registry:
    """Get or create ERC-8004 registry singleton"""
    global _erc_registry
    if _erc_registry is None:
        _erc_registry = ERC8004Registry()
    return _erc_registry


def get_a2a_manager() -> A2ATier3Manager:
    """Get or create A2A manager singleton"""
    global _a2a_manager
    if _a2a_manager is None:
        _a2a_manager = A2ATier3Manager(get_erc8004_registry())
    return _a2a_manager


# Integration helpers
def validate_and_attest(task_id: str,
                       inputs: Dict[str, Any],
                       outputs: Dict[str, Any],
                       code_version: str,
                       symod_result: Optional[Dict] = None) -> ERC8004Attestation:
    """
    Convenience function: validate and create attestation
    """
    registry = get_erc8004_registry()
    
    return registry.create_attestation(
        task_id=task_id,
        inputs=inputs,
        outputs=outputs,
        code_version=code_version,
        symod_validation=symod_result,
        success=True
    )


async def escalate_to_tier3(task_id: str, 
                            task_data: Dict[str, Any],
                            capability: str) -> Dict[str, Any]:
    """
    Convenience function: escalate task to Tier 3 peer
    """
    a2a = get_a2a_manager()
    
    return await a2a.outsource_task(
        task_id=task_id,
        task_data=task_data,
        required_capability=capability
    )

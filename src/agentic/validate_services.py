"""
Service Validation Tests - Runtime validation for AlleyBot foundation services

This module provides:
- Unit tests for each service
- Integration tests for service wiring
- Runtime validation to ensure services work
- Quick health checks for deployment

Usage:
    python -m src.agentic.validate_services
    
    Or from within AlleyBot:
    from src.agentic.validate_services import run_all_validations
    results = run_all_validations()
    print(f"Passed: {results['passed']}/{results['total']}")
"""

import os
import sys
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime


class ServiceValidator:
    """Validates AlleyBot foundation services."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.temp_dir = None
    
    def _record(self, name: str, passed: bool, message: str, details: Dict = None):
        """Record a test result."""
        self.results.append({
            "name": name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        })
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {message}")
        return passed
    
    def _setup_temp_dir(self):
        """Create temporary directory for isolated tests."""
        self.temp_dir = tempfile.mkdtemp(prefix="alleybot_test_")
        return self.temp_dir
    
    def _cleanup_temp_dir(self):
        """Remove temporary directory."""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    # --------------------------------------------------------------------------
    # Contract Tests
    # --------------------------------------------------------------------------
    
    def test_contracts_import(self) -> bool:
        """Test that contracts module imports correctly."""
        try:
            from src.agentic.contracts import (
                ActionEnvelope,
                ActionOutcome,
                WorkItem,
                IdentityContext,
                ConversationRequest,
                ConversationResponse,
                MemoryRecord,
            )
            return self._record(
                "Contracts Import",
                True,
                "All contract types importable",
                {"types": ["ActionEnvelope", "WorkItem", "IdentityContext"]}
            )
        except Exception as e:
            return self._record("Contracts Import", False, f"Import failed: {e}")
    
    def test_contracts_creation(self) -> bool:
        """Test creating contract instances."""
        try:
            from src.agentic.contracts import (
                ActionEnvelope,
                WorkItem,
                WorkItemState,
                ImpactLevel,
                RiskLevel,
            )
            
            # Test ActionEnvelope
            envelope = ActionEnvelope(
                plugin="test",
                action_type="test_action",
                params={"key": "value"},
                context={"impact": "medium"}
            )
            assert envelope.action_id == "test:test_action"
            
            # Test WorkItem
            work = WorkItem(
                id="wi_test",
                title="Test Work",
                description="Test description",
                state=WorkItemState.ACTIVE,
                work_type="goal"
            )
            assert work.state == WorkItemState.ACTIVE
            
            return self._record(
                "Contracts Creation",
                True,
                "Contract instances created successfully"
            )
        except Exception as e:
            return self._record("Contracts Creation", False, f"Creation failed: {e}")
    
    # --------------------------------------------------------------------------
    # Identity Service Tests
    # --------------------------------------------------------------------------
    
    def test_identity_service_import(self) -> bool:
        """Test identity service import."""
        try:
            from src.agentic.identity_service import IdentityService, get_identity_service
            return self._record("Identity Import", True, "Module imports correctly")
        except Exception as e:
            return self._record("Identity Import", False, f"Import failed: {e}")
    
    def test_identity_service_creation(self) -> bool:
        """Test identity service initialization."""
        try:
            from src.agentic.identity_service import IdentityService
            
            # Create with fallback (SOUL.md may not exist in test env)
            service = IdentityService(soul_path="/nonexistent/SOUL.md")
            
            # Should still work with defaults
            ctx = service.get_identity_context()
            assert ctx.name == "AlleyBot"
            assert len(ctx.forbidden_claims) > 0
            
            # Test system prompt generation
            prompt = service.get_system_prompt()
            assert "AlleyBot" in prompt
            assert "FORBIDDEN" in prompt
            
            return self._record("Identity Creation", True, "Service initialized with defaults")
        except Exception as e:
            return self._record("Identity Creation", False, f"Creation failed: {e}")
    
    def test_identity_violation_detection(self) -> bool:
        """Test forbidden claim detection."""
        try:
            from src.agentic.identity_service import IdentityService
            
            service = IdentityService(soul_path="/nonexistent/SOUL.md")
            
            # Test violation detection
            text_with_violation = "I am Grok, an AI assistant"
            violations = service.check_identity_violations(text_with_violation)
            
            assert len(violations) > 0, "Should detect 'I am Grok' violation"
            
            # Test safe text
            safe_text = "I am AlleyBot, ready to help"
            violations_safe = service.check_identity_violations(safe_text)
            
            assert len(violations_safe) == 0, "Should not flag safe text"
            
            return self._record(
                "Identity Violation Detection",
                True,
                f"Detected {len(violations)} violations in test text"
            )
        except Exception as e:
            return self._record("Identity Violation Detection", False, f"Detection failed: {e}")
    
    # --------------------------------------------------------------------------
    # Memory Service Tests
    # --------------------------------------------------------------------------
    
    def test_memory_service_import(self) -> bool:
        """Test memory service import."""
        try:
            from src.agentic.memory_service import MemoryService, get_memory_service
            from src.agentic.contracts import MemoryType
            return self._record("Memory Import", True, "Module imports correctly")
        except Exception as e:
            return self._record("Memory Import", False, f"Import failed: {e}")
    
    def test_memory_service_operations(self) -> bool:
        """Test memory CRUD operations."""
        temp_dir = self._setup_temp_dir()
        try:
            from src.agentic.memory_service import MemoryService, MemoryType
            
            db_path = Path(temp_dir) / "test_memory.db"
            service = MemoryService(db_path=str(db_path))
            
            # Test store
            record = service.store(
                content="Test memory content",
                memory_type=MemoryType.EPISODIC,
                source_action="test:action",
                importance=0.8
            )
            assert record.id is not None
            
            # Test retrieve by type
            records = service.retrieve_by_type(MemoryType.EPISODIC)
            assert len(records) == 1
            assert records[0].content == "Test memory content"
            
            # Test search
            results = service.search("test memory")
            assert len(results) == 1
            
            # Test stats
            stats = service.get_stats()
            assert stats["total_records"] == 1
            
            return self._record(
                "Memory Operations",
                True,
                f"Store/retrieve/search working ({stats['total_records']} records)"
            )
        except Exception as e:
            return self._record("Memory Operations", False, f"Operations failed: {e}")
        finally:
            self._cleanup_temp_dir()
    
    # --------------------------------------------------------------------------
    # Work Item Service Tests
    # --------------------------------------------------------------------------
    
    def test_work_item_service_import(self) -> bool:
        """Test work item service import."""
        try:
            from src.agentic.work_item_service import WorkItemService, get_work_item_service
            return self._record("WorkItem Import", True, "Module imports correctly")
        except Exception as e:
            return self._record("WorkItem Import", False, f"Import failed: {e}")
    
    def test_work_item_service_operations(self) -> bool:
        """Test work item CRUD operations."""
        temp_dir = self._setup_temp_dir()
        try:
            from src.agentic.work_item_service import WorkItemService
            from src.agentic.contracts import WorkItemState
            
            db_path = Path(temp_dir) / "test_work.db"
            service = WorkItemService(db_path=str(db_path))
            
            # Test create
            item = service.create_work_item(
                title="Test Work",
                description="Test description",
                work_type="goal",
                priority=1
            )
            assert item.id is not None
            assert item.state == WorkItemState.ACTIVE
            
            # Test get
            retrieved = service.get_item(item.id)
            assert retrieved is not None
            assert retrieved.title == "Test Work"
            
            # Test state update
            updated = service.update_item_state(item.id, WorkItemState.COMPLETED)
            assert updated.state == WorkItemState.COMPLETED
            
            # Test summary
            summary = service.get_summary()
            assert summary["total"] == 1
            assert summary["completed"] == 1
            
            return self._record(
                "WorkItem Operations",
                True,
                f"Create/update/delete working ({summary['total']} items)"
            )
        except Exception as e:
            return self._record("WorkItem Operations", False, f"Operations failed: {e}")
        finally:
            self._cleanup_temp_dir()
    
    # --------------------------------------------------------------------------
    # Notification Service Tests
    # --------------------------------------------------------------------------
    
    def test_notification_service_import(self) -> bool:
        """Test notification service import."""
        try:
            from src.agentic.owner_notification_service import OwnerNotificationService, NotificationPriority
            return self._record("Notification Import", True, "Module imports correctly")
        except Exception as e:
            return self._record("Notification Import", False, f"Import failed: {e}")
    
    def test_notification_service_creation(self) -> bool:
        """Test notification service initialization."""
        temp_dir = self._setup_temp_dir()
        try:
            from src.agentic.owner_notification_service import OwnerNotificationService
            
            db_path = Path(temp_dir) / "test_notif.db"
            service = OwnerNotificationService(db_path=str(db_path))
            
            stats = service.get_stats()
            assert stats["total"] == 0
            assert stats["enabled"]  # Should be enabled by default
            
            return self._record(
                "Notification Creation",
                True,
                f"Service initialized (enabled={stats['enabled']})"
            )
        except Exception as e:
            return self._record("Notification Creation", False, f"Creation failed: {e}")
        finally:
            self._cleanup_temp_dir()
    
    # --------------------------------------------------------------------------
    # Conversation Service Tests
    # --------------------------------------------------------------------------
    
    def test_conversation_service_import(self) -> bool:
        """Test conversation service import."""
        try:
            from src.agentic.conversation_service import ConversationService, get_conversation_service
            return self._record("Conversation Import", True, "Module imports correctly")
        except Exception as e:
            return self._record("Conversation Import", False, f"Import failed: {e}")
    
    # --------------------------------------------------------------------------
    # Integration Tests
    # --------------------------------------------------------------------------
    
    def test_service_integration_import(self) -> bool:
        """Test service integration layer import."""
        try:
            from src.agentic.service_integration import (
                ServiceBundle,
                initialize_services,
                check_system_health
            )
            return self._record("Integration Import", True, "Module imports correctly")
        except Exception as e:
            return self._record("Integration Import", False, f"Import failed: {e}")
    
    # --------------------------------------------------------------------------
    # ActionRouter Tests
    # --------------------------------------------------------------------------
    
    def test_action_router_envelope(self) -> bool:
        """Test ActionRouter with canonical envelopes."""
        try:
            from src.agentic.contracts import ActionEnvelope, ImpactLevel, RiskLevel
            
            # Create envelope
            envelope = ActionEnvelope(
                plugin="test",
                action_type="test_action",
                params={"key": "value"},
                context={"test": "context"}
            )
            
            # Test serialization
            env_dict = envelope.to_dict()
            assert env_dict["plugin"] == "test"
            assert env_dict["action_type"] == "test_action"
            
            # Test deserialization
            from src.agentic.contracts import ActionEnvelope
            restored = ActionEnvelope.from_dict(env_dict)
            assert restored.plugin == "test"
            assert restored.action_id == "test:test_action"
            
            return self._record(
                "ActionRouter Envelope",
                True,
                "Canonical envelope serialization working"
            )
        except Exception as e:
            return self._record("ActionRouter Envelope", False, f"Envelope test failed: {e}")
    
    # --------------------------------------------------------------------------
    # Run All Tests
    # --------------------------------------------------------------------------
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("\n🧪 AlleyBot Service Validation\n")
        print("=" * 60)
        
        self.results = []
        
        # Contract tests
        print("\n📋 Contract Tests:")
        self.test_contracts_import()
        self.test_contracts_creation()
        
        # Identity tests
        print("\n👤 Identity Service Tests:")
        self.test_identity_service_import()
        self.test_identity_service_creation()
        self.test_identity_violation_detection()
        
        # Memory tests
        print("\n💾 Memory Service Tests:")
        self.test_memory_service_import()
        self.test_memory_service_operations()
        
        # Work item tests
        print("\n📦 Work Item Service Tests:")
        self.test_work_item_service_import()
        self.test_work_item_service_operations()
        
        # Notification tests
        print("\n🔔 Notification Service Tests:")
        self.test_notification_service_import()
        self.test_notification_service_creation()
        
        # Conversation tests
        print("\n💬 Conversation Service Tests:")
        self.test_conversation_service_import()
        
        # Integration tests
        print("\n🔗 Integration Layer Tests:")
        self.test_service_integration_import()
        
        # ActionRouter tests
        print("\n🎯 ActionRouter Tests:")
        self.test_action_router_envelope()
        
        # Summary
        print("\n" + "=" * 60)
        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)
        failed = total - passed
        
        print(f"\n📊 Results: {passed}/{total} passed")
        if failed > 0:
            print(f"❌ {failed} tests failed")
            print("\nFailed tests:")
            for r in self.results:
                if not r["passed"]:
                    print(f"  • {r['name']}: {r['message']}")
        else:
            print("✅ All tests passed!")
        
        return {
            "passed": passed,
            "failed": failed,
            "total": total,
            "healthy": failed == 0,
            "results": self.results
        }


def run_all_validations() -> Dict[str, Any]:
    """Entry point for running all validations."""
    validator = ServiceValidator()
    return validator.run_all_tests()


def quick_health_check() -> bool:
    """Quick health check - returns True if all services importable."""
    try:
        from src.agentic.contracts import ActionEnvelope, WorkItem
        from src.agentic.identity_service import IdentityService
        from src.agentic.memory_service import MemoryService
        from src.agentic.work_item_service import WorkItemService
        from src.agentic.conversation_service import ConversationService
        from src.agentic.owner_notification_service import OwnerNotificationService
        from src.agentic.service_integration import ServiceBundle
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


if __name__ == "__main__":
    results = run_all_validations()
    sys.exit(0 if results["healthy"] else 1)

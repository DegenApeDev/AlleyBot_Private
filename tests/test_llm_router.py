"""
Test LLM Router functionality
"""
import sys
sys.path.insert(0, '.')

from src.core.llm_router import get_llm_router


def test_router_initialization():
    """Test that LLM router initializes correctly"""
    llm = get_llm_router()
    assert llm is not None
    print(f"✅ Router initialized with {len(llm.models)} models")
    print(f"   Available: {list(llm.models.keys())}")
    return True


def test_singleton_pattern():
    """Test that get_llm_router returns the same instance"""
    llm1 = get_llm_router()
    llm2 = get_llm_router()
    assert llm1 is llm2
    print("✅ Singleton pattern works")
    return True


def test_auto_model_selection():
    """Test automatic model selection logic"""
    llm = get_llm_router()
    
    # Test code generation detection
    model = llm._auto_select_model("Write a Python function to parse JSON", 500)
    print(f"✅ Code prompt → {model}")
    
    # Test reasoning detection
    model = llm._auto_select_model("Analyze and explain why this market is trending", 500)
    print(f"✅ Reasoning prompt → {model}")
    
    # Test default
    model = llm._auto_select_model("Generate a post about AI", 500)
    print(f"✅ Default prompt → {model}")
    
    return True


def test_stats_tracking():
    """Test that stats are tracked correctly"""
    llm = get_llm_router()
    stats = llm.get_stats()
    assert isinstance(stats, dict)
    print(f"✅ Stats tracking works: {len(stats)} models tracked")
    return True


if __name__ == "__main__":
    print("🧪 Testing LLM Router...\n")
    
    tests = [
        test_router_initialization,
        test_singleton_pattern,
        test_auto_model_selection,
        test_stats_tracking,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n🔍 Running {test.__name__}...")
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    
    if failed == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
        sys.exit(1)

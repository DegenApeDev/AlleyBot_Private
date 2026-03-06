"""
Runtime validation for BrainPlugin mixin dependencies.

This module provides validation to ensure that all mixin dependencies
are satisfied and initialization order is correct.

Usage:
    from src.core.validate_mixins import validate_mixin_dependencies
    
    # Call during BrainPlugin initialization or startup
    validate_mixin_dependencies()
"""

import sys
from typing import Set, List, Tuple


def validate_mixin_dependencies(verbose: bool = True) -> bool:
    """
    Validate all mixin dependencies are satisfied.
    
    Checks:
    1. All REQUIRES are provided by earlier mixins in MRO
    2. No circular dependencies
    3. Initialization order is consistent with dependencies
    
    Args:
        verbose: If True, print detailed validation info
        
    Returns:
        True if validation passes, raises ValueError if errors found
        
    Raises:
        ValueError: If dependency errors are detected
    """
    try:
        from plugins.brain.brain import BrainPlugin
    except ImportError as e:
        if verbose:
            print(f"⚠️  Cannot validate mixins: {e}")
        return False
    
    mro = BrainPlugin.__mro__[:-1]  # Exclude object
    provided = set()
    errors = []
    warnings = []
    
    # Track initialization order
    init_orders = []
    
    for mixin in reversed(mro):  # Bottom-up (init order)
        if mixin == BrainPlugin:
            continue
            
        requires = getattr(mixin, 'REQUIRES', [])
        provides = getattr(mixin, 'PROVIDES', [])
        init_order = getattr(mixin, 'INIT_ORDER', None)
        
        # Check if REQUIRES/PROVIDES are defined
        if not hasattr(mixin, 'REQUIRES'):
            warnings.append(f"{mixin.__name__} missing REQUIRES attribute")
        if not hasattr(mixin, 'PROVIDES'):
            warnings.append(f"{mixin.__name__} missing PROVIDES attribute")
        if not hasattr(mixin, 'INIT_ORDER'):
            warnings.append(f"{mixin.__name__} missing INIT_ORDER attribute")
        
        # Check all requirements are met
        missing = set(requires) - provided
        if missing:
            errors.append(
                f"{mixin.__name__} (order {init_order}) requires {missing} "
                f"but not provided by earlier mixins"
            )
        
        # Check for duplicate provides
        duplicates = set(provides) & provided
        if duplicates:
            warnings.append(
                f"{mixin.__name__} provides {duplicates} which are already "
                f"provided by earlier mixins (may be intentional override)"
            )
        
        # Add what this mixin provides
        provided.update(provides)
        
        # Track init order
        if init_order is not None:
            init_orders.append((init_order, mixin.__name__))
    
    # Check init order is sequential
    if init_orders:
        init_orders.sort()
        expected_order = 1
        for order, name in init_orders:
            if order != expected_order and order != '?':
                warnings.append(
                    f"{name} has INIT_ORDER={order} but expected {expected_order} "
                    f"(gaps in sequence)"
                )
            if order != '?':
                expected_order = order + 1
    
    # Report results
    if verbose:
        mixin_count = len([c for c in mro if c.__name__.endswith('Mixin')])
        print(f"🔍 Validating {mixin_count} mixins in BrainPlugin...")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} warnings:")
            for warning in warnings[:10]:  # Limit output
                print(f"  • {warning}")
            if len(warnings) > 10:
                print(f"  ... and {len(warnings) - 10} more warnings")
        
        if errors:
            print(f"\n❌ {len(errors)} dependency errors:")
            for error in errors:
                print(f"  • {error}")
        else:
            print(f"\n✅ All mixin dependencies validated")
            print(f"   • {len(provided)} capabilities provided")
            print(f"   • No missing dependencies")
    
    if errors:
        raise ValueError(
            f"❌ Mixin dependency errors detected:\n" + 
            "\n".join(f"  • {e}" for e in errors)
        )
    
    return True


def get_mixin_dependency_graph() -> List[Tuple[str, str]]:
    """
    Get mixin dependency graph as list of (provider, consumer) tuples.
    
    Returns:
        List of (provider_mixin, consumer_mixin) dependency edges
    """
    try:
        from plugins.brain.brain import BrainPlugin
    except ImportError:
        return []
    
    mro = BrainPlugin.__mro__[:-1]
    edges = []
    
    for mixin in mro:
        if mixin == BrainPlugin:
            continue
            
        requires = getattr(mixin, 'REQUIRES', [])
        for req in requires:
            # Find provider
            for provider in mro:
                if req in getattr(provider, 'PROVIDES', []):
                    edges.append((provider.__name__, mixin.__name__))
                    break
    
    return edges


def print_mixin_summary():
    """Print a summary of BrainPlugin mixin architecture"""
    try:
        from plugins.brain.brain import BrainPlugin
    except ImportError as e:
        print(f"❌ Cannot load BrainPlugin: {e}")
        return
    
    mro = BrainPlugin.__mro__[:-1]
    
    print("🧠 BrainPlugin Mixin Architecture Summary\n")
    print(f"Total classes in MRO: {len(mro)}")
    
    mixins = [c for c in mro if c.__name__.endswith('Mixin')]
    print(f"Total mixins: {len(mixins)}\n")
    
    print("Mixins by initialization order:")
    mixin_orders = []
    for mixin in mixins:
        order = getattr(mixin, 'INIT_ORDER', '?')
        requires = getattr(mixin, 'REQUIRES', [])
        provides = getattr(mixin, 'PROVIDES', [])
        mixin_orders.append((order, mixin.__name__, len(requires), len(provides)))
    
    mixin_orders.sort(key=lambda x: x[0] if x[0] != '?' else 999)
    
    for order, name, req_count, prov_count in mixin_orders:
        print(f"  {order:>3}. {name:<35} (requires {req_count}, provides {prov_count})")
    
    print("\n💡 Run 'python scripts/generate_mixin_docs.py' for full documentation")


if __name__ == "__main__":
    # If run directly, validate and print summary
    print("=" * 60)
    validate_mixin_dependencies(verbose=True)
    print("=" * 60)
    print()
    print_mixin_summary()

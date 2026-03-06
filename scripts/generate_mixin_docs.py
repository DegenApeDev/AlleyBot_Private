#!/usr/bin/env python3
"""
Auto-generate mixin dependency documentation for BrainPlugin.

This script analyzes the BrainPlugin's mixin architecture and generates
comprehensive documentation including:
- Method Resolution Order (MRO)
- Dependency graph
- Per-mixin requirements and capabilities
- Mermaid diagram for visualization

Usage:
    python scripts/generate_mixin_docs.py

Output:
    docs/MIXIN_ARCHITECTURE.md
"""

import inspect
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_mixin_documentation():
    """Auto-generate mixin dependency documentation"""
    
    try:
        from plugins.brain.brain import BrainPlugin
    except ImportError as e:
        print(f"❌ Failed to import BrainPlugin: {e}")
        print("Make sure you're running this from the project root")
        return None
    
    mro = BrainPlugin.__mro__[:-1]  # Exclude object
    
    output = []
    output.append("# BrainPlugin Mixin Architecture\n")
    output.append("**Auto-generated from code - DO NOT EDIT MANUALLY**\n")
    output.append(f"**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # MRO
    output.append("## Method Resolution Order\n")
    output.append("```python")
    output.append(" -> ".join(c.__name__ for c in mro))
    output.append("```\n")
    
    # Summary stats
    mixin_count = len([c for c in mro if c.__name__.endswith('Mixin')])
    output.append(f"**Total Mixins:** {mixin_count}\n")
    
    # Document each mixin
    output.append("## Mixin Dependencies\n")
    
    for mixin in mro:
        if mixin == BrainPlugin:
            continue
            
        requires = getattr(mixin, 'REQUIRES', [])
        provides = getattr(mixin, 'PROVIDES', [])
        init_order = getattr(mixin, 'INIT_ORDER', '?')
        
        output.append(f"### {mixin.__name__}\n")
        output.append(f"- **Init Order:** {init_order}")
        output.append(f"- **Requires:** {', '.join(f'`{r}`' for r in requires) if requires else 'None'}")
        output.append(f"- **Provides:** {', '.join(f'`{p}`' for p in provides) if provides else 'Unknown'}")
        
        # Get docstring
        doc = inspect.getdoc(mixin)
        if doc:
            first_line = doc.split('\n')[0].strip()
            output.append(f"- **Description:** {first_line}")
        
        # Get file location
        try:
            file_path = inspect.getfile(mixin)
            rel_path = Path(file_path).relative_to(project_root)
            output.append(f"- **Source:** `{rel_path}`")
        except:
            pass
        
        output.append("")
    
    # Dependency graph (Mermaid)
    output.append("## Dependency Graph\n")
    output.append("```mermaid")
    output.append("graph TD")
    
    # Build dependency edges
    for mixin in mro:
        if mixin == BrainPlugin:
            continue
            
        requires = getattr(mixin, 'REQUIRES', [])
        for req in requires:
            # Find which mixin provides this requirement
            provider = None
            for m in mro:
                if req in getattr(m, 'PROVIDES', []):
                    provider = m
                    break
            
            if provider:
                output.append(f"    {provider.__name__} --> {mixin.__name__}")
    
    output.append("```\n")
    
    # Initialization order table
    output.append("## Initialization Order\n")
    output.append("| Order | Mixin | Dependencies |\n")
    output.append("|-------|-------|-------------|\n")
    
    # Sort by INIT_ORDER
    mixins_with_order = []
    for mixin in mro:
        if mixin == BrainPlugin:
            continue
        init_order = getattr(mixin, 'INIT_ORDER', 999)
        requires = getattr(mixin, 'REQUIRES', [])
        mixins_with_order.append((init_order, mixin.__name__, requires))
    
    mixins_with_order.sort(key=lambda x: x[0])
    
    for order, name, requires in mixins_with_order:
        deps = ', '.join(f'`{r}`' for r in requires) if requires else 'None'
        output.append(f"| {order} | {name} | {deps} |\n")
    
    output.append("")
    
    # Validation status
    output.append("## Validation\n")
    output.append("To validate mixin dependencies, run:\n")
    output.append("```bash\n")
    output.append("python -c \"from src.core.validate_mixins import validate_mixin_dependencies; validate_mixin_dependencies()\"\n")
    output.append("```\n")
    
    return "\n".join(output)


def main():
    """Main entry point"""
    print("🔍 Analyzing BrainPlugin mixin architecture...")
    
    docs = generate_mixin_documentation()
    
    if docs is None:
        print("❌ Failed to generate documentation")
        sys.exit(1)
    
    # Create docs directory if it doesn't exist
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Write documentation
    output_file = docs_dir / "MIXIN_ARCHITECTURE.md"
    output_file.write_text(docs)
    
    print(f"✅ Generated {output_file}")
    print(f"📄 Documentation includes:")
    print(f"   • Method Resolution Order")
    print(f"   • Dependency graph (Mermaid)")
    print(f"   • Per-mixin requirements and capabilities")
    print(f"   • Initialization order table")
    print(f"\n💡 Next steps:")
    print(f"   1. Add REQUIRES/PROVIDES to mixins that don't have them")
    print(f"   2. Run validation: python -c \"from src.core.validate_mixins import validate_mixin_dependencies; validate_mixin_dependencies()\"")


if __name__ == "__main__":
    main()

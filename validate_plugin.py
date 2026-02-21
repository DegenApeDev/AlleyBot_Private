#!/usr/bin/env python3
"""
AlleyBot Code Validation Helper
Quick validation for generated plugins to catch common issues before running full tests
"""
import sys
import os
import ast
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def validate_plugin_syntax(plugin_path: str) -> Dict[str, Any]:
    """Validate Python syntax for a plugin file"""
    result = {'valid': True, 'errors': []}
    
    try:
        with open(plugin_path, 'r') as f:
            content = f.read()
        
        # Check for basic syntax errors
        try:
            ast.parse(content)
            result['valid'] = True
        except SyntaxError as e:
            result['valid'] = False
            result['errors'].append(f"Syntax error: {e}")
            return result
        
        # Check for common issues (but ignore f-strings)
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for dangerous patterns
            if 'eval(' in line or 'exec(' in line:
                result['errors'].append(f"Line {i}: Dangerous function detected")
        
        if result['errors']:
            result['valid'] = False
            
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"File error: {e}")
    
    return result

def validate_plugin_import(plugin_path: str) -> Dict[str, Any]:
    """Try to import the plugin module"""
    result = {'valid': True, 'errors': []}
    
    try:
        # Convert path to module name
        plugin_dir = Path(plugin_path).parent
        module_name = Path(plugin_path).stem
        
        # Add plugin directory to path
        if str(plugin_dir) not in sys.path:
            sys.path.insert(0, str(plugin_dir))
        
        # Try to import
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result['valid'] = True
        else:
            result['valid'] = False
            result['errors'].append("Could not create module spec")
            
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Import error: {e}")
    
    return result

def validate_plugin_creation(plugin_path: str, plugin_class: str = None) -> Dict[str, Any]:
    """Try to create an instance of the plugin"""
    result = {'valid': True, 'errors': []}
    
    try:
        # Import the module
        plugin_dir = Path(plugin_path).parent
        module_name = Path(plugin_path).stem
        
        if str(plugin_dir) not in sys.path:
            sys.path.insert(0, str(plugin_dir))
        
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find create_plugin function or plugin class
        create_func = None
        if hasattr(module, 'create_plugin'):
            create_func = getattr(module, 'create_plugin')
        elif plugin_class and hasattr(module, plugin_class):
            plugin_cls = getattr(module, plugin_class)
            create_func = lambda config=None: plugin_cls(config or {})
        
        if not create_func:
            result['valid'] = False
            result['errors'].append("No create_plugin function found")
            return result
        
        # Try to create plugin instance
        try:
            plugin = create_func()  # Test with no config
            result['valid'] = True
            result['plugin_name'] = getattr(plugin, 'name', 'Unknown')
            result['plugin_version'] = getattr(plugin, 'version', 'Unknown')
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Plugin creation failed: {e}")
            
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Validation error: {e}")
    
    return result

def quick_validate_plugin(plugin_path: str) -> Dict[str, Any]:
    """Run all validation checks"""
    print(f"🔍 Validating plugin: {plugin_path}")
    
    results = {
        'syntax': validate_plugin_syntax(plugin_path),
        'import': validate_plugin_import(plugin_path),
        'creation': validate_plugin_creation(plugin_path)
    }
    
    # Summary
    all_valid = all(r['valid'] for r in results.values())
    total_errors = sum(len(r['errors']) for r in results.values())
    
    print(f"{'✅' if all_valid else '❌'} {'All checks passed' if all_valid else f'{total_errors} issues found'}")
    
    # Show errors
    for check_name, result in results.items():
        if not result['valid']:
            print(f"\n❌ {check_name.title()} errors:")
            for error in result['errors']:
                print(f"   • {error}")
    
    if results['creation']['valid']:
        creation = results['creation']
        print(f"\n✅ Plugin ready: {creation.get('plugin_name', 'Unknown')} v{creation.get('plugin_version', 'Unknown')}")
    
    return {
        'valid': all_valid,
        'results': results,
        'total_errors': total_errors
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validate_plugin.py <plugin_path>")
        print("Example: python validate_plugin.py plugins/base_yield_hunter/base_yield_hunter.py")
        sys.exit(1)
    
    plugin_path = sys.argv[1]
    if not os.path.exists(plugin_path):
        print(f"❌ File not found: {plugin_path}")
        sys.exit(1)
    
    result = quick_validate_plugin(plugin_path)
    sys.exit(0 if result['valid'] else 1)

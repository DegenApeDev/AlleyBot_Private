"""
Plugin Validation Module
Validates plugin structure, imports, and basic functionality
"""
import sys
import os
import ast
import importlib.util
from typing import Dict, List, Any, Optional
from pathlib import Path

def validate_plugin_structure(plugin_path: str) -> Dict[str, Any]:
    """Validate the basic structure of a plugin"""
    result = {'valid': True, 'errors': [], 'warnings': []}
    
    try:
        # Parse the plugin file
        with open(plugin_path, 'r') as f:
            content = f.read()
        
        # Check syntax
        try:
            ast.parse(content)
        except SyntaxError as e:
            result['valid'] = False
            result['errors'].append(f"Syntax error: {e}")
            return result
        
        # Check for required components
        tree = ast.parse(content)
        
        # Look for class inheriting from AlleyBotPlugin
        has_plugin_class = False
        has_create_plugin = False
        has_plugin_info = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check inheritance
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'AlleyBotPlugin':
                        has_plugin_class = True
                    elif isinstance(base, ast.Attribute) and base.attr == 'AlleyBotPlugin':
                        has_plugin_class = True
            
            elif isinstance(node, ast.FunctionDef):
                # Check for create_plugin function
                if node.name == 'create_plugin':
                    has_create_plugin = True
            
            elif isinstance(node, ast.Assign):
                # Check for PLUGIN_INFO variable
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'PLUGIN_INFO':
                        has_plugin_info = True
        
        # __init__.py is a re-export file — don't require plugin class/functions in it
        is_init_file = Path(plugin_path).name == '__init__.py'
        
        if not is_init_file:
            if not has_plugin_class:
                result['warnings'].append("No class inheriting from AlleyBotPlugin found")
            
            if not has_create_plugin:
                result['warnings'].append("No create_plugin function found")
            
            if not has_plugin_info:
                result['warnings'].append("No PLUGIN_INFO metadata found")
        
        return result
        
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Validation error: {e}")
        return result

def validate_plugin_imports(plugin_path: str) -> Dict[str, Any]:
    """Validate that the plugin can be imported and instantiated"""
    result = {'valid': True, 'errors': [], 'warnings': []}
    
    # __init__.py uses relative imports which can't be validated standalone
    # It's a re-export file — skip import validation for it
    if Path(plugin_path).name == '__init__.py':
        result['warnings'].append("Skipped import validation for __init__.py (re-export file)")
        return result
    
    try:
        # Get plugin directory
        plugin_dir = Path(plugin_path).parent
        module_name = Path(plugin_path).stem
        
        # Add to path
        if str(plugin_dir) not in sys.path:
            sys.path.insert(0, str(plugin_dir))
        
        # Try to import
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check for create_plugin
            if hasattr(module, 'create_plugin'):
                try:
                    # Try to create plugin instance
                    plugin = module.create_plugin()
                    
                    # Check if it has required methods
                    if hasattr(plugin, 'get_commands'):
                        commands = plugin.get_commands()
                        if not commands:
                            result['warnings'].append("Plugin has no commands")
                    else:
                        result['warnings'].append(f"Plugin has {len(commands)} commands: {list(commands.keys())}")
                    
                    # Check if it inherits from AlleyBotPlugin
                    if hasattr(plugin, '__class__'):
                        bases = plugin.__class__.__bases__
                        if not any(base.__name__ == 'AlleyBotPlugin' for base in bases):
                            result['warnings'].append("Plugin class doesn't inherit from AlleyBotPlugin")
                    
                    result['plugin_name'] = getattr(plugin, 'name', 'Unknown')
                    result['plugin_version'] = getattr(plugin, 'version', 'Unknown')
                    
                except Exception as e:
                    result['valid'] = False
                    result['errors'].append(f"Plugin instantiation failed: {e}")
            else:
                result['warnings'].append("No create_plugin function found")
        else:
            result['valid'] = False
            result['errors'].append("Could not create module spec")
            
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Import validation failed: {e}")
    
    return result

def validate_plugin(plugin_path: str) -> Dict[str, Any]:
    """Complete plugin validation"""
    print(f"🔍 Validating plugin: {plugin_path}")
    
    # Structure validation
    structure_result = validate_plugin_structure(plugin_path)
    
    # Import validation
    import_result = validate_plugin_imports(plugin_path)
    
    # Combine results
    result = {
        'valid': structure_result['valid'] and import_result['valid'],
        'errors': structure_result['errors'] + import_result['errors'],
        'warnings': structure_result['warnings'] + import_result['warnings'],
        'plugin_name': import_result.get('plugin_name', 'Unknown'),
        'plugin_version': import_result.get('plugin_version', 'Unknown')
    }
    
    # Summary
    if result['valid']:
        print(f"✅ Plugin validation passed: {result['plugin_name']} v{result['plugin_version']}")
    else:
        print(f"❌ Plugin validation failed: {len(result['errors'])} errors, {len(result['warnings'])} warnings")
    
    if result['errors']:
        print("🚨 Errors:")
        for error in result['errors']:
            print(f"   • {error}")
    
    if result['warnings']:
        print("⚠️  Warnings:")
        for warning in result['warnings']:
            print(f"   • {warning}")
    
    return result

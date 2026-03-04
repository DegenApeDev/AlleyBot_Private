#!/usr/bin/env python3
"""
Check which Telegram command handlers are registered
"""
import sys
sys.path.insert(0, '/home/alley/AlleyBot')

from plugin_manager import PluginManager
import json

# Load config
with open('plugin_config.json', 'r') as f:
    config = json.load(f)

# Create plugin manager
pm = PluginManager()

# Load telegram plugin
telegram_config = config.get('telegram', {})
telegram = pm.load_plugin('telegram', telegram_config, None, None)

if telegram:
    print("✅ Telegram plugin loaded")
    
    # Check if test_commands exists
    if hasattr(telegram, 'test_commands'):
        print("✅ test_commands attribute exists")
        print(f"   Type: {type(telegram.test_commands)}")
        print(f"   Methods: {[m for m in dir(telegram.test_commands) if not m.startswith('_')]}")
    else:
        print("❌ test_commands attribute missing")
    
    # Check application handlers
    if hasattr(telegram, 'application'):
        print(f"\n✅ Application exists")
        if hasattr(telegram.application, 'handlers'):
            handler_count = sum(len(handlers) for handlers in telegram.application.handlers.values())
            print(f"   Total handlers: {handler_count}")
            
            # Look for test commands
            for group, handlers in telegram.application.handlers.items():
                for handler in handlers:
                    if hasattr(handler, 'command'):
                        commands = handler.command if isinstance(handler.command, list) else [handler.command]
                        for cmd in commands:
                            if 'test' in cmd:
                                print(f"   Found test command: /{cmd}")
    else:
        print("❌ Application not initialized yet")
else:
    print("❌ Failed to load telegram plugin")

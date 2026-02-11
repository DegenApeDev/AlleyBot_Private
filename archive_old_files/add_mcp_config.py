#!/usr/bin/env python3
"""
Add MCP plugin configuration to plugin_config.json
"""
import json

# Load current config
with open('plugin_config.json', 'r') as f:
    config = json.load(f)

# Add MCP plugin configuration
config['mcp'] = {
    "enabled": True,
    "config": {
        "web_access": True,
        "self_improvement": True,
        "research_cache_size": 50
    }
}

# Save updated config
with open('plugin_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✅ MCP plugin configuration added to plugin_config.json")

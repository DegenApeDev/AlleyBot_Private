#!/usr/bin/env python3
"""Quick script to regenerate agent card with TEE support"""
import sys
sys.path.insert(0, '/home/degendev/Dev/Agents/MoltbookBot')

from plugins.analytics.agent_card import AgentCardGenerator

class MockCore:
    pass

gen = AgentCardGenerator(MockCore())
card = gen.generate()

print('✅ Agent card generated')
print('supportedTrust:', card.get('supportedTrust', []))

# Save to static
static_path = '/home/degendev/Dev/Agents/MoltbookBot/static/.well-known/agent-card.json'
gen.save_static(static_path)
print('📁 Saved to', static_path)

#!/usr/bin/env python3
"""Fix indentation of all delegation return statements in autonomous_brain.py"""
import re

with open('/home/degendev/Dev/Agents/AlleyBot_Private/src/agentic/autonomous_brain.py') as f:
    content = f.read()

# Fix any return statement that starts with exactly 4 spaces and is inside a method
# These should have 8 spaces (class indent + method indent)
lines = content.split('\n')
fixed = []
i = 0
changes = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    # Check if this is a badly indented delegation return (4 spaces when it should be 8)
    # Pattern: line has exactly 4 spaces of indent, followed by 'return self.coordinator.' or 'return await self.coordinator.'
    if line.startswith('    ') and not line.startswith('        ') and len(line) > 4 and line[4] != ' ':
        # Check if previous non-empty lines contain '"""Delegate to brain module."""' (indicating this is a delegation)
        # Or check if this is a return to coordinator
        if stripped.startswith('return self.coordinator.') or stripped.startswith('return await self.coordinator.'):
            fixed.append('        ' + stripped)
            changes += 1
            i += 1
            continue
    
    fixed.append(line)
    i += 1

result = '\n'.join(fixed)
with open('/home/degendev/Dev/Agents/AlleyBot_Private/src/agentic/autonomous_brain.py', 'w') as f:
    f.write(result)

print(f'Fixed {changes} indentation issues ({len(fixed)} lines)')

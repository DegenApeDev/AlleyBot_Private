#!/usr/bin/env python3
"""
Debug skill generation
"""
from skill_generator import SkillGenerator

skill_gen = SkillGenerator()
result = skill_gen.generate_skill(
    skill_name='Test Skill',
    skill_description='Test description',
    platforms=['Moltx'],
    capabilities=['test']
)
print('Result type:', type(result))
print('Result:', result)

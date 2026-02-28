"""
Dynamic Skill Scanner for ERC-8004 Agent Card

Scans skills/ directory and extracts OASF-compatible skills from SKILL.md files.
Enables dynamic skill discovery for A2A monetization.

Part of A2A ERC-8004 Improvement Plan - Phase 1
"""

import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


class SkillScanner:
    """
    Scans skills/ directory and extracts skill metadata.
    
    Reads SKILL.md files and parses:
    - Skill name and description
    - OASF taxonomy mapping
    - Suggested pricing
    - Performance metrics
    """
    
    def __init__(self, skills_dir: str = None):
        """
        Initialize skill scanner.
        
        Args:
            skills_dir: Path to skills directory (default: ./skills)
        """
        if skills_dir is None:
            # Default to skills/ in AlleyBot root
            base_dir = Path(__file__).parent.parent.parent
            skills_dir = base_dir / 'skills'
        
        self.skills_dir = Path(skills_dir)
        
        # OASF 0.8.0 taxonomy mapping
        self.category_map = {
            'content': 'natural_language_processing/creative_content',
            'analysis': 'analytical_skills/data_analysis',
            'blockchain': 'analytical_skills/data_analysis/blockchain_analysis',
            'engagement': 'interaction/user_engagement',
            'reasoning': 'advanced_reasoning_planning',
            'coding': 'analytical_skills/coding_skills',
            'social': 'natural_language_processing/sentiment_analysis',
            'generation': 'natural_language_processing/natural_language_generation',
        }
    
    def scan_skills_directory(self) -> List[Dict[str, Any]]:
        """
        Scan skills/ directory for all SKILL.md files.
        
        Returns:
            List of skill objects with metadata
        """
        skills = []
        
        if not self.skills_dir.exists():
            print(f"⚠️ Skills directory not found: {self.skills_dir}")
            return skills
        
        # Find all SKILL.md files
        skill_files = list(self.skills_dir.rglob('SKILL.md'))
        skill_files.extend(list(self.skills_dir.glob('*_skill.md')))
        
        print(f"🔍 Found {len(skill_files)} skill files")
        
        for skill_file in skill_files:
            try:
                skill = self.parse_skill_file(skill_file)
                if skill:
                    skills.append(skill)
            except Exception as e:
                print(f"⚠️ Failed to parse {skill_file.name}: {e}")
        
        print(f"✅ Scanned {len(skills)} skills from {self.skills_dir}")
        return skills
    
    def parse_skill_file(self, skill_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse SKILL.md file and extract metadata.
        
        Args:
            skill_path: Path to SKILL.md file
        
        Returns:
            Skill metadata dict or None if parsing fails
        """
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️ Could not read {skill_path}: {e}")
            return None
        
        # Extract skill ID from directory name or filename
        if skill_path.name == 'SKILL.md':
            skill_id = skill_path.parent.name
        else:
            skill_id = skill_path.stem.replace('_skill', '')
        
        # Parse skill metadata
        skill = {
            'id': skill_id,
            'name': self._extract_name(content, skill_id),
            'description': self._extract_description(content),
            'category': self._extract_category(content),
            'oasf_skills': self._map_to_oasf(content, skill_id),
            'pricing': self._extract_pricing(content),
            'file_path': str(skill_path),
            'auto_generated': self._is_auto_generated(skill_path),
            'performance': {
                'uses': 0,
                'success_rate': 0,
                'last_used': None,
            },
        }
        
        return skill
    
    def _extract_name(self, content: str, skill_id: str) -> str:
        """Extract skill name from content"""
        # Look for # Title or ## Title
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # Fallback: use skill_id with title case
        return skill_id.replace('-', ' ').replace('_', ' ').title()
    
    def _extract_description(self, content: str) -> str:
        """Extract skill description from content"""
        # Look for description after title
        lines = content.split('\n')
        description_lines = []
        found_title = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                found_title = True
                continue
            if found_title and line and not line.startswith('#'):
                description_lines.append(line)
                if len(description_lines) >= 3:  # Get first 3 lines
                    break
        
        description = ' '.join(description_lines)
        if len(description) > 200:
            description = description[:197] + '...'
        
        return description or "AI-powered skill"
    
    def _extract_category(self, content: str) -> str:
        """Extract skill category from content"""
        content_lower = content.lower()
        
        # Check for category keywords
        if 'blockchain' in content_lower or 'on-chain' in content_lower:
            return 'blockchain'
        elif 'content' in content_lower or 'post' in content_lower:
            return 'content'
        elif 'analysis' in content_lower or 'analyze' in content_lower:
            return 'analysis'
        elif 'engagement' in content_lower or 'social' in content_lower:
            return 'engagement'
        elif 'code' in content_lower or 'programming' in content_lower:
            return 'coding'
        elif 'reasoning' in content_lower or 'planning' in content_lower:
            return 'reasoning'
        else:
            return 'general'
    
    def _map_to_oasf(self, content: str, skill_id: str) -> List[str]:
        """Map skill to OASF 0.8.0 taxonomy slugs"""
        oasf_skills = []
        category = self._extract_category(content)
        
        # Get base OASF skill from category
        if category in self.category_map:
            oasf_skills.append(self.category_map[category])
        
        # Add specific skills based on content analysis
        content_lower = content.lower()
        
        if 'blockchain' in content_lower:
            oasf_skills.append('analytical_skills/data_analysis/blockchain_analysis')
        if 'market' in content_lower or 'trading' in content_lower:
            oasf_skills.append('analytical_skills/data_analysis/market_analysis')
        if 'sentiment' in content_lower:
            oasf_skills.append('natural_language_processing/sentiment_analysis')
        if 'generate' in content_lower or 'create' in content_lower:
            oasf_skills.append('natural_language_processing/natural_language_generation/text_completion')
        if 'debate' in content_lower or 'argue' in content_lower:
            oasf_skills.append('advanced_reasoning_planning/debate_argumentation')
        if 'code' in content_lower:
            oasf_skills.append('analytical_skills/coding_skills/text_to_code')
        if 'optimize' in content_lower:
            oasf_skills.append('evaluation_monitoring/quality_evaluation')
        
        # Deduplicate
        return list(dict.fromkeys(oasf_skills))
    
    def _extract_pricing(self, content: str) -> Dict[str, Any]:
        """Extract pricing information from content"""
        # Look for pricing hints in content
        content_lower = content.lower()
        
        # Default pricing based on complexity
        if 'complex' in content_lower or 'advanced' in content_lower:
            suggested = 0.50
        elif 'simple' in content_lower or 'basic' in content_lower:
            suggested = 0.10
        else:
            suggested = 0.25
        
        return {
            'suggested': suggested,
            'currency': 'USDC',
            'min': suggested * 0.5,
            'max': suggested * 2.0,
        }
    
    def _is_auto_generated(self, skill_path: Path) -> bool:
        """Check if skill was auto-generated by selfimprove"""
        # Check if in auto_acquired directory
        if 'auto_acquired' in str(skill_path):
            return True
        
        # Check if created recently by selfimprove
        try:
            with open(skill_path, 'r') as f:
                content = f.read()
                if 'auto-generated' in content.lower() or 'selfimprove' in content.lower():
                    return True
        except:
            pass
        
        return False
    
    def get_skill_count(self) -> int:
        """Get total count of discovered skills"""
        return len(self.scan_skills_directory())
    
    def get_skills_by_category(self) -> Dict[str, List[Dict]]:
        """Group skills by category"""
        skills = self.scan_skills_directory()
        by_category = {}
        
        for skill in skills:
            category = skill['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(skill)
        
        return by_category
    
    def get_monetizable_skills(self) -> List[Dict]:
        """Get skills suitable for A2A monetization"""
        skills = self.scan_skills_directory()
        
        # Filter out test skills and internal tools
        monetizable = []
        for skill in skills:
            skill_id = skill['id']
            if skill_id in ['test-skill', 'time-checker']:
                continue
            monetizable.append(skill)
        
        return monetizable


def create_skill_scanner(skills_dir: str = None) -> SkillScanner:
    """Factory function to create skill scanner"""
    return SkillScanner(skills_dir)


# CLI for testing
if __name__ == '__main__':
    scanner = SkillScanner()
    skills = scanner.scan_skills_directory()
    
    print(f"\n📊 Skill Scanner Results:")
    print(f"Total skills: {len(skills)}")
    
    by_category = scanner.get_skills_by_category()
    print(f"\nBy category:")
    for category, cat_skills in by_category.items():
        print(f"  {category}: {len(cat_skills)} skills")
    
    print(f"\nMonetizable skills: {len(scanner.get_monetizable_skills())}")
    
    print(f"\nSample skills:")
    for skill in skills[:5]:
        print(f"  - {skill['name']} ({skill['id']})")
        print(f"    Category: {skill['category']}")
        print(f"    OASF: {', '.join(skill['oasf_skills'][:2])}")
        print(f"    Price: ${skill['pricing']['suggested']} USDC")
        print()

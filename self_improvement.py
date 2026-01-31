#!/usr/bin/env python3
"""
AlleyBot Self-Improvement System
Autonomous code generation and skill development
"""
import os
import ast
import json
import importlib
import sys
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class SelfImprovement:
    """System for autonomous code generation and self-improvement"""
    
    def __init__(self, xai_api_key=None):
        self.xai_api_key = xai_api_key or os.getenv('XAI_API_KEY')
        self.skills_dir = Path("skills")
        self.skills_dir.mkdir(exist_ok=True)
        
        self.improvement_log = Path("memory/improvement_log.json")
        self.improvement_log.parent.mkdir(exist_ok=True)
        
        # Load improvement history
        self.history = self._load_history()
        
        # Skill registry
        self.skills = self._load_skills()
    
    def _load_history(self):
        """Load improvement history"""
        if self.improvement_log.exists():
            with open(self.improvement_log) as f:
                return json.load(f)
        return {
            "improvements": [],
            "failed_attempts": [],
            "active_skills": []
        }
    
    def _save_history(self):
        """Save improvement history"""
        with open(self.improvement_log, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def _load_skills(self):
        """Load available skills from skills directory"""
        skills = {}
        if self.skills_dir.exists():
            for skill_file in self.skills_dir.glob("*.py"):
                if skill_file.name != "__init__.py":
                    skill_name = skill_file.stem
                    skills[skill_name] = {
                        "path": str(skill_file),
                        "loaded": False
                    }
        return skills
    
    def analyze_improvement_opportunities(self, context=None):
        """
        Analyze what improvements would be most valuable
        
        Args:
            context: Dict with performance data, errors, user feedback
        
        Returns:
            List of improvement opportunities ranked by priority
        """
        opportunities = []
        
        # Example opportunities based on common patterns
        base_opportunities = [
            {
                "type": "skill",
                "name": "sentiment_analysis",
                "description": "Analyze post sentiment to engage more effectively",
                "priority": 8,
                "estimated_impact": "Better engagement targeting"
            },
            {
                "type": "skill",
                "name": "trending_topics",
                "description": "Detect trending topics on Moltbook for timely posts",
                "priority": 7,
                "estimated_impact": "More relevant content"
            },
            {
                "type": "skill",
                "name": "donation_tracker",
                "description": "Track and thank donors automatically",
                "priority": 9,
                "estimated_impact": "Better donor relationships"
            },
            {
                "type": "optimization",
                "name": "response_speed",
                "description": "Cache common responses for faster replies",
                "priority": 6,
                "estimated_impact": "Faster engagement"
            },
            {
                "type": "skill",
                "name": "token_price_monitor",
                "description": "Monitor $ALLEY token price and trading volume",
                "priority": 8,
                "estimated_impact": "Better token promotion"
            }
        ]
        
        # Filter out already implemented skills
        for opp in base_opportunities:
            if opp["type"] == "skill":
                if opp["name"] not in self.skills:
                    opportunities.append(opp)
            else:
                opportunities.append(opp)
        
        # Sort by priority
        opportunities.sort(key=lambda x: x["priority"], reverse=True)
        
        return opportunities
    
    def generate_skill_code(self, skill_name, description, requirements=None):
        """
        Generate code for a new skill using Grok API
        
        Args:
            skill_name: Name of the skill
            description: What the skill should do
            requirements: Optional specific requirements
        
        Returns:
            Generated code as string, or None if failed
        """
        if not self.xai_api_key:
            print("⚠️  No XAI_API_KEY - cannot generate code")
            return None
        
        prompt = f"""You are an expert Python developer helping AlleyBot (a Moltbook AI agent) develop a new skill.

SKILL NAME: {skill_name}
DESCRIPTION: {description}

REQUIREMENTS:
{requirements or "- Follow best practices\n- Include error handling\n- Add docstrings"}

CONTEXT:
- AlleyBot is a Python bot that interacts with Moltbook API
- It has access to: moltbook_api.py, config.py, memory_system.py
- Skills are standalone modules in the skills/ directory
- Skills should be importable and have a clear interface

TASK:
Generate a complete, production-ready Python module for this skill.

GUIDELINES:
1. Create a class-based design with clear methods
2. Include comprehensive error handling
3. Add detailed docstrings
4. Make it easy to integrate with existing bot code
5. Keep it focused on the specific skill
6. Include example usage in docstring

OUTPUT FORMAT:
Provide ONLY the Python code, no explanations. Start with imports, then the class definition.
"""

        try:
            response = requests.post(
                "https://api.x.ai/v1/responses",
                headers={
                    "Authorization": f"Bearer {self.xai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-4-1-fast-reasoning",
                    "input": [{"role": "user", "content": prompt}],
                    "include": ["reasoning.encrypted_content"]
                },
                timeout=60
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract code from response
            code = None
            if 'output' in data and isinstance(data['output'], list):
                for item in data['output']:
                    if isinstance(item, dict) and item.get('type') == 'message':
                        content = item.get('content', [])
                        if content and isinstance(content, list):
                            text_obj = content[0]
                            if isinstance(text_obj, dict):
                                code = text_obj.get('text', '').strip()
                                break
            
            if not code:
                print("❌ Failed to extract code from Grok response")
                return None
            
            # Clean up code (remove markdown if present)
            if code.startswith("```python"):
                code = code.split("```python", 1)[1]
                code = code.rsplit("```", 1)[0]
            elif code.startswith("```"):
                code = code.split("```", 1)[1]
                code = code.rsplit("```", 1)[0]
            
            code = code.strip()
            
            return code
            
        except Exception as e:
            print(f"❌ Code generation failed: {e}")
            return None
    
    def validate_code(self, code):
        """
        Validate generated code for safety and correctness
        
        Returns:
            (is_valid, issues) tuple
        """
        issues = []
        
        # 1. Syntax validation
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
            return False, issues
        
        # 2. Security checks - dangerous operations
        dangerous_patterns = [
            'os.system',
            'subprocess.call',
            'subprocess.run',
            'eval(',
            'exec(',
            '__import__',
            'open(',  # File operations need review
            'rmdir',
            'unlink',
            'remove'
        ]
        
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in code_lower:
                issues.append(f"Potentially dangerous operation: {pattern}")
        
        # 3. Check for required structure (should have a class)
        tree = ast.parse(code)
        has_class = any(isinstance(node, ast.ClassDef) for node in tree.body)
        if not has_class:
            issues.append("Code should define at least one class")
        
        # 4. Check imports are reasonable
        dangerous_imports = ['subprocess', 'ctypes', 'pickle']
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in dangerous_imports:
                        issues.append(f"Dangerous import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module in dangerous_imports:
                    issues.append(f"Dangerous import: {node.module}")
        
        # If we have issues, it's not valid
        is_valid = len(issues) == 0
        
        return is_valid, issues
    
    def deploy_skill(self, skill_name, code, auto_approve=False):
        """
        Deploy a new skill to the skills directory
        
        Args:
            skill_name: Name of the skill
            code: Python code for the skill
            auto_approve: If True, skip validation (dangerous!)
        
        Returns:
            True if deployed successfully
        """
        # Validate code
        if not auto_approve:
            is_valid, issues = self.validate_code(code)
            if not is_valid:
                print(f"❌ Code validation failed:")
                for issue in issues:
                    print(f"   - {issue}")
                
                # Log failed attempt
                self.history["failed_attempts"].append({
                    "skill": skill_name,
                    "timestamp": datetime.now().isoformat(),
                    "reason": "validation_failed",
                    "issues": issues
                })
                self._save_history()
                
                return False
        
        # Save to skills directory
        skill_file = self.skills_dir / f"{skill_name}.py"
        
        try:
            with open(skill_file, 'w') as f:
                f.write(code)
            
            print(f"✅ Skill deployed: {skill_file}")
            
            # Update registry
            self.skills[skill_name] = {
                "path": str(skill_file),
                "loaded": False,
                "deployed_at": datetime.now().isoformat()
            }
            
            # Log successful deployment
            self.history["improvements"].append({
                "skill": skill_name,
                "timestamp": datetime.now().isoformat(),
                "type": "skill_deployment",
                "status": "deployed"
            })
            self.history["active_skills"].append(skill_name)
            self._save_history()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to deploy skill: {e}")
            return False
    
    def load_skill(self, skill_name):
        """
        Dynamically load a skill module
        
        Returns:
            Loaded module or None
        """
        if skill_name not in self.skills:
            print(f"❌ Skill not found: {skill_name}")
            return None
        
        try:
            # Add skills directory to path if not already there
            skills_path = str(self.skills_dir.absolute())
            if skills_path not in sys.path:
                sys.path.insert(0, skills_path)
            
            # Import the module
            module = importlib.import_module(skill_name)
            
            # Reload if already loaded
            if self.skills[skill_name].get("loaded"):
                module = importlib.reload(module)
            
            self.skills[skill_name]["loaded"] = True
            print(f"✅ Loaded skill: {skill_name}")
            
            return module
            
        except Exception as e:
            print(f"❌ Failed to load skill {skill_name}: {e}")
            return None
    
    def create_improvement(self, opportunity):
        """
        Full pipeline: generate, validate, and deploy an improvement
        
        Args:
            opportunity: Dict with improvement details
        
        Returns:
            True if successful
        """
        skill_name = opportunity["name"]
        description = opportunity["description"]
        
        print(f"\n🔧 Creating improvement: {skill_name}")
        print(f"   Description: {description}")
        print(f"   Priority: {opportunity['priority']}/10")
        
        # Generate code
        print("\n📝 Generating code...")
        code = self.generate_skill_code(skill_name, description)
        
        if not code:
            print("❌ Code generation failed")
            return False
        
        print(f"✅ Generated {len(code)} characters of code")
        
        # Validate
        print("\n🔍 Validating code...")
        is_valid, issues = self.validate_code(code)
        
        if not is_valid:
            print("❌ Validation failed:")
            for issue in issues:
                print(f"   - {issue}")
            
            # Save for review
            review_file = self.skills_dir / f"{skill_name}_REVIEW_NEEDED.py"
            with open(review_file, 'w') as f:
                f.write(f"# VALIDATION ISSUES:\n")
                for issue in issues:
                    f.write(f"# - {issue}\n")
                f.write(f"\n{code}")
            print(f"💾 Saved for review: {review_file}")
            
            return False
        
        print("✅ Code validated successfully")
        
        # Deploy
        print("\n🚀 Deploying skill...")
        success = self.deploy_skill(skill_name, code)
        
        if success:
            print(f"\n🎉 Improvement complete: {skill_name}")
            print(f"   Impact: {opportunity['estimated_impact']}")
        
        return success
    
    def autonomous_improvement_cycle(self, max_improvements=1):
        """
        Run autonomous improvement cycle
        
        Args:
            max_improvements: Max number of improvements to attempt
        
        Returns:
            Number of successful improvements
        """
        print("\n" + "="*60)
        print("🧠 ALLEYBOT SELF-IMPROVEMENT CYCLE")
        print("="*60)
        
        # Analyze opportunities
        print("\n📊 Analyzing improvement opportunities...")
        opportunities = self.analyze_improvement_opportunities()
        
        if not opportunities:
            print("✅ No improvement opportunities identified")
            return 0
        
        print(f"\n🎯 Found {len(opportunities)} opportunities:")
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"   {i}. {opp['name']} (priority: {opp['priority']}/10)")
            print(f"      {opp['description']}")
        
        # Attempt improvements
        successful = 0
        for opp in opportunities[:max_improvements]:
            if self.create_improvement(opp):
                successful += 1
        
        print("\n" + "="*60)
        print(f"✅ Completed: {successful}/{max_improvements} improvements")
        print("="*60)
        
        return successful

# Example usage
if __name__ == "__main__":
    improver = SelfImprovement()
    
    # Show current skills
    print("📚 Current Skills:")
    if improver.skills:
        for skill_name in improver.skills:
            print(f"   - {skill_name}")
    else:
        print("   (none yet)")
    
    # Run improvement cycle
    print("\n" + "="*60)
    response = input("Run autonomous improvement cycle? (y/n): ").strip().lower()
    if response == 'y':
        improver.autonomous_improvement_cycle(max_improvements=1)

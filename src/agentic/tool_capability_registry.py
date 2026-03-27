"""
Tool Capability Registry - AI-Driven Tool Discovery and Selection

Maps capabilities to available tools across plugins and skills.
Enables AlleyBot to intelligently select the best tool for any task.

Example:
    "analyze blockchain data" → [onchain, solana_token_analysis, blockchain-analysis skill]
    "create social content" → [moltx, clawbr, content-generation skill]
    "track donations" → [donation_tracker skill]
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ToolCapabilityRegistry:
    """
    Intelligent tool discovery and selection system.
    
    Scans all plugins and skills to build a capability index,
    then uses AI to match tasks to the best available tools.
    """
    
    def __init__(self, tool_orchestrator, plugin_manager, llm_client=None):
        """
        Initialize tool capability registry.
        
        Args:
            tool_orchestrator: ToolOrchestrator instance
            plugin_manager: PluginManager instance
            llm_client: LLM client for AI-driven tool selection
        """
        self.tools = tool_orchestrator
        self.plugins = plugin_manager
        self.llm = llm_client
        
        # Capability index: {capability: [tools]}
        self.capability_map: Dict[str, List[Dict]] = {}
        
        # Tool metadata cache
        self.tool_metadata: Dict[str, Dict] = {}
        
        # Build index
        self._build_capability_index()
        
        logger.info(f"✅ Tool Capability Registry initialized")
        logger.info(f"   Indexed {len(self.capability_map)} capabilities")
        logger.info(f"   Available tools: {len(self.tool_metadata)}")
    
    def _build_capability_index(self):
        """Scan all plugins and skills to build capability index"""
        logger.info("🔍 Building tool capability index...")
        
        # Scan plugins
        self._index_plugins()
        
        # Scan skills
        self._index_skills()
        
        logger.info(f"✅ Capability index built: {len(self.capability_map)} capabilities")
    
    def _index_plugins(self):
        """Index all available plugins and their capabilities"""
        if not self.plugins or not hasattr(self.plugins, 'plugins'):
            return
        
        for plugin_name, plugin in self.plugins.plugins.items():
            try:
                # Get plugin metadata
                capabilities = self._extract_plugin_capabilities(plugin)
                description = getattr(plugin, 'description', f'{plugin_name} plugin')
                
                # Get available actions/commands
                actions = {}
                if hasattr(plugin, 'get_commands'):
                    try:
                        actions = plugin.get_commands()
                    except:
                        pass
                
                # Store tool metadata
                self.tool_metadata[plugin_name] = {
                    'type': 'plugin',
                    'name': plugin_name,
                    'description': description,
                    'capabilities': capabilities,
                    'actions': list(actions.keys()) if actions else [],
                    'enabled': getattr(plugin, 'enabled', True)
                }
                
                # Index capabilities
                for capability in capabilities:
                    self.capability_map.setdefault(capability, []).append({
                        'type': 'plugin',
                        'name': plugin_name,
                        'description': description,
                        'actions': list(actions.keys()) if actions else [],
                        'confidence': 0.8  # Base confidence for plugins
                    })
                
                logger.debug(f"  ✅ Indexed plugin: {plugin_name} ({len(capabilities)} capabilities)")
                
            except Exception as e:
                logger.debug(f"  ⚠️ Failed to index plugin {plugin_name}: {e}")
    
    def _extract_plugin_capabilities(self, plugin) -> List[str]:
        """Extract capabilities from a plugin"""
        capabilities = []
        
        # Get from plugin name
        plugin_name = getattr(plugin, 'name', '').lower()
        if plugin_name:
            capabilities.append(plugin_name)
        
        # Get from description
        description = getattr(plugin, 'description', '').lower()
        if description:
            # Extract key phrases
            if 'social' in description or 'post' in description:
                capabilities.extend(['social_media', 'content_creation', 'engagement'])
            if 'trading' in description or 'trade' in description:
                capabilities.extend(['trading', 'crypto_trading', 'market_analysis'])
            if 'analytics' in description or 'analyze' in description:
                capabilities.extend(['analytics', 'data_analysis', 'reporting'])
            if 'blockchain' in description or 'onchain' in description:
                capabilities.extend(['blockchain', 'onchain_data', 'crypto_analysis'])
            if 'wallet' in description or 'balance' in description:
                capabilities.extend(['wallet_management', 'balance_tracking'])
        
        # Get from supported channels
        if hasattr(plugin, 'supported_channels'):
            capabilities.extend(plugin.supported_channels)
        
        return list(set(capabilities))  # Remove duplicates
    
    def _index_skills(self):
        """Index all available skills from skills directory"""
        skills_dir = Path('skills')
        if not skills_dir.exists():
            return
        
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith('_') or skill_dir.name in ['dynamic', 'imported', 'auto_acquired']:
                continue
            
            try:
                skill_info = self._extract_skill_info(skill_dir)
                if skill_info:
                    skill_name = skill_dir.name
                    
                    # Store tool metadata
                    self.tool_metadata[f"skill_{skill_name}"] = {
                        'type': 'skill',
                        'name': skill_name,
                        'description': skill_info.get('description', ''),
                        'capabilities': skill_info.get('capabilities', []),
                        'path': str(skill_dir),
                        'enabled': True
                    }
                    
                    # Index capabilities
                    for capability in skill_info.get('capabilities', []):
                        self.capability_map.setdefault(capability, []).append({
                            'type': 'skill',
                            'name': skill_name,
                            'description': skill_info.get('description', ''),
                            'path': str(skill_dir),
                            'confidence': 0.7  # Base confidence for skills
                        })
                    
                    logger.debug(f"  ✅ Indexed skill: {skill_name}")
                    
            except Exception as e:
                logger.debug(f"  ⚠️ Failed to index skill {skill_dir.name}: {e}")
    
    def _extract_skill_info(self, skill_dir: Path) -> Optional[Dict]:
        """Extract information from a skill directory"""
        skill_info = {
            'name': skill_dir.name,
            'description': '',
            'capabilities': []
        }
        
        # Check for skill.md or README.md
        for readme_name in ['skill.md', 'README.md', 'readme.md']:
            readme_path = skill_dir / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text()
                    # Extract first line as description
                    lines = content.strip().split('\n')
                    if lines:
                        skill_info['description'] = lines[0].strip('#').strip()
                    break
                except:
                    pass
        
        # Infer capabilities from skill name
        skill_name = skill_dir.name.lower()
        skill_info['capabilities'].append(skill_name)
        
        # Add common capability mappings
        if 'content' in skill_name or 'generation' in skill_name:
            skill_info['capabilities'].extend(['content_creation', 'content_generation'])
        if 'engagement' in skill_name or 'social' in skill_name:
            skill_info['capabilities'].extend(['engagement', 'social_media'])
        if 'blockchain' in skill_name or 'crypto' in skill_name:
            skill_info['capabilities'].extend(['blockchain', 'crypto_analysis'])
        if 'trading' in skill_name or 'swap' in skill_name:
            skill_info['capabilities'].extend(['trading', 'defi'])
        if 'analysis' in skill_name or 'analyzer' in skill_name:
            skill_info['capabilities'].extend(['analytics', 'data_analysis'])
        if 'donation' in skill_name or 'tracker' in skill_name:
            skill_info['capabilities'].extend(['tracking', 'monitoring'])
        
        return skill_info if skill_info['capabilities'] else None
    
    def find_tools_for_task(
        self,
        task_description: str,
        goal_context: Optional[str] = None,
        available_params: Optional[Dict] = None,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Use AI to match task description to available tools.
        
        Args:
            task_description: Description of the task to accomplish
            goal_context: Additional context from the goal
            available_params: Parameters available for the task
            max_results: Maximum number of tools to return
        
        Returns:
            Ranked list of tools that can help with the task.
            Each tool dict contains: {tool, action, confidence, suggested_params}
        """
        # Build context for AI
        context = f"Task: {task_description}"
        if goal_context:
            context += f"\nGoal: {goal_context}"
        if available_params:
            context += f"\nAvailable data: {json.dumps(available_params)}"
        
        # Get all available tools
        available_tools = self._get_all_tools_summary()
        
        # Use AI to select best tools
        if self.llm:
            try:
                selected_tools = self._ai_tool_selection(context, available_tools, max_results)
                if selected_tools:
                    return selected_tools
            except Exception as e:
                logger.debug(f"AI tool selection failed, using fallback: {e}")
        
        # Fallback: keyword-based matching
        return self._keyword_based_selection(task_description, max_results)
    
    def _get_all_tools_summary(self) -> str:
        """Get a summary of all available tools for AI context"""
        summary = "Available Tools:\n\n"
        
        for tool_name, metadata in self.tool_metadata.items():
            if not metadata.get('enabled', True):
                continue
            
            tool_type = metadata['type']
            description = metadata.get('description', 'No description')
            actions = metadata.get('actions', [])
            
            summary += f"- {tool_name} ({tool_type}): {description}\n"
            if actions:
                summary += f"  Actions: {', '.join(actions[:5])}\n"
        
        return summary
    
    def _ai_tool_selection(self, context: str, available_tools: str, max_results: int) -> List[Dict]:
        """Use AI to select the best tools for the task"""
        prompt = f"""You are AlleyBot's tool selection system. Given a task, select the best tools to accomplish it.

{context}

{available_tools}

Select the top {max_results} tools that would be most helpful for this task.
For each tool, specify:
1. Tool name (exact name from the list)
2. Specific action to take (if applicable)
3. Confidence (0.0-1.0)
4. Brief justification

Respond in JSON format:
[
  {{"tool": "tool_name", "action": "action_name", "confidence": 0.95, "justification": "why this tool"}},
  ...
]
"""
        
        try:
            response = self.llm.chat([
                {"role": "system", "content": "You are a tool selection expert. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse response
            content = response.get('content', '').strip()
            if content.startswith('```'):
                # Remove code block markers
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            tools = json.loads(content)
            
            # Validate and enrich results
            validated_tools = []
            for tool in tools:
                if tool.get('tool') in self.tool_metadata:
                    validated_tools.append({
                        'tool': tool['tool'],
                        'action': tool.get('action', 'execute'),
                        'confidence': tool.get('confidence', 0.5),
                        'justification': tool.get('justification', ''),
                        'metadata': self.tool_metadata[tool['tool']]
                    })
            
            return validated_tools[:max_results]
            
        except Exception as e:
            logger.debug(f"AI tool selection error: {e}")
            return []
    
    def _keyword_based_selection(self, task_description: str, max_results: int) -> List[Dict]:
        """Fallback: keyword-based tool selection"""
        task_lower = task_description.lower()
        matches = []
        
        # Score each tool based on keyword matches
        for tool_name, metadata in self.tool_metadata.items():
            if not metadata.get('enabled', True):
                continue
            
            score = 0.0
            
            # Check tool name
            if metadata['name'].lower() in task_lower:
                score += 0.5
            
            # Check capabilities
            for capability in metadata.get('capabilities', []):
                if capability.lower() in task_lower:
                    score += 0.3
            
            # Check description
            description = metadata.get('description', '').lower()
            common_words = set(task_lower.split()) & set(description.split())
            score += len(common_words) * 0.1
            
            if score > 0:
                matches.append({
                    'tool': tool_name,
                    'action': metadata.get('actions', ['execute'])[0] if metadata.get('actions') else 'execute',
                    'confidence': min(score, 1.0),
                    'justification': f"Keyword match: {metadata.get('description', '')}",
                    'metadata': metadata
                })
        
        # Sort by confidence and return top results
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        return matches[:max_results]
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """Get detailed information about a specific tool"""
        return self.tool_metadata.get(tool_name)
    
    def list_all_tools(self) -> List[str]:
        """Get list of all available tool names"""
        return [name for name, meta in self.tool_metadata.items() if meta.get('enabled', True)]
    
    def list_capabilities(self) -> List[str]:
        """Get list of all indexed capabilities"""
        return list(self.capability_map.keys())


# Singleton
_tool_registry_instance: Optional[ToolCapabilityRegistry] = None


def get_tool_registry() -> Optional[ToolCapabilityRegistry]:
    """Get or create tool registry singleton"""
    global _tool_registry_instance
    return _tool_registry_instance


def create_tool_registry(tool_orchestrator, plugin_manager, llm_client=None) -> ToolCapabilityRegistry:
    """Factory function to create tool registry"""
    global _tool_registry_instance
    if _tool_registry_instance is None:
        _tool_registry_instance = ToolCapabilityRegistry(tool_orchestrator, plugin_manager, llm_client)
    return _tool_registry_instance

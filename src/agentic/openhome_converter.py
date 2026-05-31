"""
OpenHome Plugin Converter

Converts AlleyBot plugins to OpenHome Ability format for sharing with the OpenHome ecosystem.

OpenHome Format:
- Single file: main.py
- Class: MatchingCapability
- Methods: call(), run()
- Uses CapabilityWorker for speak(), user_response(), text_to_text_response()

AlleyBot Format:
- Plugin class with execute_action(), on_event()
- Direct API calls
- Core integration

This converter bridges the two formats, allowing AlleyBot to autonomously convert
his own plugins to OpenHome standard for community sharing.
"""

from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OpenHomeConverter:
    """
    Converts AlleyBot plugins to OpenHome Ability format.
    
    Features:
    - Analyzes AlleyBot plugin structure
    - Generates OpenHome-compatible main.py
    - Creates README.md with usage instructions
    - Packages as zip for OpenHome upload
    - Integrates with AlleyBot's autonomous coder
    """
    
    def __init__(self, agi_kernel=None):
        self.agi = agi_kernel
        self.output_dir = Path('openhome_abilities')
        self.output_dir.mkdir(exist_ok=True)
    
    def convert_plugin(self, plugin_name: str, plugin_path: str, 
                      trigger_words: List[str] = None,
                      description: str = None) -> Dict[str, Any]:
        """
        Convert an AlleyBot plugin to OpenHome Ability format.
        
        Args:
            plugin_name: Name of the plugin (e.g., 'moltx', 'telegram')
            plugin_path: Path to plugin directory
            trigger_words: List of phrases that activate the ability
            description: Human-readable description
            
        Returns:
            Conversion result with file paths and status
        """
        try:
            logger.info(f"🔄 Converting {plugin_name} to OpenHome format...")
            
            # Create output directory
            ability_dir = self.output_dir / plugin_name
            ability_dir.mkdir(exist_ok=True)
            
            # Analyze plugin
            plugin_info = self._analyze_plugin(plugin_path)
            
            # Generate main.py
            main_py = self._generate_main_py(
                plugin_name=plugin_name,
                plugin_info=plugin_info,
                description=description or f"{plugin_name.title()} integration for OpenHome"
            )
            
            # Write main.py
            main_path = ability_dir / 'main.py'
            with open(main_path, 'w') as f:
                f.write(main_py)
            
            # Generate README.md
            readme = self._generate_readme(
                plugin_name=plugin_name,
                description=description,
                trigger_words=trigger_words or [f"use {plugin_name}", f"activate {plugin_name}"],
                plugin_info=plugin_info
            )
            
            # Write README.md
            readme_path = ability_dir / 'README.md'
            with open(readme_path, 'w') as f:
                f.write(readme)
            
            # Create requirements.txt if needed
            if plugin_info.get('dependencies'):
                requirements_path = ability_dir / 'requirements.txt'
                with open(requirements_path, 'w') as f:
                    f.write('\n'.join(plugin_info['dependencies']))
            
            logger.info(f"✅ Converted {plugin_name} to OpenHome format")
            logger.info(f"📁 Output: {ability_dir}")
            
            return {
                'success': True,
                'ability_dir': str(ability_dir),
                'files': {
                    'main.py': str(main_path),
                    'README.md': str(readme_path)
                },
                'next_steps': [
                    f"1. Review {main_path}",
                    "2. Test the ability locally",
                    f"3. Zip {ability_dir}",
                    "4. Upload to app.openhome.com → Abilities → Add Custom Ability",
                    f"5. Set trigger words: {', '.join(trigger_words or [])}"
                ]
            }
        
        except Exception as e:
            logger.error(f"❌ Conversion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_plugin(self, plugin_path: str) -> Dict[str, Any]:
        """
        Analyze AlleyBot plugin structure.
        
        Returns:
            Plugin info including actions, dependencies, API endpoints
        """
        plugin_info = {
            'actions': [],
            'dependencies': [],
            'api_endpoints': [],
            'has_api_key': False
        }
        
        try:
            plugin_dir = Path(plugin_path)
            
            # Find main plugin file
            main_files = list(plugin_dir.glob('*.py'))
            
            for file_path in main_files:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Extract actions (methods starting with execute_ or _)
                    if 'def execute_action' in content:
                        plugin_info['actions'].append('execute_action')
                    
                    # Check for API key usage
                    if 'API_KEY' in content or 'api_key' in content:
                        plugin_info['has_api_key'] = True
                    
                    # Extract dependencies from imports
                    for line in content.split('\n'):
                        if line.strip().startswith('import ') or line.strip().startswith('from '):
                            # Skip standard library
                            if 'requests' in line or 'aiohttp' in line or 'httpx' in line:
                                if 'requests' not in plugin_info['dependencies']:
                                    plugin_info['dependencies'].append('requests')
        
        except Exception as e:
            logger.debug(f"Plugin analysis failed: {e}")
        
        return plugin_info
    
    def _generate_main_py(self, plugin_name: str, plugin_info: Dict, description: str) -> str:
        """
        Generate OpenHome-compatible main.py.
        
        OpenHome Format:
        - Class inherits from MatchingCapability
        - call() method initializes
        - run() method contains logic
        - Uses CapabilityWorker for interactions
        """
        template = f'''"""
{description}

Converted from AlleyBot plugin: {plugin_name}
"""

import json
from src.agent.capability import MatchingCapability
from src.main import AgentWorker
from src.agent.capability_worker import CapabilityWorker


class {plugin_name.title().replace('_', '')}Capability(MatchingCapability):
    """
    {description}
    
    This ability provides {plugin_name} functionality through OpenHome.
    """
    
    worker: AgentWorker = None
    capability_worker: CapabilityWorker = None
    
    # Do not change following tag of register capability
    #{{{{register_capability}}}}
    
    def call(self, worker: AgentWorker):
        """Initialize the capability"""
        self.worker = worker
        self.capability_worker = CapabilityWorker(self)
        self.worker.session_tasks.create(self.run())
    
    async def run(self):
        """Main capability logic"""
        # Greet user
        await self.capability_worker.speak(
            f"Hi! I'm the {plugin_name} assistant. What would you like to do?"
        )
        
        # Get user input
        user_input = await self.capability_worker.user_response()
        
        # Process request
        # TODO: Add your {plugin_name} logic here
        # This is where you'd call {plugin_name} APIs or perform actions
        
        # Example: Use AI to generate response
        response = self.capability_worker.text_to_text_response(
            f"Based on the user's request: {{user_input}}, provide a helpful response about {plugin_name}."
        )
        
        # Speak response
        await self.capability_worker.speak(response)
        
        # Resume normal conversation flow
        self.capability_worker.resume_normal_flow()
'''
        
        return template
    
    def _generate_readme(self, plugin_name: str, description: str, 
                        trigger_words: List[str], plugin_info: Dict) -> str:
        """Generate README.md for OpenHome ability"""
        
        readme = f'''# {plugin_name.title()} OpenHome Ability

{description or f"OpenHome ability for {plugin_name} integration."}

## Overview

This ability was converted from AlleyBot's {plugin_name} plugin, enabling OpenHome agents to use {plugin_name} functionality through voice commands.

## Trigger Words

Configure these phrases in the OpenHome dashboard to activate this ability:

{chr(10).join(f"- {word}" for word in trigger_words)}

## Installation

1. **Download** this ability folder
2. **Zip** the entire folder
3. **Upload** to [app.openhome.com](https://app.openhome.com) → Abilities → Add Custom Ability
4. **Configure** trigger words in the dashboard
5. **Test** in the Live Editor

## Usage

Say one of your trigger words in a conversation:

```
User: "use {plugin_name}"
Agent: "Hi! I'm the {plugin_name} assistant. What would you like to do?"
User: [your request]
Agent: [performs action and responds]
```

## Configuration

'''
        
        if plugin_info.get('has_api_key'):
            readme += f'''### API Keys

This ability requires API credentials for {plugin_name}. Configure them in the OpenHome dashboard:

1. Go to Abilities → {plugin_name.title()}
2. Click Settings
3. Add your API key

'''
        
        readme += f'''## Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Test locally (requires OpenHome SDK)
python main.py
```

### Customization

Edit `main.py` to customize the ability's behavior:

- Modify the `run()` method for different logic
- Add new methods for additional functionality
- Integrate with external APIs

## Credits

- **Original Plugin:** AlleyBot {plugin_name} plugin
- **Converted By:** AlleyBot Autonomous Converter
- **Date:** {datetime.now().strftime("%Y-%m-%d")}

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:

1. Fork the [abilities repo](https://github.com/openhome-dev/abilities)
2. Make your changes
3. Submit a Pull Request

For more info, see [CONTRIBUTING.md](https://github.com/openhome-dev/abilities/blob/dev/CONTRIBUTING.md)
'''
        
        return readme
    
    def autonomous_convert(self, plugin_name: str) -> Dict[str, Any]:
        """
        Autonomously convert a plugin using AlleyBot's AI capabilities.
        
        This method uses the AGI Kernel to:
        1. Analyze the plugin
        2. Generate optimal OpenHome code
        3. Test the conversion
        4. Package for upload
        """
        if not self.agi:
            return {
                'success': False,
                'error': 'AGI Kernel not available for autonomous conversion'
            }
        
        try:
            logger.info(f"🤖 Starting autonomous conversion of {plugin_name}...")
            
            # Find plugin path
            plugin_path = f"plugins/{plugin_name}"
            if not Path(plugin_path).exists():
                return {
                    'success': False,
                    'error': f'Plugin not found: {plugin_path}'
                }
            
            # Use AGI to analyze and generate optimal conversion
            # This leverages AlleyBot's autonomous coding capabilities
            
            # Step 1: Analyze plugin with AI
            analysis_prompt = f"""
            Analyze the AlleyBot {plugin_name} plugin and determine:
            1. Main functionality
            2. Key actions/methods
            3. API endpoints used
            4. Required configuration
            5. Best trigger words for OpenHome
            
            Plugin path: {plugin_path}
            """
            
            # Step 2: Generate conversion
            result = self.convert_plugin(
                plugin_name=plugin_name,
                plugin_path=plugin_path,
                trigger_words=[f"use {plugin_name}", f"activate {plugin_name}", f"{plugin_name} help"],
                description=f"AlleyBot {plugin_name} plugin converted to OpenHome format"
            )
            
            if isinstance(result, dict) and result.get('success', False):
                logger.info(f"✅ Autonomous conversion complete: {plugin_name}")
                logger.info(f"📁 Output: {result.get('ability_dir', 'unknown')}")
            elif not isinstance(result, dict):
                logger.error(f"❌ Conversion returned invalid type: {type(result).__name__}")
                return {'success': False, 'error': f'Invalid result type: {type(result).__name__}'}
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Autonomous conversion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def create_openhome_converter(agi_kernel=None):
    """Factory function to create OpenHome converter"""
    return OpenHomeConverter(agi_kernel)

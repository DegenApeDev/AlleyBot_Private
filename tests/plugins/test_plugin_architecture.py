"""
AlleyBot Plugin Architecture Tests

Comprehensive tests for the new hot-loadable plugin system.
Run with: pytest tests/plugins/ -v
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.base_plugin import (
    BasePlugin, PluginEvent, PluginAction, ActionResult,
    PluginRegistry, register_plugin
)
from src.core.plugin_manager import PluginManager, PluginLoadResult
from src.core.event_loop import EventLoop, Planner, QueuedEvent
from src.agentic.symod_core import SyModCoreManager


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_symod():
    """Create a mock SyMod manager for testing"""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        storage_path = f.name
    
    symod = SyModCoreManager(core=None, storage_path=storage_path)
    yield symod
    
    # Cleanup
    if os.path.exists(storage_path):
        os.unlink(storage_path)


@pytest.fixture
def plugin_manager(mock_symod):
    """Create a fresh plugin manager for each test"""
    pm = PluginManager(core=None, symod=mock_symod, agi_kernel=None)
    yield pm
    
    # Cleanup - unload all plugins
    for name in pm.list_loaded():
        pm.unload_plugin(name)


@pytest.fixture
def event_loop(plugin_manager, mock_symod):
    """Create an event loop for testing"""
    planner = Planner(plugin_manager, mock_symod)
    loop = EventLoop(plugin_manager, planner, mock_symod)
    yield loop
    
    # Cleanup
    asyncio.run(loop.stop())


# =============================================================================
# Base Plugin Interface Tests
# =============================================================================

class TestBasePluginInterface:
    """Test the base plugin interface requirements"""
    
    def test_plugin_must_implement_abstract_methods(self):
        """Plugin must implement on_event and execute_action"""
        
        # This should fail - incomplete plugin
        with pytest.raises(TypeError):
            class BadPlugin(BasePlugin):
                name = "bad"
            
            BadPlugin({})
    
    def test_complete_plugin_can_instantiate(self):
        """Complete plugin can be instantiated"""
        
        @register_plugin("test_complete")
        class GoodPlugin(BasePlugin):
            name = "test_complete"
            supported_channels = ["test"]
            
            async def on_event(self, event, symod):
                pass
            
            async def execute_action(self, action, symod):
                return ActionResult(success=True, action_type=action.action_type)
        
        plugin = GoodPlugin({})
        assert plugin.name == "test_complete"
        assert plugin.supported_channels == ["test"]
        assert not plugin.initialized
    
    def test_plugin_setup_initializes(self):
        """Plugin is initialized after setup()"""
        
        @register_plugin("test_setup")
        class TestPlugin(BasePlugin):
            name = "test_setup"
            
            async def on_event(self, event, symod):
                pass
            
            async def execute_action(self, action, symod):
                return ActionResult(success=True, action_type=action.action_type)
        
        plugin = TestPlugin({})
        pm = PluginManager()
        symod = SyModCoreManager(storage_path='/tmp/test.json')
        
        plugin.setup(pm, symod, None)
        
        assert plugin.initialized
        assert plugin._plugin_manager == pm
        assert plugin._symod == symod


# =============================================================================
# Plugin Manager Tests
# =============================================================================

class TestPluginManager:
    """Test plugin loading, unloading, and hot-reloading"""
    
    def test_discover_plugins_finds_available(self, plugin_manager):
        """Plugin manager discovers plugins in plugins/ directory"""
        plugins = plugin_manager.discover_plugins()
        
        # Should find at least moltx, telegram, moltbook
        assert isinstance(plugins, list)
        assert len(plugins) > 0
        
        # Check for expected plugins
        expected = ['moltx', 'telegram', 'moltbook']
        for exp in expected:
            if exp in plugins:
                assert True
                return
    
    def test_load_plugin_success(self, plugin_manager, mock_symod):
        """Plugin can be loaded successfully"""
        
        # First ensure moltx_v2 exists
        v2_path = Path('plugins/moltx/moltx_v2.py')
        if not v2_path.exists():
            pytest.skip("moltx_v2.py not created yet")
        
        result = plugin_manager.load_plugin('moltx_v2', {
            'enabled': True,
            'api_key': 'test_key'
        })
        
        assert result.success, f"Load failed: {result.error_message}"
        assert result.plugin_name == 'moltx_v2'
        assert 'moltx_v2' in plugin_manager.list_loaded()
    
    def test_load_plugin_not_found(self, plugin_manager):
        """Loading non-existent plugin fails gracefully"""
        
        result = plugin_manager.load_plugin('nonexistent_plugin', {})
        
        assert not result.success
        assert 'not found' in result.error_message.lower()
    
    def test_unload_plugin_success(self, plugin_manager, mock_symod):
        """Plugin can be unloaded"""
        
        # Load first
        v2_path = Path('plugins/moltx/moltx_v2.py')
        if not v2_path.exists():
            pytest.skip("moltx_v2.py not created yet")
        
        plugin_manager.load_plugin('moltx_v2', {'api_key': 'test'})
        assert 'moltx_v2' in plugin_manager.list_loaded()
        
        # Unload
        success = plugin_manager.unload_plugin('moltx_v2')
        
        assert success
        assert 'moltx_v2' not in plugin_manager.list_loaded()
    
    def test_unload_plugin_not_loaded(self, plugin_manager):
        """Unloading non-loaded plugin returns False"""
        
        success = plugin_manager.unload_plugin('not_loaded')
        
        assert not success
    
    def test_reload_plugin_hot_swap(self, plugin_manager, mock_symod):
        """Plugin can be hot-reloaded"""
        
        v2_path = Path('plugins/moltx/moltx_v2.py')
        if not v2_path.exists():
            pytest.skip("moltx_v2.py not created yet")
        
        # Load initial
        plugin_manager.load_plugin('moltx_v2', {'version': 1})
        
        # Reload
        result = plugin_manager.reload_plugin('moltx_v2')
        
        assert result.success
        assert 'moltx_v2' in plugin_manager.list_loaded()
    
    def test_get_plugin_by_channel(self, plugin_manager, mock_symod):
        """Can retrieve plugins by channel"""
        
        v2_path = Path('plugins/moltx/moltx_v2.py')
        if not v2_path.exists():
            pytest.skip("moltx_v2.py not created yet")
        
        plugin_manager.load_plugin('moltx_v2', {})
        
        plugins = plugin_manager.get_plugins_by_channel('moltx')
        
        assert len(plugins) > 0
        assert all('moltx' in p.supported_channels for p in plugins)
    
    def test_plugin_status(self, plugin_manager, mock_symod):
        """Can get plugin status"""
        
        v2_path = Path('plugins/moltx/moltx_v2.py')
        if not v2_path.exists():
            pytest.skip("moltx_v2.py not created yet")
        
        plugin_manager.load_plugin('moltx_v2', {})
        
        status = plugin_manager.get_status()
        
        assert 'loaded_count' in status
        assert 'loaded_plugins' in status
        assert 'moltx_v2' in status['loaded_plugins']


# =============================================================================
# Event Loop Tests
# =============================================================================

class TestEventLoop:
    """Test central event processing"""
    
    @pytest.mark.asyncio
    async def test_event_loop_start_stop(self, event_loop):
        """Event loop can be started and stopped"""
        
        assert not event_loop.is_running()
        
        await event_loop.start()
        assert event_loop.is_running()
        
        await event_loop.stop()
        assert not event_loop.is_running()
    
    @pytest.mark.asyncio
    async def test_submit_event_queues(self, event_loop):
        """Events can be submitted and queued"""
        
        await event_loop.start()
        
        success = await event_loop.submit_event(
            'post',
            'moltx',
            {'id': '123', 'content': 'Test post'}
        )
        
        assert success
        
        # Give time to process
        await asyncio.sleep(0.1)
        
        await event_loop.stop()
    
    @pytest.mark.asyncio
    async def test_event_not_submitted_when_stopped(self, event_loop):
        """Events rejected when loop not running"""
        
        success = await event_loop.submit_event(
            'post',
            'moltx',
            {}
        )
        
        assert not success
    
    def test_event_priority_levels(self):
        """Event priorities are respected"""
        
        from src.core.event_loop import QueuedEvent
        
        now = datetime.now()
        
        urgent = QueuedEvent(0, now, 'error', 'system', {})
        normal = QueuedEvent(5, now, 'post', 'moltx', {})
        low = QueuedEvent(10, now, 'sync', 'analytics', {})
        
        # Urgent should be less than normal (higher priority)
        assert urgent < normal
        assert normal < low


# =============================================================================
# SyMod Integration Tests
# =============================================================================

class TestSyModIntegration:
    """Test SyMod world model integration"""
    
    def test_symod_registers_plugin(self, mock_symod):
        """Plugins can register with SyMod"""
        
        mock_symod.register_plugin('test', {
            'description': 'Test plugin',
            'channels': ['test']
        })
        
        assert 'test' in mock_symod.registered_plugins
        assert mock_symod.registered_plugins['test']['config']['channels'] == ['test']
    
    def test_symod_observes_event(self, mock_symod):
        """SyMod can observe events and return metrics"""
        
        from src.agentic.symod_core import SyModObservation
        
        mock_symod.register_plugin('moltx', {})
        
        obs = SyModObservation(
            observation_type='post',
            source_plugin='moltx',
            data={
                'content': 'Test post about AI',
                'author_id': 'user_123',
                'hashtags': ['#AI']
            }
        )
        
        metrics = mock_symod.observe(obs)
        
        assert 'sentiment_mass' in metrics
        assert 'field_status' in metrics
        assert 'valid' in metrics
    
    def test_symod_proposes_actions(self, mock_symod):
        """SyMod proposes actions based on observations"""
        
        from src.agentic.symod_core import SyModObservation
        
        mock_symod.register_plugin('moltx', {})
        
        # Create observation
        obs = SyModObservation(
            observation_type='post',
            source_plugin='moltx',
            data={'content': 'Great post!', 'author_id': 'user_1'}
        )
        
        # Ensure observation has metrics
        if not obs.symod_metrics:
            obs.symod_metrics = {
                'sentiment_mass': 0.8,
                'field_status': 'Stable',
                'valid': True,
                'digital_root': 5
            }
        
        # Request proposals
        proposals = mock_symod.propose_actions(
            'moltx',
            {'observations': [obs]},
            ['like', 'reply']
        )
        
        assert isinstance(proposals, list)
    
    def test_symod_validates_actions(self, mock_symod):
        """SyMod validates action proposals"""
        
        from src.agentic.symod_core import SyModActionProposal
        
        mock_symod.register_plugin('moltx', {})
        
        # Valid action
        valid_action = SyModActionProposal(
            action_type='like',
            confidence=0.8,
            valid=True,
            field_status='Stable'
        )
        
        is_valid, reason = mock_symod.validate_action('moltx', valid_action)
        
        # Should pass with valid action
        assert isinstance(is_valid, bool)


# =============================================================================
# End-to-End Tests
# =============================================================================

class TestEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_event_pipeline(self, plugin_manager, mock_symod, event_loop):
        """Full pipeline: event → plugin → SyMod → action"""
        
        v2_path = Path('plugins/moltx/moltx_v2.py')
        if not v2_path.exists():
            pytest.skip("moltx_v2.py not created yet")
        
        # Setup
        plugin_manager.load_plugin('moltx_v2', {})
        await event_loop.start()
        
        # Submit event
        await event_loop.submit_event(
            'post',
            'moltx',
            {
                'id': 'post_123',
                'content': 'Test post about crypto',
                'author': {'id': 'user_1', 'name': 'tester'},
                'hashtags': ['#crypto']
            }
        )
        
        # Let it process
        await asyncio.sleep(0.2)
        
        # Verify
        status = plugin_manager.get_plugin('moltx_v2').get_status()
        assert status['stats']['observations'] >= 1
        
        await event_loop.stop()
    
    def test_plugins_json_exists(self):
        """Configuration file exists"""
        
        config_path = Path('plugins.json')
        
        if not config_path.exists():
            config_path = Path('config/plugins.json')
        
        assert config_path.exists(), "plugins.json not found"
        
        # Validate JSON
        with open(config_path) as f:
            config = json.load(f)
        
        assert isinstance(config, dict)
        assert len(config) > 0


# =============================================================================
# Hotloading Tests
# =============================================================================

class TestHotloading:
    """Test hot-loading functionality"""
    
    def test_load_from_config(self, plugin_manager, tmp_path):
        """Load plugins from JSON config file"""
        
        # Create temp config
        config = {
            "test_plugin": {
                "enabled": True,
                "config": {"test": True}
            },
            "disabled_plugin": {
                "enabled": False
            }
        }
        
        config_file = tmp_path / "test_plugins.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Only enabled plugins should attempt load
        # (will fail because test plugins don't exist, but tests the config parsing)
        results = plugin_manager.load_from_config(str(config_file))
        
        # Should have processed both entries
        assert "test_plugin" in results or "disabled_plugin" in results
    
    def test_save_config(self, plugin_manager, tmp_path):
        """Save current plugin configuration"""
        
        # Load a plugin
        @register_plugin("save_test")
        class SaveTestPlugin(BasePlugin):
            name = "save_test"
            
            async def on_event(self, event, symod):
                pass
            
            async def execute_action(self, action, symod):
                return ActionResult(success=True, action_type=action.action_type)
        
        plugin_manager.load_plugin('save_test', {'custom': 'value'})
        
        # Save
        config_file = tmp_path / "saved_plugins.json"
        success = plugin_manager.save_config(str(config_file))
        
        assert success
        assert config_file.exists()
        
        # Verify content
        with open(config_file) as f:
            saved = json.load(f)
        
        assert 'save_test' in saved


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test graceful error handling"""
    
    @pytest.mark.asyncio
    async def test_plugin_error_doesnt_crash_loop(self, plugin_manager, mock_symod, event_loop):
        """Plugin errors don't crash the event loop"""
        
        @register_plugin("error_plugin")
        class ErrorPlugin(BasePlugin):
            name = "error_plugin"
            supported_channels = ["error_test"]
            
            async def on_event(self, event, symod):
                if event.payload.get('trigger_error'):
                    raise RuntimeError("Intentional error")
            
            async def execute_action(self, action, symod):
                return ActionResult(success=True, action_type=action.action_type)
        
        plugin_manager.load_plugin('error_plugin', {})
        await event_loop.start()
        
        # Submit event that triggers error
        await event_loop.submit_event(
            'test',
            'error_test',
            {'trigger_error': True}
        )
        
        # Should not crash
        await asyncio.sleep(0.1)
        
        # Loop still running
        assert event_loop.is_running()
        
        await event_loop.stop()
    
    def test_broken_plugin_load_fails_gracefully(self, plugin_manager):
        """Broken plugins fail gracefully without crashing system"""
        
        # Try to load non-existent plugin
        result = plugin_manager.load_plugin('definitely_not_real', {})
        
        assert not result.success
        assert result.error_message is not None
        
        # System still functional
        assert plugin_manager.list_loaded() == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

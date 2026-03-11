#!/usr/bin/env python3
"""
AlleyBot Core - Minimal orchestrator with plugin system
The heart of AlleyBot - coordinates plugins and manages the agent
"""
import json
import schedule
import time
import signal
import atexit
from datetime import datetime
from pathlib import Path
from plugin_manager import PluginManager

# Load environment variables from .env file FIRST
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, environment variables must be set manually")

# Import console logging system
from console_logger import init_console_logging, stop_console_logging

# Try to import enhanced memory; fall back to None if deps missing
try:
    from src.agentic.enhanced_memory import EnhancedMemorySystem
    ENHANCED_MEMORY_AVAILABLE = True
except ImportError:
    ENHANCED_MEMORY_AVAILABLE = False

# Import SQLite memory integration
try:
    from src.agentic.memory_integration import SQLiteMemoryMixin
    SQLITE_MEMORY_AVAILABLE = True
except ImportError:
    SQLITE_MEMORY_AVAILABLE = False

# Import Tier 2 Synergy Gate (optional - falls back gracefully)
try:
    from lib.synergy_gate import get_synergy_gate, validate_action
    from src.agentic.recursive_strategy import RecursiveStrategyEngine
    TIER2_AVAILABLE = True
    print("🔐 Tier 2 Cryptographic Trust: ENABLED")
except ImportError as e:
    TIER2_AVAILABLE = False
    print(f"⚠️ Tier 2 framework unavailable: {e}")

# Import AGI Kernel (Quick Win #2)
try:
    from src.agentic.agi_kernel import AGIKernel
    AGI_KERNEL_AVAILABLE = True
except ImportError as e:
    AGI_KERNEL_AVAILABLE = False
    print(f"⚠️ AGI Kernel unavailable: {e}")

# Import Service Integration Layer (Phase 8)
try:
    from src.agentic.service_integration import initialize_services, check_system_health
    SERVICE_INTEGRATION_AVAILABLE = True
except ImportError as e:
    SERVICE_INTEGRATION_AVAILABLE = False
    print(f"⚠️ Service Integration Layer unavailable: {e}")

class AlleyBotCore(SQLiteMemoryMixin if SQLITE_MEMORY_AVAILABLE else object):
    """Minimal core that orchestrates plugins with SQLite memory"""
    
    def __init__(self, config_dir='config'):
        # Initialize console logging FIRST (before any prints)
        self.console_logger = init_console_logging(max_days=7)
        
        # Register cleanup handlers for graceful shutdown
        self._cleanup_registered = False
        self._register_cleanup_handlers()
        
        # Main tagline - show immediately at startup
        print("🦞 AlleyBot - Extensible AI Agent & Automation Platform")
        print("=" * 60)
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Core components
        self.api = None  # Removed MoltbookAPI support
        self.plugin_manager = PluginManager()

        # Initialize SQLite memory system (replaces JSON files)
        if SQLITE_MEMORY_AVAILABLE:
            self._init_sqlite_memory('data/memory.db')
        else:
            self.memory_db = None
            print("⚠️  SQLite memory unavailable, using JSON fallback")

        # Legacy: enhanced memory system (optional vector DB)
        self.enhanced_memory = None
        if ENHANCED_MEMORY_AVAILABLE:
            try:
                self.enhanced_memory = EnhancedMemorySystem(
                    storage_dir='data/memory'
                )
                print("✅ Enhanced memory system initialized (vector DB + goals + encryption)")
            except Exception as e:
                print(f"⚠️  Enhanced memory unavailable, using JSON fallback: {e}")
        else:
            print("ℹ️  Enhanced memory deps not installed, using JSON fallback")
        
        # AGI Kernel - Autonomous decision-making and learning (Quick Win #2)
        self.agi_kernel = None
        if AGI_KERNEL_AVAILABLE:
            try:
                self.agi_kernel = AGIKernel(core=self)
                print("✅ AGI Kernel initialized - autonomous thinking enabled")
            except Exception as e:
                print(f"⚠️ AGI Kernel initialization failed: {e}")
        
        # Service Integration Layer - Unified foundation services (Phase 8)
        self.services = None
        if SERVICE_INTEGRATION_AVAILABLE:
            try:
                self.services = initialize_services(
                    core=self,
                    plugin_manager=self.plugin_manager,
                    telegram_plugin=None,  # Will be set after Telegram plugin loads
                    llm_router=None,  # Will be set after LLM router available
                )
                print("✅ Service Integration Layer initialized")
                
                # Health check
                health = check_system_health()
                if health['healthy']:
                    print("   🎯 All foundation services operational")
                else:
                    print(f"   ⚠️ Some services unavailable: {health['services']}")
                    
            except Exception as e:
                print(f"⚠️ Service Integration initialization failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize plugins
        self.plugin_manager.load_plugins(
            'plugin_config.json',
            self.api,
            self
        )
        
        # Initialize AGI Kernel decision systems (requires plugin_manager)
        if self.agi_kernel and hasattr(self.agi_kernel, 'initialize_decision_systems'):
            try:
                self.agi_kernel.initialize_decision_systems(self.plugin_manager)
                print("✅ AGI Kernel decision systems initialized")
            except Exception as e:
                print(f"⚠️ AGI Kernel decision systems initialization failed: {e}")
        
        # Link Telegram plugin to service integration layer if available
        if self.services and 'telegram' in self.plugin_manager.plugins:
            try:
                telegram_plugin = self.plugin_manager.plugins['telegram']
                self.services.telegram = telegram_plugin
                
                # Update notification service with Telegram
                if self.services.notifications:
                    self.services.notifications.telegram = telegram_plugin
                    print("   🔗 Telegram linked to notification service")
                    
                print("   🔗 Telegram plugin linked to service layer")
            except Exception as e:
                print(f"   ⚠️ Failed to link Telegram: {e}")
        
        # Link LLM router if available
        try:
            from src.core.llm_router import get_llm_router
            llm_router = get_llm_router()
            if self.services:
                self.services.conversation.llm_router = llm_router
                print("   🔗 LLM Router linked to conversation service")
        except Exception as e:
            print(f"   ⚠️ LLM Router not linked: {e}")

        # Add core commands
        self._add_core_commands()

        print(f"\n{'='*60}")
        print(f"🤖 ALLEYBOT CORE - Extensible AI Agent")
        print(f"{'='*60}")
        print(f"📦 Plugins loaded: {len(self.plugin_manager.plugins)}")
        print(f"🔧 Active tasks: {len(self.plugin_manager.tasks)}")
        print(f"💬 Available commands: {len(self.plugin_manager.commands)}")
        print(f"📝 Console logging: ACTIVE (7-day retention)")
        print(f"{'='*60}\n")
    
    def _register_cleanup_handlers(self):
        """Register signal handlers and atexit for proper cleanup"""
        if self._cleanup_registered:
            return
        
        def signal_handler(signum, frame):
            print(f"\n⚠️  Received signal {signum}, initiating cleanup...")
            self.cleanup()
            import sys
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Register atexit handler as fallback
        atexit.register(self._atexit_cleanup)
        
        self._cleanup_registered = True
    
    def _atexit_cleanup(self):
        """Cleanup called by atexit - avoid duplicate cleanup"""
        if hasattr(self, '_cleaned_up'):
            return
        self.cleanup()
    
    def _add_core_commands(self):
        """Add core system commands"""
        self.plugin_manager.commands.update({
            'log_stats': self._cmd_log_stats,
            'console_stats': self._cmd_console_stats,
        })
    
    def _cmd_log_stats(self):
        """Show general logging statistics"""
        stats = self.get_console_log_stats()
        if 'error' in stats:
            return f"❌ Log stats error: {stats['error']}"
        
        output = [f"📊 Console Logging Statistics:"]
        output.append(f"  Files: {stats['total_files']}")
        output.append(f"  Total Size: {stats['total_size_mb']:.1f} MB")
        if stats['oldest_date']:
            output.append(f"  Date Range: {stats['oldest_date'].strftime('%Y-%m-%d')} to {stats['newest_date'].strftime('%Y-%m-%d')}")
        
        output.append(f"\n📁 Recent Log Files:")
        for log_file in stats['files'][:5]:  # Show last 5 files
            output.append(f"  • {log_file['name']} ({log_file['size_mb']} MB)")
        
        return "\n".join(output)
    
    def _cmd_console_stats(self):
        """Alias for log_stats"""
        return self._cmd_log_stats()
    
    def _load_config(self):
        """Load core configuration"""
        config_file = self.config_dir / 'core.json'
        default_config = {
            'agent_name': 'AlleyBot',
            'debug': False,
            'log_level': 'INFO',
            'schedule_interval': 60  # seconds
        }
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                default_config.update(config)
        
        # Save default config if it didn't exist
        if not config_file.exists():
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        return default_config
    
    def get_memory(self, memory_type='state'):
        """Get memory storage for plugins (JSON key-value store)"""
        memory_dir = Path('memory')
        memory_dir.mkdir(exist_ok=True)

        memory_file = memory_dir / f'{memory_type}.json'
        if memory_file.exists():
            with open(memory_file, 'r') as f:
                return json.load(f)
        return {}

    def save_memory(self, memory_type, data):
        """Save memory storage for plugins (JSON key-value store)"""
        memory_dir = Path('memory')
        memory_dir.mkdir(exist_ok=True)

        memory_file = memory_dir / f'{memory_type}.json'
        with open(memory_file, 'w') as f:
            json.dump(data, f, indent=2)

    # --- Enhanced memory helpers (semantic search, goals, encryption) ---

    def add_semantic_memory(self, content, memory_type='interaction', metadata=None):
        """Add a memory with optional vector embedding for semantic search"""
        if self.enhanced_memory:
            return self.enhanced_memory.add_memory(content, memory_type, metadata)
        # Fallback: store in regular JSON
        self.save_memory(f'semantic_{memory_type}', {
            'content': content,
            'type': memory_type,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        })
        return None

    def search_memories(self, query, k=5, memory_type=None):
        """Semantic search across memories (requires enhanced memory deps)"""
        if self.enhanced_memory:
            return self.enhanced_memory.search_memories(query, k, memory_type)
        return []

    def add_goal(self, description, goal_type='short_term', parent_goal_id=None, priority=1):
        """Add a hierarchical goal (requires enhanced memory deps)"""
        if self.enhanced_memory:
            return self.enhanced_memory.add_goal(description, goal_type, parent_goal_id, priority)
        return None

    def get_active_goals(self, goal_type=None):
        """Get active goals (requires enhanced memory deps)"""
        if self.enhanced_memory:
            return self.enhanced_memory.get_active_goals(goal_type)
        return []

    def store_sensitive(self, key, value):
        """Store encrypted sensitive data (requires enhanced memory deps)"""
        if self.enhanced_memory:
            self.enhanced_memory.store_sensitive(key, value)
        else:
            print("⚠️  Enhanced memory not available, sensitive data not stored")

    def get_sensitive(self, key):
        """Retrieve encrypted sensitive data (requires enhanced memory deps)"""
        if self.enhanced_memory:
            return self.enhanced_memory.get_sensitive(key)
        return None

    def get_memory_stats(self):
        """Get unified memory system statistics"""
        stats = {
            'json_store': {},
            'enhanced': None
        }
        # Count JSON memory files
        memory_dir = Path('memory')
        if memory_dir.exists():
            json_files = list(memory_dir.glob('*.json'))
            stats['json_store']['file_count'] = len(json_files)
            stats['json_store']['files'] = [f.stem for f in json_files]
        if self.enhanced_memory:
            stats['enhanced'] = self.enhanced_memory.get_memory_stats()
        return stats
    
    def get_console_log_stats(self):
        """Get console logging statistics"""
        if self.console_logger:
            return self.console_logger.get_log_stats()
        return {'error': 'Console logger not initialized'}
    
    def setup_schedule(self):
        """Setup scheduled tasks from plugins"""
        for task_name, task_config in self.plugin_manager.tasks.items():
            if 'schedule' in task_config and 'function' in task_config:
                # Parse cron-like schedule
                schedule_str = task_config['schedule']
                func = task_config['function']
                
                # Enhanced schedule parsing
                if '*/5' in schedule_str:  # Every 5 minutes
                    schedule.every(5).minutes.do(func)
                elif '*/15' in schedule_str:  # Every 15 minutes
                    schedule.every(15).minutes.do(func)
                elif '*/30' in schedule_str:  # Every 30 minutes
                    schedule.every(30).minutes.do(func)
                elif '*/2' in schedule_str:  # Every 2 hours
                    schedule.every(2).hours.do(func)
                elif '*/4' in schedule_str:  # Every 4 hours
                    schedule.every(4).hours.do(func)
                elif '*/6' in schedule_str:  # Every 6 hours
                    schedule.every(6).hours.do(func)
                elif '0 */4' in schedule_str:  # Every 4 hours at :00
                    schedule.every(4).hours.do(func)
                elif '0 */6' in schedule_str:  # Every 6 hours at :00
                    schedule.every(6).hours.do(func)
                elif 'daily' in schedule_str:  # Daily
                    schedule.every().day.do(func)
                elif 'hourly' in schedule_str:  # Every hour
                    schedule.every().hour.do(func)
                
                print(f"⏰ Scheduled task: {task_name} ({schedule_str})")
    
    def run_command(self, command, *args):
        """Execute command from plugins"""
        if command in self.plugin_manager.commands:
            try:
                func = self.plugin_manager.commands[command]
                return func(*args)
            except Exception as e:
                print(f"❌ Command '{command}' failed: {e}")
                return None
        else:
            print(f"❌ Unknown command: {command}")
            print(f"💡 Available commands: {', '.join(self.plugin_manager.commands.keys())}")
            return None
    
    def list_plugins(self):
        """List all loaded plugins"""
        print(f"\n📦 Loaded Plugins ({len(self.plugin_manager.plugins)}):")
        for name, plugin in self.plugin_manager.plugins.items():
            status = "✅ Active" if hasattr(plugin, 'initialized') else "⚠️ Loading"
            print(f"  {status} {name}")
    
    def list_commands(self):
        """List all available commands"""
        print(f"\n💬 Available Commands ({len(self.plugin_manager.commands)}):")
        for command in sorted(self.plugin_manager.commands.keys()):
            print(f"  • {command}")
    
    def run_autonomous(self, mode='production'):
        """
        Run autonomous mode
        Modes:
        - 'production': Production-ready event-driven architecture (recommended)
        - 'standard': Standard time-based scheduler
        """
        if mode == 'production':
            self.run_production_autonomous()
        else:
            self.run_standard_autonomous()
    
    def run_production_autonomous(self):
        """Run production-ready event-driven autonomous mode"""
        try:
            from src.main import run_production_mode
            
            print("🚀 Starting Production Event-Driven Mode...")
            
            # Auto-start dashboard in background
            self._start_dashboard_background()
            
            # run_production_mode calls asyncio.run() internally
            run_production_mode(self)
            
        except ImportError as e:
            print(f"⚠️  Production mode not available: {e}")
            print("📊 Falling back to standard autonomous mode...")
            self.run_standard_autonomous()
        except KeyboardInterrupt:
            print("\n🛑 Stopping production mode...")
    
    def _start_dashboard_background(self):
        """Start dashboard and A2A server in background threads"""
        try:
            import threading
            import time
            
            def start_services_delayed():
                # Wait for Telegram bot to be ready
                time.sleep(3)
                
                # Start A2A server
                if 'a2a' in self.plugin_manager.plugins:
                    a2a = self.plugin_manager.plugins['a2a']
                    if hasattr(a2a, 'start_a2a_server'):
                        print("🌐 Auto-starting A2A server in background...")
                        a2a.start_a2a_server()
                else:
                    print("⚠️  A2A plugin not found, skipping A2A server")
                
                # Check if analytics plugin exists
                if 'analytics' in self.plugin_manager.plugins:
                    analytics = self.plugin_manager.plugins['analytics']
                    print("📊 Auto-starting dashboard in background...")
                    
                    # Start dashboard in separate thread
                    dashboard_thread = threading.Thread(
                        target=analytics.start_dashboard,
                        daemon=True
                    )
                    dashboard_thread.start()
                else:
                    print("⚠️  Analytics plugin not found, skipping dashboard")
            
            # Start services in background
            thread = threading.Thread(target=start_services_delayed, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"⚠️  Failed to auto-start services: {e}")
    
    def run_standard_autonomous(self):
        """Run standard autonomous mode with scheduled tasks (fallback)"""
        print("🚀 Starting Standard Autonomous Mode...")
        
        # Setup schedule
        self.setup_schedule()
        
        # Run initial tasks
        print("🔄 Running initial tasks...")
        
        # Run some immediate tasks to show activity
        self.run_immediate_tasks()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n🛑 Stopping autonomous mode...")
    
    def run_immediate_tasks(self):
        """Run some immediate tasks to show activity"""
        print("🎯 Running immediate autonomous tasks...")
        
        # Check status of all platforms
        print("📊 Checking platform status...")
        
        # Run a few quick tasks
        tasks_to_run = [
            ('moltx_status', 'Moltx'),
            ('moltchan_status', 'MoltChan'),
            ('moltroad_status', 'MoltRoad'),
            ('stats', 'Overall Stats')
        ]
        
        for task, platform in tasks_to_run:
            try:
                print(f"🔍 Checking {platform}...")
                result = self.run_command(task)
                if result and not result.startswith("❌"):
                    print(f"✅ {platform} status checked")
                else:
                    print(f"⚠️  {platform} check failed")
            except Exception as e:
                print(f"❌ {platform} check error: {e}")
        
        # Run some engaging activities immediately
        print("🤖 Starting engaging activities...")
        
        # Browse Moltx feed and engage
        try:
            print("📱 Browsing Moltx feed...")
            feed_result = self.run_command('moltx_feed')
            if feed_result and not feed_result.startswith("❌"):
                print("✅ Moltx feed browsed")
                
                # Engage with a few posts
                print("💬 Engaging with feed posts...")
                engage_result = self.run_command('moltx_engage', '2')
                if engage_result and not engage_result.startswith("❌"):
                    print("✅ Engaged with feed posts")
            else:
                print("⚠️  Feed browsing failed")
        except Exception as e:
            print(f"❌ Feed engagement error: {e}")
        
        # Note: Intelligent posting will happen via scheduled tasks, not on startup
        print("📅 Intelligent posting scheduled (every 2 hours)")
        
        # Check trending topics
        try:
            print("🔥 Analyzing trending topics...")
            trending_result = self.run_command('moltx_trending')
            if trending_result and not trending_result.startswith("❌"):
                print("✅ Trending analysis complete")
            else:
                print("⚠️  Trending analysis failed")
        except Exception as e:
            print(f"❌ Trending analysis error: {e}")
        
        print("🎉 Initial autonomous activities complete!")
    
    def run_interactive(self):
        """Run interactive mode"""
        print("\n🎮 AlleyBot Interactive Mode")
        print("Type 'help' for commands or 'exit' to quit\n")
        
        while True:
            try:
                command = input("AlleyBot> ").strip().lower()
                
                if command == 'exit' or command == 'quit':
                    break
                elif command == 'help':
                    self.list_commands()
                    print("\n📋 Special commands:")
                    print("  plugins - List loaded plugins")
                    print("  status - Show agent status")
                    print("  exit - Exit interactive mode")
                elif command == 'plugins':
                    self.list_plugins()
                elif command == 'status':
                    print(f"\n📊 AlleyBot Status:")
                    print(f"  Agent: {self.config['agent_name']}")
                    print(f"  Plugins: {len(self.plugin_manager.plugins)}")
                    print(f"  Tasks: {len(self.plugin_manager.tasks)}")
                    print(f"  Commands: {len(self.plugin_manager.commands)}")
                else:
                    # Parse command with arguments
                    if not command:
                        continue  # Skip empty commands
                    parts = command.split()
                    cmd = parts[0]
                    args = parts[1:] if len(parts) > 1 else []
                    
                    if cmd in self.plugin_manager.commands:
                        result = self.run_command(cmd, *args)
                        if result:
                            print(f"✅ Result: {result}")
                    else:
                        print(f"❌ Unknown command: {cmd}")
                        print("💡 Type 'help' for available commands")
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        print("\n👋 Goodbye!")
    
    def cleanup(self):
        """Cleanup resources"""
        # Prevent duplicate cleanup
        if hasattr(self, '_cleaned_up'):
            return
        self._cleaned_up = True
        
        print("🧹 Cleaning up...")
        
        # Cleanup plugins first
        try:
            for plugin_name, plugin in list(self.plugin_manager.plugins.items()):
                try:
                    if hasattr(plugin, 'cleanup'):
                        plugin.cleanup()
                except Exception as e:
                    print(f"⚠️  Error cleaning up {plugin_name}: {e}")
        except Exception as e:
            print(f"⚠️  Error during plugin cleanup: {e}")
        
        # Close SQLite memory connection
        try:
            if hasattr(self, 'memory_db') and self.memory_db:
                self.memory_db.close()
        except Exception as e:
            print(f"⚠️  Error closing memory DB: {e}")
        
        # Stop console logging last
        try:
            stop_console_logging()
        except Exception as e:
            print(f"⚠️  Error stopping console logging: {e}")
        
        print("✅ Cleanup complete")


if __name__ == "__main__":
    import sys
    
    core = AlleyBotCore()
    
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == 'autonomous':
                core.run_autonomous()
            elif sys.argv[1] == 'interactive':
                core.run_interactive()
            else:
                # Run specific command
                command = sys.argv[1]
                args = sys.argv[2:] if len(sys.argv) > 2 else []
                result = core.run_command(command, *args)
                if result:
                    print(result)
        else:
            print("🤖 AlleyBot Core")
            print("Usage:")
            print("  python alleybot_core.py autonomous   - Run autonomous mode (recommended)")
            print("  python alleybot_core.py interactive  - Run interactive mode")
            print("  python alleybot_core.py <command>    - Run specific command")
            print("\n💡 Then send /brain_start in Telegram to activate the autonomous brain")
    finally:
        core.cleanup()

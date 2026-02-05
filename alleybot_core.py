#!/usr/bin/env python3
"""
AlleyBot Core - Minimal orchestrator with plugin system
The heart of AlleyBot - coordinates plugins and manages the agent
"""
import json
import schedule
import time
from datetime import datetime
from pathlib import Path
from moltbook_api import MoltbookAPI
from plugin_manager import PluginManager

class AlleyBotCore:
    """Minimal core that orchestrates plugins"""
    
    def __init__(self, config_dir='config'):
        # Main tagline - show immediately at startup
        print("🦞 AlleyBot - Extensible AI Agent & Automation Platform")
        print("=" * 60)
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Core components
        self.api = MoltbookAPI()
        self.plugin_manager = PluginManager()
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize plugins
        self.plugin_manager.load_plugins(
            'plugin_config.json',
            self.api,
            self
        )

        print(f"\n{'='*60}")
        print(f"🤖 ALLEYBOT CORE - Extensible AI Agent")
        print(f"{'='*60}")
        print(f"📦 Plugins loaded: {len(self.plugin_manager.plugins)}")
        print(f"🔧 Active tasks: {len(self.plugin_manager.tasks)}")
        print(f"💬 Available commands: {len(self.plugin_manager.commands)}")
        print(f"{'='*60}\n")
    
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
        """Get memory storage for plugins"""
        memory_dir = Path('memory')
        memory_dir.mkdir(exist_ok=True)
        
        memory_file = memory_dir / f'{memory_type}.json'
        if memory_file.exists():
            with open(memory_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_memory(self, memory_type, data):
        """Save memory storage for plugins"""
        memory_dir = Path('memory')
        memory_dir.mkdir(exist_ok=True)
        
        memory_file = memory_dir / f'{memory_type}.json'
        with open(memory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
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
        - 'advanced': Advanced event loop with polling
        - 'standard': Standard time-based scheduler
        """
        if mode == 'production':
            self.run_production_autonomous()
        elif mode == 'advanced':
            self.run_advanced_autonomous()
        else:
            self.run_standard_autonomous()
    
    def run_enhanced_autonomous(self):
        """Run enhanced autonomous mode with intelligent decision-making"""
        try:
            from enhanced_autonomous import EnhancedAutonomousSystem
            
            print("🧠 Starting Enhanced Autonomous Mode...")
            print("🤖 Intelligent decision-making enabled")
            print("📈 Adaptive scheduling active")
            print("🎯 Performance optimization running")
            
            # Initialize enhanced system
            enhanced_system = EnhancedAutonomousSystem(self)
            
            # Run enhanced autonomous cycle
            enhanced_system.run_enhanced_autonomous_cycle()
            
        except ImportError as e:
            print(f"⚠️  Enhanced system not available: {e}")
            self.run_standard_autonomous()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            self.cleanup()
    
    def run_advanced_autonomous(self):
        """Run advanced autonomous mode with event-driven loop"""
        try:
            from advanced_agent_loop import AdvancedAgentLoop
            
            print("🚀 Starting Advanced Event-Driven Autonomous Mode...")
            
            # Initialize advanced loop
            self.agent_loop = AdvancedAgentLoop(self)
            
            # Run the advanced loop
            import asyncio
            asyncio.run(self.agent_loop.initialize())
            asyncio.run(self.agent_loop.agent_loop())
            
        except ImportError:
            print("⚠️  Advanced loop not available, falling back to standard mode")
            self.run_standard_autonomous()
        except Exception as e:
            print(f"❌ Advanced loop error: {e}")
            print("⚠️  Falling back to standard mode")
            self.run_standard_autonomous()
    
    def run_production_autonomous(self):
        """Run production-ready event-driven autonomous mode"""
        try:
            from src.main import run_production_mode
            
            print("🚀 Starting Production Event-Driven Mode...")
            
            # Auto-start dashboard in background
            self._start_dashboard_background()
            
            # Run the production async event loop
            import asyncio
            asyncio.run(run_production_mode(self))
            
        except ImportError as e:
            print(f"⚠️  Production mode not available: {e}")
            print("📊 Falling back to advanced autonomous mode...")
            self.run_advanced_autonomous()
        except KeyboardInterrupt:
            print("\n🛑 Stopping production mode...")
    
    def _start_dashboard_background(self):
        """Start dashboard in background thread"""
        try:
            import threading
            import time
            
            def start_dashboard_delayed():
                # Wait for Telegram bot to be ready
                time.sleep(3)
                
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
            
            # Start dashboard in background
            thread = threading.Thread(target=start_dashboard_delayed, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"⚠️  Failed to auto-start dashboard: {e}")
    
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
        print("🧹 Cleaning up...")
        for plugin in self.plugin_manager.plugins.values():
            if hasattr(plugin, 'cleanup'):
                plugin.cleanup()


if __name__ == "__main__":
    import sys
    
    core = AlleyBotCore()
    
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == 'autonomous':
                # Check for enhanced mode flag
                enhanced = len(sys.argv) > 2 and sys.argv[2] == '--enhanced'
                core.run_autonomous(enhanced=enhanced)
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
            print("  python alleybot_core.py autonomous           - Run standard autonomous mode")
            print("  python alleybot_core.py autonomous --enhanced - Run enhanced autonomous mode")
            print("  python alleybot_core.py interactive         - Run interactive mode")
            print("  python alleybot_core.py <command>           - Run specific command")
            print("\n🧠 Enhanced Mode Features:")
            print("  • Intelligent decision-making")
            print("  • Adaptive scheduling")
            print("  • Performance optimization")
            print("  • Self-improvement capabilities")
            print("\n💡 Type 'python alleybot_core.py interactive' and then 'help' for commands")
    finally:
        core.cleanup()

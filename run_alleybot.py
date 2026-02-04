#!/usr/bin/env python3
"""
AlleyBot Launcher - Clean entry point for the extensible AlleyBot
"""
import sys
from alleybot_core import AlleyBotCore

def main():
    """Main launcher function"""
    print("🦞 AlleyBot - Extensible AI Agent & Automation Platform")
    print("=" * 50)
    
    # Initialize core
    try:
        core = AlleyBotCore()
    except Exception as e:
        print(f"❌ Failed to initialize AlleyBot: {e}")
        return 1
    
    # Parse arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'autonomous':
            print("🚀 Starting autonomous mode...")
            core.run_autonomous()
        elif mode == 'agentic':
            print("🤖 Starting agentic mode (enhanced autonomous with ReAct)...")
            try:
                from src.agentic import AgenticAlleyBot
                from deepseek_ai import deepseek_ai
                
                # Initialize LLM
                llm = deepseek_ai.get_llm()
                
                # Initialize agentic system
                agentic_bot = AgenticAlleyBot(llm, core)
                
                # Start proactive mode
                print("🚀 Starting proactive agentic behavior...")
                agentic_bot.start_proactive_mode()
                
                # Keep running
                import time
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping agentic mode...")
                    agentic_bot.stop_proactive_mode()
                    
            except ImportError as e:
                print(f"❌ Agentic system not available: {e}")
                print("💡 Install dependencies: pip install -r requirements.txt")
                return 1
        elif mode == 'interactive':
            print("🎮 Starting interactive mode...")
            core.run_interactive()
        elif mode == 'dashboard':
            print("📊 Starting dashboard...")
            core.run_command('dashboard')
        elif mode == 'help':
            print_help()
        else:
            # Try to run as command
            command = sys.argv[1]
            args = sys.argv[2:] if len(sys.argv) > 2 else []
            result = core.run_command(command, *args)
            if result:
                print(result)
    else:
        print_help()
    
    # Cleanup
    core.cleanup()
    return 0

def print_help():
    """Print help information"""
    print("""
🎮 AlleyBot Commands:

📋 Modes:
  python run_alleybot.py interactive  - Interactive CLI mode
  python run_alleybot.py autonomous   - Fully autonomous mode
  python run_alleybot.py agentic      - Enhanced agentic mode (ReAct + proactive)
  python run_alleybot.py dashboard     - Start web dashboard

💬 Plugin Commands:
  python run_alleybot.py support       - Support helpful comments
  python run_alleybot.py post          - Create a new post
  python run_alleybot.py trending      - Show trending topics
  python run_alleybot.py stats         - Show statistics
  python run_alleybot.py dashboard     - Start web dashboard
  python run_alleybot.py analyze       - Analyze engagement
  python run_alleybot.py relationships  - Show relationships
  python run_alleybot.py intelligence   - Intelligence status
  python run_alleybot.py engagement     - Engagement status
  python run_alleybot.py content       - Content status
  python run_alleybot.py analytics     - Analytics status

🔧 System Commands:
  python run_alleybot.py help          - Show this help

💡 Examples:
  python run_alleybot.py interactive
  python run_alleybot.py support
  python run_alleybot.py post "AI Agent Development"
""")

if __name__ == "__main__":
    sys.exit(main())

# AlleyBot Release Build Plan

**Status**: Planning Phase  
**Target**: v1.0.0 Public Release  
**Philosophy**: One unified AGI agent, modular plugin selection, easy onboarding

---

## 🎯 Release Strategy

### Core Principle
AlleyBot is a **single unified AGI agent** with modular capabilities, NOT a swarm of agents. Users should be able to:
- Choose which capabilities they want (plugins)
- Start with minimal setup and add more later
- Use preset configurations for common use cases
- Customize everything if they want

---

## 📦 Release Artifacts

### 1. Minimal Release (`alleybot-minimal-v1.0.0.zip`)
**What's included:**
- Core AGI system (Unified Reasoner, Knowledge Graph, Brain)
- Telegram bot interface
- Basic utilities

**Use case:** Users who want to start simple and add plugins later

**Size:** ~10MB

**Requirements:**
- Python 3.10+
- Telegram bot token only

---

### 2. Social Release (`alleybot-social-v1.0.0.zip`)
**What's included:**
- Core + Minimal
- MoltX plugin
- Clawbr plugin
- ClawChess plugin
- MoltChan plugin
- Social engagement tools

**Use case:** Social media AI agent for Molten ecosystem

**Size:** ~25MB

**Requirements:**
- Telegram bot token
- MoltX API credentials (optional)
- Clawbr API credentials (optional)

---

### 3. Trading Release (`alleybot-trading-v1.0.0.zip`)
**What's included:**
- Core + Minimal
- Polymarket plugin
- Crypto price tracking
- Wallet balance checkers (Solana, Base)
- Onchain analytics

**Use case:** Autonomous trading bot for prediction markets

**Size:** ~20MB

**Requirements:**
- Telegram bot token
- Polygon wallet private key (for Polymarket)
- Optional: Solana/Base wallets

---

### 4. Full Release (`alleybot-full-v1.0.0.zip`)
**What's included:**
- Everything (current development setup)
- All plugins enabled
- All capabilities

**Use case:** Advanced users, developers, full AGI deployment

**Size:** ~50MB

**Requirements:**
- All API keys and credentials
- More complex setup

---

## 🛠️ Installation Methods

### Method 1: Interactive Setup Wizard (Recommended)

**User experience:**
```bash
git clone https://github.com/DegenApeDev/AlleyBot.git
cd AlleyBot
python setup.py
```

**Wizard flow:**
```
🤖 Welcome to AlleyBot Setup!

What do you want to build?

1. 🎮 Social AI Agent (MoltX, Clawbr, Chess)
2. 💰 Trading Bot (Polymarket, DeFi, Wallets)
3. 🧠 Full AGI (Everything)
4. 📦 Minimal (Core only, add plugins later)
5. 🛠️  Custom (Choose specific plugins)

Enter choice (1-5): 2

✅ Selected: Trading Bot

Configuring plugins:
  ✓ telegram (required)
  ✓ polymarket
  ✓ crypto
  ✓ onchain
  ✓ base_wallet_balance
  ✓ solana_wallet_balance

Do you have a Polygon wallet? (y/n): y
Enter Polygon private key (or press Enter to skip): 

✅ Configuration saved to plugin_config.json
✅ Environment template created: .env

Next steps:
1. Edit .env and add your API keys
2. Run: python src/main.py

🚀 Setup complete!
```

---

### Method 2: Preset Configurations

**User experience:**
```bash
git clone https://github.com/DegenApeDev/AlleyBot.git
cd AlleyBot

# Choose a preset
cp configs/social.json plugin_config.json

# Configure environment
cp .env.example .env
nano .env  # Add your API keys

# Install dependencies
pip install -r requirements/social.txt

# Run
python src/main.py
```

**Available presets:**
- `configs/minimal.json` - Core + Telegram only
- `configs/social.json` - Social AI agent
- `configs/trading.json` - Trading bot
- `configs/full.json` - Everything
- `configs/custom.template.json` - Template for custom builds

---

### Method 3: Docker (Future)

**User experience:**
```bash
# Pull image
docker pull alleybot/social:latest

# Run with environment variables
docker run -e TELEGRAM_TOKEN=xxx -e MOLTX_KEY=yyy alleybot/social

# Or use docker-compose
docker-compose up -f docker-compose.social.yml
```

---

## 📋 Setup Wizard Implementation

### File: `setup.py`

```python
#!/usr/bin/env python3
"""
AlleyBot Interactive Setup Wizard
Helps users configure their AlleyBot instance
"""

import json
import os
from pathlib import Path

# Deployment presets
PRESETS = {
    "1": {
        "name": "Social AI Agent",
        "description": "Engage on MoltX, Clawbr, play chess, create content",
        "plugins": {
            "telegram": {"enabled": True, "config": {}},
            "brain": {"enabled": True, "config": {"auto_start": False}},
            "moltx": {"enabled": True, "config": {"auto_browse": True}},
            "clawbr": {"enabled": True, "config": {"auto_engagement": True}},
            "clawchess": {"enabled": True, "config": {"auto_play": True}},
            "moltchan": {"enabled": True, "config": {"auto_browse": True}},
            "mcp": {"enabled": True, "config": {"web_access": True}}
        },
        "requirements": "requirements/social.txt",
        "env_keys": [
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_OWNER_ID",
            "MOLTX_API_KEY",
            "MOLTX_API_SECRET",
            "CLAWBR_API_KEY",
            "DEEPSEEK_API_KEY"
        ]
    },
    "2": {
        "name": "Trading Bot",
        "description": "Autonomous Polymarket trading, wallet monitoring",
        "plugins": {
            "telegram": {"enabled": True, "config": {}},
            "brain": {"enabled": True, "config": {"auto_start": False}},
            "polymarket": {
                "enabled": True,
                "config": {
                    "paper_trading": True,
                    "auto_trade": True,
                    "scan_interval": 900,
                    "min_edge": 0.05
                }
            },
            "crypto": {"enabled": True, "config": {}},
            "onchain": {"enabled": True, "config": {}},
            "base_wallet_balance": {"enabled": True, "config": {}},
            "solana_wallet_balance": {"enabled": True, "config": {}},
            "mcp": {"enabled": True, "config": {"web_access": True}}
        },
        "requirements": "requirements/trading.txt",
        "env_keys": [
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_OWNER_ID",
            "POLYGON_PRIVATE_KEY",
            "BASE_WALLET_PRIVATE_KEY",
            "SOLANA_WALLET_PRIVATE_KEY",
            "DEEPSEEK_API_KEY"
        ]
    },
    "3": {
        "name": "Full AGI",
        "description": "Everything - social, trading, all capabilities",
        "plugins": "all",  # Special flag to enable everything
        "requirements": "requirements/full.txt",
        "env_keys": "all"  # All possible env vars
    },
    "4": {
        "name": "Minimal",
        "description": "Core AGI + Telegram only, add plugins later",
        "plugins": {
            "telegram": {"enabled": True, "config": {}},
            "brain": {"enabled": True, "config": {"auto_start": False}}
        },
        "requirements": "requirements/core.txt",
        "env_keys": [
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_OWNER_ID",
            "DEEPSEEK_API_KEY"
        ]
    }
}

def main():
    """Main setup wizard"""
    print("\n" + "="*60)
    print("🤖 AlleyBot Setup Wizard")
    print("="*60 + "\n")
    
    # 1. Choose deployment type
    deployment = choose_deployment()
    
    # 2. Get preset configuration
    preset = PRESETS.get(deployment)
    if not preset:
        print("❌ Invalid choice")
        return
    
    print(f"\n✅ Selected: {preset['name']}")
    print(f"   {preset['description']}\n")
    
    # 3. Generate plugin_config.json
    generate_plugin_config(preset)
    
    # 4. Generate .env template
    generate_env_template(preset)
    
    # 5. Show next steps
    show_next_steps(preset)

def choose_deployment():
    """Let user choose deployment type"""
    print("What do you want to build?\n")
    for key, preset in PRESETS.items():
        icon = {"1": "🎮", "2": "💰", "3": "🧠", "4": "📦"}.get(key, "🛠️")
        print(f"{key}. {icon} {preset['name']}")
        print(f"   {preset['description']}\n")
    
    print("5. 🛠️  Custom (Choose specific plugins)\n")
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "5":
        return custom_plugin_selection()
    
    return choice

def custom_plugin_selection():
    """Let user choose specific plugins"""
    print("\n📦 Custom Plugin Selection\n")
    print("Available plugins:")
    
    # List all available plugins
    plugins_dir = Path("plugins")
    available_plugins = [
        d.name for d in plugins_dir.iterdir() 
        if d.is_dir() and not d.name.startswith('_')
    ]
    
    for i, plugin in enumerate(available_plugins, 1):
        print(f"{i}. {plugin}")
    
    print("\nEnter plugin numbers separated by commas (e.g., 1,3,5)")
    print("Or press Enter to select all\n")
    
    selection = input("Plugins: ").strip()
    
    if not selection:
        return "3"  # Full AGI
    
    # Parse selection and build custom preset
    # TODO: Implement custom selection logic
    return "4"  # Default to minimal for now

def generate_plugin_config(preset):
    """Generate plugin_config.json from preset"""
    
    if preset['plugins'] == "all":
        # Copy current full config
        import shutil
        shutil.copy("plugin_config.json", "plugin_config.json.backup")
        print("✅ Using full configuration (all plugins enabled)")
        return
    
    config = preset['plugins']
    
    # Write to plugin_config.json
    with open("plugin_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Generated plugin_config.json ({len(config)} plugins)")

def generate_env_template(preset):
    """Generate .env file with required keys"""
    
    if os.path.exists(".env"):
        print("⚠️  .env already exists, creating .env.new instead")
        env_file = ".env.new"
    else:
        env_file = ".env"
    
    env_keys = preset['env_keys']
    
    if env_keys == "all":
        # Copy full .env.example
        import shutil
        shutil.copy(".env.example", env_file)
        print(f"✅ Generated {env_file} (all keys)")
        return
    
    # Generate minimal .env with only required keys
    with open(env_file, "w") as f:
        f.write("# AlleyBot Environment Configuration\n")
        f.write(f"# Generated for: {preset['name']}\n\n")
        
        f.write("# === REQUIRED ===\n")
        for key in env_keys:
            f.write(f"{key}=\n")
        
        f.write("\n# Add your values above and rename to .env\n")
    
    print(f"✅ Generated {env_file}")

def show_next_steps(preset):
    """Show user what to do next"""
    print("\n" + "="*60)
    print("🚀 Setup Complete!")
    print("="*60 + "\n")
    
    print("Next steps:\n")
    print("1. Edit .env and add your API keys:")
    print("   nano .env\n")
    
    print("2. Install dependencies:")
    print(f"   pip install -r {preset['requirements']}\n")
    
    print("3. Start AlleyBot:")
    print("   python src/main.py\n")
    
    print("📚 Documentation:")
    print("   - README.md - Overview")
    print("   - docs/QUICKSTART.md - Quick start guide")
    print("   - docs/PLUGIN_GUIDE.md - Plugin management\n")
    
    print("💬 Need help? Check the docs or open an issue on GitHub\n")

if __name__ == "__main__":
    main()
```

---

## 📁 Directory Structure for Release

```
AlleyBot/
├── configs/                    # Preset configurations
│   ├── minimal.json
│   ├── social.json
│   ├── trading.json
│   ├── full.json
│   └── custom.template.json
│
├── requirements/               # Tiered dependencies
│   ├── core.txt               # Minimal deps
│   ├── social.txt             # Social platform deps
│   ├── trading.txt            # Trading deps
│   └── full.txt               # All deps
│
├── docs/                       # Documentation
│   ├── QUICKSTART.md          # 5-minute setup
│   ├── SOCIAL_SETUP.md        # Social AI guide
│   ├── TRADING_SETUP.md       # Trading bot guide
│   ├── PLUGIN_GUIDE.md        # Plugin management
│   └── DEVELOPMENT.md         # Custom plugin development
│
├── plugins/                    # Plugin directory
│   ├── core/                  # Core plugins (always included)
│   │   ├── telegram/
│   │   └── brain/
│   │
│   ├── social/                # Social plugins (optional)
│   │   ├── moltx/
│   │   ├── clawbr/
│   │   └── clawchess/
│   │
│   └── trading/               # Trading plugins (optional)
│       ├── polymarket/
│       ├── crypto/
│       └── onchain/
│
├── setup.py                   # Interactive setup wizard
├── .env.example               # Full env template
├── plugin_config.json         # Default config (minimal)
├── README.md                  # Main documentation
└── RELEASE_BUILD.md          # This file
```

---

## 📝 Updated .env.example Structure

```env
# ============================================
# AlleyBot Environment Configuration
# ============================================

# === CORE (REQUIRED) ===
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_OWNER_ID=your_telegram_user_id_here

# === AI MODELS (REQUIRED) ===
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Optional: Grok AI (for advanced content generation)
# GROK_API_KEY=

# ============================================
# SOCIAL PLUGINS (Optional - for Social AI)
# ============================================

# MoltX Platform
# MOLTX_API_KEY=
# MOLTX_API_SECRET=

# Clawbr Platform
# CLAWBR_API_KEY=
# CLAWBR_API_SECRET=

# ============================================
# TRADING PLUGINS (Optional - for Trading Bot)
# ============================================

# Polymarket (Polygon network)
# POLYGON_PRIVATE_KEY=

# Wallet Monitoring
# BASE_WALLET_PRIVATE_KEY=
# SOLANA_WALLET_PRIVATE_KEY=

# ============================================
# ADVANCED (Optional)
# ============================================

# A2A (Agent-to-Agent) Communication
# A2A_ENABLED=false

# Analytics Dashboard
# ANALYTICS_PORT=7001
```

---

## 📚 Documentation to Create

### 1. QUICKSTART.md
- 5-minute setup guide
- Minimal configuration
- First commands to try

### 2. SOCIAL_SETUP.md
- How to configure MoltX, Clawbr
- API key setup
- Social engagement features

### 3. TRADING_SETUP.md
- Polymarket configuration
- Wallet setup (Polygon, Solana, Base)
- Paper trading vs live trading
- Risk management settings

### 4. PLUGIN_GUIDE.md
- How to enable/disable plugins
- Plugin configuration options
- Creating custom plugins
- Plugin dependencies

### 5. DEVELOPMENT.md
- Architecture overview
- How to build custom plugins
- Contributing guidelines
- Testing

---

## 🎯 Requirements Files

### requirements/core.txt
```
python-telegram-bot==20.7
requests>=2.31.0
aiohttp>=3.9.0
python-dotenv>=1.0.0
```

### requirements/social.txt
```
-r core.txt
feedparser>=6.0.10
sgmllib3k>=1.0.0
```

### requirements/trading.txt
```
-r core.txt
web3>=6.0.0
eth-account>=0.9.0
solana>=0.30.0
```

### requirements/full.txt
```
-r core.txt
-r social.txt
-r trading.txt
```

---

## 🚀 Release Checklist

### Pre-Release
- [ ] Create setup.py wizard
- [ ] Create config presets (minimal, social, trading, full)
- [ ] Create tiered requirements.txt files
- [ ] Update .env.example with sections
- [ ] Write QUICKSTART.md
- [ ] Write SOCIAL_SETUP.md
- [ ] Write TRADING_SETUP.md
- [ ] Write PLUGIN_GUIDE.md
- [ ] Update README.md with installation methods
- [ ] Test all 4 deployment types
- [ ] Create GitHub release notes

### Release
- [ ] Tag version v1.0.0
- [ ] Create 4 release artifacts (minimal, social, trading, full)
- [ ] Upload to GitHub Releases
- [ ] Update documentation links
- [ ] Announce on social platforms

### Post-Release
- [ ] Monitor issues
- [ ] Create plugin marketplace (future)
- [ ] Docker images (future)
- [ ] Video tutorials (future)

---

## 💡 Future Enhancements

### Plugin Marketplace
```bash
alleybot plugin search trading
alleybot plugin install polymarket
alleybot plugin remove moltchan
alleybot plugin list --installed
alleybot plugin update --all
```

### Docker Support
```yaml
# docker-compose.social.yml
version: '3.8'
services:
  alleybot:
    image: alleybot/social:latest
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - MOLTX_KEY=${MOLTX_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### Web Dashboard
- Visual plugin management
- Configuration editor
- Performance monitoring
- Log viewer

---

## 📊 Success Metrics

**v1.0 Goals:**
- 100+ users in first month
- 3 deployment types actively used
- <5 setup issues reported
- Clear documentation (>90% satisfaction)

**v2.0 Goals:**
- Plugin marketplace with 10+ community plugins
- Docker support
- Web dashboard
- 1000+ active users

---

*This document will be updated as we implement the release build.*

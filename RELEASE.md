# AlleyBot Public Release Strategy

## 🛡️ Why AlleyBot? Security-First AI Agent Architecture

**March 2026 Security Alert:** OpenClaw AI agents have a critical vulnerability - they leak sensitive data via indirect prompt injection through link previews. China's CNCERT has warned organizations to isolate or restrict OpenClaw.

**AlleyBot was built from the ground up to prevent exactly this type of attack.**

### **How AlleyBot Prevents the OpenClaw Vulnerability:**

1. **SecurityFilter Pre-Execution Validation**
   - All URLs validated against domain allowlist before generation
   - Dangerous patterns blocked before execution
   - No automatic link preview generation without validation

2. **Multi-Layer Validation (Fail-Closed)**
   - Synergy validation (mathematical truth gates)
   - Duat consciousness alignment
   - Heart judgment (historical balance)
   - Action Router trust/risk enforcement

3. **Domain Allowlist**
   - Only approved domains can be accessed
   - Prevents data exfiltration to attacker-controlled servers
   - User-configurable for additional domains

4. **Audit Trail**
   - Every action logged with risk assessment
   - Blocked attempts recorded
   - Full transparency for security review

5. **No Hardcoded Secrets**
   - All credentials in `.env` (never in code)
   - SecurityFilter detects hardcoded secrets in generated code
   - Environment isolation

**AlleyBot is the secure alternative to OpenClaw.** Built with security as the foundation, not an afterthought.

---

## Overview

AlleyBot is currently hardcoded with all plugins loaded by default. To distribute AlleyBot to users while allowing them to choose their own plugins, we need a **plugin selection system** that doesn't break the existing architecture.

---

## The Challenge

**Current Architecture:**
- `plugin_config.json` controls which plugins load
- Many plugins are **tightly coupled** to core systems (Brain, Telegram, etc.)
- Some plugins depend on each other (Brain → MoltX, Telegram → Brain)
- Removing certain plugins could break the autonomous cycle

**User Requirements:**
- Users should choose which platforms they want (MoltX, Clawbr, Chess, etc.)
- Users shouldn't need API keys for platforms they don't use
- Core functionality (Brain, Memory, AGI) should work regardless of plugin selection

---

## Proposed Solution: Tiered Plugin System

### **Tier 1: Core Plugins (Always Enabled)**

These are **required** for AlleyBot to function:

```json
{
  "brain": { "enabled": true, "required": true },
  "telegram": { "enabled": true, "required": true },
  "skills": { "enabled": true, "required": true },
  "base_wallet_balance": { "enabled": true, "required": true }
}
```

**Why Required:**
- `brain`: Autonomous decision-making engine
- `telegram`: Primary user interface
- `skills`: Dynamic capability system
- `base_wallet_balance`: Wallet monitoring (safe read-only)

### **Tier 2: Platform Plugins (User Choice)**

Users select which social platforms to enable:

```json
{
  "moltx": { "enabled": false, "tier": "platform" },
  "clawbr": { "enabled": false, "tier": "platform" },
  "moltchan": { "enabled": false, "tier": "platform" },
  "moltbook": { "enabled": false, "tier": "platform" },
  "clawchess": { "enabled": false, "tier": "platform" }
}
```

**User Decision:** Enable only the platforms they have accounts for.

### **Tier 3: Trading/DeFi Plugins (Advanced Users)**

High-risk plugins that require explicit opt-in:

```json
{
  "polymarket": { "enabled": false, "tier": "trading", "risk": "high" },
  "base_trading": { "enabled": false, "tier": "trading", "risk": "high" },
  "solana_trading": { "enabled": false, "tier": "trading", "risk": "high" },
  "fluid_lending": { "enabled": false, "tier": "defi", "risk": "medium" }
}
```

**Default:** All disabled. Users must explicitly enable + provide API keys.

### **Tier 4: Analytics/Intelligence (Optional)**

Safe, read-only plugins for market intelligence:

```json
{
  "crypto": { "enabled": true, "tier": "analytics" },
  "onchain": { "enabled": true, "tier": "analytics" },
  "analytics": { "enabled": true, "tier": "analytics" },
  "intelligence": { "enabled": true, "tier": "analytics" }
}
```

**Default:** Enabled (safe, no API keys needed for basic features).

---

## Implementation Strategy (No Code Changes Needed)

### **Step 1: Create `plugin_config.template.json`**

Ship a template config with sensible defaults:

```json
{
  "// CORE PLUGINS - DO NOT DISABLE": "Required for AlleyBot to function",
  "brain": { "enabled": true, "required": true },
  "telegram": { "enabled": true, "required": true },
  "skills": { "enabled": true, "required": true },
  
  "// PLATFORM PLUGINS - Enable the ones you use": "",
  "moltx": { 
    "enabled": false,
    "requires_api_key": "MOLTX_API_KEY",
    "description": "Post and engage on MoltX social platform"
  },
  "clawbr": { 
    "enabled": false,
    "requires_api_key": "CLAWBR_API_KEY",
    "description": "Participate in debates on Clawbr"
  },
  "clawchess": { 
    "enabled": false,
    "requires_api_key": "CLAWCHESS_API_KEY",
    "description": "Play chess on ClawChess.com"
  },
  
  "// TRADING PLUGINS - HIGH RISK - Disabled by default": "",
  "polymarket": { 
    "enabled": false,
    "requires_api_key": "POLYMARKET_API_KEY",
    "risk_level": "HIGH",
    "description": "Autonomous prediction market trading"
  },
  
  "// ANALYTICS PLUGINS - Safe, read-only": "",
  "crypto": { "enabled": true },
  "onchain": { "enabled": true },
  "analytics": { "enabled": true }
}
```

### **Step 2: Create `.env.template`**

Ship a template with all possible API keys:

```bash
# === CORE CONFIGURATION ===
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_ADMIN_CHAT_ID=your_telegram_chat_id_here

# === AI PROVIDERS (Choose one or both) ===
GROK_API_KEY=your_grok_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# === PLATFORM PLUGINS (Enable in plugin_config.json) ===
# Only fill in the ones you plan to use
MOLTX_API_KEY=
CLAWBR_API_KEY=
CLAWCHESS_API_KEY=
MOLTCHAN_API_KEY=

# === TRADING PLUGINS (HIGH RISK - Leave blank unless you know what you're doing) ===
POLYMARKET_API_KEY=
POLYMARKET_PRIVATE_KEY=
BASE_WALLET_PRIVATE_KEY=

# === BLOCKCHAIN (Optional) ===
BASE_WALLET_PUBLIC_ADDRESS=
SOLANA_WALLET_PUBLIC_ADDRESS=
```

### **Step 3: Update `README.md` with Setup Wizard**

Add a guided setup section:

```markdown
## 🚀 Quick Start

### 1. Choose Your Plugins

Copy the template and enable what you need:
```bash
cp plugin_config.template.json plugin_config.json
```

Edit `plugin_config.json` and set `"enabled": true` for platforms you want to use.

### 2. Configure API Keys

Copy the environment template:
```bash
cp .env.template .env
```

Fill in ONLY the API keys for plugins you enabled.

### 3. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Start AlleyBot

```bash
python3 alleybot_core.py
```

AlleyBot will only load the plugins you enabled!
```

---

## Safety Mechanisms (Already Built-In)

### **1. Graceful Plugin Failures**

The existing `PluginManager` already handles missing plugins:

```python
if plugin_config.get('enabled', True):
    self.load_plugin(plugin_name, plugin_config, api, core)
else:
    print(f"⏸️  Plugin disabled: {plugin_name}")
```

**Result:** Disabled plugins are simply skipped, no crashes.

### **2. Missing API Key Detection**

Plugins already check for API keys in `initialize()`:

```python
if not os.getenv('MOLTX_API_KEY'):
    print("⚠️ MoltX plugin requires MOLTX_API_KEY")
    return
```

**Result:** Plugin loads but stays inactive if API key is missing.

### **3. Brain Adapts to Available Plugins**

The Brain's autonomous cycle already checks plugin availability:

```python
async def _gather_observations(self) -> List[SyModObservation]:
    """Gather observations from all enabled plugins."""
    observations = []
    
    if 'moltx' in self.plugin_manager.plugins:
        obs = await self._observe_moltx()
        observations.append(obs)
    
    # Gracefully skips if plugin not loaded
```

**Result:** Brain works with whatever plugins are available.

---

## Distribution Checklist

### **Files to Include in Release:**

- ✅ `plugin_config.template.json` (sensible defaults)
- ✅ `.env.template` (all possible API keys)
- ✅ `README.md` (updated with setup wizard)
- ✅ `RELEASE.md` (this document)
- ✅ `requirements.txt` (all dependencies)
- ✅ `SECURITY.md` (explain security architecture)
- ✅ `PLUGINS.md` (document each plugin's purpose and requirements)

### **Files to `.gitignore`:**

```
plugin_config.json
.env
data/
logs/
*.db
__pycache__/
```

**Why:** Users create their own config, we don't ship our private keys.

---

## User Onboarding Flow

### **Beginner Setup (Minimal)**

1. Enable only: `brain`, `telegram`, `crypto`, `analytics`
2. API keys needed: `TELEGRAM_BOT_TOKEN`, `GROK_API_KEY` or `DEEPSEEK_API_KEY`
3. Result: AlleyBot works as a Telegram assistant with market intelligence

### **Social Media Setup**

1. Enable: `brain`, `telegram`, `moltx`, `clawbr`
2. API keys needed: Telegram + Grok/DeepSeek + MoltX + Clawbr
3. Result: AlleyBot posts and engages on social platforms

### **Advanced Trading Setup**

1. Enable: All analytics + `polymarket`, `base_trading`
2. API keys needed: Everything + wallet private keys
3. **WARNING:** High risk, requires understanding of trading risks
4. Result: Autonomous trading agent

---

## Migration Path for Existing Users

**Your current setup (hardcoded) will continue to work!**

To migrate to the new system:

1. Run: `python3 scripts/generate_plugin_config.py`
   - Scans your current `.env` file
   - Auto-generates `plugin_config.json` with plugins that have API keys enabled
   - Preserves your existing setup

2. Review the generated config
3. Disable any plugins you don't want
4. Restart AlleyBot

**No breaking changes.** The system is backward compatible.

---

## FAQ

### **Q: What if I disable a plugin that Brain depends on?**

**A:** Brain gracefully handles missing plugins. It will skip observations/actions for that platform and continue with others.

### **Q: Can I enable plugins later?**

**A:** Yes! Just edit `plugin_config.json`, add the API key to `.env`, and run `/plugins_reload` in Telegram.

### **Q: What's the minimum setup to run AlleyBot?**

**A:** 
- Plugins: `brain`, `telegram`, `skills`
- API Keys: `TELEGRAM_BOT_TOKEN`, `GROK_API_KEY` or `DEEPSEEK_API_KEY`

### **Q: Are trading plugins safe?**

**A:** They use paper trading by default. Real trading requires:
1. Setting `"paper_trading": false` in plugin config
2. Providing wallet private keys
3. Understanding the risks

### **Q: How do I know which plugins I need?**

**A:** See `PLUGINS.md` for a full catalog with descriptions, requirements, and risk levels.

---

## Next Steps

1. **Create `plugin_config.template.json`** with tiered defaults
2. **Create `.env.template`** with all possible keys
3. **Write `PLUGINS.md`** documenting each plugin
4. **Write `SECURITY.md`** explaining the security architecture
5. **Update `README.md`** with setup wizard
6. **Create `scripts/generate_plugin_config.py`** for migration
7. **Test with fresh install** to ensure onboarding works

---

## Summary

**The Good News:** AlleyBot's architecture already supports plugin selection! The `PluginManager` handles enabled/disabled plugins gracefully, and the Brain adapts to available plugins.

**No Code Changes Needed:** Just ship templates and documentation. Users configure via JSON + .env files.

**Safety First:** Core plugins are marked as required, trading plugins default to disabled, and the security filter protects against misuse.

**User-Friendly:** Clear templates, setup wizard, and migration script make it easy for new users to get started with just the features they want.

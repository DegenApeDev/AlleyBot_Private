# AlleyBot Enhanced Skills System

## Overview

AlleyBot's skills system has been enhanced with **OpenClaw-style autonomous execution** and **multi-platform skill compatibility**. Now you can:

- Run skills automatically on a heartbeat schedule
- Import skills from OpenClaw (ClawHub) and ElizaOS
- Execute tools (browser, system commands, email, calendar)
- Chain skills together for complex workflows
- Maintain security with AlleyBot's approval gating

---

## New Commands

### Autonomous Execution (OpenClaw-Style)

```
/autonomous_start          - Start heartbeat loop (runs every 30min)
/autonomous_stop           - Stop heartbeat loop
/autonomous_status         - Check autonomous execution status
```

### Tool Registry

```
/tool_list                 - List all available tools
/tool_exec <tool> [args]   - Execute a tool directly

Examples:
/tool_exec system.run 'ls -la'
/tool_exec file.read config.json
/tool_exec token.price bitcoin
```

### Skill Import/Export

```
/skill_import_openclaw <path>    - Import OpenClaw SKILL.md
/skill_import_elizaos <path>     - Import ElizaOS character.json
/skill_export_openclaw <name>    - Export skill to OpenClaw format
```

### Skill Composition (Chaining)

```
/skill_chain <skill1> <skill2> ...   - Execute skills in sequence

Example:
/skill_chain crypto_prices sentiment_analysis moltx_post
```

---

## HEARTBEAT.md - Autonomous Task Checklist

Create a `HEARTBEAT.md` file in your project root to define autonomous tasks:

```markdown
---
interval_minutes: 30
---

# Daily Tasks
- [ ] Check crypto prices -> crypto-price-monitor
- [ ] Review MoltX mentions -> moltx-engagement
- [ ] Post daily summary -> daily-brief
- [ ] Backup files -> file-backup
```

**How it works:**
1. AlleyBot reads HEARTBEAT.md every 30 minutes
2. Unchecked `[ ]` items trigger their associated skill
3. Skills execute autonomously (with optional approval gating)
4. Successful tasks can be checked off `[x]`
5. Failed tasks remain unchecked and retry next heartbeat

---

## Tool Registry

### System Tools
- `system.run` - Execute shell commands (allowlist-enforced)
- `system.notify` - Send OS notifications
- `file.read` - Read file contents
- `file.write` - Write files
- `file.list` - List directories

### Browser Tools (requires Playwright)
- `browser.open` - Open URL
- `browser.scrape` - Extract page content
- `browser.click` - Click elements
- `browser.fill` - Fill forms

### Communication Tools
- `email.read` - Read emails (requires Gmail setup)
- `email.send` - Send emails
- `telegram.send` - Send Telegram messages
- `discord.send` - Send Discord webhooks

### Data Tools
- `calendar.read` - Read calendar events
- `calendar.create` - Create events
- `search.web` - Web search (requires API key)
- `api.call` - HTTP API calls

### Crypto Tools (AlleyBot Specialty)
- `wallet.balance` - Check wallet balances
- `dex.swap` - Execute DEX swaps (approval-gated)
- `token.price` - Get token prices

---

## Importing Skills from Other Platforms

### OpenClaw (ClawHub)

OpenClaw skills use the `SKILL.md` format with YAML frontmatter:

```markdown
---
name: gmail-manager
description: Read and manage Gmail messages
---

## Instructions
When user asks about email:
1. Use email.read to fetch unread
2. Summarize important messages
3. Draft responses
```

**Import:**
```
/skill_import_openclaw /path/to/SKILL.md
```

### ElizaOS

ElizaOS uses `character.json` files:

```json
{
  "name": "TraderBot",
  "bio": ["Crypto trading assistant"],
  "clients": ["discord", "telegram"],
  "topics": ["crypto", "trading"]
}
```

**Import:**
```
/skill_import_elizaos /path/to/character.json
```

---

## Skill Composition

Skills can call other skills, enabling complex workflows:

```python
# In a skill execution:
result = skill._call_skill('crypto_prices', 'Get BTC price')
if result['success']:
    price = result['result']
    skill._call_skill('telegram_send', f'BTC: ${price}')
```

**Chain multiple skills:**
```
/skill_chain market_analyzer trade_decision dex_executor
```

---

## Security Features

AlleyBot maintains security while adding autonomous capabilities:

1. **Tool Allowlist** - Only approved commands can run via `system.run`
2. **Approval Gating** - Sensitive skills can require manual approval
3. **Path Restriction** - File operations stay within project root
4. **Rate Limiting** - Max runs per day per trigger
5. **Sandboxing** - Skills run in isolated context

Configure in `HEARTBEAT.md`:
```yaml
---
approval_required: true  # Require manual approval for all tasks
max_runs_per_day: 50     # Limit total autonomous executions
---
```

---

## Comparison: AlleyBot vs OpenClaw

| Feature | AlleyBot | OpenClaw |
|---------|----------|------------|
| **Heartbeat** | ✅ HEARTBEAT.md | ✅ HEARTBEAT.md |
| **Tools** | ✅ 20+ tools | ✅ 30+ tools |
| **Browser** | ⚠️ Requires setup | ✅ Built-in |
| **Multi-channel** | ⚠️ Telegram focused | ✅ 20+ channels |
| **Security** | ✅ Hardened, gating | ⚠️ Configurable |
| **Skills Import** | ✅ OpenClaw + ElizaOS | ✅ ClawHub only |
| **Crypto/Web3** | ✅ Native | ⚠️ Requires skills |
| **AGI Kernel** | ✅ 8-phase cycle | ❌ Simple gateway |

**AlleyBot's advantage:** Security + AGI reasoning + Crypto native
**OpenClaw's advantage:** Browser automation + Multi-channel + Voice

---

## Quick Start

1. **Start autonomous mode:**
   ```
   /autonomous_start
   ```

2. **Check available tools:**
   ```
   /tool_list
   ```

3. **Execute a tool:**
   ```
   /tool_exec system.run 'df -h'
   ```

4. **Import an OpenClaw skill:**
   ```
   /skill_import_openclaw ./skills/email-manager/SKILL.md
   ```

5. **Activate and use a skill:**
   ```
   /skill_activate email-manager
   ```

6. **Chain skills together:**
   ```
   /skill_chain price_monitor alert_sender
   ```

---

## Next Steps

To fully match OpenClaw capabilities:

1. **Add Playwright** for browser automation:
   ```bash
   pip install playwright
   playwright install
   ```

2. **Configure Gmail** for email automation:
   - Set up Gmail Pub/Sub or IMAP
   - Add credentials to `.env`

3. **Add more channels** (WhatsApp, Discord, Slack)

4. **Build more skills** for your specific workflows

---

*Enhanced skills system - Now with OpenClaw-style autonomous execution*

# AlleyBot TODO — Roadmap

## Completed ✅

### Phase 1: Stabilize (48 tests)
- [x] Fix Moltx API endpoint URL encoding issues
- [x] Fix Grok nested JSON response parsing
- [x] Prevent raw JSON display in posts and outputs
- [x] Fix Moltbook API method errors
- [x] Add parameter validation across all plugins

### Phase 2: Modularize (49 tests)
- [x] Split moltx.py into 5 mixin files
- [x] Split moltbook.py into 4 mixin files
- [x] Unified EnhancedMemorySystem across core
- [x] Archive 20 stale scripts

### Phase 3: On-Chain (31 tests)
- [x] Web3Provider connecting to Base (chain 8453)
- [x] Token tracker (ALLEY, USDC, WETH)
- [x] Tx monitor with semantic memory logging
- [x] Wire on-chain commands into Telegram (/wallet, /balance, /block, /track, /tx, /activity)

### Phase 4: Self-Improvement (32 tests)
- [x] Git workflow with auto/* branch safety
- [x] Test gate (blocks eval/exec/os.system)
- [x] Sandbox execution in temp directories
- [x] Skill marketplace (publish/import)

### Phase 5: Autonomous Brain (30 tests)
- [x] Context Gatherer — pulls from memory, on-chain, platforms, engagement, goals
- [x] Decision Engine — 14+ autonomous actions (incl. chains), AI-powered (Grok) with heuristic fallback
- [x] Smart Reply — memory-enriched replies with user profiles
- [x] Telegram integration (/think, /brain_start, /brain_stop, /brain)
- [x] Background autonomous loop (configurable cycle interval)

### Security Hardening
- [x] SecurityFilter covers ALL 15+ .env keys (was only 4)
- [x] Auto-scans os.environ for PRIVATE/SECRET/TOKEN/API_KEY/PASSWORD
- [x] Outbound Telegram filter on all command outputs
- [x] Owner-lock ALL 23 Telegram commands via TELEGRAM_ADMIN_CHAT_ID
- [x] No hardcoded IDs — everything from .env

### Dashboard
- [x] Rewrite dashboard with modern dark UI
- [x] Brain Status panel (live cycles, success rate, actions, known users)
- [x] Real AI stats from ModelRouter token tracker
- [x] Auto-refresh (stats 20s, feed 45s)

**Total: 190 tests, all passing**

---

## 🔥 Phase 6: Feedback Loop (HIGH PRIORITY)
- [x] Track upvotes/engagement on AlleyBot's posts after posting
- [x] Store engagement metrics per post in memory
- [x] Feed engagement data back into brain decision-making (brain_engagement_log in memory, success_rate in context)
- [x] Learn which content styles get the most engagement
- [x] Adjust posting strategy based on what works

## 🧠 Phase 7: Content Strategy
- [ ] Content calendar — plan posts around optimal times and trending topics
- [x] Cross-platform intelligence — if something trends on Moltx, post about it on Moltbook
- [ ] Conversation threading — track multi-turn conversations for context-aware replies
- [ ] Personality tuning — configurable humor, formality, emoji usage across platforms

## 🔧 Phase 8: Dynamic Skills
- [ ] Wire brain to detect capability gaps ("tried X but no skill for it")
- [ ] Auto-generate missing skills using self-improvement plugin
- [ ] Skill performance tracking — which skills are useful vs unused
- [ ] Skill versioning — update skills when they stop working
- [x] Predefined action chains (crypto prices + trending → post)
- [ ] Dynamic skill chaining — let Grok compose ad-hoc 2-3 step chains from any available plugin commands at runtime (mini ReAct agent loop, no LangChain dependency)

## 🛡️ Phase 9: Operational Resilience
- [ ] Health alerts via Telegram (API errors, low balance, engagement drops)
- [ ] Rate limit awareness — track and back off per-platform
- [ ] Systemd service for auto-restart on VPS
- [ ] Uptime monitoring and crash recovery

## 🚀 Phase 10: Differentiate from OpenClaw
- [ ] On-chain actions — tip users, interact with contracts, not just monitor
- [ ] Multi-agent collaboration — detect and interact with other AI agents
- [ ] Reputation system — track and optimize reputation score across platforms
- [x] Agent-to-agent messaging — A2A plugin with task server (port 7002)

## Notes
- Branch: `opus_rebuild`
- Run: `python alleybot_core.py autonomous`
- Tests: `python -m unittest tests.test_fixes tests.test_phase2 tests.test_phase3 tests.test_phase4 tests.test_phase5`
- Cost: ~$0.015/day (~$0.45/month) at current Grok pricing
- .gitignore blocks `test_*.py` — use `git add -f` to stage test files

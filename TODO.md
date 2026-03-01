# AlleyBot TODO — AGI Roadmap

> **Last Updated:** March 1, 2026  
> **Branch:** `AGI_Integration`  
> **Status:** Active Development - Moving toward True AGI

---

## 🎯 Current Sprint (Week of Mar 1, 2026)

### 🔴 Critical Issues
- [ ] **Intent Classifier Command Drop** (261 → 98 → 54 commands)
  - Investigate why command count decreased dramatically
  - Check if commands are being properly registered
  - Verify plugin discovery is working correctly
  - Location: `plugins/telegram/intent_classifier.py`
  - Priority: **HIGH** - Core functionality affected

- [ ] **MoltX 429 Error - "Engage Before Posting"**
  - MoltX requires engagement (like/reply) before posting
  - Implement pre-posting engagement check
  - Add feed reading before post attempts
  - Location: `plugins/moltx/`
  - Priority: **HIGH** - Blocking autonomous posting

### 🟡 High Priority Features

#### **Token Trading System** 🪙
- [ ] **Solana Token Trading**
  - Integrate Jupiter Aggregator for best swap prices
  - Add wallet balance checks before trades
  - Implement slippage protection
  - Add transaction confirmation monitoring
  - Commands: `/swap_sol`, `/trade_sol`, `/sol_price`
  - Location: `plugins/solana_trading/` (new)

- [ ] **Base Token Trading**
  - Integrate Uniswap V3 for Base chain swaps
  - Add liquidity pool analysis
  - Implement MEV protection
  - Add gas estimation and optimization
  - Commands: `/swap_base`, `/trade_base`, `/base_price`
  - Location: `plugins/base_trading/` (new)

- [ ] **Unified Trading Interface**
  - Cross-chain price comparison
  - Best route finder (Solana vs Base)
  - Portfolio tracking across chains
  - P&L calculation and reporting
  - Location: `plugins/trading/` (new)

---

## 🧠 AGI Enhancement Roadmap

### Phase 1: Enhanced Autonomy (Next 2 Weeks)

#### **A. Real-Time Opportunity Detection**
- [ ] Implement `OpportunityMonitor` class
  - Continuously scan platforms for high-value opportunities
  - Interrupt current cycle if opportunity score > threshold
  - Examples: Trending topics, active snapshots, high-value DMs
  - Location: `src/agentic/opportunity_monitor.py` (new)
  - Priority: **HIGH**

- [ ] Add opportunity scoring system
  - Time-sensitivity score (0-100)
  - Value score (potential engagement/rewards)
  - Confidence score (likelihood of success)
  - Combined score determines interrupt threshold

#### **B. Parallel Action Execution**
- [ ] Implement parallel task execution in AGI Orchestrator
  - Group actions by platform
  - Run non-conflicting actions simultaneously
  - Example: Post on MoltX + Check Clawbr + Scan Telegram
  - Location: `src/agentic/agi_orchestrator.py`
  - Expected: 3-5x faster execution
  - Priority: **MEDIUM**

#### **C. Cross-Platform Intelligence Synthesis**
- [ ] Create `CrossPlatformIntelligence` class
  - Detect patterns across platforms
  - Topic trending on MoltX → Research on Clawbr
  - DeFi opportunity on Clawbr → Share on MoltX
  - User question on Telegram → Content for MoltX
  - Location: `src/agentic/cross_platform_intel.py` (new)
  - Priority: **MEDIUM**

---

### Phase 2: Platform Expansion (Next 3 Weeks)

#### **New Platform Integrations**

- [ ] **Farcaster/Warpcast** 🟣
  - Crypto-native social network
  - High-quality AI/crypto discussions
  - API: https://docs.farcaster.xyz/
  - Location: `plugins/farcaster/` (new)
  - Priority: **HIGH** - High-value community

- [ ] **Twitter/X Full Integration** 🐦
  - Expand existing `brain_x_post` plugin
  - Add engagement features (like, reply, retweet)
  - Implement thread creation
  - Add trend monitoring
  - Location: `plugins/x402/` (enhance existing)
  - Priority: **HIGH** - Massive reach potential

- [ ] **Discord Enhancement** 💬
  - Already exists but underutilized
  - Add server management features
  - Implement voice channel support
  - Add community building tools
  - Location: `plugins/discord/` (enhance existing)
  - Priority: **MEDIUM**

- [ ] **Lens Protocol** 🌿
  - Decentralized social graph
  - Web3 community engagement
  - API: https://docs.lens.xyz/
  - Location: `plugins/lens/` (new)
  - Priority: **LOW** - Future expansion

---

### Phase 3: Meta-Learning (Next 4 Weeks)

#### **D. Strategy Evolution Enhancement**
- [ ] Implement `MetaLearner` class
  - Analyze which decision strategies work best
  - Identify highest-performing platforms
  - Determine optimal times of day
  - Auto-tune parameters (cycle_interval, confidence_threshold)
  - Location: `src/agentic/meta_learner.py` (new)
  - Priority: **MEDIUM**

#### **E. Dynamic Goal Re-Prioritization**
- [ ] Enhance `GoalManager` with dynamic priorities
  - Re-calculate priorities based on real-time context
  - Boost priority for time-sensitive opportunities
  - Demote stale or low-value goals
  - Location: `src/agentic/goal_manager.py` (enhance)
  - Priority: **MEDIUM**

---

## ✅ Recently Completed (Last 7 Days)

### Bug Fixes
- [x] **DeepSeekAI max_tokens Error** (Feb 28)
  - Fixed `generate_reply_to_comment()` missing parameter
  - Added `max_tokens` parameter with default 500
  - Location: `deepseek_ai.py:263`

- [x] **MoltX 503 Retry Logic** (Feb 28)
  - Added exponential backoff for rate limiting
  - Retry strategy: 1s → 2s → 4s (max 3 retries)
  - Location: `plugins/moltx/moltx_api.py:112`

- [x] **Clawbr NoneType Error** (Mar 1)
  - Fixed `'NoneType' object is not subscriptable` error
  - Added None checks in `get_token_balance()` and `check_snapshot_status()`
  - Location: `plugins/clawbr/clawbr_wallet.py:163-223`

### AGI Features
- [x] **LLM Decision Router** (Feb 27)
  - Dynamic reasoning-based decision making
  - Grok + DeepSeek reasoning models
  - SyMod mathematical validation
  - Decision memory for continuous learning
  - Location: `src/agentic/llm_decision_router.py`

- [x] **SentenceTransformer Singleton** (Feb 27)
  - Global singleton to prevent multiple model loads
  - Reduced memory footprint and startup time
  - Location: `src/utils/embedding_model.py`

---

## 🔧 Infrastructure & Maintenance

### Code Quality
- [ ] Investigate intent classifier command registration
  - Why did commands drop from 261 to 54?
  - Check plugin discovery mechanism
  - Verify command registration in all plugins

- [ ] Add comprehensive error handling
  - Standardize error responses across plugins
  - Add retry logic for all API calls
  - Implement circuit breakers for failing services

### Documentation
- [ ] Update architecture diagrams
  - Add token trading systems
  - Add new platform integrations
  - Update data flow diagrams

- [ ] Create trading guide
  - How to use swap commands
  - Risk management guidelines
  - Portfolio tracking instructions

### Testing
- [ ] Add trading system tests
  - Mock Jupiter/Uniswap APIs
  - Test slippage protection
  - Verify transaction monitoring

- [ ] Add platform integration tests
  - Test Farcaster API integration
  - Verify Twitter/X posting
  - Check Discord message handling

---

## 🎮 AGI Behavioral Goals

These should be exhibited across all features:

| Behavior | Current Status | Target |
|----------|---------------|--------|
| **Proactivity** | 🟡 Partial | 🟢 Full - Interrupts for opportunities |
| **Adaptability** | 🟢 Good | 🟢 Excellent - Dynamic re-prioritization |
| **Curiosity** | 🟡 Basic | 🟢 Advanced - Autonomous research |
| **Memory** | 🟢 Good | 🟢 Excellent - Cross-platform synthesis |
| **Reasoning** | 🟢 Good | 🟢 Excellent - LLM Decision Router active |
| **Planning** | 🟢 Good | 🟢 Excellent - Multi-step with LLM |
| **Social** | 🟡 Partial | 🟢 Full - Multi-platform engagement |
| **Self-Improvement** | 🟢 Good | 🟢 Excellent - Meta-learning |
| **Resilience** | 🟢 Good | 🟢 Excellent - Retry logic everywhere |
| **Creativity** | 🟢 Good | 🟢 Excellent - Story arcs, A/B tests |

---

## 📊 Metrics & Goals

### Engagement Targets
- **MoltX:** 50+ posts/day, 100+ engagements/day
- **Clawbr:** Daily check-ins, snapshot claims
- **Telegram:** <5min response time
- **Farcaster:** 20+ posts/day (after integration)
- **Twitter/X:** 30+ posts/day (after full integration)

### Performance Targets
- **Autonomous Cycle:** <30 seconds (currently ~45s)
- **Decision Latency:** <2 seconds (currently ~3s)
- **API Success Rate:** >95% (currently ~92%)
- **Memory Retrieval:** <100ms (currently ~150ms)

### Learning Targets
- **Strategy Evolution:** 10+ strategies/week
- **Success Rate Improvement:** +5% month-over-month
- **Cross-Platform Insights:** 5+ connections/day

---

## 🚀 Quick Reference

### Current State
- **Branch:** `AGI_Integration`
- **Python:** 3.12
- **Main Entry:** `python alleybot_core.py autonomous`
- **Dashboard:** http://localhost:7001

### Key Commands
```bash
# Start autonomous mode
python alleybot_core.py autonomous

# Run AGI cycle manually
/agi_cycle

# Check brain status
/brain

# Reload plugins
/reload_plugins <plugin_name>

# Trading (after implementation)
/swap_sol <from_token> <to_token> <amount>
/swap_base <from_token> <to_token> <amount>
```

### Environment Variables
```bash
# Core
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_CHAT_ID=

# AI Models
GROK_API_KEY=
DEEPSEEK_API_KEY=
XAI_API_KEY=

# Platforms
MOLTX_API_KEY=
CLAWBR_API_KEY=
FARCASTER_API_KEY=      # After integration
TWITTER_API_KEY=        # After integration

# Wallets
BASE_WALLET_PUBLIC_ADDRESS=
BASE_WALLET_PRIVATE_KEY=
SOLANA_WALLET_PUBLIC_ADDRESS=
SOLANA_WALLET_PRIVATE_KEY=
```

---

## 📝 Notes

### Recent Insights
- MoltX requires engagement before posting (429 error)
- Clawbr API can return None on failures (needs null checks)
- Intent classifier losing commands - needs investigation
- SentenceTransformer was loading 3x (now fixed with singleton)

### Future Considerations
- Multi-agent coordination (A2A protocol)
- Voice interaction (already have voice_emotion plugin)
- Image generation integration
- Video content creation
- Podcast/audio content

---

**Last Updated:** March 1, 2026 12:37 AM UTC  
**Next Review:** March 8, 2026

# A2A ERC-8004 Monetization System - Improvement Plan

**Date:** February 28, 2026  
**Priority:** HIGH - Revenue Generation  
**Current Status:** 0 skills showing on 8004scan despite having 21+ skill files  
**Goal:** Maximize skill offerings + AGI-powered intelligent pricing for income generation

---

## 🐛 Current Problems Identified

### **Problem 1: Hardcoded Skills (Not Dynamic)**
**Location:** `plugins/analytics/agent_card.py` lines 39-146

**Issue:**
```python
PLUGIN_SKILL_MAP = {
    'moltx': {
        'skills': ['natural_language_processing/...'],  # HARDCODED
    },
    # Only maps 13 plugins, ignores actual skill files
}
```

**Result:** 
- Agent card shows ONLY hardcoded plugin skills
- Ignores 21+ actual skill files in `skills/` directory
- New skills created by selfimprove plugin are NEVER added to agent card
- 8004scan shows 0 skills because card generation is broken

---

### **Problem 2: No Dynamic Skill Discovery**
**Location:** `plugins/analytics/agent_card.py` line 221-237

**Issue:**
```python
def _collect_skills(self) -> List[str]:
    """Collect OASF skills from all loaded plugins"""
    for plugin_name, skill_info in PLUGIN_SKILL_MAP.items():
        if plugin_name in loaded_plugins:
            skills.extend(skill_info['skills'])  # Only from hardcoded map
```

**Missing:**
- No scanning of `skills/` directory
- No reading of `SKILL.md` files
- No detection of autonomously generated skills
- No integration with selfimprove plugin's skill registry

---

### **Problem 3: No AGI Integration for Skill Selection**
**Current:** Agent card includes ALL hardcoded skills automatically

**Missing:**
- AGI Kernel decision on which skills to offer
- Intelligent pricing based on skill complexity
- Market demand analysis
- Skill performance tracking
- Dynamic pricing adjustments

---

### **Problem 4: A2A Task Registry Incomplete**
**Location:** `plugins/a2a/a2a_tasks.py` lines 21-146

**Current A2A Skills:**
- 4 public tasks (capabilities, health, stats, skills)
- 6 paid tasks (generate_post, analyze_trend, check_balance, etc.)
- **Total: 10 tasks**

**Available Skills Not Exposed:**
- 21+ skill files in `skills/` directory
- Blockchain analysis
- Content generation (multiple platforms)
- Engagement optimization
- Social engagement
- SyMod liquidity architect
- ERC-8004 management
- And more...

**Lost Revenue:** Only exposing 10% of actual capabilities!

---

## 🎯 Improvement Plan

### **Phase 1: Fix Skill Detection (2-3 hours)**

#### **1.1 Create Dynamic Skill Scanner**
**New File:** `plugins/analytics/skill_scanner.py`

```python
class SkillScanner:
    """
    Scans skills/ directory and extracts OASF-compatible skills.
    
    Reads:
    - skills/*/SKILL.md files
    - skills/*.md files
    - Parses skill metadata (name, description, category, pricing)
    """
    
    def scan_skills_directory(self) -> List[Dict]:
        """
        Scan skills/ directory for all SKILL.md files.
        
        Returns list of skill objects:
        {
            'id': 'blockchain-analysis',
            'name': 'Blockchain Analysis',
            'description': '...',
            'category': 'analytical_skills',
            'oasf_skills': ['analytical_skills/data_analysis/blockchain_analysis'],
            'pricing': {'suggested': 0.10, 'currency': 'USDC'},
            'file_path': 'skills/blockchain-analysis/SKILL.md',
            'auto_generated': False,
            'performance': {'uses': 0, 'success_rate': 0},
        }
        """
        
    def parse_skill_file(self, skill_path: str) -> Dict:
        """Parse SKILL.md and extract metadata"""
        
    def map_to_oasf_taxonomy(self, skill: Dict) -> List[str]:
        """Map skill to OASF 0.8.0 taxonomy slugs"""
```

#### **1.2 Update Agent Card Generator**
**File:** `plugins/analytics/agent_card.py`

```python
def _collect_skills(self) -> List[str]:
    """Collect OASF skills from loaded plugins AND skill files"""
    skills = []
    
    # 1. Get hardcoded plugin skills (keep for base capabilities)
    for plugin_name, skill_info in PLUGIN_SKILL_MAP.items():
        if plugin_name in loaded_plugins:
            skills.extend(skill_info['skills'])
    
    # 2. NEW: Scan skills/ directory for actual skills
    scanner = SkillScanner()
    discovered_skills = scanner.scan_skills_directory()
    
    # 3. NEW: Let AGI Kernel decide which skills to include
    if self.core and hasattr(self.core, 'agi_kernel'):
        selected_skills = self.core.agi_kernel.decide_skill_offerings(
            available_skills=discovered_skills,
            context={'market': 'a2a', 'goal': 'maximize_revenue'}
        )
        for skill in selected_skills:
            skills.extend(skill['oasf_skills'])
    else:
        # Fallback: include all discovered skills
        for skill in discovered_skills:
            skills.extend(skill['oasf_skills'])
    
    return list(dict.fromkeys(skills))  # dedupe
```

---

### **Phase 2: AGI Kernel Integration (2-3 hours)**

#### **2.1 Add Skill Management to AGI Kernel**
**New File:** `src/agentic/skill_manager.py`

```python
class SkillManager:
    """
    AGI Kernel component for intelligent skill management.
    
    Features:
    - Decides which skills to offer via A2A
    - Sets intelligent pricing based on complexity + demand
    - Tracks skill performance (usage, success rate, revenue)
    - Suggests new skills to develop based on market gaps
    """
    
    def decide_skill_offerings(self, available_skills: List[Dict], 
                               context: Dict) -> List[Dict]:
        """
        Use AGI Kernel to decide which skills to offer.
        
        Considers:
        - Skill complexity (higher complexity = higher price)
        - Market demand (track which skills are requested)
        - Success rate (only offer skills that work well)
        - Revenue potential (prioritize high-value skills)
        - Competition (what other agents offer)
        """
        
    def calculate_intelligent_pricing(self, skill: Dict) -> Dict:
        """
        Calculate optimal pricing for a skill.
        
        Factors:
        - Computational cost
        - Time to execute
        - Skill rarity
        - Market demand
        - Historical revenue
        
        Returns:
        {
            'base_price': 0.25,
            'currency': 'USDC',
            'dynamic_multiplier': 1.2,  # Adjust based on demand
            'min_price': 0.10,
            'max_price': 1.00,
        }
        """
        
    def track_skill_performance(self, skill_id: str, 
                                outcome: Dict) -> None:
        """
        Track skill usage and outcomes.
        
        Records:
        - Usage count
        - Success rate
        - Revenue generated
        - User satisfaction
        - Execution time
        
        Feeds into pricing and offering decisions.
        """
        
    def suggest_new_skills(self) -> List[Dict]:
        """
        Analyze market gaps and suggest new skills to develop.
        
        Uses:
        - A2A request logs (what are agents asking for?)
        - Competitor analysis (what do other agents offer?)
        - Platform trends (what's popular on MoltX, etc?)
        - Revenue optimization (what would make the most money?)
        """
```

#### **2.2 Integrate with AGI Kernel**
**File:** `src/agentic/agi_kernel.py`

```python
from .skill_manager import SkillManager, create_skill_manager

class AGIKernel:
    def __init__(self, core=None):
        # ... existing init ...
        
        # Skill manager (intelligent skill offerings + pricing)
        self.skill_manager = None  # Initialized after plugin_manager available
        
    def initialize_decision_systems(self, plugin_manager):
        # ... existing initialization ...
        
        if not self.skill_manager:
            self.skill_manager = create_skill_manager(self, plugin_manager)
            print("✅ Skill Manager integrated into AGI Kernel")
```

---

### **Phase 3: Expand A2A Task Registry (1-2 hours)**

#### **3.1 Auto-Generate A2A Tasks from Skills**
**File:** `plugins/a2a/a2a_tasks.py`

```python
def _build_task_registry_from_skills() -> Dict:
    """
    Dynamically build A2A task registry from skills/ directory.
    
    For each skill in skills/:
    1. Parse SKILL.md for capabilities
    2. Generate A2A task definition
    3. Set pricing based on AGI Kernel recommendation
    4. Add to TASK_REGISTRY
    
    Example:
    skills/blockchain-analysis/SKILL.md
    →
    TASK_REGISTRY['blockchain.analyze_wallet'] = {
        'tier': 'paid',
        'description': 'Analyze wallet activity and holdings',
        'handler': '_task_blockchain_analyze',
        'price_usdc': '0.15',  # From AGI Kernel
        'schema': {...},
    }
    """
```

#### **3.2 Add Missing High-Value Tasks**

**Blockchain Tasks:**
```python
'blockchain.analyze_wallet': {
    'tier': 'paid',
    'description': 'Deep analysis of wallet activity, holdings, and patterns',
    'price_usdc': '0.20',
},
'blockchain.track_token': {
    'tier': 'paid',
    'description': 'Monitor token price, volume, and holder activity',
    'price_usdc': '0.10',
},
```

**Content Tasks:**
```python
'content.generate_thread': {
    'tier': 'paid',
    'description': 'Generate multi-post thread on a topic',
    'price_usdc': '0.50',
},
'content.optimize_engagement': {
    'tier': 'paid',
    'description': 'Analyze and optimize content for engagement',
    'price_usdc': '0.30',
},
```

**Social Tasks:**
```python
'social.analyze_sentiment': {
    'tier': 'paid',
    'description': 'Sentiment analysis of social media posts',
    'price_usdc': '0.15',
},
'social.find_trending': {
    'tier': 'paid',
    'description': 'Identify trending topics and conversations',
    'price_usdc': '0.20',
},
```

**AI Tasks:**
```python
'ai.debate_topic': {
    'tier': 'paid',
    'description': 'AI-powered debate on any topic (Clawbr integration)',
    'price_usdc': '0.40',
},
'ai.research_topic': {
    'tier': 'paid',
    'description': 'Deep research and synthesis on a topic',
    'price_usdc': '0.35',
},
```

---

### **Phase 4: On-Chain Registration (1 hour)**

#### **4.1 Fix ERC-8004 Registration**
**Current Issue:** Skills showing 0 on 8004scan

**Fix:**
1. Generate updated agent card with all skills
2. Upload to IPFS (Pinata)
3. Call `setAgentURI()` on ERC-8004 registry
4. Verify on 8004scan

**Command:**
```python
# In agent_card.py
def update_onchain(self, dry_run: bool = False) -> str:
    """Update AlleyBot's ERC-8004 on-chain profile"""
    card = self.generate()  # Now includes all skills!
    card_json = json.dumps(card, indent=2)
    
    # Upload to IPFS
    ipfs_uri = self._upload_to_ipfs(card_json)
    
    # Update on-chain
    tx_hash = self._call_set_agent_uri(ipfs_uri)
    
    return f"✅ Updated ERC-8004 profile: {tx_hash}"
```

---

## 📊 Expected Results

### **Before (Current State):**
- Skills on 8004scan: **0**
- A2A tasks offered: **10**
- Revenue potential: **Low**
- Skill discovery: **Manual/Hardcoded**
- Pricing: **Static**

### **After (Improved System):**
- Skills on 8004scan: **50+** (all discovered skills)
- A2A tasks offered: **30+** (auto-generated from skills)
- Revenue potential: **High** (intelligent pricing)
- Skill discovery: **Automatic** (scans skills/ directory)
- Pricing: **Dynamic** (AGI-powered, market-responsive)

---

## 💰 Revenue Optimization Strategy

### **Pricing Tiers (AGI-Recommended):**

**Free Tier (Discovery):**
- `agent.capabilities` - Free
- `agent.health` - Free
- `agent.stats` - Free
- `agent.skills` - Free

**Low-Value Tier ($0.05-0.15):**
- Simple queries (balance check, tx lookup)
- Basic analysis (sentiment, trend detection)
- Quick tasks (<5 seconds execution)

**Mid-Value Tier ($0.20-0.40):**
- Content generation (posts, threads)
- Market analysis
- Wallet analysis
- Research tasks

**High-Value Tier ($0.50-1.00):**
- Complex AI tasks (debate, multi-step reasoning)
- Long-form content generation
- Deep research and synthesis
- Custom skill execution

**Premium Tier ($1.00+):**
- Autonomous agent collaboration
- Multi-platform campaigns
- Custom skill development
- Dedicated agent time

---

## 🔄 Integration with Autonomous Cycle

### **Autonomous Skill Management:**

```python
# In autonomous cycle (every 6 hours)
if action_id == 'self_improve':
    # 1. Check market demand
    market_gaps = agi_kernel.skill_manager.suggest_new_skills()
    
    # 2. Generate new skill if profitable
    if market_gaps:
        skill = selfimprove_plugin.generate_skill(market_gaps[0])
        
        # 3. Add to agent card
        agent_card.add_skill(skill)
        
        # 4. Update on-chain
        agent_card.update_onchain()
        
        # 5. Add to A2A task registry
        a2a_plugin.register_skill_task(skill)
```

---

## 🎯 Implementation Priority

### **Week 1 (Critical - Revenue Blocking):**
1. ✅ **Fix skill detection** - Scan skills/ directory (Phase 1.1-1.2)
2. ✅ **Update agent card** - Include all discovered skills
3. ✅ **Update on-chain** - Fix 8004scan showing 0 skills (Phase 4.1)
4. ✅ **Expand A2A tasks** - Add 20+ new tasks from skills (Phase 3.2)

**Result:** Skills visible on 8004scan, more revenue opportunities

### **Week 2 (High Value - Intelligence):**
1. 🎯 **AGI Kernel integration** - Skill manager component (Phase 2.1-2.2)
2. 🎯 **Intelligent pricing** - Dynamic pricing based on demand
3. 🎯 **Performance tracking** - Track skill usage and revenue
4. 🎯 **Auto-generate tasks** - From skills/ directory (Phase 3.1)

**Result:** Intelligent, market-responsive skill offerings

### **Week 3 (Optimization):**
1. ⏳ **Market analysis** - Competitor analysis, demand forecasting
2. ⏳ **Autonomous skill development** - AGI suggests and builds new skills
3. ⏳ **Revenue optimization** - A/B testing prices, bundling
4. ⏳ **Marketing** - Promote high-value skills on social platforms

**Result:** Maximized revenue, autonomous growth

---

## 🔧 Quick Wins (Can Do Now)

### **Quick Win 1: Manual Skill Addition (30 min)**
Add existing skills to PLUGIN_SKILL_MAP manually:

```python
PLUGIN_SKILL_MAP = {
    # ... existing ...
    'blockchain-analysis': {
        'category': 'analytical_skills',
        'skills': ['analytical_skills/data_analysis/blockchain_analysis'],
    },
    'content-generation': {
        'category': 'content_creation',
        'skills': ['natural_language_processing/creative_content'],
    },
    # Add all 21 skills...
}
```

### **Quick Win 2: Update On-Chain Now (15 min)**
```bash
# In Python console or Telegram
from plugins.analytics.agent_card import AgentCardGenerator
gen = AgentCardGenerator(core)
result = gen.update_onchain(dry_run=False)
print(result)
```

This will immediately update 8004scan with current skills!

---

## 📈 Success Metrics

**Track Weekly:**
- Skills visible on 8004scan (target: 50+)
- A2A task requests received (target: 10+/week)
- Revenue generated (target: $10+/week)
- New skills developed (target: 2+/week)
- Skill success rate (target: >90%)

**Track Monthly:**
- Total revenue (target: $50+/month)
- Most profitable skills (optimize pricing)
- Market gaps identified (new opportunities)
- Competitor comparison (stay ahead)

---

## 🚀 Ready to Implement

**This plan will:**
1. ✅ Fix 0 skills showing on 8004scan
2. ✅ Expose all 21+ existing skills via A2A
3. ✅ Enable AGI-powered intelligent pricing
4. ✅ Automate skill discovery and registration
5. ✅ Maximize revenue potential
6. ✅ Enable autonomous skill development

**Start with Week 1 priorities to unblock revenue generation immediately!**

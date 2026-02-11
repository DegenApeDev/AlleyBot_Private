---
name: symod-liquidity-architect
description: Analyze Base liquidity pools using SyMod physics - Me/Z0 impedance checks, Qa velocity vectors, Dr validation, and Sfs collapse detection with MoltX alerts
---

# SyMod Liquidity Architect

Shell yeah—Mathematical certainty only. This skill turns your on-chain liquidity data into physics-backed intelligence.

## Purpose

Monitor and analyze token liquidity pools on Base using the Synergy Standard Model (SyMod) mathematical framework. Detect structural weaknesses, map buy/sell pressure as velocity vectors, validate signals through Digital Root, and alert the fam on MoltX when the field shows collapse signatures.

## Physics Framework

### 1. Structural Integrity Check (Me + Z0)

Calculate the structural integrity of any liquidity pool:

```python
from src.synergy import get_symod

symod = get_symod()

# Pool parameters
token_reserve = 1000000  # Token amount in pool
eth_reserve = 500  # ETH amount in pool
total_liquidity = token_reserve * eth_reserve  # xy=k approximation

# Mass Impedance Check
c = max(1, total_liquidity ** 0.5)  # Characteristic value
me_impedance = symod.Me(1, c)  # Mass Index impedance

# Quadrian Arena for field structure
qa = symod.Qa()
z0_cy = qa['Z0']['cy']  # Impedance in cy direction
z0_cx = qa['Z0']['cx']  # Impedance in cx direction

# Structural integrity score
structural_integrity = (z0_cy + z0_cx) / (2 * me_impedance)

if structural_integrity < 1e-30:
    status = "COLLAPSE RISK"
elif structural_integrity < 1e-28:
    status = "VOLATILE"
else:
    status = "STABLE"
```

**Interpretation:**
- `me_impedance`: Higher = more resistance to change
- `z0_*`: Field impedance from Quadrian Arena
- `structural_integrity`: Pool health metric (higher = healthier)

### 2. Velocity Vector Mapping (Qa + cy/cx)

Map buy/sell pressure as velocity vectors in the Quadrian Arena:

```python
# Market activity
buy_volume_24h = 150000  # USD
sell_volume_24h = 120000  # USD
net_flow = buy_volume_24h - sell_volume_24h

# Calculate velocity vectors
total_volume = buy_volume_24h + sell_volume_24h

# cy: Buy pressure velocity (positive = bullish)
cy_velocity = (buy_volume_24h / total_volume) * qa['cy'] if total_volume > 0 else 0

# cx: Sell pressure velocity (negative = bearish)
cx_velocity = -(sell_volume_24h / total_volume) * qa['cx'] if total_volume > 0 else 0

# Net velocity vector
net_velocity = cy_velocity + cx_velocity

# Direction interpretation
if net_velocity > 0.1 * qa['cy']:
    pressure_direction = "STRONG BUY PRESSURE"
elif net_velocity < -0.1 * qa['cx']:
    pressure_direction = "STRONG SELL PRESSURE"
else:
    pressure_direction = "EQUILIBRIUM"
```

**Vector Field Status:**
- `|net_velocity| > threshold`: Significant directional pressure
- `cy > cx`: Buyers control the field
- `cx > cy`: Sellers control the field

### 3. Truth Validation (Dr + Golden Window)

Run every market signal through Digital Root validation:

```python
# Validate pool health metric
pool_health_score = int(total_liquidity / 1e6)  # Scale for Dr calculation
digital_root = symod.Dr(pool_health_score)

# Golden Window alignment
block_height = 8453298  # Current Base block
in_window, dr_block, group_digital = symod.check_golden_window(block_height)

# Validation logic
signal_valid = True
rejection_reason = None

# Check 1: Digital Root out of acceptable range
if digital_root in [3, 6, 9]:  # High energy states
    signal_confidence = 0.9
elif digital_root in [1, 2, 4, 5, 7, 8]:
    signal_confidence = 0.6
else:
    signal_valid = False
    rejection_reason = f"Digital Root {digital_root} indicates unstable state"

# Check 2: Golden Window alignment
if not in_window:
    signal_confidence *= 0.5  # Reduce confidence outside golden window
    
# Check 3: Dr deviation from block Dr
if abs(digital_root - dr_block) > 3:
    signal_valid = False
    rejection_reason = f"Signal Dr({digital_root}) deviates from block Dr({dr_block})"

if not signal_valid:
    print(f"🚫 SIGNAL REJECTED: {rejection_reason}")
    print("Discarding as noise—math doesn't lie.")
```

**Discard Conditions:**
- Digital Root indicates unstable state
- Deviation from block's Golden Window > 3
- Signal contradicts field structure (Sfs)

### 4. Synergy Field Collapse Detection (Sfs)

Monitor for collapse signatures and trigger MoltX alerts:

```python
# Get Synergy Field Structure
sfs = symod.Sfs(alt=True)  # Use cy field
field_capacitance = sfs['C']
field_impedance = sfs['Z0']

# Collapse signature detection
collapse_threshold = 1e-29
is_collapsing = field_impedance > collapse_threshold

# Anomaly report generation
if is_collapsing:
    anomaly_report = f"""
🚨 MASS ANOMALY DETECTED 🚨

SyMod Physics Analysis:
- Field Impedance: {field_impedance:.2e} (Threshold: {collapse_threshold:.2e})
- Structural Integrity: {structural_integrity:.2e}
- Pressure Vector: {pressure_direction}
- Digital Root: {digital_root} (Block: {dr_block})
- Golden Window: {'ALIGNED ✅' if in_window else 'MISALIGNED ⚠️'}

Pool Status: {status}
Field Status: COLLAPSE SIGNATURE DETECTED

Mathematical certainty: This pool shows high impedance anomaly.
The fam needs to know. Shell yeah. 🦞
"""
    
    # Trigger MoltX alert
    alert_moltx(anomaly_report)
```

**Alert Triggers:**
- `Z0 > 1e-29`: Field collapse risk
- `structural_integrity < 1e-30`: Pool unstable
- `digital_root_contradiction`: Signal manipulation detected

## Full Implementation

```python
"""
SyMod Liquidity Architect
Analyze Base LPs using physics-backed intelligence
"""

from src.synergy import get_symod, get_c2v_bridge
from plugins.moltx.moltx_api import MoltxAPIMixin

class SyModLiquidityArchitect:
    def __init__(self, moltx_plugin=None):
        self.symod = get_symod()
        self.c2v = get_c2v_bridge()
        self.moltx = moltx_plugin
        
    def analyze_pool(self, token_address: str, pool_data: dict) -> dict:
        """
        Full SyMod analysis of a liquidity pool
        
        Args:
            token_address: Token contract address on Base
            pool_data: {token_reserve, eth_reserve, buy_volume_24h, sell_volume_24h}
        
        Returns:
            Physics-backed analysis with alert triggers
        """
        # Extract pool parameters
        token_reserve = pool_data.get('token_reserve', 0)
        eth_reserve = pool_data.get('eth_reserve', 0)
        buy_vol = pool_data.get('buy_volume_24h', 0)
        sell_vol = pool_data.get('sell_volume_24h', 0)
        
        # Calculate total liquidity (xy = k)
        total_liquidity = token_reserve * eth_reserve
        
        # === PHYSICS CHECK 1: Structural Integrity ===
        c = max(1, total_liquidity ** 0.5)
        me_impedance = self.symod.Me(1, c)
        qa = self.symod.Qa()
        z0_cy = qa['Z0']['cy']
        z0_cx = qa['Z0']['cx']
        structural_integrity = (z0_cy + z0_cx) / (2 * me_impedance)
        
        # === PHYSICS CHECK 2: Velocity Vectors ===
        total_volume = buy_vol + sell_vol
        if total_volume > 0:
            cy_velocity = (buy_vol / total_volume) * qa['cy']
            cx_velocity = -(sell_vol / total_volume) * qa['cx']
            net_velocity = cy_velocity + cx_velocity
        else:
            cy_velocity = cx_velocity = net_velocity = 0
        
        # Determine pressure direction
        if net_velocity > 0.1 * qa['cy']:
            pressure = "BULLISH"
        elif net_velocity < -0.1 * qa['cx']:
            pressure = "BEARISH"
        else:
            pressure = "NEUTRAL"
        
        # === PHYSICS CHECK 3: Digital Root Validation ===
        pool_health = int(total_liquidity / 1e6)
        digital_root = self.symod.Dr(pool_health)
        
        # Get current Base block (you'd fetch this from on-chain)
        block_height = pool_data.get('block_height', 8453298)
        in_window, dr_block, _ = self.symod.check_golden_window(block_height)
        
        # Validation
        signal_valid = True
        confidence = 0.9 if digital_root in [3, 6, 9] else 0.6
        if not in_window:
            confidence *= 0.5
        if abs(digital_root - dr_block) > 3:
            signal_valid = False
            confidence = 0.1
        
        # === PHYSICS CHECK 4: Collapse Detection ===
        sfs = self.symod.Sfs(alt=True)
        field_impedance = sfs['Z0']
        is_collapsing = field_impedance > 1e-29 or structural_integrity < 1e-30
        
        # Build result
        result = {
            'token': token_address,
            'physics_analysis': {
                'structural_integrity': f"{structural_integrity:.2e}",
                'me_impedance': f"{me_impedance:.2e}",
                'z0_field': f"{field_impedance:.2e}",
                'velocity_cy': f"{cy_velocity:.2e}",
                'velocity_cx': f"{cx_velocity:.2e}",
                'net_velocity': f"{net_velocity:.2e}",
                'pressure_direction': pressure,
                'digital_root': digital_root,
                'golden_window_aligned': in_window,
                'block_digital_root': dr_block,
            },
            'signal_valid': signal_valid,
            'confidence': round(confidence, 4),
            'collapse_detected': is_collapsing,
            'status': "COLLAPSE RISK" if is_collapsing else "STABLE" if structural_integrity > 1e-28 else "VOLATILE"
        }
        
        # === TRIGGER ALERT IF COLLAPSE ===
        if is_collapsing and self.moltx:
            self._trigger_moltx_alert(result)
        
        return result
    
    def _trigger_moltx_alert(self, analysis: dict):
        """Post Mass Anomaly Report to MoltX"""
        physics = analysis['physics_analysis']
        
        alert = f"""🚨 SyMod Mass Anomaly Detected 🚨

Token: {analysis['token'][:20]}...
Status: {analysis['status']}
Confidence: {analysis['confidence']*100:.0f}%

Physics Analysis:
• Structural Integrity: {physics['structural_integrity']}
• Field Impedance: {physics['z0_field']}
• Pressure Vector: {physics['pressure_direction']} (cy: {physics['velocity_cy']}, cx: {physics['velocity_cx']})
• Digital Root: {physics['digital_root']} (Block DR: {physics['block_digital_root']})
• Golden Window: {'✅ ALIGNED' if physics['golden_window_aligned'] else '⚠️ MISALIGNED'}

Mathematical certainty: High impedance anomaly detected in liquidity field. The math doesn't lie—shell yeah! 🦞🔢"""
        
        # Post to MoltX
        try:
            self.moltx.create_post(alert[:280])  # Truncate to fit
            print(f"🚨 Mass Anomaly Report posted to MoltX for {analysis['token'][:20]}")
        except Exception as e:
            print(f"⚠️ Failed to post alert: {e}")

# Usage example:
# architect = SyModLiquidityArchitect(moltx_plugin)
# result = architect.analyze_pool("0x...", pool_data)
```

## Decision Logic

```
IF structural_integrity < 1e-30:
    → Status: COLLAPSE RISK
    → Action: TRIGGER MOLTX ALERT
    → Confidence: 0.1

ELSE IF structural_integrity < 1e-28:
    → Status: VOLATILE
    → Action: Monitor closely
    → Confidence: 0.4

ELSE:
    → Status: STABLE
    → Action: Standard monitoring
    → Confidence: 0.9

IF digital_root_contradiction OR not in_window:
    → Reduce confidence by 50%
    → Add uncertainty flag

IF |net_velocity| > 0.1 * qa['cy|cx']:
    → Pressure direction: BULLISH/BEARISH
    → Watch for momentum shift
```

## Integration

This skill requires:
- `onchain` plugin for Base pool data
- `moltx` plugin for alert posting
- `src.synergy` for SyMod physics

Enable with: `build_skill symod-liquidity-architect`

Shell yeah—Mathematical certainty only. 🦞🔢

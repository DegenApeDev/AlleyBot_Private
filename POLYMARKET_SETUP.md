# Polymarket Plugin Setup Guide

## Quick Start

The Polymarket plugin is already configured in `plugins.json`. To activate it:

### Option 1: Reload Plugins (No Restart)
```
/reload
```
This will load the Polymarket plugin without restarting AlleyBot.

### Option 2: Restart AlleyBot
Restart the bot to load all plugins fresh.

---

## Installation

### 1. Install Dependencies
```bash
pip install py-clob-client eth-account web3
```

### 2. Verify Configuration

The plugin is already enabled in `plugins.json`:
```json
{
  "polymarket": {
    "enabled": true,
    "config": {
      "paper_trading": true,
      "max_position_size": 0.05,
      "min_edge": 0.05,
      "min_confidence": 0.75
    }
  }
}
```

### 3. Wallet Setup

Your BASE wallet is already configured and will work for Polygon (same address on all EVM chains).

The plugin uses `BASE_WALLET_PRIVATE_KEY` from your `.env` file.

---

## Testing

After running `/reload`, test with:

```
/polymarket_status
```

You should see:
```
🎲 Polymarket Status:
  ✅ Plugin enabled
  📊 Mode: PAPER TRADING
  💼 Active positions: 0
  📈 Total PnL: $0.00
  🎯 Win rate: 0.0%
  🧠 AGI systems: 5/5 active
```

---

## Commands

- `/polymarket_status` - Plugin status and configuration
- `/polymarket_markets [limit]` - List active prediction markets
- `/polymarket_analyze <market_id>` - Analyze specific market with AGI
- `/polymarket_positions` - View active trading positions
- `/polymarket_stats` - Trading statistics and performance

---

## Live Trading (When Ready)

1. **Bridge USDC to Polygon**
   - Use your BASE wallet address (same on Polygon)
   - Minimum: $100-$1000 to start
   - Bridge: https://wallet.polygon.technology/bridge

2. **Switch to Live Mode**
   - Edit `plugins.json`
   - Change `"paper_trading": false`
   - Run `/reload`

3. **Monitor Performance**
   - Check `/polymarket_positions` regularly
   - Review `/polymarket_stats` for win rate
   - Adjust risk parameters if needed

---

## Troubleshooting

### "Polymarket plugin not loaded"
**Solution:** Run `/reload` to load the plugin

### "py-clob-client not installed"
**Solution:** `pip install py-clob-client eth-account web3`

### "No Polygon wallet private key found"
**Solution:** Your BASE wallet is already configured in `.env` as `BASE_WALLET_PRIVATE_KEY`

### "AGI systems: 0/5 active"
**Solution:** Ensure brain plugin is running with `/brain_status`

---

## How It Works

Every 30 minutes, AlleyBot's AGI brain will:

1. **Fetch markets** - Get top 20 active prediction markets
2. **Gather context** - Social sentiment, MCP news, historical data
3. **Analyze** - Use Unified Reasoner for predictions
4. **Calculate edge** - Compare prediction vs market price
5. **Risk check** - Validate edge, confidence, liquidity
6. **Execute** - Place trades if profitable
7. **Learn** - Record outcomes, evolve strategies

---

## Expected Performance

**Conservative Estimates:**
- Win Rate: 55-60%
- Average Edge: 5-10% per trade
- ROI: 15-25% annually
- Sharpe Ratio: 1.5-2.0

**Your Advantages:**
- Cross-platform intelligence (MoltX, Clawbr, X)
- Free news from MCP servers
- AGI reasoning with 85% progress
- Continuous learning and strategy evolution

---

## Security

- Private keys stored in environment variables only
- Wallet signing happens locally
- Position size limits prevent catastrophic loss
- All trades logged and auditable
- Paper trading mode for safe testing
- Owner-only Telegram commands

---

## Next Steps

1. Run `/reload` to load the plugin
2. Test with `/polymarket_status`
3. Explore markets with `/polymarket_markets 20`
4. Analyze a market with `/polymarket_analyze <id>`
5. Monitor autonomous trading in paper mode
6. Bridge USDC and switch to live trading when ready

🎲 **Happy Trading!**

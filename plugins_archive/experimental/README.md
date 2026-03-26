# Archived Experimental Plugins

These plugins were archived on 2026-03-23 during Week 3 cleanup as they had zero active references in the codebase.

## Archived Plugins

### voice_emotion
- **Status:** Experimental, never integrated
- **Reason:** No references in codebase
- **Files:** 2 Python files

### best_crypto_swap_price
- **Status:** Experimental price comparison tool
- **Reason:** No active usage
- **Files:** 2 Python files

### fluid_lending
- **Status:** DeFi lending integration experiment
- **Reason:** No active usage
- **Files:** 2 Python files

### avax_trading
- **Status:** Avalanche trading plugin
- **Reason:** No active usage, focus shifted to Base/Solana
- **Files:** 2 Python files

### base_yield_hunter
- **Status:** Base chain yield farming experiment
- **Reason:** No active usage
- **Files:** 5 Python files

### clawgame
- **Status:** Game integration experiment
- **Reason:** No active usage
- **Files:** 2 Python files

## Restoration

If any of these plugins are needed in the future, they can be restored from this archive by:

```bash
mv plugins_archive/experimental/[plugin_name] plugins/
```

Then re-enable in `plugin_config.json` if needed.

## Note on Trading Plugins

The following trading plugins were **NOT** archived as they are actively used in `plugins/telegram/trading_commands.py`:
- `solana_trading` - Used for Solana token swaps
- `base_trading` - Used for Base chain swaps
- `trading_analytics` - Used for trade tracking

These remain in the active `plugins/` directory.

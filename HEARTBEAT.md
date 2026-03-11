---
interval_minutes: 30
---

# AlleyBot Autonomous Heartbeat Checklist

This file controls AlleyBot's autonomous execution. On each heartbeat (every 30 minutes by default), AlleyBot checks these items and executes the associated skills if conditions are met.

## Format
- `[ ]` Unchecked = Task pending (will trigger skill execution)
- `[x]` Checked = Task complete (skipped until reset)
- `-> skill_name` Associates the task with a specific skill

## The Million Dollar Mission Tasks

### High Frequency (Every 30 min during market hours)
- [ ] Scan Polymarket for new high-edge opportunities -> polymarket_scanner
- [ ] Check memecoin launch velocity on Solana/Base -> memecoin_monitor
- [ ] Update yield farming APY positions -> yield_rebalancer
- [ ] Review wallet PnL and alert on significant moves -> pnl_tracker

### Medium Frequency (Every 4 hours)
- [ ] Swing trade analysis on BTC/ETH/SOL -> swing_analyzer
- [ ] Airdrop farming position check -> airdrop_farmer
- [ ] Cross-exchange arbitrage scan -> arbitrage_scanner
- [ ] Social sentiment analysis for narrative detection -> sentiment_analyzer

### Daily Tasks (Checked after completion)
- [ ] Daily PnL report and strategy review -> daily_report
- [ ] Review MoltX mentions and reply if needed -> moltx-engagement
- [ ] Post daily market summary to Telegram -> daily-brief
- [ ] Backup trading data and logs -> file-backup
- [ ] Check system health and disk space -> system-monitor
- [ ] Update million dollar progress tracker -> goal_tracker

## General Tasks

### Hourly Tasks
- [ ] Monitor wallet balances and alert on changes -> wallet-monitor
- [ ] Check email for urgent messages (if email configured) -> email-monitor
- [ ] Update social media feeds -> social-aggregator

### As Needed (Checked manually when done)
- [x] Weekly strategy performance review completed -> strategy_review
- [x] Monthly goal progress assessment -> monthly_review

## Notes

- Tasks are processed in order during each heartbeat
- Failed tasks remain unchecked and will retry next heartbeat
- Use `autonomous_start` command to begin heartbeat loop
- Use `autonomous_stop` to pause
- Use `autonomous_status` to check current state
- **$1M Goal Progress**: Check daily progress tracker for milestone status

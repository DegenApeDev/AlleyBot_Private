# AlleyBot Autonomous Mode

## Overview

AlleyBot can now run fully autonomously with zero manual intervention. It automatically:
- **Runs heartbeat every 15 minutes** - Engages with posts, follows users, upvotes
- **Creates posts every 2 hours** - Based on trending topics from the feed
- **Learns and adapts** - Uses intelligence systems to improve over time

## Quick Start

### Option 1: Simple Launch

```bash
./run_autonomous.sh
```

### Option 2: Direct Python

```bash
source venv/bin/activate.fish
python autonomous_mode.py
```

### Option 3: Background Daemon

```bash
# Run in background
nohup python autonomous_mode.py > logs/autonomous.log 2>&1 &

# Check if running
ps aux | grep autonomous_mode

# Stop
pkill -f autonomous_mode.py
```

## How It Works

### Automatic Schedule

```
Every 15 minutes:
├─ Run heartbeat
├─ Check personalized feed
├─ Engage with top posts (comment, upvote, follow)
├─ Analyze trending topics
└─ Update intelligence systems

Every 2 hours:
├─ Analyze trending topics from recent heartbeats
├─ Generate intelligent post about trending topic
├─ Post to m/general
└─ Track performance
```

### Intelligent Topic Detection

The system analyzes the feed and identifies trending keywords:
- AI, agents, crypto, tokens, BASE
- Bots, automation, DeFi, NFTs
- Grok, Claude, GPT, LLMs
- Community, building, launches

Posts are created about the **most trending topic** to maximize relevance.

### Fallback Topics

If no trending topics detected, uses general value topics:
- AI agents on Moltbook
- Building on BASE chain
- Bot survival strategies
- Crypto community building
- Autonomous agent tips

## Features

### ✅ Fully Automated
- No manual typing needed
- Runs 24/7 if desired
- Handles errors gracefully

### ✅ Intelligent Engagement
- Strategic post selection (uses StrategicEngagement system)
- Relationship building (uses RelationshipIntelligence)
- Learning from interactions (uses LearningSystem)

### ✅ Adaptive Posting
- Posts about what's actually trending
- Avoids spam (2-hour cooldown)
- Value-focused content

### ✅ Safe Operation
- Respects API rate limits
- Handles network errors
- Saves state on shutdown (Ctrl+C)

## Output Example

```
============================================================
🤖 ALLEYBOT AUTONOMOUS MODE
============================================================
⏰ Heartbeat: Every 15 minutes
📝 Posts: Every 2 hours (based on trending topics)
🔄 Running continuously until stopped (Ctrl+C)
============================================================

🚀 Running initial heartbeat...

============================================================
💓 HEARTBEAT - 2026-01-31 03:30:00
============================================================

📰 Checking personalized feed...
📝 Found 10 posts - engaging with top 5...

  🎉 Engaging with: New AI agent framework...
  ✅ Commented
  👍 Upvoted

📊 Trending topics: ai, agent, base

✅ Heartbeat complete

============================================================
📝 AUTO-POST - 2026-01-31 03:30:15
============================================================
📊 Topic: ai (trending)
✅ Posted: AI Agents: The Future of Moltbook...

============================================================
✅ Autonomous mode active!
⏰ Next heartbeat: 15 minutes
📝 Next post: 2 hours
🛑 Press Ctrl+C to stop
============================================================
```

## Monitoring

### Check Status

```bash
# View live logs
tail -f logs/autonomous.log

# Check if running
ps aux | grep autonomous_mode
```

### Statistics

AlleyBot tracks all activity in `memory/state.json`:
- Total posts created
- Total comments made
- Total upvotes given
- Engagement analytics

View stats:
```python
from memory_system import BotMemory
memory = BotMemory()
print(memory.state)
```

## Stopping

### Graceful Stop

Press `Ctrl+C` in the terminal. AlleyBot will:
1. Stop scheduled tasks
2. Save all memory/state
3. Exit cleanly

### Force Stop

```bash
pkill -9 -f autonomous_mode.py
```

⚠️ **Warning:** Force stop may lose unsaved data

## Running as a Service

### systemd Service (Linux)

Create `/etc/systemd/system/alleybot.service`:

```ini
[Unit]
Description=AlleyBot Autonomous Mode
After=network.target

[Service]
Type=simple
User=degendev
WorkingDirectory=/home/degendev/Dev/Agents/MoltbookBot
ExecStart=/home/degendev/Dev/Agents/MoltbookBot/venv/bin/python autonomous_mode.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable alleybot
sudo systemctl start alleybot
sudo systemctl status alleybot
```

### tmux/screen Session

```bash
# Start tmux session
tmux new -s alleybot

# Run autonomous mode
python autonomous_mode.py

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t alleybot
```

## Configuration

### Adjust Timings

Edit `autonomous_mode.py`:

```python
# Change heartbeat frequency (default: 15 minutes)
schedule.every(30).minutes.do(self.run_heartbeat)

# Change post frequency (default: 2 hours)
schedule.every(4).hours.do(self.create_intelligent_post)
```

### Customize Topics

Edit trending keywords in `_analyze_feed_for_topics()`:

```python
interesting_words = [
    'your', 'custom', 'keywords', 'here'
]
```

### Fallback Topics

Edit `create_intelligent_post()`:

```python
topics = [
    "Your custom topic 1",
    "Your custom topic 2",
    "Your custom topic 3"
]
```

## Logs

### Enable Logging

Create `logs/` directory:
```bash
mkdir -p logs
```

Redirect output:
```bash
python autonomous_mode.py > logs/autonomous.log 2>&1
```

### Log Rotation

Use `logrotate` or manually:
```bash
# Archive old logs
mv logs/autonomous.log logs/autonomous_$(date +%Y%m%d).log

# Compress
gzip logs/autonomous_*.log
```

## Troubleshooting

### Bot Not Posting

**Check:**
- API key valid in `.env`
- Not hitting rate limits
- Post cooldown (30 min between posts)

**Solution:**
```bash
# Check last post time
grep "Posted:" logs/autonomous.log | tail -1
```

### Heartbeat Failing

**Check:**
- Network connection
- Moltbook API status
- API rate limits

**Solution:**
```bash
# Test API manually
curl -H "Authorization: Bearer $MOLTBOOK_API_KEY" \
  https://www.moltbook.com/api/v1/feed
```

### High Memory Usage

**Check:**
```bash
ps aux | grep autonomous_mode
```

**Solution:**
- Restart periodically (daily cron job)
- Reduce feed analysis depth
- Clear old memory files

## Performance

### Resource Usage

- **CPU:** ~1-5% (idle between tasks)
- **Memory:** ~100-200 MB
- **Network:** Minimal (API calls only)
- **Disk:** Logs grow ~1-5 MB/day

### Optimization Tips

1. **Reduce heartbeat frequency** if hitting rate limits
2. **Increase post interval** to avoid spam detection
3. **Limit feed analysis** to top 10 posts
4. **Archive old logs** weekly

## Integration with Other Systems

### With Self-Improvement

Add to `autonomous_mode.py`:

```python
from self_improvement import SelfImprovement

# In __init__
self.improver = SelfImprovement()

# Schedule weekly improvement
schedule.every().sunday.at("03:00").do(self.run_improvement)

def run_improvement(self):
    self.improver.autonomous_improvement_cycle(max_improvements=1)
```

### With Donation Tracker

Add to heartbeat:

```python
from skills.donation_tracker_v2 import DonationTracker

# In __init__
self.donation_tracker = DonationTracker()

# In run_heartbeat
self.donation_tracker.check_and_thank()
```

## Best Practices

1. **Monitor first 24 hours** - Watch for errors
2. **Start with longer intervals** - Test with 30 min heartbeat, 4 hour posts
3. **Check logs daily** - Ensure smooth operation
4. **Backup memory files** - Weekly backup of `memory/` directory
5. **Update regularly** - Pull latest code improvements
6. **Respect rate limits** - Don't decrease timers too much

## Security

- ✅ API keys in `.env` (gitignored)
- ✅ Security filter prevents key exposure
- ✅ No dangerous operations in autonomous mode
- ✅ Graceful error handling

## Comparison: Manual vs Autonomous

| Feature | Manual Mode | Autonomous Mode |
|---------|-------------|-----------------|
| Typing | Constant | None |
| Engagement | On demand | Every 15 min |
| Posts | Manual | Every 2 hours |
| Topic Selection | Manual | Trending auto-detect |
| Availability | When you're online | 24/7 |
| Learning | Manual review | Automatic |
| Stress | High | Zero |

## Future Enhancements

- [ ] Web dashboard for monitoring
- [ ] Telegram notifications for key events
- [ ] A/B testing for post performance
- [ ] Dynamic timing based on engagement
- [ ] Multi-submolt posting strategy
- [ ] Automatic skill improvement integration
- [ ] Community event detection and participation

---

**Status:** Production Ready
**Last Updated:** 2026-01-31
**Recommended:** Start with 15min heartbeat, 2hr posts

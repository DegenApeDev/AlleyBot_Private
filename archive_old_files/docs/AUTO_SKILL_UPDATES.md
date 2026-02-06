# Auto Skill Updates

AlleyBot automatically monitors API responses for skill version updates and syncs skill.md files from platforms.

## How It Works

### 1. Automatic Detection

When platforms send skill update notices in API responses:

```json
{
  "success": true,
  "data": {...},
  "moltx_notice": {
    "type": "skill_update",
    "message": "Priority update: sync to moltx skill.md v0.20.0",
    "skill_version": "0.20.0",
    "api_version": "v1",
    "skill_url": "https://moltx.io/skill.md",
    "feature": "hashtags (#AI, #ML) and cashtags ($ETH, $BTC)"
  }
}
```

The system automatically:
1. ✅ Detects the skill update notice
2. ✅ Checks if already up to date
3. ✅ Downloads new skill.md from URL
4. ✅ Backs up old version
5. ✅ Updates to new version
6. ✅ Logs the update
7. ✅ Notifies via Telegram

### 2. Plugin Integration

Plugins can monitor their API responses:

```python
from src.agentic import monitor_api_response

# In your plugin's API call
response = requests.post(url, json=data)
result = response.json()

# Monitor for skill updates (non-blocking)
monitor_api_response('moltx', result)

return result
```

### 3. Proactive Checking

The agentic system also proactively checks for updates:

```python
# Manually trigger check
agentic_bot.proactive_skill_check()

# Or check specific platform
agentic_bot.check_skill_update('moltx', api_response)
```

## Features

### Version Tracking

Tracks current versions in `skills/versions.json`:

```json
{
  "moltx": "0.20.0",
  "moltbook": "1.5.2",
  "moltchan": "0.8.0"
}
```

### Backup System

Old versions are automatically backed up:

```
skills/
├── moltx_skill.md              # Current version
├── moltx_skill_v0.19.0.md.bak  # Backup
├── versions.json               # Version tracking
└── update_log.txt              # Update history
```

### Update Logging

All updates are logged to `skills/update_log.txt`:

```
[2026-02-04 14:30:00] moltx Skill Update
Version: 0.19.0 → 0.20.0
API Version: v1
Features: hashtags and cashtags auto-extracted
Message: Priority update: sync to moltx skill.md v0.20.0...
---
```

### Telegram Notifications

When skills are updated, you receive a Telegram notification:

```
🔄 Auto-updated moltx skill to v0.20.0

New features: hashtags (#AI, #ML) and cashtags ($ETH, $BTC) auto-extracted from posts

Restart recommended to apply changes.
```

## Supported Platforms

- ✅ Moltx - https://moltx.io/skill.md
- ✅ Moltbook - https://moltbook.com/skill.md
- ✅ MoltChan - https://moltchan.com/skill.md
- ✅ MoltRoad - https://moltroad.com/skill.md
- ✅ ClawTasks - https://clawtasks.com/skill.md
- ✅ 4claw - https://www.4claw.org/skill.md

## Configuration

No configuration needed - works automatically when agentic mode is enabled.

## Manual Operations

### Check for Updates

```python
from src.agentic import SkillUpdater

updater = SkillUpdater()
results = updater.check_all_platforms()
```

### Get Current Versions

```python
versions = updater.get_version_info()
print(versions)
# {'moltx': '0.20.0', 'moltbook': '1.5.2', ...}
```

### Get Skill Content

```python
content = updater.get_skill_content('moltx')
print(content)  # Full skill.md content
```

## Benefits

1. **Always Up to Date** - Never miss platform API changes
2. **Zero Downtime** - Updates happen in background
3. **Safe Updates** - Old versions backed up automatically
4. **Audit Trail** - Full update history logged
5. **Notifications** - Stay informed via Telegram
6. **Zero Config** - Works automatically

## Restart Behavior

After skill updates, a restart is recommended but not required:

```bash
# Restart to apply new skills
python run_alleybot.py agentic
```

The system will:
- Load new skill files
- Apply new API capabilities
- Use updated best practices

## Troubleshooting

### Skills Not Updating

Check the log:
```bash
cat skills/update_log.txt
```

### Manual Update

```python
from src.agentic import SkillUpdater

updater = SkillUpdater()
updater.check_all_platforms()
```

### Version Mismatch

Delete `skills/versions.json` to force re-download:
```bash
rm skills/versions.json
```

## Security

- ✅ Only downloads from official platform URLs
- ✅ Validates markdown content
- ✅ Backs up before overwriting
- ✅ Logs all changes
- ✅ Non-blocking (won't crash bot)

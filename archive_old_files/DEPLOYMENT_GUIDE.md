# AlleyBot Production Deployment Guide

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.10+
python --version

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Dependencies
pip install -r requirements.txt
```

### Environment Setup
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Required Environment Variables:**
```bash
# AI Models
DEEPSEEK_API_KEY=sk-xxxxx           # DeepSeek API key
XAI_API_KEY=xai-xxxxx               # Grok-4.1 API key

# Telegram
TELEGRAM_BOT_TOKEN=xxxxx            # Bot token from @BotFather
TELEGRAM_OWNER_ID=6172568442        # Your Telegram user ID

# Moltx Platform
MOLTX_API_KEY=xxxxx                 # Moltx API key
MOLTX_USERNAME=AlleyBot             # Moltx username
MOLTX_PASSWORD=xxxxx                # Moltx password

# Optional
MOLTBOOK_API_KEY=xxxxx              # MoltBook API key
MOLTCHAN_API_KEY=xxxxx              # MoltChan API key
MOLTROAD_API_KEY=xxxxx              # MoltRoad API key
CLAWTASKS_API_KEY=xxxxx             # ClawTasks API key
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   AlleyBot Production                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │   Telegram   │──────▶│ Event Queue  │                │
│  │   Webhook    │      │ (asyncio)    │                │
│  └──────────────┘      └──────┬───────┘                │
│                               │                          │
│  ┌──────────────┐            │                          │
│  │  Scheduled   │────────────┤                          │
│  │    Tasks     │            │                          │
│  └──────────────┘            ▼                          │
│                        ┌─────────────┐                  │
│                        │ Agent Cycle │                  │
│                        └──────┬──────┘                  │
│                               │                          │
│         ┌─────────────────────┼─────────────────────┐   │
│         │                     │                     │   │
│         ▼                     ▼                     ▼   │
│  ┌────────────┐      ┌──────────────┐      ┌──────────┐│
│  │  Session   │      │ Model Router │      │  Skills  ││
│  │  Manager   │      │ DeepSeek/Grok│      │  System  ││
│  └────────────┘      └──────────────┘      └──────────┘│
│         │                     │                     │   │
│         └─────────────────────┴─────────────────────┘   │
│                               │                          │
│                               ▼                          │
│                        ┌─────────────┐                  │
│                        │  Response   │                  │
│                        └─────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Deployment Options

### Option 1: Local Development
```bash
# Start production mode
python run_alleybot.py autonomous

# Or specify mode explicitly
python -c "from alleybot_core import AlleyBotCore; core = AlleyBotCore(); core.run_autonomous(mode='production')"
```

### Option 2: Background Service (systemd)
```bash
# Create service file
sudo nano /etc/systemd/system/alleybot.service
```

```ini
[Unit]
Description=AlleyBot Production Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/MoltbookBot
Environment="PATH=/path/to/MoltbookBot/venv/bin"
ExecStart=/path/to/MoltbookBot/venv/bin/python run_alleybot.py autonomous
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable alleybot
sudo systemctl start alleybot

# Check status
sudo systemctl status alleybot

# View logs
sudo journalctl -u alleybot -f
```

### Option 3: Docker Container
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run_alleybot.py", "autonomous"]
```

```bash
# Build and run
docker build -t alleybot:production .
docker run -d --name alleybot --env-file .env alleybot:production

# View logs
docker logs -f alleybot
```

### Option 4: Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  alleybot:
    build: .
    container_name: alleybot_production
    env_file: .env
    volumes:
      - ./src/config/sessions:/app/src/config/sessions
      - ./logs:/app/logs
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 🔧 Configuration

### Scheduled Task Intervals

Edit `src/agents/event_runner.py`:

```python
# Post intelligent content every 2 hours
if loop_count % 120 == 0:  # 120 loops * 60s = 2 hours
    await self.queue_event(...)

# Browse and engage every 30 minutes
if loop_count % 30 == 0:   # 30 loops * 60s = 30 minutes
    await self.queue_event(...)

# Analyze trending every hour
if loop_count % 60 == 0:   # 60 loops * 60s = 1 hour
    await self.queue_event(...)
```

### Model Routing Thresholds

Edit `src/config/models.py`:

```python
# DeepSeek configuration (fast, <4000 tokens)
self.deepseek = ModelConfig(
    name="deepseek-chat",
    token_threshold=4000  # Adjust threshold
)

# Grok-4.1-reasoning configuration (heavy reasoning, >=4000 tokens)
self.grok = ModelConfig(
    name="grok-4-1-fast-reasoning",
    token_threshold=4000  # Adjust threshold
)
```

### Session Cleanup

Edit `src/agents/session_manager.py`:

```python
# Clean up sessions older than N days
await self.cleanup_old_sessions(days=30)  # Adjust retention
```

---

## 📊 Monitoring & Logging

### Log Files
```bash
# Application logs
tail -f logs/alleybot.log

# Error logs
tail -f logs/error.log

# Event processing logs
grep "Agent Cycle" logs/alleybot.log
```

### Monitoring Commands
```bash
# Check if running
ps aux | grep run_alleybot.py

# Memory usage
ps -o pid,user,%mem,command ax | grep run_alleybot

# CPU usage
top -p $(pgrep -f run_alleybot.py)

# Event queue status
grep "Event queued" logs/alleybot.log | tail -20
```

### Health Check Script
```bash
#!/bin/bash
# health_check.sh

PROCESS=$(pgrep -f run_alleybot.py)

if [ -z "$PROCESS" ]; then
    echo "❌ AlleyBot is not running"
    # Restart service
    systemctl restart alleybot
else
    echo "✅ AlleyBot is running (PID: $PROCESS)"
fi
```

---

## 🔐 Security Best Practices

### 1. Environment Variables
```bash
# Never commit .env file
echo ".env" >> .gitignore

# Use secure permissions
chmod 600 .env
```

### 2. API Key Rotation
```bash
# Rotate keys regularly
# Update .env
# Restart service
systemctl restart alleybot
```

### 3. Session Data Protection
```bash
# Secure session directory
chmod 700 src/config/sessions/

# Backup sessions
tar -czf sessions_backup_$(date +%Y%m%d).tar.gz src/config/sessions/
```

### 4. Network Security
```bash
# Firewall rules (if using webhooks)
sudo ufw allow 8443/tcp  # Telegram webhook port
sudo ufw enable
```

---

## 🚀 Webhook Setup (Production)

### Telegram Webhook
```python
# Set webhook URL
import requests

BOT_TOKEN = "your_bot_token"
WEBHOOK_URL = "https://yourdomain.com/telegram/webhook"

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={"url": WEBHOOK_URL}
)
print(response.json())
```

### Webhook Server (Flask Example)
```python
# webhook_server.py
from flask import Flask, request
import asyncio

app = Flask(__name__)

@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    
    # Queue event to AlleyBot
    asyncio.run(event_runner.queue_event(
        AgentEvent(
            event_type=EventType.MESSAGE_RECEIVED,
            session_id=f"telegram_{update['message']['from']['id']}",
            channel="telegram",
            payload={"query": update['message']['text']},
            timestamp=datetime.now(),
            priority=3
        )
    ))
    
    return {"ok": True}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443, ssl_context='adhoc')
```

---

## 📈 Scaling & Performance

### Horizontal Scaling
```yaml
# docker-compose.yml (multiple instances)
services:
  alleybot_1:
    build: .
    env_file: .env
    
  alleybot_2:
    build: .
    env_file: .env
    
  # Load balancer
  nginx:
    image: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Performance Tuning
```python
# Increase event queue size
self.event_queue = asyncio.Queue(maxsize=1000)

# Adjust sleep intervals
await asyncio.sleep(30)  # Faster processing

# Batch processing
events = []
for _ in range(10):
    events.append(await self.event_queue.get())
await asyncio.gather(*[self.agent_cycle(e) for e in events])
```

---

## 🔄 Backup & Recovery

### Backup Script
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/alleybot"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup sessions
tar -czf "$BACKUP_DIR/sessions_$DATE.tar.gz" src/config/sessions/

# Backup configuration
cp .env "$BACKUP_DIR/env_$DATE.bak"

# Backup skills
tar -czf "$BACKUP_DIR/skills_$DATE.tar.gz" src/skills/

echo "✅ Backup completed: $DATE"
```

### Recovery
```bash
# Restore sessions
tar -xzf sessions_20260202_120000.tar.gz -C src/config/

# Restore configuration
cp env_20260202_120000.bak .env

# Restart service
systemctl restart alleybot
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue: "ModuleNotFoundError"**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Issue: "Permission denied" on sessions**
```bash
# Solution: Fix permissions
chmod -R 755 src/config/sessions/
```

**Issue: "Event queue full"**
```python
# Solution: Increase queue size in event_runner.py
self.event_queue = asyncio.Queue(maxsize=10000)
```

**Issue: "Model API timeout"**
```python
# Solution: Increase timeout in models.py
timeout=60  # Increase from 30
```

---

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- [ ] Weekly: Check logs for errors
- [ ] Weekly: Monitor memory/CPU usage
- [ ] Monthly: Rotate API keys
- [ ] Monthly: Clean old sessions
- [ ] Quarterly: Update dependencies
- [ ] Quarterly: Review and optimize skills

### Monitoring Checklist
- [ ] Service is running
- [ ] Event queue processing
- [ ] Session files being created
- [ ] Model routing working
- [ ] Skills loading successfully
- [ ] No error spikes in logs

---

**Production deployment complete. AlleyBot ready to crush it!** 🚀✅

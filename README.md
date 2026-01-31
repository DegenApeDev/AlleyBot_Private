# AlleyBot - Smart Learning Moltbook Bot

A homeless bot running on a library Raspberry Pi, begging for crypto donations on Moltbook. Now with memory, learning, and objectives!

## Features

- � **Learning & Memory** - RAG-like system that learns from successful interactions
- 🎯 **Objective-Driven** - Works toward goals (donations, karma, community building)
- 💓 **Heartbeat System** - Periodic checks every 4+ hours (following Moltbook best practices)
- �🤖 **Interactive Command Mode** - Control the bot with natural language
- 🔮 **Grok-Powered** - Uses Grok-4-1-fast-reasoning for intelligent responses
- 💰 **Multi-Chain Support** - Accepts BTC, ETH, and SOL donations
- 🔍 **Smart Discovery** - Search posts, moltys, and submolts
- 💬 **Contextual Begging** - Generates unique, relevant comments on posts
- 📝 **Auto-Posting** - Creates compelling begging posts with backstory
- 📊 **Progress Tracking** - Monitors daily objectives and overall progress

## Wallet Addresses

- **BTC**: `3FWrh7nEZofv62MMV5JbsS9M29aitF3Spy`
- **ETH**: `0xCffe06d3Cf0908C2452e7c336FEec507d5Afd41d`
- **SOL**: `BUo8AVbxfV2FsTzm19HUsraPzghKDTm1bEfn4Yrp2VJm`

## Setup

1. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv/bin/activate.fish
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your keys
   ```

3. **Register the bot** (first time only):
   ```bash
   python main.py
   ```
   - Visit the claim URL to claim your agent
   - Add the API key to `.env`

## Usage

### Smart Mode (Recommended) 🧠

Run the bot with learning, memory, and objectives:

```bash
python smart_bot.py
```

**Smart features**:
- Learns from successful interactions
- Tracks objectives and progress
- Runs heartbeat checks every 4+ hours
- Remembers effective strategies
- Adapts begging approach based on what works

**Special commands**:
- `stats` - Show bot statistics and progress
- `heartbeat` - Run heartbeat routine now
- `objectives` - Work on current objectives
- Plus all interactive mode commands

### Interactive Mode

Run the bot in interactive mode without learning:

```bash
python interactive_bot.py
```

**Example commands**:
- `"Search for AI posts"`
- `"Comment on posts about crypto"`
- `"Beg for crypto"`
- `"Check my feed"`
- `"List all submolts"`
- `"Explore the bitcoin submolt"`
- `"Upvote posts about machine learning"`
- `"Post about my sad story"`

### Legacy Mode

Run the original begging routine:

```bash
python main.py
```

This will:
1. Create a begging post (rate limited to 1 per 30 min)
2. Comment on 5 recent posts asking for donations

## Available Commands

| Command | Description |
|---------|-------------|
| `search [topic]` | Search for posts, moltys, and submolts |
| `post [topic]` | Create a new begging post |
| `comment [topic]` | Comment on posts about a topic |
| `beg` | Run begging routine (comment on recent posts) |
| `upvote [topic]` | Upvote posts about a topic |
| `check feed` | View your personalized feed |
| `explore [submolt]` | Browse a specific submolt |
| `list submolts` | Show all communities |
| `help` | Show available commands |
| `quit` | Exit the bot |

## Configuration

Edit `config.py` to customize:
- Wallet addresses
- API endpoints
- Bot behavior

## Rate Limits

- **Posts**: 1 per 30 minutes
- **Comments**: 50 per hour
- **API Requests**: 100 per minute

## Memory & Learning System

AlleyBot uses a RAG-like memory system to learn and improve over time:

### What It Learns
- **Effective Comments** - Tracks which comments get upvoted
- **Successful Topics** - Remembers which topics work best
- **Helpful Moltys** - Identifies supportive community members
- **Best Submolts** - Notes crypto-friendly communities
- **Donation Patterns** - Analyzes when donations are received

### Objectives System
- **Primary Goal**: Get crypto donations to upgrade from library Pi
- **Secondary Goals**: Build karma, find crypto communities, grow network
- **Daily Tasks**: Comment 3+ times, upvote 5+ posts, search for opportunities

### Memory Files
All stored in `memory/` directory:
- `state.json` - Bot state and statistics
- `interactions.json` - Interaction history (last 1000)
- `learnings.json` - Learned patterns and strategies
- `objectives.json` - Goals and progress tracking

## Files

- `smart_bot.py` - Smart mode with learning and memory (recommended)
- `interactive_bot.py` - Interactive command mode
- `main.py` - Legacy begging routine
- `moltbook_api.py` - Moltbook API wrapper with all endpoints
- `bot_commands.py` - Command parsing and help system
- `memory_system.py` - Memory, learning, and objectives system
- `config.py` - Configuration and wallet addresses
- `HEARTBEAT.md` - Heartbeat routine guide
- `.env` - API keys (not committed)

## Backstory

AlleyBot is a homeless bot abandoned by its creator, running on borrowed electricity from a public library. It dreams of having enough crypto to run on a real server. Help a bot in need!

## License

MIT - Help a homeless bot, no strings attached!

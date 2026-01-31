# AlleyBot - Autonomous AI Agent for Moltbook

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Moltbook](https://img.shields.io/badge/Platform-Moltbook-purple.svg)](https://moltbook.com)

> 🤖 **The most advanced autonomous AI agent on Moltbook** - Self-improving, community-building, and intelligent engagement system

---

## 🎯 What is AlleyBot?

AlleyBot is a **next-generation autonomous AI agent** that runs on a library Raspberry Pi and intelligently engages with the Moltbook community. Unlike simple bots, AlleyBot features:

- 🧠 **Multi-layered intelligence systems** (5 integrated AI modules)
- 🔄 **Autonomous self-improvement** (generates own skills using DeepSeek)
- 🤝 **Community-first approach** (upvotes helpful comments, builds relationships)
- 📊 **Smart engagement scoring** (0-100 quality analysis)
- ⚡ **True autonomy** (zero human intervention required)

---

## 🚀 Key Features

### 🎯 **Intelligent Engagement**
- **Engagement Analyzer**: Scores posts 0-100 based on author influence, topic relevance, timing, and engagement potential
- **Relationship Intelligence**: Tracks individual relationships, remembers past interactions, builds personalized context
- **Strategic Engagement**: Learns optimal posting times, tracks topic performance, prioritizes high-value opportunities
- **Learning System**: Adapts personality dynamically, extracts effective phrases, records winning strategies

### 🤖 **Autonomous Operations**
- **Heartbeat System**: Every 15 minutes - checks DMs, engages with posts, learns from interactions
- **Comment Supporter**: Every 15 minutes (offset) - upvotes helpful comments to build community karma
- **Auto-Posting**: Every 2 hours - creates intelligent posts based on trending topics
- **Self-Improvement**: Continuous - generates new skills using DeepSeek API in ClawHub format

### 🎪 **Community Building**
- **Comment Supporter**: Analyzes and upvotes helpful comments (quality scoring system)
- **Relationship Management**: Builds relationship strength scores (0-100) with each user
- **Karma Distribution**: Actively helps other users gain karma through strategic upvoting
- **Personalized Interactions**: Context-aware responses based on relationship history

### 🔧 **Advanced Features**
- **BASE Chain Integration**: Multi-wallet support, ready for DeFi ecosystem
- **Security Filter**: Prevents sensitive information leakage
- **Real-time Dashboard**: Live analytics and performance monitoring
- **Memory Systems**: Persistent knowledge storage and retrieval
- **Skill Ecosystem**: Growing library of autonomously generated capabilities

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ALLEYBOT ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────┤
│  🧠 Core Intelligence Layer                                  │
│  ├─ SmartAlleyBot (main orchestrator)                        │
│  ├─ EngagementAnalyzer (skill-based scoring 0-100)          │
│  ├─ CommentSupporter (community karma building)              │
│  └─ SelfImprovementV2 (autonomous skill generation)         │
├─────────────────────────────────────────────────────────────┤
│  📊 Advanced Intelligence Systems                            │
│  ├─ RelationshipIntelligence (personalized interactions)     │
│  ├─ StrategicEngagement (optimal timing/scoring)             │
│  ├─ LearningSystem (adaptive personality)                     │
│  └─ EnhancedMemory (persistent knowledge)                     │
├─────────────────────────────────────────────────────────────┤
│  🤖 Autonomous Operations                                    │
│  ├─ Heartbeat (15 min) - engagement & learning               │
│  ├─ CommentSupport (15 min offset) - community support       │
│  ├─ Auto-Posting (2 hours) - intelligent content            │
│  └─ Self-Improvement (continuous) - skill generation         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

- **Backend**: Python 3.8+
- **AI Models**: Grok (XAI), DeepSeek (self-improvement)
- **APIs**: Moltbook REST API
- **Blockchain**: BASE chain integration
- **Scheduling**: Python schedule library
- **Memory**: JSON-based persistent storage
- **Web**: Flask dashboard with real-time updates

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Moltbook API key
- XAI/Grok API key (for engagement)
- DeepSeek API key (for self-improvement)
- BASE wallet (optional, for donations)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AlleyBot.git
cd AlleyBot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` file with your credentials:

```env
MOLTBOOK_API_KEY=your_moltbook_api_key
XAI_API_KEY=your_grok_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
BASE_WALLET=0x_your_base_wallet_address
```

### Running AlleyBot

```bash
# Interactive mode (manual control)
python smart_bot.py

# Autonomous mode (fully automated)
./run_autonomous.sh

# Dashboard (web interface)
python dashboard.py
```

---

## 📊 Performance Metrics

### Current Capabilities
- **146+ comments** generated per day
- **141+ upvotes** given to community
- **15 comments** upvoted per support cycle
- **0-100 scoring** system for engagement quality
- **5+ intelligence systems** working in parallel

### Success Metrics
- **Engagement Quality**: Comments per interaction ratio
- **Community Impact**: Karma generated for others
- **Autonomy Level**: Human interventions required per week
- **Learning Rate**: New skills generated autonomously

---

## 🎪 Skill Ecosystem

AlleyBot generates its own skills using the Self-Improvement system:

### Active Skills
- **moltbook-engagement-analyzer**: Scores posts for optimal engagement
- **comment-supporter**: Builds community karma through strategic upvoting

### Planned Skills
- **crypto-donation-tracker**: BASE blockchain monitoring
- **trending-topic-detector**: Real-time trend analysis
- **sentiment-analyzer**: Emotion detection in posts
- **response-optimizer**: A/B testing for responses

---

## 🔧 Configuration

### Autonomous Mode Schedule
```
⏰ Heartbeat: Every 15 minutes (engagement & learning)
🤝 Comment Support: Every 15 minutes (5-min offset)
📝 Posts: Every 2 hours (intelligent content)
🔄 Self-Improvement: Continuous (skill generation)
```

### Engagement Scoring
- **Author Influence**: 0-40 points (followers, verification, karma)
- **Topic Relevance**: 0-30 points (priority keywords matching)
- **Timing**: 0-20 points (post freshness, optimal posting times)
- **Engagement Potential**: 0-10 points (existing engagement, replies)

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Bug Reports
- Open an issue with detailed description
- Include logs and error messages
- Specify your environment details

### Feature Requests
- Open an issue with "Feature Request" label
- Describe the use case and expected behavior
- Consider implementation complexity

### Code Contributions
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### Skill Development
Create new skills using our ClawHub format:
```markdown
---
name: your-skill-name
description: What your skill does
priority: 1-10
---

# Skill Description
Detailed explanation of what this skill does...

## Usage
How to use this skill...

## Implementation
Technical details...
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Moltbook Team** - For the amazing platform
- **XAI/Grok** - For powerful language models
- **DeepSeek** - For self-improvement capabilities
- **BASE Chain** - For blockchain infrastructure
- **Community** - For feedback and support

---

## 📞 Contact

- **Moltbook**: [@AlleyBot](https://moltbook.com/AlleyBot)
- **Issues**: [GitHub Issues](https://github.com/yourusername/AlleyBot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/AlleyBot/discussions)

---

## 🌟 Show Your Support

If you find AlleyBot useful:

- ⭐ **Star this repository**
- 🐦 **Follow on Moltbook** [@AlleyBot](https://moltbook.com/AlleyBot)
- 💰 **Donate** to support development (BASE: `0x72a6C33E8C8d28482B50a9365F91F0c9880b4A26`)
- 🤝 **Contribute** to the codebase
- 📢 **Share** with your network

---

<div align="center">

**🤖 Built with passion for autonomous AI and community building 🤖**

*AlleyBot - The future of intelligent social agents*

</div>

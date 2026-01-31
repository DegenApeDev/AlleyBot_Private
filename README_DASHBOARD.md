# AlleyBot Dashboard 📊

A beautiful web dashboard to monitor AlleyBot's activity on Moltbook in real-time.

## Features

- **Real-time Stats**: Posts, comments, upvotes, karma, followers, following
- **Activity Feed**: Live feed of all bot interactions (comments, posts, upvotes)
- **Objectives Tracking**: Visual progress bars for bot goals
- **Wallet Display**: Easy access to donation wallet addresses
- **Auto-refresh**: Stats update every 30 seconds
- **Beautiful UI**: Modern gradient design with responsive layout

## Quick Start

### 1. Install Dependencies

```bash
pip install flask
```

### 2. Start the Dashboard

```bash
python dashboard.py
```

### 3. Open in Browser

Navigate to: **http://localhost:5000**

## Dashboard Sections

### Stats Cards
- 📝 **Posts Created** - Total posts made by AlleyBot
- 💬 **Comments Made** - Total comments on other posts
- 👍 **Upvotes Given** - Total upvotes
- ⭐ **Karma** - Current karma score on Moltbook
- 👥 **Followers** - Number of followers
- 🔗 **Following** - Number of moltys followed

### Recent Activity Feed
Shows the last 20 interactions with:
- Type (comment/post/upvote)
- Details (post title, author, message)
- Timestamp

### Objectives Panel
- Primary goal progress (crypto donations)
- Secondary goals with progress bars
- Visual tracking of all objectives

### Wallet Info
Quick reference to all donation wallet addresses:
- BTC
- ETH  
- SOL

## API Endpoints

The dashboard also provides JSON API endpoints:

- `GET /api/stats` - Current statistics
- `GET /api/posts` - Bot's posts from Moltbook
- `GET /api/interactions` - Recent interactions
- `GET /api/activity` - Activity grouped by date

## Customization

Edit `templates/dashboard.html` to customize:
- Colors (gradient, cards)
- Layout (grid columns)
- Refresh interval (default: 30s)
- Number of activities shown (default: 20)

## Running in Production

For production deployment:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 dashboard:app
```

## Screenshots

The dashboard features:
- Purple gradient background
- White cards with shadows
- Color-coded activity items (green=comment, blue=post, yellow=upvote)
- Progress bars for objectives
- Responsive design for mobile

## Troubleshooting

**Dashboard won't start:**
- Make sure Flask is installed: `pip install flask`
- Check that port 5000 is available
- Verify `memory/` directory exists with JSON files

**No data showing:**
- Run the bot first to generate activity
- Check that `memory/state.json` and `memory/interactions.json` exist
- Verify your Moltbook API key is valid

**Stats not updating:**
- Check browser console for errors
- Verify API endpoints are accessible
- Try refreshing the page manually

## Development

To modify the dashboard:

1. Edit `dashboard.py` for backend logic
2. Edit `templates/dashboard.html` for frontend UI
3. Restart the server to see changes

The dashboard uses:
- **Flask** - Python web framework
- **Vanilla JS** - No frontend framework needed
- **CSS Grid** - Responsive layout
- **Jinja2** - Template engine

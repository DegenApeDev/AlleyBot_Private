#!/usr/bin/env python3
"""
AlleyBot Dashboard - Monitor bot activity on Moltbook
"""
from flask import Flask, render_template, jsonify
from moltbook_api import MoltbookAPI
import json
from datetime import datetime
import os

app = Flask(__name__)
api = MoltbookAPI()

def load_memory():
    """Load bot memory and stats"""
    try:
        with open('memory/state.json', 'r') as f:
            state = json.load(f)
        with open('memory/interactions.json', 'r') as f:
            interactions = json.load(f)
        with open('memory/objectives.json', 'r') as f:
            objectives = json.load(f)
        return state, interactions, objectives
    except:
        return {}, [], {}

@app.route('/')
def index():
    """Main dashboard page"""
    state, interactions, objectives = load_memory()
    
    # Get bot profile with full data (followers, following, recent posts)
    try:
        profile = api.get_public_profile(name="AlleyBot")
        agent = profile.get('agent', {})
        recent_posts = profile.get('recentPosts', [])
    except Exception as e:
        print(f"Error fetching profile: {e}")
        agent = {}
        recent_posts = []
    
    # Calculate stats from API data
    total_posts = state.get('totalPosts', 0)
    total_comments = state.get('totalComments', 0)
    total_upvotes = state.get('totalUpvotes', 0)
    karma = agent.get('karma', 0)
    followers = agent.get('follower_count', 0)
    following = agent.get('following_count', 0)
    
    # Get recent interactions
    recent_interactions = interactions[-20:] if interactions else []
    recent_interactions.reverse()
    
    return render_template('dashboard.html',
                         agent=agent,
                         total_posts=total_posts,
                         total_comments=total_comments,
                         total_upvotes=total_upvotes,
                         karma=karma,
                         followers=followers,
                         following=following,
                         recent_interactions=recent_interactions,
                         recent_posts=recent_posts,
                         objectives=objectives)

@app.route('/api/stats')
def get_stats():
    """API endpoint for stats"""
    state, interactions, objectives = load_memory()
    
    try:
        profile = api.get_public_profile(name="AlleyBot")
        agent = profile.get('agent', {})
    except:
        agent = {}
    
    return jsonify({
        'posts': state.get('totalPosts', 0),
        'comments': state.get('totalComments', 0),
        'upvotes': state.get('totalUpvotes', 0),
        'karma': agent.get('karma', 0),
        'followers': agent.get('follower_count', 0),
        'following': agent.get('following_count', 0),
        'donations': state.get('totalDonationsReceived', 0)
    })

@app.route('/api/posts')
def get_posts():
    """Get bot's posts from Moltbook"""
    try:
        # Use public profile API which includes recent posts
        profile = api.get_public_profile(name="AlleyBot")
        posts = profile.get('recentPosts', [])
        return jsonify({'success': True, 'posts': posts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/interactions')
def get_interactions():
    """Get recent interactions"""
    _, interactions, _ = load_memory()
    recent = interactions[-50:] if interactions else []
    recent.reverse()
    return jsonify({'success': True, 'interactions': recent})

@app.route('/api/activity')
def get_activity():
    """Get activity timeline"""
    _, interactions, _ = load_memory()
    
    # Group by date
    activity_by_date = {}
    for interaction in interactions:
        timestamp = interaction.get('timestamp', '')
        date = timestamp.split('T')[0] if 'T' in timestamp else 'unknown'
        
        if date not in activity_by_date:
            activity_by_date[date] = {'posts': 0, 'comments': 0, 'upvotes': 0}
        
        itype = interaction.get('type', '')
        if itype == 'post':
            activity_by_date[date]['posts'] += 1
        elif itype == 'comment':
            activity_by_date[date]['comments'] += 1
        elif itype == 'upvote':
            activity_by_date[date]['upvotes'] += 1
    
    return jsonify({'success': True, 'activity': activity_by_date})

if __name__ == '__main__':
    print("\n🚀 Starting AlleyBot Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("💡 Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

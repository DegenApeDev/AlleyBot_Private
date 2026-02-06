#!/usr/bin/env python3
"""
AlleyBot Dashboard with Human Approval System
Enhanced dashboard for reviewing and approving AI-generated code
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime
from autonomous_coder import AutonomousCoder

app = Flask(__name__)

# Initialize autonomous coder
coder = AutonomousCoder()

@app.route('/')
def dashboard():
    """Main dashboard with approval queue"""
    pending_drafts = coder.get_pending_drafts()
    recent_logs = coder.get_activity_logs()[:10]
    
    return render_template('approval_dashboard.html', 
                         pending_drafts=pending_drafts,
                         recent_logs=recent_logs)

@app.route('/draft/<draft_id>')
def view_draft(draft_id):
    """View specific draft details"""
    draft_file = os.path.join(coder.drafts_dir, f"{draft_id}.json")
    
    if not os.path.exists(draft_file):
        return "Draft not found", 404
    
    with open(draft_file, 'r') as f:
        draft = json.load(f)
    
    return render_template('draft_detail.html', draft=draft)

@app.route('/approve/<draft_id>', methods=['POST'])
def approve_draft(draft_id):
    """Approve a draft"""
    human_review = {
        "reviewer": request.form.get('reviewer', 'human'),
        "comments": request.form.get('comments', ''),
        "modifications": request.form.get('modifications', '').split('\n') if request.form.get('modifications') else []
    }
    
    result = coder.approve_draft(draft_id, human_review)
    
    return jsonify(result)

@app.route('/deploy/<draft_id>', methods=['POST'])
def deploy_code(draft_id):
    """Deploy approved code"""
    result = coder.deploy_code(draft_id)
    
    return jsonify(result)

@app.route('/test/<draft_id>', methods=['POST'])
def test_draft(draft_id):
    """Test draft code"""
    result = coder.test_code(draft_id)
    
    return jsonify(result)

@app.route('/logs')
def view_logs():
    """View activity logs"""
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    logs = coder.get_activity_logs(date)
    
    return render_template('activity_logs.html', logs=logs, date=date)

@app.route('/api/generate_code', methods=['POST'])
def generate_code():
    """API endpoint for code generation"""
    task = request.json.get('task')
    context = request.json.get('context', {})
    
    result = coder.generate_code(task, context)
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

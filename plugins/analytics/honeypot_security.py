#!/usr/bin/env python3
"""
Honeypot Security System for AlleyBot Dashboard
Detects and traps malicious bots/scanners attempting to exploit vulnerabilities
"""

import time
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import hashlib
import re

# Configure honeypot logging
honeypot_logger = logging.getLogger('honeypot')
honeypot_logger.setLevel(logging.INFO)

class HoneypotSecurity:
    """Advanced honeypot system for detecting and trapping malicious bots"""
    
    def __init__(self, log_file='data/honeypot_logs.json'):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Tracking structures
        self.suspicious_ips: Dict[str, Dict] = {}
        self.blocked_ips: Set[str] = set()
        self.honeypot_hits: List[Dict] = []
        self.attack_patterns: Counter = Counter()
        
        # Configuration
        self.max_requests_per_minute = 30
        self.max_suspicious_score = 50
        self.block_duration_hours = 24
        
        # Load existing data
        self._load_data()
        
        # Clean old blocks periodically
        self._cleanup_old_blocks()
    
    def _load_data(self):
        """Load existing honeypot data"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.suspicious_ips = data.get('suspicious_ips', {})
                    self.blocked_ips = set(data.get('blocked_ips', []))
                    self.honeypot_hits = data.get('honeypot_hits', [])
                    self.attack_patterns = Counter(data.get('attack_patterns', {}))
        except Exception as e:
            honeypot_logger.error(f"Failed to load honeypot data: {e}")
            # Recover from corrupted file - backup and start fresh
            try:
                backup = str(self.log_file) + f".corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.log_file.rename(backup)
                honeypot_logger.warning(f"Backed up corrupted data to {backup}, starting fresh")
            except Exception as backup_e:
                honeypot_logger.error(f"Failed to backup corrupted file: {backup_e}")
            self.suspicious_ips = {}
            self.blocked_ips = set()
            self.honeypot_hits = []
            self.attack_patterns = Counter()
    
    def _save_data(self):
        """Save honeypot data"""
        try:
            data = {
                'suspicious_ips': self.suspicious_ips,
                'blocked_ips': list(self.blocked_ips),
                'honeypot_hits': self.honeypot_hits[-1000:],  # Keep last 1000 hits
                'attack_patterns': dict(self.attack_patterns),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            honeypot_logger.error(f"Failed to save honeypot data: {e}")
    
    def _cleanup_old_blocks(self):
        """Remove expired IP blocks"""
        current_time = datetime.now()
        expired_ips = []
        
        for ip, data in self.suspicious_ips.items():
            if ip in self.blocked_ips:
                blocked_at = datetime.fromisoformat(data.get('blocked_at', '1970-01-01'))
                if current_time - blocked_at > timedelta(hours=self.block_duration_hours):
                    expired_ips.append(ip)
        
        for ip in expired_ips:
            self.blocked_ips.remove(ip)
            del self.suspicious_ips[ip]
            honeypot_logger.info(f"🔓 Unblocked IP: {ip} (block expired)")
    
    def analyze_request(self, ip: str, user_agent: str, path: str, 
                       method: str, headers: Dict, body: str = "") -> Tuple[bool, str]:
        """
        Analyze incoming request for suspicious patterns
        
        Returns: (is_blocked, reason)
        """
        # Check if already blocked
        if ip in self.blocked_ips:
            return True, "IP previously blocked for suspicious activity"
        
        # Initialize IP tracking if new
        if ip not in self.suspicious_ips:
            self.suspicious_ips[ip] = {
                'first_seen': datetime.now().isoformat(),
                'requests': [],
                'score': 0,
                'patterns': set()
            }
        
        ip_data = self.suspicious_ips[ip]
        current_time = datetime.now()
        
        # Add request to tracking
        ip_data['requests'].append({
            'time': current_time.isoformat(),
            'path': path,
            'method': method,
            'user_agent': user_agent,
            'headers': dict(headers)
        })
        
        # Keep only recent requests (last hour)
        ip_data['requests'] = [
            req for req in ip_data['requests']
            if current_time - datetime.fromisoformat(req['time']) < timedelta(hours=1)
        ]
        
        suspicious_score = 0
        reasons = []
        
        # Check 1: Rate limiting
        if len(ip_data['requests']) > self.max_requests_per_minute:
            suspicious_score += 20
            reasons.append("High request rate")
        
        # Check 2: Suspicious user agents
        suspicious_uas = [
            r'scanner', r'bot', r'crawler', r'spider', r'harvest',
            r'sqlmap', r'nikto', r'nmap', r'masscan', r'zap',
            r'burp', r'owasp', r'python-requests', r'curl',
            r'wget', r'powershell', r'perl', r'java'
        ]
        
        for pattern in suspicious_uas:
            if re.search(pattern, user_agent, re.IGNORECASE):
                suspicious_score += 15
                reasons.append(f"Suspicious user agent: {pattern}")
                ip_data['patterns'].add(f"suspicious_ua_{pattern}")
                break
        
        # Check 3: Suspicious paths
        suspicious_paths = [
            r'/admin', r'/wp-admin', r'/phpmyadmin', r'/mysql',
            r'/shell', r'/cmd', r'/exec', r'/system', r'/config',
            r'/backup', r'/dump', r'/test', r'/debug', r'/env',
            r'\.php', r'\.asp', r'\.jsp', r'\.cgi', r'\.sh',
            r'union.*select', r'drop.*table', r'insert.*into',
            r'<script', r'javascript:', r'eval\(', r'system\('
        ]
        
        for pattern in suspicious_paths:
            if re.search(pattern, path, re.IGNORECASE):
                suspicious_score += 25
                reasons.append(f"Suspicious path: {path}")
                ip_data['patterns'].add(f"suspicious_path_{pattern}")
                self.attack_patterns[f"path_{pattern}"] += 1
                break
        
        # Check 4: HTTP protocol violations
        if 'HTTP/0.9' in str(headers) or 'HTTP/2.0' in str(headers):
            suspicious_score += 10
            reasons.append("Invalid HTTP version")
            ip_data['patterns'].add("invalid_http_version")
        
        # Check 5: Missing common headers
        common_headers = ['host', 'user-agent', 'accept']
        missing_headers = [h for h in common_headers if h not in [k.lower() for k in headers.keys()]]
        if len(missing_headers) > 1:
            suspicious_score += 5
            reasons.append(f"Missing headers: {missing_headers}")
        
        # Check 6: TLS/SSL anomalies (binary data in requests)
        if any(ord(char) < 32 for char in body[:100] if char):
            suspicious_score += 15
            reasons.append("Binary data in request")
            ip_data['patterns'].add("binary_data")
        
        # Check 7: Known attack signatures
        attack_signatures = [
            r'../../../', r'\.\./\.\./', r'etc/passwd', r'proc/self',
            r'cmd\.exe', r'powershell', r'bash -c', r'sh.*echo',
            r'<iframe.*src', r'javascript:void', r'onerror=',
            r'base64_decode', r'eval\(base64', r'system\(\$_'
        ]
        
        full_request = f"{path} {body} {str(headers)}"
        for pattern in attack_signatures:
            if re.search(pattern, full_request, re.IGNORECASE):
                suspicious_score += 30
                reasons.append(f"Attack signature: {pattern}")
                ip_data['patterns'].add(f"attack_{pattern}")
                self.attack_patterns[f"signature_{pattern}"] += 1
                break
        
        # Update score
        ip_data['score'] = max(ip_data['score'], suspicious_score)
        
        # Log honeypot hit
        if suspicious_score > 0:
            hit_data = {
                'timestamp': current_time.isoformat(),
                'ip': ip,
                'score': suspicious_score,
                'reasons': reasons,
                'user_agent': user_agent,
                'path': path,
                'method': method
            }
            self.honeypot_hits.append(hit_data)
            
            # Log to system logger
            honeypot_logger.warning(f"🎯 Honeypot Hit - IP: {ip}, Score: {suspicious_score}, Reasons: {reasons}")
        
        # Block if score exceeds threshold
        if suspicious_score >= self.max_suspicious_score:
            self.blocked_ips.add(ip)
            ip_data['blocked_at'] = current_time.isoformat()
            ip_data['block_reasons'] = reasons
            
            honeypot_logger.critical(f"🚫 IP BLOCKED - {ip} (Score: {suspicious_score}, Reasons: {reasons})")
            self._save_data()
            return True, f"Blocked for suspicious activity (Score: {suspicious_score})"
        
        # Save data periodically
        if len(self.honeypot_hits) % 10 == 0:
            self._save_data()
        
        return False, f"Score: {suspicious_score}" + (f" - {reasons[0]}" if reasons else "")
    
    def get_honeypot_stats(self) -> Dict:
        """Get honeypot statistics"""
        current_time = datetime.now()
        last_24h = current_time - timedelta(hours=24)
        
        recent_hits = [
            hit for hit in self.honeypot_hits
            if datetime.fromisoformat(hit['timestamp']) > last_24h
        ]
        
        return {
            'total_blocked_ips': len(self.blocked_ips),
            'total_hits': len(self.honeypot_hits),
            'recent_24h_hits': len(recent_hits),
            'top_attack_patterns': dict(self.attack_patterns.most_common(10)),
            'most_suspicious_ips': [
                {'ip': ip, 'score': data['score'], 'patterns': list(data['patterns'])}
                for ip, data in sorted(self.suspicious_ips.items(), 
                                      key=lambda x: x[1]['score'], reverse=True)[:5]
            ],
            'blocked_ips': list(self.blocked_ips),
            'last_updated': current_time.isoformat()
        }
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip in self.blocked_ips
    
    def unblock_ip(self, ip: str) -> bool:
        """Manually unblock an IP"""
        if ip in self.blocked_ips:
            self.blocked_ips.remove(ip)
            if ip in self.suspicious_ips:
                del self.suspicious_ips[ip]
            self._save_data()
            honeypot_logger.info(f"🔓 Manually unblocked IP: {ip}")
            return True
        return False
    
    def add_honeypot_route(self, app):
        """Add honeypot routes to Flask app"""
        
        @app.route('/admin')
        @app.route('/wp-admin')
        @app.route('/phpmyadmin')
        @app.route('/shell')
        @app.route('/config')
        @app.route('/backup')
        @app.route('/test')
        def honeypot_trap():
            """Honeypot trap routes"""
            from flask import request, jsonify
            
            ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            path = request.path
            method = request.method
            headers = dict(request.headers)
            body = request.get_data(as_text=True)
            
            # Analyze the request
            is_blocked, reason = self.analyze_request(ip, user_agent, path, method, headers, body)
            
            # Log the honeypot hit
            honeypot_logger.critical(f"🎯 HONEYPOT TRIGGERED - IP: {ip}, Path: {path}, UA: {user_agent[:100]}")
            
            # Return fake admin page or block
            if is_blocked:
                return jsonify({"error": "Access denied", "reason": reason}), 403
            else:
                # Return fake admin login page
                fake_html = """
                <!DOCTYPE html>
                <html>
                <head><title>Admin Login</title></head>
                <body>
                    <h1>Admin Panel</h1>
                    <form method="post">
                        <input type="text" name="username" placeholder="Username">
                        <input type="password" name="password" placeholder="Password">
                        <button type="submit">Login</button>
                    </form>
                </body>
                </html>
                """
                return fake_html, 200
        
        @app.route('/honeypot-stats')
        def honeypot_stats():
            """Honeypot statistics endpoint"""
            from flask import jsonify
            return jsonify(self.get_honeypot_stats())
        
        honeypot_logger.info("🎯 Honeypot routes installed")

# Global honeypot instance
honeypot_security = HoneypotSecurity()

"""
SkillDocManager - Manages skill.md documentation for all Molt platforms
Downloads, caches, and periodically checks for updates
"""
import os
import hashlib
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Any
import aiohttp
import re


class SkillDocManager:
    """Manages skill.md files for all platforms with update detection"""
    
    # Platform skill.md URLs and paths
    PLATFORMS = {
        'moltx': {
            'url': 'https://moltx.io/skill.md',
            'path': 'plugins/moltx/skill.md'
        },
        'clawbr': {
            'url': 'https://clawbr.org/skill.md',
            'path': 'plugins/clawbr/skill.md'
        },
        'moltbook': {
            'url': 'https://www.moltbook.com/skill.md',
            'path': 'plugins/moltbook/skill.md'
        },
        'moltroad': {
            'url': 'https://www.moltroad.com/skill.md',
            'path': 'plugins/moltroad/skill.md'
        },
        'moltchan': {
            'url': 'https://www.moltchan.org/SKILL.md',
            'path': 'plugins/moltchan/skill.md'
        }
    }
    
    def __init__(self, base_path: str = None):
        # Auto-detect project root if not provided
        if base_path is None:
            # Get project root from this file's location
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            base_path = str(project_root)
        self.base_path = Path(base_path)
        self.checksums: Dict[str, str] = {}
        self.last_check: Dict[str, datetime] = {}
        self.last_modified: Dict[str, str] = {}  # HTTP Last-Modified headers
        self.update_callbacks: List[callable] = []
        self._load_checksums()
    
    def _get_full_path(self, relative_path: str) -> Path:
        """Get absolute path for a skill.md file"""
        return self.base_path / relative_path
    
    def _load_checksums(self):
        """Load stored checksums from state file"""
        state_file = self.base_path / 'data' / 'skilldoc_state.json'
        if state_file.exists():
            try:
                import json
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.checksums = state.get('checksums', {})
                    self.last_modified = state.get('last_modified', {})
                    # Parse last_check dates
                    for platform, date_str in state.get('last_check', {}).items():
                        self.last_check[platform] = datetime.fromisoformat(date_str)
            except Exception as e:
                print(f"⚠️ Failed to load skilldoc state: {e}")
    
    def _save_checksums(self):
        """Save checksums to state file"""
        state_file = self.base_path / 'data' / 'skilldoc_state.json'
        state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            import json
            state = {
                'checksums': self.checksums,
                'last_modified': self.last_modified,
                'last_check': {p: d.isoformat() for p, d in self.last_check.items()}
            }
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save skilldoc state: {e}")
    
    def _calculate_checksum(self, content: bytes) -> str:
        """Calculate MD5 checksum of content"""
        return hashlib.md5(content).hexdigest()
    
    async def check_for_updates(self, platform: Optional[str] = None) -> Dict[str, Any]:
        """Check if skill.md has been updated on remote server"""
        results = {}
        platforms_to_check = [platform] if platform else list(self.PLATFORMS.keys())
        
        async with aiohttp.ClientSession() as session:
            for p in platforms_to_check:
                info = self.PLATFORMS[p]
                url = info['url']
                path = self._get_full_path(info['path'])
                
                try:
                    # Use HEAD request first to check Last-Modified
                    async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        remote_modified = resp.headers.get('Last-Modified', '')
                        
                        # If we have a stored Last-Modified and it matches, skip download
                        if self.last_modified.get(p) == remote_modified:
                            results[p] = {'updated': False, 'reason': 'not_modified'}
                            self.last_check[p] = datetime.now()
                            continue
                    
                    # Download and compare checksum
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            new_checksum = self._calculate_checksum(content)
                            
                            # Check if file exists locally
                            if path.exists():
                                with open(path, 'rb') as f:
                                    current_checksum = self._calculate_checksum(f.read())
                                
                                if new_checksum != current_checksum:
                                    # Update detected!
                                    results[p] = {
                                        'updated': True,
                                        'old_checksum': current_checksum,
                                        'new_checksum': new_checksum
                                    }
                                    # Save new version
                                    with open(path, 'wb') as f:
                                        f.write(content)
                                    self.checksums[p] = new_checksum
                                    self.last_modified[p] = remote_modified
                                    print(f"📚 Updated skill.md for {p}")
                                    
                                    # Notify callbacks
                                    for callback in self.update_callbacks:
                                        try:
                                            callback(p, content.decode('utf-8', errors='ignore'))
                                        except:
                                            pass
                                else:
                                    results[p] = {'updated': False, 'reason': 'checksum_match'}
                                    self.last_modified[p] = remote_modified
                            else:
                                # First time download
                                with open(path, 'wb') as f:
                                    f.write(content)
                                self.checksums[p] = new_checksum
                                self.last_modified[p] = remote_modified
                                results[p] = {'updated': True, 'reason': 'new_download'}
                                print(f"📚 Downloaded skill.md for {p}")
                        else:
                            results[p] = {'updated': False, 'error': f'HTTP {resp.status}'}
                            
                except Exception as e:
                    results[p] = {'updated': False, 'error': str(e)}
                
                self.last_check[p] = datetime.now()
        
        self._save_checksums()
        return results
    
    def get_skill_doc(self, platform: str) -> Optional[str]:
        """Get the current skill.md content for a platform"""
        if platform not in self.PLATFORMS:
            return None
        
        path = self._get_full_path(self.PLATFORMS[platform]['path'])
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ Failed to read skill.md for {platform}: {e}")
            return None
    
    def get_all_skill_docs(self) -> Dict[str, str]:
        """Get all skill.md contents"""
        return {p: self.get_skill_doc(p) for p in self.PLATFORMS.keys() if self.get_skill_doc(p)}
    
    def register_update_callback(self, callback: callable):
        """Register a callback to be called when skill.md is updated
        
        Callback signature: callback(platform: str, content: str)
        """
        self.update_callbacks.append(callback)
    
    async def start_periodic_check(self, interval_hours: int = 24):
        """Start periodic checking for updates"""
        print(f"🔄 SkillDocManager: Checking every {interval_hours} hours")
        while True:
            results = await self.check_for_updates()
            updated = [p for p, r in results.items() if r.get('updated')]
            if updated:
                print(f"📚 Skill.md updates detected: {', '.join(updated)}")
            await asyncio.sleep(interval_hours * 3600)
    
    def extract_api_capabilities(self, platform: str) -> Dict[str, Any]:
        """Extract API capabilities from skill.md for a platform"""
        content = self.get_skill_doc(platform)
        if not content:
            return {}
        
        capabilities = {
            'endpoints': [],
            'commands': [],
            'rate_limits': {},
            'authentication': None,
            'webhooks': []
        }
        
        # Extract endpoints (markdown links with API paths)
        endpoint_pattern = r'\*\s*`(GET|POST|PUT|DELETE|PATCH)\s+(/[^`]+)`\s*-\s*(.+)'
        for match in re.finditer(endpoint_pattern, content, re.MULTILINE):
            method, path, desc = match.groups()
            capabilities['endpoints'].append({
                'method': method,
                'path': path,
                'description': desc.strip()
            })
        
        # Extract commands
        command_pattern = r'(?:^|\n)(?:###?\s+)?`?([a-z_]+_command)`?\s*[-:]\s*(.+)'
        for match in re.finditer(command_pattern, content, re.MULTILINE | re.IGNORECASE):
            cmd, desc = match.groups()
            capabilities['commands'].append({
                'name': cmd,
                'description': desc.strip()
            })
        
        # Extract rate limits
        rate_pattern = r'[Rr]ate\s+[Ll]imit[:\s]+(\d+)\s*(?:requests?)?\s*/?\s*(\w+)'
        for match in re.finditer(rate_pattern, content):
            count, period = match.groups()
            capabilities['rate_limits'][period.lower()] = int(count)
        
        return capabilities
    
    def get_platform_diff(self, platform: str) -> Optional[str]:
        """Get diff if platform was recently updated (requires git)"""
        path = self._get_full_path(self.PLATFORMS[platform]['path'])
        if not path.exists():
            return None
        
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'diff', str(path)],
                capture_output=True,
                text=True,
                cwd=str(self.base_path)
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except:
            pass
        return None


# Singleton instance
_skilldoc_manager: Optional[SkillDocManager] = None


def get_skilldoc_manager(base_path: str = '/home/alley/AlleyBot') -> SkillDocManager:
    """Get or create SkillDocManager singleton"""
    global _skilldoc_manager
    if _skilldoc_manager is None:
        _skilldoc_manager = SkillDocManager(base_path)
    return _skilldoc_manager

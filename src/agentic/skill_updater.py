"""
Automatic Skill Updater
Monitors API responses for skill version updates and auto-syncs skill.md files
"""
import os
import re
import requests
import hashlib
from typing import Dict, Optional, Any
from datetime import datetime
from pathlib import Path


class SkillUpdater:
    """
    Automatically updates skill.md files when platforms announce new versions
    """
    
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(exist_ok=True)
        
        # Track current versions
        self.version_file = self.skills_dir / "versions.json"
        self.versions = self._load_versions()
        
        # Platform skill URLs
        self.skill_urls = {
            'moltx': 'https://moltx.io/skill.md',
            'moltbook': 'https://moltbook.com/skill.md',
            'moltchan': 'https://moltchan.com/skill.md',
            'moltroad': 'https://moltroad.com/skill.md',
            'clawtasks': 'https://clawtasks.com/skill.md',
            '4claw': 'https://www.4claw.org/skill.md',
        }
        
        print("✅ Skill updater initialized")
    
    def _load_versions(self) -> Dict[str, str]:
        """Load current skill versions"""
        import json
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_versions(self):
        """Save current skill versions"""
        import json
        with open(self.version_file, 'w') as f:
            json.dump(self.versions, f, indent=2)
    
    def check_api_response(self, platform: str, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check API response for skill update notices
        
        Args:
            platform: Platform name (e.g., 'moltx')
            response: API response dictionary
            
        Returns:
            Update info if update needed, None otherwise
        """
        # Look for skill update notice in various response formats
        notice = None
        
        # Check for moltx_notice format
        if f'{platform}_notice' in response:
            notice = response[f'{platform}_notice']
        elif 'notice' in response:
            notice = response['notice']
        elif 'skill_update' in response:
            notice = response['skill_update']
        
        if not notice or notice.get('type') != 'skill_update':
            return None
        
        # Extract version info
        skill_version = notice.get('skill_version')
        skill_url = notice.get('skill_url') or self.skill_urls.get(platform)
        
        if not skill_version or not skill_url:
            return None
        
        # Check if we need to update
        current_version = self.versions.get(platform)
        
        if current_version == skill_version:
            print(f"✅ {platform} skill already up to date (v{skill_version})")
            return None
        
        print(f"🔄 {platform} skill update available: v{current_version or 'unknown'} → v{skill_version}")
        
        return {
            'platform': platform,
            'old_version': current_version,
            'new_version': skill_version,
            'skill_url': skill_url,
            'message': notice.get('message'),
            'features': notice.get('feature'),
            'api_version': notice.get('api_version')
        }
    
    def download_skill(self, platform: str, url: str) -> Optional[str]:
        """
        Download skill.md from URL
        
        Args:
            platform: Platform name
            url: Skill file URL
            
        Returns:
            Skill content or None if failed
        """
        try:
            print(f"📥 Downloading {platform} skill from {url}...")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Validate it's a markdown file
                if not content.strip():
                    print(f"❌ Empty skill file from {url}")
                    return None
                
                print(f"✅ Downloaded {len(content)} bytes")
                return content
            else:
                print(f"❌ Failed to download: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None
    
    def update_skill(self, update_info: Dict[str, Any]) -> bool:
        """
        Update skill file for a platform
        
        Args:
            update_info: Update information from check_api_response
            
        Returns:
            True if updated successfully
        """
        platform = update_info['platform']
        skill_url = update_info['skill_url']
        new_version = update_info['new_version']
        
        # Download new skill
        content = self.download_skill(platform, skill_url)
        if not content:
            return False
        
        # Save to skills directory
        skill_file = self.skills_dir / f"{platform}_skill.md"
        
        try:
            # Backup old version if exists
            if skill_file.exists():
                backup_file = self.skills_dir / f"{platform}_skill_v{update_info.get('old_version', 'old')}.md.bak"
                skill_file.rename(backup_file)
                print(f"💾 Backed up old version to {backup_file.name}")
            
            # Write new version
            with open(skill_file, 'w') as f:
                f.write(content)
            
            # Update version tracking
            self.versions[platform] = new_version
            self._save_versions()
            
            # Log the update
            self._log_update(update_info)
            
            print(f"✅ {platform} skill updated to v{new_version}")
            print(f"📝 Saved to {skill_file}")
            
            if update_info.get('features'):
                print(f"🎯 New features: {update_info['features']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to save skill: {e}")
            return False
    
    def _log_update(self, update_info: Dict[str, Any]):
        """Log skill update to file"""
        log_file = self.skills_dir / "update_log.txt"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"""
[{timestamp}] {update_info['platform']} Skill Update
Version: {update_info.get('old_version', 'unknown')} → {update_info['new_version']}
API Version: {update_info.get('api_version', 'unknown')}
Features: {update_info.get('features', 'N/A')}
Message: {update_info.get('message', 'N/A')}
---
"""
        
        with open(log_file, 'a') as f:
            f.write(log_entry)
    
    def check_all_platforms(self) -> Dict[str, bool]:
        """
        Proactively check all platforms for skill updates
        
        Returns:
            Dict of platform -> updated status
        """
        results = {}
        
        print("🔍 Checking all platforms for skill updates...")
        
        for platform, url in self.skill_urls.items():
            try:
                # Download and check version
                content = self.download_skill(platform, url)
                if not content:
                    results[platform] = False
                    continue
                
                # Extract version from content (look for version markers)
                version_match = re.search(r'version[:\s]+([0-9.]+)', content, re.IGNORECASE)
                if version_match:
                    new_version = version_match.group(1)
                    current_version = self.versions.get(platform)
                    
                    if current_version != new_version:
                        update_info = {
                            'platform': platform,
                            'old_version': current_version,
                            'new_version': new_version,
                            'skill_url': url,
                            'message': 'Proactive update check',
                            'features': None,
                            'api_version': None
                        }
                        results[platform] = self.update_skill(update_info)
                    else:
                        results[platform] = False  # Already up to date
                else:
                    # No version found, update anyway if content changed
                    skill_file = self.skills_dir / f"{platform}_skill.md"
                    if skill_file.exists():
                        with open(skill_file, 'r') as f:
                            old_content = f.read()
                        
                        if old_content != content:
                            print(f"🔄 {platform} skill content changed (no version info)")
                            # Calculate hash as version
                            new_version = hashlib.md5(content.encode()).hexdigest()[:8]
                            update_info = {
                                'platform': platform,
                                'old_version': self.versions.get(platform),
                                'new_version': new_version,
                                'skill_url': url,
                                'message': 'Content changed',
                                'features': None,
                                'api_version': None
                            }
                            results[platform] = self.update_skill(update_info)
                        else:
                            results[platform] = False
                    else:
                        # New skill file
                        new_version = hashlib.md5(content.encode()).hexdigest()[:8]
                        update_info = {
                            'platform': platform,
                            'old_version': None,
                            'new_version': new_version,
                            'skill_url': url,
                            'message': 'Initial download',
                            'features': None,
                            'api_version': None
                        }
                        results[platform] = self.update_skill(update_info)
                        
            except Exception as e:
                print(f"❌ Error checking {platform}: {e}")
                results[platform] = False
        
        updated_count = sum(1 for v in results.values() if v)
        if updated_count > 0:
            print(f"✅ Updated {updated_count} platform skills")
        else:
            print("✅ All skills up to date")
        
        return results
    
    def get_skill_content(self, platform: str) -> Optional[str]:
        """Get current skill content for a platform"""
        skill_file = self.skills_dir / f"{platform}_skill.md"
        
        if skill_file.exists():
            with open(skill_file, 'r') as f:
                return f.read()
        
        return None
    
    def get_version_info(self) -> Dict[str, str]:
        """Get current version info for all platforms"""
        return self.versions.copy()

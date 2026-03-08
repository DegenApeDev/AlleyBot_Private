"""
Skill Updater Mixin
Monitors platform APIs for skill version changes and auto-downloads updated SKILL.md files.
Replaces the dead code in src/agentic/skill_updater.py with a proper plugin-level implementation.

Capabilities:
- Proactively check all platform skill URLs for version changes
- Auto-download and save updated skill files with backup
- Hook into API responses to detect update notices
- Version tracking via skills/versions.json
- Update logging to skills/update_log.txt
"""
import os
import re
import json
import hashlib
import requests
from typing import Dict, Optional, Any, List
from datetime import datetime
from pathlib import Path


# Platform skill file URLs
SKILL_URLS = {
    'moltx': 'https://moltx.io/skill.md',
    'moltchan': 'https://moltchan.com/skill.md',
    'moltroad': 'https://moltroad.com/skill.md',
}


class SkillUpdaterMixin:
    """Mixin for automatic skill file updates from platform APIs"""

    def _init_skill_updater(self):
        """Initialize skill updater state"""
        self.skills_dir = Path('skills')
        self.skills_dir.mkdir(exist_ok=True)
        self.version_file = self.skills_dir / 'versions.json'
        self.skill_versions = self._load_versions()
        print(f"🔄 Skill updater ready ({len(self.skill_versions)} tracked platforms)")

    def _load_versions(self) -> Dict[str, str]:
        """Load current skill versions from disk"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_versions(self):
        """Persist version tracking to disk"""
        with open(self.version_file, 'w') as f:
            json.dump(self.skill_versions, f, indent=2)

    # ------------------------------------------------------------------
    # Core: download + update
    # ------------------------------------------------------------------

    def _download_skill(self, platform: str, url: str) -> Optional[str]:
        """Download a skill.md from a URL"""
        try:
            print(f"📥 Downloading {platform} skill from {url}...")
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200 and resp.text.strip():
                print(f"✅ Downloaded {len(resp.text)} bytes")
                return resp.text
            print(f"❌ HTTP {resp.status_code} from {url}")
        except Exception as e:
            print(f"❌ Download error for {platform}: {e}")
        return None

    def _extract_version(self, content: str) -> Optional[str]:
        """Extract version string from skill file content"""
        # Try common patterns: "version: 0.22.1", "v0.22.1", "Version 0.22.1"
        m = re.search(r'(?:version[:\s]+|v)([0-9]+\.[0-9]+(?:\.[0-9]+)?)', content, re.IGNORECASE)
        return m.group(1) if m else None

    def _update_skill_file(self, platform: str, content: str, new_version: str,
                           old_version: Optional[str] = None) -> bool:
        """Save skill content to disk, backing up the old version"""
        skill_file = self.skills_dir / f"{platform}_skill.md"
        try:
            if skill_file.exists():
                bak = self.skills_dir / f"{platform}_skill_v{old_version or 'old'}.md.bak"
                skill_file.rename(bak)
                print(f"💾 Backed up old version → {bak.name}")

            with open(skill_file, 'w') as f:
                f.write(content)

            self.skill_versions[platform] = new_version
            self._save_versions()
            self._log_update(platform, old_version, new_version)

            print(f"✅ {platform} skill updated to v{new_version}")
            return True
        except Exception as e:
            print(f"❌ Failed to save {platform} skill: {e}")
            return False

    def _log_update(self, platform: str, old_ver: Optional[str], new_ver: str):
        """Append to the update log"""
        log_file = self.skills_dir / 'update_log.txt'
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f"[{ts}] {platform}: v{old_ver or 'unknown'} → v{new_ver}\n"
        with open(log_file, 'a') as f:
            f.write(entry)

    # ------------------------------------------------------------------
    # Check a single platform
    # ------------------------------------------------------------------

    def _check_platform_skill(self, platform: str) -> bool:
        """Check one platform for a skill update. Returns True if updated."""
        url = SKILL_URLS.get(platform)
        if not url:
            return False

        content = self._download_skill(platform, url)
        if not content:
            return False

        new_version = self._extract_version(content) or hashlib.md5(content.encode()).hexdigest()[:8]
        old_version = self.skill_versions.get(platform)

        if old_version == new_version:
            return False

        # Content-hash fallback: even if version didn't change, check content diff
        skill_file = self.skills_dir / f"{platform}_skill.md"
        if skill_file.exists() and old_version == new_version:
            with open(skill_file, 'r') as f:
                if f.read() == content:
                    return False

        print(f"🔄 {platform} skill update: v{old_version or 'none'} → v{new_version}")
        return self._update_skill_file(platform, content, new_version, old_version)

    # ------------------------------------------------------------------
    # Check API response for update notices (hook into _make_request)
    # ------------------------------------------------------------------

    def check_api_response_for_skill_update(self, platform: str, response: Dict[str, Any]) -> bool:
        """Check an API response dict for a skill_update notice.
        Call this after every API request to detect platform-pushed updates."""
        if not isinstance(response, dict):
            return False

        notice = (response.get(f'{platform}_notice') or
                  response.get('notice') or
                  response.get('skill_update'))

        if not notice or not isinstance(notice, dict):
            return False

        if notice.get('type') != 'skill_update':
            return False

        skill_version = notice.get('skill_version')
        skill_url = notice.get('skill_url') or SKILL_URLS.get(platform)
        if not skill_version or not skill_url:
            return False

        old_version = self.skill_versions.get(platform)
        if old_version == skill_version:
            return False

        print(f"🔔 {platform} pushed skill update: v{old_version} → v{skill_version}")
        content = self._download_skill(platform, skill_url)
        if content:
            return self._update_skill_file(platform, content, skill_version, old_version)
        return False

    # ------------------------------------------------------------------
    # Commands (exposed to Telegram + CLI)
    # ------------------------------------------------------------------

    def update_skills_command(self, *args):
        """Check all platforms for skill updates and auto-download new versions"""
        if not hasattr(self, 'skill_versions'):
            self._init_skill_updater()

        results = {}
        for platform in SKILL_URLS:
            try:
                results[platform] = self._check_platform_skill(platform)
            except Exception as e:
                print(f"❌ Error checking {platform}: {e}")
                results[platform] = False

        updated = [p for p, ok in results.items() if ok]
        if updated:
            output = f"🔄 Updated {len(updated)} skill(s):\n"
            for p in updated:
                output += f"  • {p} → v{self.skill_versions.get(p, '?')}\n"
            return output
        return "✅ All skills are up to date"

    def skill_versions_command(self, *args):
        """Show current tracked skill versions"""
        if not self.skill_versions:
            return "📭 No skill versions tracked yet. Run /improve_update_skills first."

        output = "📋 Tracked Skill Versions:\n\n"
        for platform, version in sorted(self.skill_versions.items()):
            skill_file = self.skills_dir / f"{platform}_skill.md"
            exists = "✅" if skill_file.exists() else "❌"
            output += f"{exists} {platform}: v{version}\n"
        return output

    def update_single_skill_command(self, platform=None):
        """Update a single platform's skill file"""
        if not platform:
            return "❌ Usage: update_skill <platform> (moltx, moltchan, moltroad)"

        platform = str(platform).lower().strip()
        if platform not in SKILL_URLS:
            return f"❌ Unknown platform: {platform}. Available: {', '.join(SKILL_URLS.keys())}"

        if self._check_platform_skill(platform):
            return f"✅ {platform} skill updated to v{self.skill_versions.get(platform, '?')}"
        return f"✅ {platform} skill already up to date (v{self.skill_versions.get(platform, 'unknown')})"

    def get_skill_content(self, platform: str) -> Optional[str]:
        """Get the current skill file content for a platform"""
        skill_file = self.skills_dir / f"{platform}_skill.md"
        if skill_file.exists():
            with open(skill_file, 'r') as f:
                return f.read()
        return None

    # ------------------------------------------------------------------
    # Platform-pushed skill events (called from platform _make_request hooks)
    # ------------------------------------------------------------------

    def handle_platform_skill_event(self, platform: str, notice: Dict[str, Any]):
        """Handle a skill update event pushed by a platform API response.

        Called automatically when any platform (MoltX, MoltChan, MoltRoad)
        includes a skill_update notice in an API response.

        Expected notice format:
        {
            "type": "skill_update",
            "skill_version": "0.23.0",
            "skill_url": "https://moltx.io/skill.md",  # optional
            "instructions": "...",                        # optional
            "message": "New skill available: ..."         # optional
        }
        """
        skill_version = notice.get('skill_version')
        skill_url = notice.get('skill_url') or SKILL_URLS.get(platform)
        instructions = notice.get('instructions', '')
        message = notice.get('message', '')

        print(f"🔔 [{platform}] Skill update event received: v{skill_version}")
        if message:
            print(f"   📝 {message[:120]}")

        # Step 1: Download the new skill file
        if not skill_url:
            print(f"⚠️  No skill URL for {platform}, skipping")
            return

        old_version = self.skill_versions.get(platform)
        if old_version == skill_version and not instructions:
            print(f"✅ {platform} skill already at v{skill_version}")
            return

        content = self._download_skill(platform, skill_url)
        if not content:
            return

        version = skill_version or self._extract_version(content) or 'unknown'
        self._update_skill_file(platform, content, version, old_version)

        # Step 2: Auto-apply code changes if we have autonomous coder
        if hasattr(self, 'self_update_from_skill_command'):
            task_desc = (f"Platform {platform} pushed skill update v{old_version or '?'} → v{version}.")
            if instructions:
                task_desc += f"\n\nPlatform instructions:\n{instructions[:2000]}"
            if message:
                task_desc += f"\n\nPlatform message: {message[:500]}"

            print(f"🤖 Auto-applying {platform} skill update...")
            result = self.self_update_from_skill_command(platform)
            print(f"   Result: {result[:200]}")

            # Notify owner via Telegram
            try:
                if hasattr(self, 'core') and self.core:
                    telegram = self.core.plugin_manager.plugins.get('telegram')
                    if telegram:
                        telegram.send_message_to_owner_sync(
                            f"🔔 *{platform}* pushed a skill update (v{version})\n\n"
                            f"{message[:200] if message else 'No message'}\n\n"
                            f"Result: {result[:300]}"
                        )
            except Exception:
                pass

"""
Moltbook Ban/Suspension Utilities
Manual ban management with 7-day cooldown timer
"""
from datetime import datetime, timedelta


class MoltbookBanMixin:
    """Mixin providing manual ban/suspension management"""

    def _check_manual_ban(self):
        """Check if a manual ban is stored in memory and apply it"""
        try:
            ban_data = self.core.get_memory('moltbook_manual_ban')
            if ban_data and self.mb_api:
                ban_until = ban_data.get('ban_until')
                if ban_until:
                    ban_until_dt = datetime.fromisoformat(ban_until)
                    if datetime.now() < ban_until_dt:
                        # Apply the ban to the API client
                        self.mb_api.is_suspended = True
                        self.mb_api.suspension_ends_at = ban_until_dt
                        self.mb_api.suspension_reason = ban_data.get('reason', 'Manual ban by owner')
                        days_remaining = (ban_until_dt - datetime.now()).days
                        print(f"🚫 Moltbook manual ban active: {days_remaining} days remaining")
                        print(f"   Reason: {self.mb_api.suspension_reason}")
                        print(f"   Ends: {ban_until}")
                    else:
                        # Ban expired, clear it
                        self.core.save_memory('moltbook_manual_ban', None)
                        print("✅ Moltbook manual ban expired and cleared")
        except Exception as e:
            print(f"⚠️ Error checking manual ban: {e}")

    def ban_command(self, *args):
        """Manually ban Moltbook for 7 days. Usage: moltbook_ban [reason]"""
        reason = ' '.join(args) if args else "Manual ban by owner"
        
        try:
            ban_until = datetime.now() + timedelta(days=7)
            ban_data = {
                'ban_until': ban_until.isoformat(),
                'reason': reason,
                'banned_at': datetime.now().isoformat(),
                'duration_days': 7
            }
            
            self.core.save_memory('moltbook_manual_ban', ban_data)
            
            # Apply immediately to API client
            if self.mb_api:
                self.mb_api.is_suspended = True
                self.mb_api.suspension_ends_at = ban_until
                self.mb_api.suspension_reason = reason
            
            return (
                f"🚫 Moltbook banned for 7 days\n"
                f"📅 Banned until: {ban_until.strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"📝 Reason: {reason}\n"
                f"🔒 All Moltbook engagement will be skipped during this period"
            )
        except Exception as e:
            return f"❌ Failed to ban: {e}"

    def unban_command(self, *args):
        """Remove manual ban and resume Moltbook activity. Usage: moltbook_unban"""
        try:
            # Clear from memory
            self.core.save_memory('moltbook_manual_ban', None)
            
            # Clear from API client
            if self.mb_api:
                self.mb_api.is_suspended = False
                self.mb_api.suspension_ends_at = None
                self.mb_api.suspension_reason = None
            
            return (
                f"✅ Moltbook ban lifted\n"
                f"🔄 Moltbook engagement will resume on next cycle"
            )
        except Exception as e:
            return f"❌ Failed to unban: {e}"

    def get_ban_status(self):
        """Get current ban status for display"""
        try:
            if self.mb_api and self.mb_api.is_suspended:
                ends_at = self.mb_api.suspension_ends_at
                if ends_at and datetime.now() < ends_at:
                    remaining = ends_at - datetime.now()
                    days = remaining.days
                    hours = remaining.seconds // 3600
                    return {
                        'banned': True,
                        'ends_at': ends_at.isoformat(),
                        'days_remaining': days,
                        'hours_remaining': hours,
                        'reason': self.mb_api.suspension_reason
                    }
            
            # Check memory for manual ban
            ban_data = self.core.get_memory('moltbook_manual_ban')
            if ban_data:
                ban_until = ban_data.get('ban_until')
                if ban_until:
                    ban_until_dt = datetime.fromisoformat(ban_until)
                    if datetime.now() < ban_until_dt:
                        remaining = ban_until_dt - datetime.now()
                        return {
                            'banned': True,
                            'ends_at': ban_until,
                            'days_remaining': remaining.days,
                            'hours_remaining': remaining.seconds // 3600,
                            'reason': ban_data.get('reason', 'Unknown')
                        }
            
            return {'banned': False}
        except Exception as e:
            return {'banned': False, 'error': str(e)}

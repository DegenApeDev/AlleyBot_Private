"""
Git Branch Workflow Mixin
Safe git branching for autonomous self-edits with human approval.
"""
import os
import subprocess
import datetime
from typing import Dict, List, Any, Optional


class GitWorkflowMixin:
    """Mixin for git branch workflow - create branches, commit, request merge"""

    def _init_git_workflow(self):
        """Initialize git workflow state"""
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.active_branch: Optional[str] = None
        self.branch_history: List[Dict] = []
        self._load_git_state()

    def _load_git_state(self):
        """Load git workflow state from memory"""
        try:
            state = self.core.get_memory('selfimprove_git_state')
            if state:
                self.branch_history = state.get('branch_history', [])
        except Exception:
            pass

    def _save_git_state(self):
        """Save git workflow state"""
        try:
            self.core.save_memory('selfimprove_git_state', {
                'branch_history': self.branch_history[-50:],
            })
        except Exception as e:
            print(f"⚠️  Failed to save git state: {e}")

    def _run_git(self, *args, check: bool = True) -> Dict[str, Any]:
        """Run a git command safely"""
        try:
            result = subprocess.run(
                ['git'] + list(args),
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'stdout': '', 'stderr': 'Git command timed out', 'returncode': -1}
        except Exception as e:
            return {'success': False, 'stdout': '', 'stderr': str(e), 'returncode': -1}

    def _current_branch(self) -> str:
        """Get current git branch name"""
        result = self._run_git('rev-parse', '--abbrev-ref', 'HEAD')
        return result['stdout'] if result['success'] else 'unknown'

    def _has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes"""
        result = self._run_git('status', '--porcelain')
        return bool(result['stdout'])

    def create_improvement_branch(self, feature_name: str) -> Dict[str, Any]:
        """Create a new branch for a self-improvement task"""
        if not feature_name:
            return {'success': False, 'error': 'Feature name required'}

        # Sanitize branch name
        safe_name = feature_name.lower().replace(' ', '-').replace('_', '-')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '-')
        timestamp = datetime.datetime.now().strftime('%Y%m%d')
        branch_name = f"auto/{safe_name}-{timestamp}"

        # Check for uncommitted changes on current branch
        if self._has_uncommitted_changes():
            return {'success': False, 'error': 'Uncommitted changes on current branch. Commit or stash first.'}

        # Get base branch
        base_branch = self._current_branch()

        # Create and checkout new branch
        result = self._run_git('checkout', '-b', branch_name)
        if not result['success']:
            return {'success': False, 'error': f"Failed to create branch: {result['stderr']}"}

        self.active_branch = branch_name

        record = {
            'branch': branch_name,
            'base': base_branch,
            'feature': feature_name,
            'created': datetime.datetime.now().isoformat(),
            'status': 'active',
            'commits': [],
        }
        self.branch_history.append(record)
        self._save_git_state()

        return {
            'success': True,
            'branch': branch_name,
            'base': base_branch,
            'message': f"Created branch {branch_name} from {base_branch}",
        }

    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Commit changes on the current improvement branch"""
        current = self._current_branch()

        # Safety: only allow commits on auto/ branches
        if not current.startswith('auto/'):
            return {'success': False, 'error': f"Cannot auto-commit on branch '{current}'. Only auto/* branches allowed."}

        if not self._has_uncommitted_changes():
            return {'success': False, 'error': 'No changes to commit'}

        # Stage files
        if files:
            for f in files:
                self._run_git('add', f)
        else:
            self._run_git('add', '-A')

        # Commit
        result = self._run_git('commit', '-m', f"[auto] {message}")
        if not result['success']:
            return {'success': False, 'error': f"Commit failed: {result['stderr']}"}

        # Record commit
        for record in reversed(self.branch_history):
            if record['branch'] == current:
                record['commits'].append({
                    'message': message,
                    'timestamp': datetime.datetime.now().isoformat(),
                })
                break

        self._save_git_state()

        return {
            'success': True,
            'branch': current,
            'message': message,
            'output': result['stdout'],
        }

    def switch_back_to_base(self) -> Dict[str, Any]:
        """Switch back to the base branch (e.g. opus_rebuild)"""
        # Find base branch from history
        current = self._current_branch()
        base = 'opus_rebuild'

        for record in reversed(self.branch_history):
            if record['branch'] == current:
                base = record.get('base', 'opus_rebuild')
                record['status'] = 'pending_review'
                break

        result = self._run_git('checkout', base)
        if not result['success']:
            return {'success': False, 'error': f"Failed to switch to {base}: {result['stderr']}"}

        self.active_branch = None
        self._save_git_state()

        return {
            'success': True,
            'previous': current,
            'current': base,
        }

    def git_branch_command(self, *args):
        """Create an improvement branch. Usage: improve_branch <feature_name>"""
        if not args:
            return "❌ Usage: improve_branch <feature_name>"
        feature = ' '.join(args)
        result = self.create_improvement_branch(feature)
        if result['success']:
            return f"✅ Branch created: {result['branch']}\n📍 Base: {result['base']}"
        return f"❌ {result['error']}"

    def git_commit_command(self, *args):
        """Commit changes on improvement branch. Usage: improve_commit <message>"""
        if not args:
            return "❌ Usage: improve_commit <message>"
        message = ' '.join(args)
        result = self.commit_changes(message)
        if result['success']:
            return f"✅ Committed on {result['branch']}: {message}"
        return f"❌ {result['error']}"

    def git_done_command(self, *args):
        """Finish improvement and switch back to base branch"""
        result = self.switch_back_to_base()
        if result['success']:
            return f"✅ Switched from {result['previous']} → {result['current']}\n📋 Branch ready for review"
        return f"❌ {result['error']}"

    def git_status_command(self, *args):
        """Show git status and improvement branches"""
        current = self._current_branch()
        has_changes = self._has_uncommitted_changes()

        output = "🔧 Git Workflow Status\n\n"
        output += f"  📍 Branch: {current}\n"
        output += f"  {'📝' if has_changes else '✅'} Changes: {'uncommitted' if has_changes else 'clean'}\n\n"

        # Show recent improvement branches
        auto_branches = [b for b in self.branch_history if b['branch'].startswith('auto/')]
        if auto_branches:
            output += "📋 Recent Improvement Branches:\n"
            for b in auto_branches[-5:]:
                status_icon = {'active': '🟢', 'pending_review': '🟡', 'merged': '✅', 'rejected': '❌'}.get(b['status'], '⚪')
                output += f"  {status_icon} {b['branch']} ({b['status']})\n"
                output += f"     Feature: {b['feature']}\n"
                output += f"     Commits: {len(b.get('commits', []))}\n"
        else:
            output += "📋 No improvement branches yet\n"

        return output

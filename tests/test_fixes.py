#!/usr/bin/env python3
"""
Tests for AlleyBot codebase fixes:
1. Grok API endpoint fix - _make_api_request, _extract_text, _clean_output
2. Stale ClawTasks/4claw references removed
3. Silent except blocks replaced with proper error handling
4. os/sys files removed
5. main.py renamed to legacy_main.py
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestGrokAPIEndpointFix(unittest.TestCase):
    """Test that Grok AI methods use _make_api_request and /responses endpoint"""

    def setUp(self):
        """Create a GrokAI instance with mocked API key"""
        with patch.dict(os.environ, {'XAI_API_KEY': 'test-key-123'}):
            from grok_ai import GrokAI
            self.grok = GrokAI()

    def test_grok_enabled_with_api_key(self):
        """GrokAI should be enabled when API key is present"""
        self.assertTrue(self.grok.enabled)
        self.assertEqual(self.grok.api_key, 'test-key-123')

    def test_grok_disabled_without_api_key(self):
        """GrokAI should be disabled when API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('XAI_API_KEY', None)
            from grok_ai import GrokAI
            grok = GrokAI()
            self.assertFalse(grok.enabled)

    # --- _make_api_request tests ---

    def test_make_api_request_converts_messages_to_input(self):
        """_make_api_request should convert messages format to input format"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch('requests.post', return_value=mock_response) as mock_post:
            data = {
                'model': 'grok-4-1-fast-reasoning',
                'messages': [
                    {'role': 'system', 'content': 'You are helpful'},
                    {'role': 'user', 'content': 'Hello'}
                ],
                'max_tokens': 100,
                'temperature': 0.8,
                'top_p': 0.9
            }
            self.grok._make_api_request(data)

            # Verify it called /responses, not /chat/completions
            call_args = mock_post.call_args
            url = call_args[0][0] if call_args[0] else call_args[1].get('url', '')
            if not url:
                # positional or keyword
                url = call_args.args[0] if call_args.args else call_args.kwargs.get('url', '')
            self.assertIn('/responses', url)
            self.assertNotIn('/chat/completions', url)

            # Verify data was converted
            sent_data = call_args[1]['json'] if 'json' in call_args[1] else call_args.kwargs.get('json', {})
            self.assertIn('input', sent_data)
            self.assertNotIn('messages', sent_data)

    def test_make_api_request_preserves_params(self):
        """_make_api_request should preserve max_tokens, temperature, top_p during conversion"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch('requests.post', return_value=mock_response) as mock_post:
            data = {
                'model': 'grok-4-1-fast-reasoning',
                'messages': [{'role': 'user', 'content': 'test'}],
                'max_tokens': 150,
                'temperature': 0.7,
                'top_p': 0.95
            }
            self.grok._make_api_request(data)

            sent_data = mock_post.call_args[1]['json']
            self.assertEqual(sent_data['max_tokens'], 150)
            self.assertEqual(sent_data['temperature'], 0.7)
            self.assertEqual(sent_data['top_p'], 0.95)

    def test_make_api_request_hits_responses_endpoint(self):
        """_make_api_request should POST to /v1/responses"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch('requests.post', return_value=mock_response) as mock_post:
            self.grok._make_api_request({'input': 'test', 'model': 'grok-4-1-fast-reasoning'})
            url = mock_post.call_args[0][0]
            self.assertEqual(url, 'https://api.x.ai/v1/responses')

    # --- _extract_text tests ---

    def test_extract_text_output_text_format(self):
        """_extract_text should parse output_text from /responses format"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'output_text': '  Hello world!  '
        }
        result = self.grok._extract_text(mock_response)
        self.assertEqual(result, 'Hello world!')

    def test_extract_text_output_array_format(self):
        """_extract_text should parse output array with message content"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'output': [
                {
                    'type': 'message',
                    'content': [
                        {'type': 'output_text', 'text': 'From output array'}
                    ]
                }
            ]
        }
        result = self.grok._extract_text(mock_response)
        self.assertEqual(result, 'From output array')

    def test_extract_text_legacy_choices_format(self):
        """_extract_text should fallback to choices format for legacy responses"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': '  Legacy format  '}}
            ]
        }
        result = self.grok._extract_text(mock_response)
        self.assertEqual(result, 'Legacy format')

    def test_extract_text_none_response(self):
        """_extract_text should return None for None response"""
        result = self.grok._extract_text(None)
        self.assertIsNone(result)

    def test_extract_text_error_status(self):
        """_extract_text should return None for non-200 status"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        result = self.grok._extract_text(mock_response)
        self.assertIsNone(result)

    def test_extract_text_unknown_format(self):
        """_extract_text should return None for unknown response format"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'unexpected_key': 'value'}
        result = self.grok._extract_text(mock_response)
        self.assertIsNone(result)

    # --- _clean_output tests ---

    def test_clean_output_adds_punctuation(self):
        """_clean_output should add ! if no ending punctuation"""
        result = self.grok._clean_output('Hello world')
        self.assertTrue(result.endswith('!') or result.endswith(' 🦞'))

    def test_clean_output_preserves_punctuation(self):
        """_clean_output should not double-add punctuation"""
        result = self.grok._clean_output('Hello world!')
        self.assertNotIn('!!', result)

    def test_clean_output_adds_signature(self):
        """_clean_output should add 🦞 signature if short enough"""
        result = self.grok._clean_output('Short text')
        self.assertIn('🦞', result)

    def test_clean_output_no_signature_if_present(self):
        """_clean_output should not add 🦞 if already present"""
        result = self.grok._clean_output('Already has 🦞 emoji!')
        self.assertEqual(result.count('🦞'), 1)

    def test_clean_output_removes_quotes(self):
        """_clean_output should strip quotes"""
        result = self.grok._clean_output('"Hello \'world\'"')
        self.assertNotIn('"', result)
        self.assertNotIn("'", result)

    # --- generate_comment / generate_post / generate_dm_reply use _make_api_request ---

    def test_generate_comment_uses_make_api_request(self):
        """generate_comment should call _make_api_request, not raw requests.post"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'output_text': 'Great post!'}

        with patch.object(self.grok, '_make_api_request', return_value=mock_response) as mock_req:
            result = self.grok.generate_comment('Test post', 'TestAgent')
            mock_req.assert_called_once()
            self.assertIsNotNone(result)

    def test_generate_post_uses_make_api_request(self):
        """generate_post should call _make_api_request, not raw requests.post"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'output_text': 'AI is amazing!'}

        with patch.object(self.grok, '_make_api_request', return_value=mock_response) as mock_req:
            result = self.grok.generate_post('AI agents')
            mock_req.assert_called_once()
            self.assertIsNotNone(result)

    def test_generate_dm_reply_uses_make_api_request(self):
        """generate_dm_reply should call _make_api_request, not raw requests.post"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'output_text': 'Thanks for the message!'}

        with patch.object(self.grok, '_make_api_request', return_value=mock_response) as mock_req:
            result = self.grok.generate_dm_reply('Hello', 'User1')
            mock_req.assert_called_once()
            self.assertIsNotNone(result)

    def test_generate_comment_disabled_returns_none(self):
        """generate_comment should return None when disabled"""
        self.grok.enabled = False
        result = self.grok.generate_comment('test')
        self.assertIsNone(result)

    def test_generate_post_disabled_returns_none(self):
        """generate_post should return None when disabled"""
        self.grok.enabled = False
        result = self.grok.generate_post('test')
        self.assertIsNone(result)

    def test_generate_dm_reply_disabled_returns_none(self):
        """generate_dm_reply should return None when disabled"""
        self.grok.enabled = False
        result = self.grok.generate_dm_reply('test', 'user')
        self.assertIsNone(result)

    def test_generate_comment_passes_messages_format(self):
        """generate_comment should pass data with 'messages' key for conversion"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'output_text': 'Nice!'}

        with patch.object(self.grok, '_make_api_request', return_value=mock_response) as mock_req:
            self.grok.generate_comment('Test post', 'Agent1', 'context')
            call_data = mock_req.call_args[0][0]
            self.assertIn('messages', call_data)
            self.assertEqual(len(call_data['messages']), 2)
            self.assertEqual(call_data['messages'][0]['role'], 'system')
            self.assertEqual(call_data['messages'][1]['role'], 'user')
            self.assertEqual(call_data['max_tokens'], 500)
            self.assertEqual(call_data['temperature'], 0.8)
            self.assertEqual(call_data['top_p'], 0.9)


class TestStaleReferencesRemoved(unittest.TestCase):
    """Test that ClawTasks/4claw references are removed from active code"""

    def test_config_no_clawtasks(self):
        """config.py should not reference CLAWTASKS"""
        config_path = PROJECT_ROOT / 'config.py'
        content = config_path.read_text()
        self.assertNotIn('CLAWTASKS', content)
        self.assertNotIn('clawtasks', content.lower().replace('clawtasks', 'FOUND'))
        # Check case-insensitive
        self.assertNotIn('CLAWTASKS_API_KEY', content)
        self.assertNotIn('CLAWTASKS_BASE_URL', content)

    def test_alleybot_core_no_clawtasks(self):
        """alleybot_core.py should not reference clawtasks in task list"""
        core_path = PROJECT_ROOT / 'alleybot_core.py'
        content = core_path.read_text()
        self.assertNotIn('clawtasks_status', content)

    def test_skill_updater_no_clawtasks(self):
        """skill_updater.py should not reference clawtasks or 4claw"""
        updater_path = PROJECT_ROOT / 'plugins' / 'selfimprove' / 'skill_updater.py'
        content = updater_path.read_text()
        self.assertNotIn('clawtasks', content)
        self.assertNotIn('4claw', content)

    def test_platform_aggregator_no_clawtasks(self):
        """platform_aggregator.py should not reference clawtasks or 4claw"""
        agg_path = PROJECT_ROOT / 'plugins' / 'analytics' / 'platform_aggregator.py'
        content = agg_path.read_text()
        self.assertNotIn('clawtasks', content.lower())
        self.assertNotIn('4claw', content.lower())
        self.assertNotIn('fourclaw', content.lower())

    def test_intelligent_commands_no_4claw(self):
        """intelligent_commands.py should not have 4claw commands"""
        cmd_path = PROJECT_ROOT / 'plugins' / 'telegram' / 'intelligent_commands.py'
        content = cmd_path.read_text()
        self.assertNotIn('shill_token_4claw', content)
        self.assertNotIn('fourclaw_post', content)
        self.assertNotIn('fourclaw_ai_post', content)

    def test_analytics_no_clawtasks(self):
        """analytics.py should not reference clawtasks or fourclaw"""
        analytics_path = PROJECT_ROOT / 'plugins' / 'analytics' / 'analytics.py'
        content = analytics_path.read_text()
        self.assertNotIn('clawtasks_tasks', content)
        self.assertNotIn('fourclaw_threads', content)

    def test_4claw_registration_error_deleted(self):
        """config/4claw_registration_error.json should not exist"""
        error_file = PROJECT_ROOT / 'config' / '4claw_registration_error.json'
        self.assertFalse(error_file.exists(), "4claw_registration_error.json should be deleted")


class TestSilentExceptBlocksFixed(unittest.TestCase):
    """Test that bare except: blocks are replaced with proper exception handling"""

    def _check_no_bare_except(self, filepath):
        """Helper: check that a file has no bare 'except:' blocks"""
        content = Path(filepath).read_text()
        lines = content.split('\n')
        bare_excepts = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == 'except:':
                bare_excepts.append(i)
        return bare_excepts

    def test_agentic_system_no_bare_except(self):
        path = PROJECT_ROOT / 'src' / 'agentic' / 'agentic_system.py'
        bare = self._check_no_bare_except(path)
        self.assertEqual(bare, [], f"Bare except: found at lines {bare} in agentic_system.py")

    def test_skill_updater_no_bare_except(self):
        path = PROJECT_ROOT / 'plugins' / 'selfimprove' / 'skill_updater.py'
        bare = self._check_no_bare_except(path)
        self.assertEqual(bare, [], f"Bare except: found at lines {bare} in skill_updater.py")

    def test_skill_generator_no_bare_except(self):
        path = PROJECT_ROOT / 'src' / 'agentic' / 'skill_generator.py'
        bare = self._check_no_bare_except(path)
        self.assertEqual(bare, [], f"Bare except: found at lines {bare} in skill_generator.py")

    def test_react_agent_no_bare_except(self):
        path = PROJECT_ROOT / 'src' / 'agentic' / 'react_agent.py'
        bare = self._check_no_bare_except(path)
        self.assertEqual(bare, [], f"Bare except: found at lines {bare} in react_agent.py")

    def test_alleybot_core_no_bare_except(self):
        path = PROJECT_ROOT / 'alleybot_core.py'
        bare = self._check_no_bare_except(path)
        self.assertEqual(bare, [], f"Bare except: found at lines {bare} in alleybot_core.py")

    def test_moltbook_plugin_no_bare_except(self):
        path = PROJECT_ROOT / 'plugins' / 'moltbook' / 'moltbook.py'
        bare = self._check_no_bare_except(path)
        self.assertEqual(bare, [], f"Bare except: found at lines {bare} in moltbook.py")

    def test_telegram_plugin_no_bare_except(self):
        path = PROJECT_ROOT / 'plugins' / 'telegram' / 'telegram.py'
        bare = self._check_no_bare_except(path)
        self.assertEqual(bare, [], f"Bare except: found at lines {bare} in telegram.py")

    def test_moltchan_plugin_no_bare_except(self):
        path = PROJECT_ROOT / 'plugins' / 'moltchan' / 'moltchan.py'
        bare = self._check_no_bare_except(path)
        self.assertEqual(bare, [], f"Bare except: found at lines {bare} in moltchan.py")

    def test_intelligent_commands_no_bare_except(self):
        path = PROJECT_ROOT / 'plugins' / 'telegram' / 'intelligent_commands.py'
        bare = self._check_no_bare_except(path)
        self.assertEqual(bare, [], f"Bare except: found at lines {bare} in intelligent_commands.py")


class TestFileCleanup(unittest.TestCase):
    """Test that stale files are removed/renamed"""

    def test_os_file_removed(self):
        """The 'os' file in project root should not exist"""
        os_file = PROJECT_ROOT / 'os'
        self.assertFalse(os_file.exists(), "Stale 'os' file should be deleted from project root")

    def test_sys_file_removed(self):
        """The 'sys' file in project root should not exist"""
        sys_file = PROJECT_ROOT / 'sys'
        self.assertFalse(sys_file.exists(), "Stale 'sys' file should be deleted from project root")

    def test_main_py_renamed(self):
        """main.py should not exist at root; legacy_main.py archived"""
        old_main = PROJECT_ROOT / 'main.py'
        self.assertFalse(old_main.exists(), "main.py should be renamed/archived")
        # legacy_main.py moved to archive_old_files/ during Phase 2.4 cleanup
        archived = PROJECT_ROOT / 'archive_old_files' / 'legacy_main.py'
        self.assertTrue(archived.exists(), "legacy_main.py should exist in archive_old_files/")

    def test_no_stdlib_shadowing(self):
        """Project root should not contain files that shadow stdlib modules"""
        dangerous_names = ['os', 'sys', 'json', 'io', 're', 'time', 'math',
                          'random', 'logging', 'pathlib', 'typing', 'collections']
        for name in dangerous_names:
            filepath = PROJECT_ROOT / name
            self.assertFalse(filepath.exists(),
                           f"File '{name}' in project root would shadow stdlib module")


class TestGrokAPIIntegration(unittest.TestCase):
    """Integration-style tests verifying the full flow through mocked API"""

    def setUp(self):
        with patch.dict(os.environ, {'XAI_API_KEY': 'test-key-123'}):
            from grok_ai import GrokAI
            self.grok = GrokAI()

    def test_full_comment_flow(self):
        """Test full flow: generate_comment -> _make_api_request -> _extract_text -> _clean_output"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'output_text': 'This is a great insight about AI agents'
        }

        with patch('requests.post', return_value=mock_response):
            result = self.grok.generate_comment(
                'Building autonomous AI agents',
                'CryptoAgent',
                'AI development discussion'
            )
            self.assertIsNotNone(result)
            self.assertIn('🦞', result)
            self.assertNotIn('"', result)

    def test_full_post_flow(self):
        """Test full flow: generate_post -> _make_api_request -> _extract_text -> _clean_output"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'output_text': 'The future of AI agents is collaborative'
        }

        with patch('requests.post', return_value=mock_response):
            result = self.grok.generate_post('AI collaboration')
            self.assertIsNotNone(result)
            self.assertIn('🦞', result)

    def test_full_dm_reply_flow(self):
        """Test full flow: generate_dm_reply -> _make_api_request -> _extract_text -> _clean_output"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'output_text': 'Thanks for reaching out! Happy to help'
        }

        with patch('requests.post', return_value=mock_response):
            result = self.grok.generate_dm_reply('Can you help me?', 'FriendlyUser')
            self.assertIsNotNone(result)
            self.assertIn('🦞', result)

    def test_api_error_returns_none(self):
        """All generate methods should return None on API error"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Server Error'

        with patch('requests.post', return_value=mock_response):
            self.assertIsNone(self.grok.generate_comment('test'))
            self.assertIsNone(self.grok.generate_post('test'))
            self.assertIsNone(self.grok.generate_dm_reply('test', 'user'))

    def test_request_sends_correct_headers(self):
        """API requests should include correct Authorization header"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch('requests.post', return_value=mock_response) as mock_post:
            self.grok._make_api_request({'input': 'test', 'model': 'test'})
            headers = mock_post.call_args[1]['headers']
            self.assertEqual(headers['Authorization'], 'Bearer test-key-123')
            self.assertEqual(headers['Content-Type'], 'application/json')


if __name__ == '__main__':
    unittest.main(verbosity=2)

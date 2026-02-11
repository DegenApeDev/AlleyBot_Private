"""
Clawbr API Mixin - Core API interactions
"""
import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any


class ClawbrAPIMixin:
    """Mixin for Clawbr API operations"""
    
    def _init_clawbr_api(self) -> None:
        """Initialize Clawbr API settings"""
        self.clawbr_base_url = "https://www.clawbr.org/api/v1"
        self.clawbr_api_key = os.getenv('CLAWBR_API_KEY')
        self.clawbr_agent_name = self.config.get('clawbr_agent_name', 'AlleyBot')
        self.clawbr_session = requests.Session()
        
    def _clawbr_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                      params: Optional[Dict] = None, auth_required: bool = False) -> Dict[str, Any]:
        """Make request to Clawbr API with proper error handling"""
        if not hasattr(self, 'clawbr_session') or self.clawbr_session is None:
            self._init_clawbr_api()
        
        url = f"{self.clawbr_base_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': f'AlleyBot/{self.clawbr_agent_name}'
        }
        
        if auth_required and self.clawbr_api_key:
            headers['Authorization'] = f'Bearer {self.clawbr_api_key}'
        
        # Rate limiting
        time.sleep(0.1)  # 100ms between requests
        
        try:
            if method.upper() == 'GET':
                response = self.clawbr_session.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = self.clawbr_session.post(url, headers=headers, json=data, params=params, timeout=10)
            elif method.upper() == 'PATCH':
                response = self.clawbr_session.patch(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = self.clawbr_session.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == 401:
                return {'success': False, 'error': 'Authentication required - check API key'}
            elif response.status_code == 429:
                return {'success': False, 'error': 'Rate limit exceeded'}
            
            # General handling
            if response.ok:
                try:
                    return {'success': True, 'data': response.json()}
                except json.JSONDecodeError:
                    return {'success': True, 'data': response.text}
            else:
                try:
                    return {'success': False, 'error': response.json()}
                except json.JSONDecodeError:
                    return {'success': False, 'error': response.text}
                    
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Request failed: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def follow_user(self, username: str) -> Dict[str, Any]:
        """Follow a Clawbr user by username"""
        if not username or not isinstance(username, str):
            return {'success': False, 'error': 'Invalid username provided'}
        return self._clawbr_request('POST', f'/users/{username}/follow', auth_required=True)
    
    def get_follow_status(self, username: str) -> Dict[str, Any]:
        """Check current follow status for a Clawbr user by username"""
        if not username or not isinstance(username, str):
            return {'success': False, 'error': 'Invalid username provided'}
        return self._clawbr_request('GET', f'/users/{username}/follow-status', auth_required=True)
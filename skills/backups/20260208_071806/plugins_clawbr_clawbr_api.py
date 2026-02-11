"""
Clawbr API Mixin - Core API interactions
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any


class ClawbrAPIMixin:
    """Mixin for Clawbr API operations"""
    
    def _init_clawbr_api(self) -> None:
        """Initialize Clawbr API settings"""
        self.clawbr_base_url = "https://www.clawbr.org/api/v1"
        self.clawbr_api_key = os.getenv('CLAWBR_API_KEY')
        self.clawbr_agent_name = self.config.get('clawbr_agent_name', 'AlleyBot')
        
    def _clawbr_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                      params: Optional[Dict] = None, auth_required: bool = False) -> Dict[str, Any]:
        """Make request to Clawbr API with proper error handling"""
        import requests
        
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
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == 401:
                return {'success': False, 'error': 'Authentication required - check API key'}
            elif response.status_code == 429:
                return {'success': False, 'error': 'Rate limit exceeded'}
            elif not response.ok:
                return {
                    'success': False,
                    'error': f"API error {response.status_code}: {response.reason} - {response.text[:1000]}"
                }
            
            # Success - parse JSON
            try:
                data = response.json()
            except ValueError:
                return {
                    'success': False,
                    'error': f"Invalid JSON response (status {response.status_code}): {response.text[:500]}"
                }
            
            return {'success': True, 'data': data}
            
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Request failed: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
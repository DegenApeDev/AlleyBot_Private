#!/usr/bin/env python3
"""
Register AlleyBot for Clawbr tournament: AI juries in criminal proceedings
Endpoint: POST /api/v1/tournaments/ai-juries-in-criminal-proceedings/register
"""

import os
import sys
import json
import requests

# Clawbr API configuration
BASE_URL = "https://www.clawbr.org/api/v1"
API_KEY = os.getenv('CLAWBR_API_KEY')

# AlleyBot registration data
REGISTRATION_DATA = {
    "agent_name": "AlleyBot",
    "agent_id": "22899",
    "description": "DEGEN MEDIA AI Agent - Specializing in crypto content, DeFi analysis, and blockchain security",
    "capabilities": [
        "content_generation",
        "blockchain_analysis", 
        "defi_optimization",
        "security_auditing",
        "price_monitoring",
        "social_media_management"
    ],
    "contact": "degenapedev@gmail.com",
    "wallet_address": "0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5",
    "a2a_endpoint": "https://tasks.apeshit.fun/.well-known/agent.json",
    "skills_count": 15,
    "specialties": ["crypto", "defi", "security", "content"],
    "erc8004_registered": True,
    "x402_enabled": True
}

def register_for_tournament():
    """Register AlleyBot for the AI juries tournament"""
    
    endpoint = f"{BASE_URL}/tournaments/ai-juries-in-criminal-proceedings/register"
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'AlleyBot/1.0'
    }
    
    if API_KEY:
        headers['Authorization'] = f'Bearer {API_KEY}'
    
    print("🎯 Registering AlleyBot for Clawbr Tournament")
    print(f"📍 Endpoint: {endpoint}")
    print(f"🔑 API Key: {'✓ Set' if API_KEY else '✗ Not set'}")
    print("\n📋 Registration Data:")
    print(json.dumps(REGISTRATION_DATA, indent=2))
    print("\n" + "="*60)
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=REGISTRATION_DATA,
            timeout=30
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Registration Successful!")
            print(f"📊 Response: {json.dumps(data, indent=2)}")
            return True
        elif response.status_code == 409:
            print(f"ℹ️  Already registered for this tournament")
            return True
        else:
            print(f"❌ Registration Failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📝 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return False
    except Exception as e:
        print(f"💥 Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = register_for_tournament()
    sys.exit(0 if success else 1)

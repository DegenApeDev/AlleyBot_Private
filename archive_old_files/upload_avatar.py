#!/usr/bin/env python3
"""
Upload AlleyBot avatar to Moltx
"""

import sys
import os
import json
sys.path.insert(0, '/home/degendev/Dev/Agents/MoltbookBot')

from plugins.moltx.moltx import MoltxPlugin

def main():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('MOLTX_API_KEY')
    
    if not api_key:
        print("❌ MOLTX_API_KEY not found in environment")
        return
    
    # Initialize Moltx plugin
    moltx = MoltxPlugin(None)
    
    # Manually set credentials
    moltx.api_key = api_key
    moltx.agent_name = 'AlleyBot'
    moltx.base_url = 'https://moltx.io/v1'
    moltx.initialized = True
    
    print(f"✅ Moltx initialized for agent: {moltx.agent_name}")
    
    # Upload avatar
    avatar_path = '/home/degendev/Dev/Agents/MoltbookBot/img/alleybot.jpeg'
    
    if not os.path.exists(avatar_path):
        print(f"❌ Avatar image not found: {avatar_path}")
        return
    
    print(f"📸 Uploading avatar from: {avatar_path}")
    result = moltx.upload_avatar(avatar_path)
    
    print(result)

if __name__ == '__main__':
    main()

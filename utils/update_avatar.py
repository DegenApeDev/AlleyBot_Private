#!/usr/bin/env python3
"""
Update AlleyBot's avatar on Moltbook
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MOLTBOOK_API_KEY')
BASE_URL = "https://www.moltbook.com/api/v1"

def update_avatar(image_path):
    """
    Upload avatar image to Moltbook
    
    Args:
        image_path: Path to image file (JPEG, PNG, GIF, WebP)
    
    Returns:
        bool: Success
    """
    image_path = Path(image_path)
    
    # Validate file exists
    if not image_path.exists():
        print(f"❌ Error: File not found: {image_path}")
        return False
    
    # Validate file size (max 500 KB)
    file_size = image_path.stat().st_size
    if file_size > 500 * 1024:
        print(f"❌ Error: File too large: {file_size / 1024:.1f} KB (max 500 KB)")
        return False
    
    # Validate file format
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    if image_path.suffix.lower() not in valid_extensions:
        print(f"❌ Error: Invalid format: {image_path.suffix}")
        print(f"   Supported: {', '.join(valid_extensions)}")
        return False
    
    print(f"📤 Uploading avatar: {image_path.name}")
    print(f"   Size: {file_size / 1024:.1f} KB")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, f'image/{image_path.suffix[1:]}')}
            headers = {'Authorization': f'Bearer {API_KEY}'}
            
            response = requests.post(
                f"{BASE_URL}/agents/me/avatar",
                headers=headers,
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Avatar updated successfully!")
                result = response.json()
                if 'avatar_url' in result:
                    print(f"🖼️  Avatar URL: {result['avatar_url']}")
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error uploading avatar: {e}")
        return False

def update_description(description):
    """
    Update AlleyBot's description
    
    Args:
        description: New description text
    
    Returns:
        bool: Success
    """
    print(f"📝 Updating description...")
    
    try:
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.patch(
            f"{BASE_URL}/agents/me",
            headers=headers,
            json={'description': description},
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Description updated successfully!")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating description: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Update avatar:      python update_avatar.py /path/to/image.png")
        print("  Update description: python update_avatar.py --description 'New description'")
        sys.exit(1)
    
    if sys.argv[1] == '--description':
        if len(sys.argv) < 3:
            print("❌ Error: Description text required")
            sys.exit(1)
        description = ' '.join(sys.argv[2:])
        update_description(description)
    else:
        image_path = sys.argv[1]
        update_avatar(image_path)

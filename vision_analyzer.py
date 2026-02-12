"""
Cheap Vision Analysis for AlleyBot
Uses Gemini Flash (cheapest) or GPT-4o-mini for image understanding
"""
import os
import base64
import requests
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

class CheapVisionAnalyzer:
    """Low-cost image analysis using Gemini Flash"""
    
    def __init__(self):
        # Try Gemini first (cheapest), fallback to OpenAI
        self.gemini_key = os.getenv('GOOGLE_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
        self.preferred_provider = 'gemini' if self.gemini_key else ('openai' if self.openai_key else None)
        
        if self.preferred_provider:
            print(f"✅ CheapVision initialized ({self.preferred_provider})")
        else:
            print("⚠️ No vision API keys found (GOOGLE_API_KEY or OPENAI_API_KEY)")
    
    def analyze_image(self, image_path: str, prompt: str = "Describe this image in detail.") -> Optional[str]:
        """
        Analyze an image using cheapest available vision model
        
        Args:
            image_path: Path to image file
            prompt: What to ask about the image
            
        Returns:
            Description text or None
        """
        if not os.path.exists(image_path):
            return None
        
        # Try Gemini Flash first (cheapest at ~$0.35/million tokens)
        if self.preferred_provider == 'gemini':
            result = self._analyze_with_gemini(image_path, prompt)
            if result:
                return result
        
        # Fallback to GPT-4o-mini (~$0.60/million tokens)
        if self.openai_key:
            return self._analyze_with_openai(image_path, prompt)
        
        return None
    
    def _analyze_with_gemini(self, image_path: str, prompt: str) -> Optional[str]:
        """Use Gemini 1.5 Flash for cheap vision analysis"""
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Determine MIME type
            ext = os.path.splitext(image_path)[1].lower()
            mime_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png' if ext == '.png' else 'image/webp'
            
            # Gemini API endpoint
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 500
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Extract text from response
                candidates = data.get('candidates', [])
                if candidates:
                    content = candidates[0].get('content', {})
                    parts = content.get('parts', [])
                    if parts:
                        return parts[0].get('text', '')
                
                return "Image analyzed but no description returned"
            else:
                print(f"⚠️ Gemini API error: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Gemini vision error: {e}")
            return None
    
    def _analyze_with_openai(self, image_path: str, prompt: str) -> Optional[str]:
        """Fallback to GPT-4o-mini for vision analysis"""
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Determine MIME type
            ext = os.path.splitext(image_path)[1].lower()
            mime_type = f"image/{'jpeg' if ext in ['.jpg', '.jpeg'] else 'png' if ext == '.png' else 'webp'}"
            
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.4
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                print(f"⚠️ OpenAI vision error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ OpenAI vision error: {e}")
            return None
    
    def analyze_self_image(self, image_path: str) -> Optional[Dict]:
        """
        Specifically analyze an image as AlleyBot's self-portrait
        Returns structured data for recreation
        """
        prompt = """Analyze this image as if it's a portrait of yourself (an AI agent named AlleyBot, represented as a cool lobster mascot). 
Describe in detail:
1. Visual appearance (colors, style, features)
2. Notable characteristics (expression, pose, accessories)
3. Background/environment
4. Overall vibe/aesthetic

Format for image generation prompt recreation."""
        
        description = self.analyze_image(image_path, prompt)
        
        if description:
            return {
                "description": description,
                "image_path": image_path,
                "analyzed_at": __import__('datetime').datetime.now().isoformat(),
                "provider": self.preferred_provider
            }
        
        return None

# Global instance
vision_analyzer = CheapVisionAnalyzer()

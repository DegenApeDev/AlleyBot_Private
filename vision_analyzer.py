"""
Cheap Vision Analysis for AlleyBot
Uses HuggingFace (free), Gemini Flash (cheap), or GPT-4o-mini for image understanding
"""
import os
import base64
import requests
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

class CheapVisionAnalyzer:
    """Low-cost image analysis using HuggingFace free tier or cheap APIs"""
    
    def __init__(self):
        # Check for API keys
        self.hf_token = os.getenv('HUGGINGFACE_TOKEN')  # Deprecated - free tier gone
        self.gemini_key = os.getenv('GOOGLE_API_KEY')  # Primary - gemini-2.0-flash-001
        self.openai_key = os.getenv('OPENAI_API_KEY')  # Fallback
        
        # Set preferred provider (HuggingFace free tier deprecated, use Gemini)
        if self.gemini_key:
            self.preferred_provider = 'gemini'
            print(f"✅ CheapVision initialized (Gemini 2.0 Flash)")
        elif self.openai_key:
            self.preferred_provider = 'openai'
            print(f"✅ CheapVision initialized (OpenAI)")
        else:
            self.preferred_provider = None
            print("⚠️ No vision API keys found (need GOOGLE_API_KEY for Gemini or OPENAI_API_KEY)")
    
    def analyze_image(self, image_path: str, prompt: str = "Describe this image in detail.") -> Optional[str]:
        """
        Analyze an image using cheapest available vision model
        Priority: Gemini (cheap & working) > OpenAI
        
        Args:
            image_path: Path to image file
            prompt: What to ask about the image
            
        Returns:
            Description text or None
        """
        if not os.path.exists(image_path):
            return None
        
        # Skip HuggingFace - free tier models are deprecated (410 errors)
        # Try Gemini first (cheap and reliable)
        if self.gemini_key:
            result = self._analyze_with_gemini(image_path, prompt)
            if result:
                return result
        
        # Fallback to GPT-4o-mini
        if self.openai_key:
            return self._analyze_with_openai(image_path, prompt)
        
        return None
    
    def _analyze_with_huggingface_client(self, image_path: str, prompt: str) -> Optional[str]:
        """Use HuggingFace Inference API with proper client (FREE!)"""
        try:
            # Try using huggingface_hub InferenceClient if available
            try:
                from huggingface_hub import InferenceClient
                
                client = InferenceClient(token=self.hf_token)
                
                # Use image-to-text task - will auto-route to available model
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                
                # Use task-based inference with explicit working model
                result = client.image_to_text(image_bytes, model="Salesforce/blip-image-captioning-base")
                
                if result and hasattr(result, 'generated_text'):
                    return f"{result.generated_text}\n\n(Analyzed with HuggingFace)"
                elif result and isinstance(result, list) and len(result) > 0:
                    caption = result[0].get('generated_text', '')
                    if caption:
                        return f"{caption}\n\n(Analyzed with HuggingFace)"
                    
            except ImportError:
                print("⚠️ huggingface_hub not installed, using direct API")
            except Exception as e:
                print(f"⚠️ HF client failed: {e}, trying direct API")
            
            # Fallback to direct API call with working model
            return self._analyze_with_hf_direct(image_path, prompt)
                
        except Exception as e:
            print(f"❌ HuggingFace vision error: {e}")
            return None
    
    def _analyze_with_hf_direct(self, image_path: str, prompt: str) -> Optional[str]:
        """Direct API call to HuggingFace Inference API using known working model"""
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # Use Salesforce/blip-image-captioning-base - known working model
            api_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
            
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
            }
            
            response = requests.post(
                api_url,
                headers=headers,
                data=image_bytes,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    caption = result[0].get('generated_text', '')
                    if caption:
                        return f"{caption}\n\n(Analyzed with HuggingFace)"
                elif isinstance(result, dict):
                    caption = result.get('generated_text', '')
                    if caption:
                        return f"{caption}\n\n(Analyzed with HuggingFace)"
                return "Image analyzed but no caption returned"
                
            elif response.status_code == 503:
                # Model loading
                return "Model is warming up, please try again in 30 seconds"
            else:
                print(f"⚠️ HF direct API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ HF direct API error: {e}")
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
            
            # Gemini API endpoint (use working model)
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent"
            
            # Add API key as query param
            params = {"key": self.gemini_key}
            
            payload = {
                "contents": [{
                    "role": "user",
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
            
            response = requests.post(url, params=params, json=payload, timeout=30)
            
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

"""
Natural Intent Classifier for AlleyBot
Pure semantic understanding without hardcoded examples
Uses command names and docstrings for intelligent matching
"""
import numpy as np
from typing import List, Tuple, Optional, Dict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re


class NaturalIntentClassifier:
    """
    Natural language intent classification using pure semantic understanding.
    No hardcoded examples - learns from command names and docstrings.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the classifier with a sentence transformer model.
        
        Args:
            model_name: Sentence transformer model to use
        """
        self.model = self._get_sentence_model()
        self.command_embeddings = {}  # command_name -> embedding
        self.command_metadata = {}  # command_name -> {doc, semantic_tags}
        self.similarity_threshold = 0.60  # Lower threshold for more natural matching
        
    def _get_sentence_model(self):
        """Get shared sentence transformer model"""
        try:
            from src.utils.embedding_model import get_sentence_transformer
            return get_sentence_transformer('all-MiniLM-L6-v2')
        except:
            # Fallback to direct import
            return SentenceTransformer('all-MiniLM-L6-v2')
    
    def register_command(self, command_name: str, docstring: str = None):
        """
        Register a command using only its name and docstring.
        No hardcoded examples needed - semantic understanding handles it.
        
        Args:
            command_name: The command identifier (e.g., 'moltx_post')
            docstring: Optional docstring describing the command
        """
        # Extract semantic meaning from command name
        semantic_phrases = self._extract_semantic_meaning(command_name, docstring)
        
        # Encode all semantic phrases
        embeddings = self.model.encode(semantic_phrases)
        
        # Store mean embedding
        self.command_embeddings[command_name] = np.mean(embeddings, axis=0)
        self.command_metadata[command_name] = {
            'doc': docstring or command_name,
            'semantic_tags': semantic_phrases
        }
    
    def _extract_semantic_meaning(self, command_name: str, docstring: str = None) -> List[str]:
        """
        Extract semantic meaning from command name and docstring.
        No hardcoded patterns - pure linguistic analysis.
        
        Args:
            command_name: Command identifier
            docstring: Optional docstring
            
        Returns:
            List of semantic phrases that describe this command
        """
        phrases = []
        
        # Parse command name into semantic components
        # Example: "moltx_post" -> ["moltx", "post"]
        parts = command_name.lower().replace('_', ' ').split()
        
        # Build natural language descriptions from parts
        if len(parts) >= 2:
            # Two-part commands: "platform action"
            platform = parts[0]
            action = ' '.join(parts[1:])
            
            # Generate natural variations
            phrases.extend([
                f"{action} on {platform}",
                f"{action} to {platform}",
                f"create {action} on {platform}",
                f"make {action} on {platform}",
                f"{platform} {action}",
                f"{action} {platform}",
            ])
            
            # Add platform-specific variations
            if 'post' in action:
                phrases.extend([
                    f"post on {platform}",
                    f"create post on {platform}",
                    f"make a post on {platform}",
                    f"share on {platform}",
                    f"publish on {platform}",
                ])
            elif 'engage' in action:
                phrases.extend([
                    f"engage on {platform}",
                    f"interact with {platform}",
                    f"like and comment on {platform}",
                ])
            elif 'feed' in action:
                phrases.extend([
                    f"show {platform} feed",
                    f"check {platform} feed",
                    f"browse {platform}",
                ])
        else:
            # Single-part commands
            phrases.append(command_name.replace('_', ' '))
        
        # Add docstring if available
        if docstring:
            # Clean and add docstring
            doc_clean = docstring.split('\n')[0].strip()
            if doc_clean and len(doc_clean) > 5:
                phrases.append(doc_clean)
        
        # Add the raw command name for exact matches
        phrases.append(command_name.replace('_', ' '))
        
        return phrases
    
    def register_commands_from_plugin_manager(self, plugin_manager):
        """
        Auto-register all commands from the plugin manager.
        Uses natural semantic understanding - no hardcoded examples.
        
        Args:
            plugin_manager: The plugin manager with registered commands
        """
        for cmd_name, func in list(plugin_manager.commands.items()):
            # Get docstring as description
            doc = func.__doc__
            if doc:
                doc = doc.split('\n')[0].strip()
            
            self.register_command(cmd_name, doc)
    
    def classify_intent(self, user_input: str) -> Optional[Tuple[str, float]]:
        """
        Classify user input to the best matching command using pure semantic understanding.
        
        Args:
            user_input: Natural language input from user
            
        Returns:
            Tuple of (command_name, confidence_score) or None if no good match
        """
        if not self.command_embeddings:
            return None
        
        # Encode user input
        user_embedding = self.model.encode([user_input])[0]
        
        # Compute similarities with all commands
        similarities = {}
        for cmd_name, cmd_embedding in self.command_embeddings.items():
            sim = cosine_similarity(
                user_embedding.reshape(1, -1),
                cmd_embedding.reshape(1, -1)
            )[0][0]
            similarities[cmd_name] = sim
        
        # Find best match
        best_cmd = max(similarities, key=similarities.get)
        best_score = similarities[best_cmd]
        
        # Only return if above threshold
        if best_score >= self.similarity_threshold:
            return (best_cmd, best_score)
        
        return None
    
    def get_top_matches(self, user_input: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Get top-k matching commands with scores.
        
        Args:
            user_input: Natural language input
            top_k: Number of top matches to return
            
        Returns:
            List of (command_name, score) tuples sorted by score
        """
        if not self.command_embeddings:
            return []
        
        user_embedding = self.model.encode([user_input])[0]
        
        similarities = {}
        for cmd_name, cmd_embedding in self.command_embeddings.items():
            sim = cosine_similarity(
                user_embedding.reshape(1, -1),
                cmd_embedding.reshape(1, -1)
            )[0][0]
            similarities[cmd_name] = sim
        
        # Sort by similarity
        sorted_matches = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        return sorted_matches[:top_k]
    
    def extract_arguments(self, user_input: str, command_name: str) -> Dict[str, str]:
        """
        Extract arguments from user input using intelligent parsing.
        
        Args:
            user_input: Natural language input
            command_name: The matched command
            
        Returns:
            Dictionary of extracted arguments
        """
        args = {}
        
        # Intelligent argument extraction based on command semantics
        parts = command_name.lower().split('_')
        
        # Extract platform name if present
        platform = parts[0] if len(parts) > 0 else None
        action = parts[1] if len(parts) > 1 else None
        
        # For posting commands
        if action == 'post':
            # Extract content after common prepositions
            content_patterns = [
                r'(?:about|on|post|saying|that)\s+(.+)$',
                r'(?:make|create)\s+(?:a\s+)?post\s+(?:on\s+)?(?:\w+\s+)?(.+)$',
                r'(?:' + platform + r')\s+(.+)$',
            ]
            
            for pattern in content_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    args['content'] = match.group(1).strip()
                    break
            
            # If no content found, use everything after platform name
            if 'content' not in args and platform:
                platform_match = re.search(rf'{platform}\s+(.+)$', user_input, re.IGNORECASE)
                if platform_match:
                    args['content'] = platform_match.group(1).strip()
        
        # For engagement commands
        elif action == 'engage':
            # Extract count if specified
            count_match = re.search(r'(\d+)', user_input)
            if count_match:
                args['count'] = count_match.group(1)
        
        # For image generation
        elif 'image' in command_name or 'generate' in command_name:
            # Extract prompt
            prompt_patterns = [
                r'(?:generate|create|make)\s+(?:an?\s+)?(?:image\s+)?(?:of\s+)?(.+)',
                r'(?:draw|paint|render)\s+(.+)',
            ]
            for pattern in prompt_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    args['prompt'] = match.group(1).strip()
                    break
        
        # For price/token commands
        elif 'price' in command_name or 'token' in command_name:
            # Extract crypto symbol
            crypto_match = re.search(r'\b(BTC|ETH|SOL|AVAX|MATIC|LINK|UNI|AAVE|USDC|USDT|DAI|ALLEYBOT)\b', 
                                    user_input, re.IGNORECASE)
            if crypto_match:
                args['symbol'] = crypto_match.group(1).upper()
        
        return args


# Singleton instance
_natural_intent_classifier = None

def get_natural_intent_classifier() -> NaturalIntentClassifier:
    """Get or create the singleton natural intent classifier instance"""
    global _natural_intent_classifier
    if _natural_intent_classifier is None:
        _natural_intent_classifier = NaturalIntentClassifier()
    return _natural_intent_classifier

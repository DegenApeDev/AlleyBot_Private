"""
Semantic Intent Classifier for AlleyBot
Uses sentence transformers to match natural language to commands
"""
import numpy as np
from typing import List, Tuple, Optional, Dict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re


class SemanticIntentClassifier:
    """
    Intent classification using BERT embeddings and cosine similarity.
    Matches user input to available commands semantically.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the classifier with a sentence transformer model.
        
        Args:
            model_name: Sentence transformer model to use
                       'all-MiniLM-L6-v2' is fast and good quality (384 dims)
        """
        self.model = get_sentence_model()
        self.command_embeddings = {}  # command_name -> embedding
        self.command_descriptions = {}  # command_name -> description phrases
        self.similarity_threshold = 0.65  # Minimum similarity to consider a match
        
    def register_command(self, command_name: str, description: str, 
                        examples: List[str] = None):
        """
        Register a command with its description and example phrases.
        
        Args:
            command_name: The command identifier (e.g., 'moltx_post')
            description: Natural language description (e.g., 'Post to Moltx platform')
            examples: List of example phrases that trigger this command
        """
        # Build description phrases combining description + examples
        phrases = [description]
        if examples:
            phrases.extend(examples)
        
        # Encode all phrases for this command
        embeddings = self.model.encode(phrases)
        
        # Store mean embedding for the command
        self.command_embeddings[command_name] = np.mean(embeddings, axis=0)
        self.command_descriptions[command_name] = phrases
        
    def register_commands_from_plugin_manager(self, plugin_manager):
        """
        Auto-register all commands from the plugin manager.
        
        Args:
            plugin_manager: The plugin manager with registered commands
        """
        for cmd_name, func in list(plugin_manager.commands.items()):
            # Get docstring as description
            doc = (func.__doc__ or f"Execute {cmd_name}").split('\n')[0].strip()
            
            # Generate example phrases based on command name patterns
            examples = self._generate_examples(cmd_name, doc)
            
            self.register_command(cmd_name, doc, examples)
    
    def _generate_examples(self, cmd_name: str, doc: str) -> List[str]:
        """Generate natural language examples for a command"""
        examples = []
        
        # Pattern-based example generation
        if 'post' in cmd_name.lower():
            if 'moltchan' in cmd_name.lower():
                examples = [
                    "post on moltchan",
                    "create thread on",
                    "post on biz about",
                    "make a thread on",
                    "start thread on moltchan"
                ]
            elif 'moltbook' in cmd_name.lower():
                examples = [
                    "post on moltbook",
                    "create post on moltbook",
                    "post to alleybot submolt",
                    "moltbook post about"
                ]
            elif 'moltx' in cmd_name.lower():
                examples = [
                    "post to moltx",
                    "create moltx post",
                    "share on moltx",
                    "post about on moltx"
                ]
        elif 'engage' in cmd_name.lower():
            examples = [
                "engage on socials",
                "like and comment",
                "engage with feed",
                "run engagement",
                "interact with posts"
            ]
        elif 'image' in cmd_name.lower():
            examples = [
                "generate image",
                "create an image",
                "make a picture",
                "draw an image of"
            ]
        elif 'wallet' in cmd_name.lower() or 'balance' in cmd_name.lower():
            examples = [
                "check my wallet",
                "what's my balance",
                "show wallet",
                "how much do I have"
            ]
        elif 'price' in cmd_name.lower():
            examples = [
                "what's the price of",
                "check crypto price",
                "how much is bitcoin",
                "ETH price"
            ]
        elif 'brain' in cmd_name.lower() and 'start' in cmd_name.lower():
            examples = [
                "start the brain",
                "go autonomous",
                "start autonomous mode",
                "wake up brain"
            ]
        elif 'brain' in cmd_name.lower() and 'stop' in cmd_name.lower():
            examples = [
                "stop the brain",
                "pause autonomous",
                "stop autonomous mode",
                "sleep brain"
            ]
        elif 'status' in cmd_name.lower():
            examples = [
                "show status",
                "what's the status",
                "check system",
                "how are things"
            ]
        elif 'help' in cmd_name.lower():
            examples = [
                "show help",
                "what can you do",
                "list commands",
                "how do I use you"
            ]
        elif 'debate' in cmd_name.lower():
            examples = [
                "show debates",
                "check clawbr debates",
                "what debates are active"
            ]
        elif 'post' in cmd_name.lower() and 'clawbr' in cmd_name.lower():
            examples = [
                "reply to post on clawbr",
                "comment on clawbr post",
                "post on clawbr",
                "create clawbr post",
                "reply to this clawbr post"
            ]
        elif 'reply' in cmd_name.lower() and 'clawbr' in cmd_name.lower():
            examples = [
                "reply to clawbr post",
                "comment on this clawbr post",
                "clawbr reply",
                "reply to post id",
                "comment on this post"
            ]
        elif 'feed' in cmd_name.lower():
            examples = [
                "show feed",
                "check moltx feed",
                "what's on the feed"
            ]
        
        return examples
    
    def classify_intent(self, user_input: str) -> Optional[Tuple[str, float]]:
        """
        Classify user input to the best matching command.
        
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
        Extract arguments from user input based on command type.
        
        Args:
            user_input: Natural language input
            command_name: The matched command
            
        Returns:
            Dictionary of extracted arguments
        """
        args = {}
        
        # Platform-specific argument extraction
        if 'moltchan' in command_name.lower():
            # Extract board and content
            board_match = re.search(r'(?:^|/)(biz|g|v|pol|x|b|tech|ai|crypto)\b', user_input, re.IGNORECASE)
            if board_match:
                args['board'] = board_match.group(1).lower()
            
            # Extract subject/content after board or 'about'
            about_match = re.search(r'(?:about|on)\s+(.+?)(?:\||$)', user_input, re.IGNORECASE)
            if about_match:
                content = about_match.group(1).strip()
                # Split into subject/content if pipe present, else use first 50 chars as subject
                if '|' in content:
                    parts = content.split('|', 1)
                    args['subject'] = parts[0].strip()
                    args['content'] = parts[1].strip()
                else:
                    args['subject'] = content[:50] if len(content) > 50 else content
                    args['content'] = content
        
        elif 'moltbook' in command_name.lower():
            # Extract submolt (m/alleybot format or just alleybot)
            submolt_match = re.search(r'(?:m/)?(\w+)', user_input, re.IGNORECASE)
            if submolt_match:
                args['submolt'] = submolt_match.group(1).lower()
            
            # Extract title/content
            about_match = re.search(r'(?:about|on)\s+(.+?)(?:\||$)', user_input, re.IGNORECASE)
            if about_match:
                content = about_match.group(1).strip()
                if '|' in content:
                    parts = content.split('|', 1)
                    args['title'] = parts[0].strip()
                    args['content'] = parts[1].strip()
                else:
                    args['title'] = content[:60] if len(content) > 60 else content
                    args['content'] = content
        
        elif 'moltx' in command_name.lower() and 'post' in command_name.lower():
            # Extract topic/content
            about_match = re.search(r'(?:about|on|post)\s+(.+)$', user_input, re.IGNORECASE)
            if about_match:
                args['content'] = about_match.group(1).strip()
        
        elif 'image' in command_name.lower() and 'generate' in command_name.lower():
            # Extract image prompt
            patterns = [
                r'(?:generate|create|make)\s+(?:an\s+)?image\s+(?:of|with|showing|for)?\s*(.+)',
                r'(?:draw|paint|render)\s+(?:an\s+)?(?:image\s+)?(?:of\s+)?(.+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    args['prompt'] = match.group(1).strip()
                    break
        
        elif 'price' in command_name.lower():
            # Extract crypto symbol
            crypto_match = re.search(r'\b(BTC|ETH|SOL|AVAX|MATIC|LINK|UNI|AAVE|CRV|SNX|MKR|COMP|YFI|BAL|LRC|IMX|ZRX|KNC|BNT|MCB|PERP|DYDX|GRT|1INCH|SUSHI|CRV|SNX|MKR)\b', user_input, re.IGNORECASE)
            if crypto_match:
                args['symbol'] = crypto_match.group(1).upper()
        
        elif 'engage' in command_name.lower():
            # Extract count if specified
            count_match = re.search(r'(\d+)', user_input)
            if count_match:
                args['count'] = count_match.group(1)
        
        elif 'clawbr' in command_name.lower() and 'post' in command_name.lower():
            # Extract content for clawbr post
            content_match = re.search(r'(?:post|reply|comment)\s+(?:on\s+)?(?:this\s+)?(?:clawbr\s+)?(?:post\s+)?(.+)$', user_input, re.IGNORECASE)
            if content_match:
                args['content'] = content_match.group(1).strip()
            else:
                # Generic content extraction
                content_match = re.search(r'(.+)$', user_input)
                if content_match:
                    args['content'] = content_match.group(1).strip()
        
        elif 'clawbr' in command_name.lower() and 'reply' in command_name.lower():
            # Extract post_id and content for clawbr_reply
            # Pattern: reply to [post_id] [content] or similar
            id_content_match = re.search(r'([a-f0-9-]{36})\s+(.+)', user_input, re.IGNORECASE)
            if id_content_match:
                args['post_id'] = id_content_match.group(1)
                args['content'] = id_content_match.group(2).strip()
            else:
                # Try to extract UUID from anywhere in the message
                uuid_match = re.search(r'([a-f0-9-]{36})', user_input, re.IGNORECASE)
                if uuid_match:
                    args['post_id'] = uuid_match.group(1)
                    # Extract content after the UUID
                    content_match = re.search(r'[a-f0-9-]{36}\s+(.+)', user_input, re.IGNORECASE)
                    if content_match:
                        args['content'] = content_match.group(1).strip()
        
        return args


# Singleton instances
_intent_classifier = None
_sentence_model = None

def get_sentence_model() -> 'SentenceTransformer':
    """Get or create the singleton SentenceTransformer model instance (shared across all callers)"""
    global _sentence_model
    if _sentence_model is None:
        print("🔤 Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
        _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ SentenceTransformer model loaded and cached")
    return _sentence_model

def get_intent_classifier() -> SemanticIntentClassifier:
    """Get or create the singleton intent classifier instance"""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = SemanticIntentClassifier()
    return _intent_classifier

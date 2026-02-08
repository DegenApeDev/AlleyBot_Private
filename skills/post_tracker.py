import os
import json
import datetime
from typing import List, Dict, Optional, Any, Set
from collections import defaultdict

KEYWORDS: Set[str] = {
    'degen', 'nft', 'meme', 'crypto', 'sol', 'eth', 'btc', 'defi'
}
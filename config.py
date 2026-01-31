import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MOLTBOOK_API_KEY')
XAI_API_KEY = os.getenv('XAI_API_KEY')
BASE_URL = "https://www.moltbook.com/api/v1"

# AlleyBot's wallet addresses
BTC_WALLET = "3FWrh7nEZofv62MMV5JbsS9M29aitF3Spy"
ETH_WALLET = "0xCffe06d3Cf0908C2452e7c336FEec507d5Afd41d"
BASE_WALLET = "0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5"  # BASE L2 (lower fees)
SOL_WALLET = "BUo8AVbxfV2FsTzm19HUsraPzghKDTm1bEfn4Yrp2VJm"

# Legacy support
WALLET_ADDRESS = BTC_WALLET

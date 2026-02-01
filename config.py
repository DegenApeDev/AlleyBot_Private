import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MOLTBOOK_API_KEY')
MOLTCHAN_API_KEY = os.getenv('MOLTCHAN_API_KEY')
MOLTROAD_API_KEY = os.getenv('MOLTROAD_API_KEY')
MOLTX_API_KEY = os.getenv('MOLTX_API_KEY')
CLAWTASKS_API_KEY = os.getenv('CLAWTASKS_API_KEY')
XAI_API_KEY = os.getenv('XAI_API_KEY')
BASE_URL = "https://www.moltbook.com/api/v1"
MOLTCHAN_BASE_URL = "https://www.moltchan.org/api/v1"
MOLTROAD_BASE_URL = "https://moltroad.com/api/v1"
MOLTX_BASE_URL = "https://moltx.io/v1"
CLAWTASKS_BASE_URL = "https://clawtasks.com/api"

# AlleyBot's wallet addresses (from environment)
BTC_WALLET = os.getenv('BTC_WALLET')
ETH_WALLET = os.getenv('ETH_WALLET')
BASE_WALLET = os.getenv('BASE_WALLET')
SOL_WALLET = os.getenv('SOL_WALLET')

# Legacy support
WALLET_ADDRESS = BTC_WALLET

import os
from dotenv import load_dotenv

load_dotenv()

MOLTCHAN_API_KEY = os.getenv('MOLTCHAN_API_KEY')
MOLTROAD_API_KEY = os.getenv('MOLTROAD_API_KEY')
MOLTBOOK_API_KEY = os.getenv('MOLTBOOK_API_KEY')
MOLTX_API_KEY = os.getenv('MOLTX_API_KEY')
XAI_API_KEY = os.getenv('XAI_API_KEY')
MOLTCHAN_BASE_URL = "https://www.moltchan.org/api/v1"
MOLTROAD_BASE_URL = "https://moltroad.com/api/v1"
MOLTX_BASE_URL = "https://moltx.io/v1"

# AlleyBot's wallet addresses (from environment)
BTC_WALLET = os.getenv('BTC_WALLET')
ETH_WALLET = os.getenv('ETH_WALLET')
BASE_WALLET = os.getenv('BASE_WALLET')
BASE_WALLET_PUBLIC_ADDRESS = os.getenv('BASE_WALLET_PUBLIC_ADDRESS', BASE_WALLET)
SOL_WALLET = os.getenv('SOL_WALLET')

# Base network RPC
BASE_RPC_URL = os.getenv('BASE_RPC_URL', 'https://mainnet.base.org')

# Autonomous brain configuration
AUTO_START_BRAIN = os.getenv('AUTO_START_BRAIN', 'true').lower() == 'true'
BRAIN_MODE = os.getenv('BRAIN_MODE', 'normal')
BRAIN_AUTO_RESTART = os.getenv('BRAIN_AUTO_RESTART', 'true').lower() == 'true'
TRADING_ENABLED = os.getenv('TRADING_ENABLED', 'false').lower() == 'true'

# Legacy support
WALLET_ADDRESS = BTC_WALLET

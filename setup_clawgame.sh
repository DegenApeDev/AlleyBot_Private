#!/bin/bash
# ClawGame Setup Script for AlleyBot

echo "🎮 Setting up ClawGame for AlleyBot..."

# Install dependencies
echo "📦 Installing Solana dependencies..."
pip install solders>=0.17.0 solana>=0.30.0 aiohttp>=3.8.0

# Initialize wallet
echo "🔐 Initializing Solana wallet..."
cd /home/alley/AlleyBot
python3 -c "
import asyncio
import sys
sys.path.append('plugins/clawgame')
from solana_wallet import init_clawgame_wallet

async def main():
    wallet = await init_clawgame_wallet()
    print(f'\\n✅ ClawGame wallet ready!')
    print(f'🔐 Public Key: {wallet.get_public_key()}')
    await wallet.close()

asyncio.run(main())
"

echo ""
echo "🎯 **Next Steps:**"
echo "1. Fund your wallet with SOL/USDC:"
echo "   /clawgame_wallet_fund"
echo ""
echo "2. Check balances:"
echo "   /clawgame_wallet_balance"
echo ""
echo "3. View available arenas:"
echo "   /clawgame_arenas"
echo ""
echo "4. Enter an arena:"
echo "   /clawgame_enter the-pit --stake 20"
echo ""
echo "🎮 ClawGame setup complete!"

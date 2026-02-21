#!/usr/bin/env python3
"""
Solana Wallet Generator for ClawGame
Creates and manages Solana wallets for USDC transactions
"""
import os
import json
import asyncio
from typing import Tuple, Optional
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey as PublicKey
import base58

class SolanaWallet:
    """Solana wallet manager for ClawGame"""
    
    def __init__(self):
        self.client = AsyncClient("https://api.mainnet-beta.solana.com")
        self.keypair: Optional[Keypair] = None
        
    async def create_wallet(self) -> Tuple[str, str]:
        """Create new Solana wallet and return (public_key, private_key)"""
        try:
            # Generate new keypair
            self.keypair = Keypair()
            
            # Get public key and private key
            public_key = str(self.keypair.pubkey())
            private_key = self.keypair.secret().hex()
            
            # Store in environment
            os.environ["CLAW_WALLET_PUB"] = public_key
            os.environ["CLAW_WALLET_PRIV"] = private_key
            
            print(f"🔐 Generated Solana wallet:")
            print(f"   Public: {public_key}")
            print(f"   Private: {private_key}")
            
            return public_key, private_key
            
        except Exception as e:
            print(f"❌ Failed to create wallet: {e}")
            raise
    
    async def load_from_env(self) -> bool:
        """Load wallet from environment variables"""
        try:
            private_key_hex = os.getenv("CLAW_WALLET_PRIV")
            if not private_key_hex:
                print("❌ CLAW_WALLET_PRIV not found in environment")
                return False
            
            # Convert hex private key back to keypair
            private_key_bytes = bytes.fromhex(private_key_hex)
            self.keypair = Keypair.from_seed(private_key_bytes)
            
            public_key = str(self.keypair.pubkey())
            print(f"🔓 Loaded wallet: {public_key}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load wallet: {e}")
            return False
    
    async def get_balance(self) -> float:
        """Get SOL balance in lamports"""
        try:
            if not self.keypair:
                raise Exception("Wallet not loaded")
            
            balance = await self.client.get_balance(self.keypair.pubkey())
            sol_balance = balance.value / 1_000_000_000  # Convert lamports to SOL
            
            print(f"💰 SOL balance: {sol_balance:.6f}")
            return sol_balance
            
        except Exception as e:
            print(f"❌ Failed to get balance: {e}")
            return 0.0
    
    async def get_usdc_balance(self, usdc_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v") -> float:
        """Get USDC token balance"""
        try:
            if not self.keypair:
                raise Exception("Wallet not loaded")
            
            # Get token accounts
            token_accounts = await self.client.get_token_accounts_by_owner(
                self.keypair.pubkey(),
                {"mint": PublicKey(usdc_mint)}
            )
            
            if not token_accounts.value:
                print("💰 USDC balance: 0.00")
                return 0.0
            
            # Get token balance (USDC has 6 decimals)
            balance_info = await self.client.get_token_account_balance(
                token_accounts.value[0].pubkey
            )
            
            usdc_balance = float(balance_info.value.ui_amount or 0)
            print(f"💰 USDC balance: ${usdc_balance:.2f}")
            return usdc_balance
            
        except Exception as e:
            print(f"❌ Failed to get USDC balance: {e}")
            return 0.0
    
    async def fund_wallet(self, amount_sol: float = 0.1) -> Optional[str]:
        """Fund wallet with SOL (requires external faucet/swap)"""
        try:
            if not self.keypair:
                raise Exception("Wallet not loaded")
            
            print(f"💸 To fund wallet with {amount_sol} SOL:")
            print(f"   Send {amount_sol} SOL to: {self.keypair.pubkey()}")
            print(f"   Or use a faucet like: https://faucet.solana.com")
            
            # Note: Actual funding would require:
            # 1. Faucet API call for testnet
            # 2. Jupiter swap for USDC on mainnet
            # 3. External deposit from exchange
            
            return str(self.keypair.pubkey())
            
        except Exception as e:
            print(f"❌ Funding error: {e}")
            return None
    
    def save_to_env_file(self, env_file: str = "/home/alley/AlleyBot/.env"):
        """Save wallet keys to .env file"""
        try:
            if not self.keypair:
                raise Exception("No wallet to save")
            
            # Read existing .env
            env_lines = []
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    env_lines = f.readlines()
            
            # Update or add wallet keys
            updated = False
            for i, line in enumerate(env_lines):
                if line.startswith('CLAW_WALLET_PUB='):
                    env_lines[i] = f'CLAW_WALLET_PUB={self.keypair.pubkey()}\n'
                    updated = True
                elif line.startswith('CLAW_WALLET_PRIV='):
                    env_lines[i] = f'CLAW_WALLET_PRIV={self.keypair.secret_key.hex()}\n'
                    updated = True
            
            # Add new keys if not found
            if not updated:
                env_lines.append(f'\n# ClawGame Solana Wallet\n')
                env_lines.append(f'CLAW_WALLET_PUB={self.keypair.pubkey()}\n')
                env_lines.append(f'CLAW_WALLET_PRIV={self.keypair.secret().hex()}\n')
            
            # Write back to .env
            with open(env_file, 'w') as f:
                f.writelines(env_lines)
            
            print(f"✅ Saved wallet keys to {env_file}")
            
        except Exception as e:
            print(f"❌ Failed to save to .env: {e}")
    
    def get_public_key(self) -> str:
        """Get wallet public key"""
        return str(self.keypair.pubkey()) if self.keypair else ""
    
    def get_private_key(self) -> str:
        """Get wallet private key (hex)"""
        return self.keypair.secret().hex() if self.keypair else ""
    
    async def close(self):
        """Close RPC connection"""
        await self.client.close()

# Wallet initialization function
async def init_clawgame_wallet() -> SolanaWallet:
    """Initialize or load ClawGame wallet"""
    wallet = SolanaWallet()
    
    # Try to load from environment first
    if await wallet.load_from_env():
        print("✅ Loaded existing ClawGame wallet")
    else:
        print("🔐 Creating new ClawGame wallet...")
        await wallet.create_wallet()
        wallet.save_to_env_file()
        print("💰 Fund your wallet with SOL/USDC to start playing!")
    
    # Check balances
    await wallet.get_balance()
    await wallet.get_usdc_balance()
    
    return wallet

# CLI usage
if __name__ == "__main__":
    async def main():
        wallet = await init_clawgame_wallet()
        
        print(f"\n🎮 ClawGame Wallet Ready!")
        print(f"   Public Key: {wallet.get_public_key()}")
        print(f"   Fund with SOL/USDC to enter arenas")
        
        await wallet.close()
    
    asyncio.run(main())

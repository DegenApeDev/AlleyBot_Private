"""
OnChain Actions Mixin for Phase 10
Provides tipping, contract interactions, and advanced on-chain operations
"""
import os
from typing import Dict, Any, Optional
from decimal import Decimal
from pathlib import Path


class OnChainActionsMixin:
    """Mixin for advanced on-chain actions like tipping and contract interactions"""

    def _init_onchain_actions(self):
        """Initialize on-chain actions system"""
        self.tip_history: list = []
        self.contract_interactions: list = []
        self.tip_limits = {
            'max_eth_per_tip': 0.01,  # Max 0.01 ETH per tip
            'max_daily_eth': 0.1,     # Max 0.1 ETH per day
            'min_eth_per_tip': 0.001, # Min 0.001 ETH
        }
        self._load_actions_state()

    def _load_actions_state(self):
        """Load action state from memory"""
        try:
            if hasattr(self, 'core') and self.core:
                state = self.core.get_memory('onchain_actions_state')
                if state:
                    self.tip_history = state.get('tip_history', [])
                    self.contract_interactions = state.get('contract_interactions', [])
        except Exception:
            pass

    def _save_actions_state(self):
        """Save action state to memory"""
        try:
            if hasattr(self, 'core') and self.core:
                self.core.save_memory('onchain_actions_state', {
                    'tip_history': self.tip_history[-100:],
                    'contract_interactions': self.contract_interactions[-100:],
                })
        except Exception as e:
            print(f"⚠️  Failed to save actions state: {e}")

    def tip_user(self, recipient_address: str, amount_eth: float, platform: str = "", 
                 user_id: str = "", reason: str = "") -> Dict[str, Any]:
        """
        Send ETH tip to a user
        
        Args:
            recipient_address: Ethereum address to tip
            amount_eth: Amount in ETH
            platform: Platform where user was tipped (e.g., 'clawbr', 'moltx')
            user_id: User identifier on the platform
            reason: Reason for the tip
        
        Returns:
            Dict with transaction result
        """
        # Validate amount
        if amount_eth < self.tip_limits['min_eth_per_tip']:
            return {
                'success': False,
                'error': f"Tip too small. Minimum is {self.tip_limits['min_eth_per_tip']} ETH"
            }
        
        if amount_eth > self.tip_limits['max_eth_per_tip']:
            return {
                'success': False,
                'error': f"Tip too large. Maximum is {self.tip_limits['max_eth_per_tip']} ETH"
            }

        # Check daily limit
        daily_total = sum(tip['amount_eth'] for tip in self.tip_history 
                         if tip['timestamp'] > self._get_hours_ago(24))
        if daily_total + amount_eth > self.tip_limits['max_daily_eth']:
            return {
                'success': False,
                'error': f"Daily tip limit reached. Max {self.tip_limits['max_daily_eth']} ETH per day"
            }

        # Get wallet credentials
        private_key = os.getenv('BASE_WALLET_PRIVATE_KEY')
        if not private_key:
            return {
                'success': False,
                'error': 'No private key configured for tipping (set BASE_WALLET_PRIVATE_KEY)'
            }

        try:
            if not self.web3_provider or not self.web3_provider.connected:
                return {'success': False, 'error': 'Web3 not connected'}

            w3 = self.web3_provider.w3
            sender_address = self.web3_provider.wallet_address

            if not sender_address:
                return {'success': False, 'error': 'No sender wallet configured'}

            # Convert ETH to wei
            amount_wei = w3.to_wei(amount_eth, 'ether')

            # Get gas estimate
            gas_estimate = w3.eth.estimate_gas({
                'from': sender_address,
                'to': recipient_address,
                'value': amount_wei
            })

            # Build transaction
            tx = {
                'from': sender_address,
                'to': recipient_address,
                'value': amount_wei,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(sender_address),
                'chainId': self.web3_provider.network_config['chain_id'],
            }

            # Sign and send
            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Wait for receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt['status'] == 1:
                # Record successful tip
                tip_record = {
                    'timestamp': self._now_iso(),
                    'recipient': recipient_address,
                    'amount_eth': amount_eth,
                    'tx_hash': tx_hash.hex(),
                    'platform': platform,
                    'user_id': user_id,
                    'reason': reason,
                    'gas_used': receipt['gasUsed'],
                }
                self.tip_history.append(tip_record)
                self._save_actions_state()

                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'amount_eth': amount_eth,
                    'recipient': recipient_address,
                    'gas_used': receipt['gasUsed'],
                    'explorer_url': f"{self.web3_provider.network_config['explorer']}/tx/{tx_hash.hex()}"
                }
            else:
                return {
                    'success': False,
                    'error': 'Transaction failed on-chain',
                    'tx_hash': tx_hash.hex()
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Tip failed: {str(e)}'
            }

    def tip_with_token(self, recipient_address: str, token_address: str, 
                       amount: float, platform: str = "", user_id: str = "",
                       reason: str = "") -> Dict[str, Any]:
        """
        Send ERC-20 token tip to a user
        
        Args:
            recipient_address: Ethereum address to tip
            token_address: Token contract address
            amount: Token amount (in token units, not wei)
            platform: Platform where user was tipped
            user_id: User identifier on the platform
            reason: Reason for the tip
        """
        private_key = os.getenv('BASE_WALLET_PRIVATE_KEY')
        if not private_key:
            return {'success': False, 'error': 'No private key configured'}

        try:
            if not self.web3_provider or not self.web3_provider.connected:
                return {'success': False, 'error': 'Web3 not connected'}

            w3 = self.web3_provider.w3
            sender_address = self.web3_provider.wallet_address

            # Create token contract
            token_contract = w3.eth.contract(address=token_address, abi=self._get_erc20_abi())

            # Get decimals
            decimals = token_contract.functions.decimals().call()
            amount_wei = int(amount * (10 ** decimals))

            # Build transfer transaction
            tx = token_contract.functions.transfer(recipient_address, amount_wei).build_transaction({
                'from': sender_address,
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(sender_address),
                'chainId': self.web3_provider.network_config['chain_id'],
            })

            # Sign and send
            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Wait for receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt['status'] == 1:
                token_symbol = token_contract.functions.symbol().call()
                
                tip_record = {
                    'timestamp': self._now_iso(),
                    'recipient': recipient_address,
                    'token_address': token_address,
                    'token_symbol': token_symbol,
                    'amount': amount,
                    'tx_hash': tx_hash.hex(),
                    'platform': platform,
                    'user_id': user_id,
                    'reason': reason,
                }
                self.tip_history.append(tip_record)
                self._save_actions_state()

                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'amount': amount,
                    'token': token_symbol,
                    'recipient': recipient_address,
                }
            else:
                return {'success': False, 'error': 'Token transfer failed'}

        except Exception as e:
            return {'success': False, 'error': f'Token tip failed: {str(e)}'}

    def read_contract(self, contract_address: str, function_name: str, 
                      abi: list, *args) -> Dict[str, Any]:
        """
        Read data from a smart contract
        
        Args:
            contract_address: Contract address
            function_name: Function to call
            abi: Contract ABI
            *args: Function arguments
        """
        try:
            if not self.web3_provider or not self.web3_provider.connected:
                return {'success': False, 'error': 'Web3 not connected'}

            w3 = self.web3_provider.w3
            contract = w3.eth.contract(address=contract_address, abi=abi)
            
            # Call function
            result = getattr(contract.functions, function_name)(*args).call()
            
            return {
                'success': True,
                'result': result,
                'function': function_name,
                'contract': contract_address,
            }
        except Exception as e:
            return {'success': False, 'error': f'Contract read failed: {str(e)}'}

    def write_contract(self, contract_address: str, function_name: str,
                       abi: list, value_eth: float = 0, *args) -> Dict[str, Any]:
        """
        Write to a smart contract (state-changing transaction)
        
        Args:
            contract_address: Contract address
            function_name: Function to call
            abi: Contract ABI
            value_eth: ETH to send with transaction
            *args: Function arguments
        """
        private_key = os.getenv('BASE_WALLET_PRIVATE_KEY')
        if not private_key:
            return {'success': False, 'error': 'No private key configured'}

        try:
            if not self.web3_provider or not self.web3_provider.connected:
                return {'success': False, 'error': 'Web3 not connected'}

            w3 = self.web3_provider.w3
            sender_address = self.web3_provider.wallet_address
            contract = w3.eth.contract(address=contract_address, abi=abi)

            # Build transaction
            value_wei = w3.to_wei(value_eth, 'ether') if value_eth > 0 else 0
            
            tx = getattr(contract.functions, function_name)(*args).build_transaction({
                'from': sender_address,
                'value': value_wei,
                'gas': 200000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(sender_address),
                'chainId': self.web3_provider.network_config['chain_id'],
            })

            # Sign and send
            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Wait for receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            # Record interaction
            interaction = {
                'timestamp': self._now_iso(),
                'contract': contract_address,
                'function': function_name,
                'tx_hash': tx_hash.hex(),
                'value_eth': value_eth,
                'success': receipt['status'] == 1,
            }
            self.contract_interactions.append(interaction)
            self._save_actions_state()

            return {
                'success': receipt['status'] == 1,
                'tx_hash': tx_hash.hex(),
                'gas_used': receipt['gasUsed'],
            }

        except Exception as e:
            return {'success': False, 'error': f'Contract write failed: {str(e)}'}

    def get_tip_stats(self) -> Dict[str, Any]:
        """Get tipping statistics"""
        total_tipped = sum(tip['amount_eth'] for tip in self.tip_history)
        recent_tips = [tip for tip in self.tip_history 
                      if tip['timestamp'] > self._get_hours_ago(24)]
        daily_total = sum(tip['amount_eth'] for tip in recent_tips)
        
        return {
            'total_tips': len(self.tip_history),
            'total_eth_tipped': round(total_tipped, 6),
            'daily_eth_tipped': round(daily_total, 6),
            'daily_limit': self.tip_limits['max_daily_eth'],
            'daily_remaining': round(self.tip_limits['max_daily_eth'] - daily_total, 6),
            'recent_tips': recent_tips[-10:],
        }

    def _get_erc20_abi(self) -> list:
        """Get standard ERC20 ABI"""
        from plugins.onchain.web3_provider import ERC20_ABI
        return ERC20_ABI

    def _now_iso(self) -> str:
        """Get current ISO timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _get_hours_ago(self, hours: int) -> str:
        """Get ISO timestamp for X hours ago"""
        from datetime import datetime, timedelta
        return (datetime.now() - timedelta(hours=hours)).isoformat()

    # CLI Commands
    def tip_command(self, *args) -> str:
        """Tip a user: tip <address> <amount_eth> [reason]"""
        if len(args) < 2:
            return "Usage: tip <address> <amount_eth> [reason]"
        
        recipient = args[0]
        try:
            amount = float(args[1])
        except ValueError:
            return "❌ Amount must be a number"
        
        reason = ' '.join(args[2:]) if len(args) > 2 else "Manual tip"
        
        result = self.tip_user(recipient, amount, reason=reason)
        
        if result['success']:
            return f"✅ Tipped {amount} ETH to {recipient[:10]}...\nTX: {result['tx_hash'][:20]}..."
        else:
            return f"❌ Tip failed: {result['error']}"

    def tipstats_command(self, *args) -> str:
        """Show tipping statistics"""
        stats = self.get_tip_stats()
        
        output = "💰 Tipping Statistics\n\n"
        output += f"Total Tips: {stats['total_tips']}\n"
        output += f"Total Tipped: {stats['total_eth_tipped']:.6f} ETH\n"
        output += f"24h Tipped: {stats['daily_eth_tipped']:.6f} / {stats['daily_limit']} ETH\n"
        output += f"24h Remaining: {stats['daily_remaining']:.6f} ETH\n\n"
        
        if stats['recent_tips']:
            output += "Recent Tips:\n"
            for tip in stats['recent_tips'][-5:]:
                output += f"  • {tip['amount_eth']:.4f} ETH to {tip['recipient'][:10]}... ({tip['platform']})\n"
        
        return output

    def contract_read_command(self, *args) -> str:
        """Read contract: contract_read <address> <function> <abi_path> [args...]"""
        if len(args) < 3:
            return "Usage: contract_read <address> <function> <abi_json_path> [args...]"
        
        address = args[0]
        function = args[1]
        abi_path = args[2]
        func_args = args[3:] if len(args) > 3 else []
        
        try:
            import json
            with open(abi_path, 'r') as f:
                abi = json.load(f)
        except Exception as e:
            return f"❌ Failed to load ABI: {e}"
        
        result = self.read_contract(address, function, abi, *func_args)
        
        if result['success']:
            return f"✅ {function}() = {result['result']}"
        else:
            return f"❌ {result['error']}"

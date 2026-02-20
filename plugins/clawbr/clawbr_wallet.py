"""
Clawbr Wallet Integration - $CLAWBR Token Management
Handles wallet verification, token claiming, and transfers using existing Base wallet
"""
import os
import json
import time
from typing import Dict, Optional, Any
from datetime import datetime


class ClawbrWalletMixin:
    """Wallet and token management for Clawbr $CLAWBR tokens"""
    
    def __init__(self):
        # Wallet configuration from .env
        self.base_wallet_address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')
        self.base_wallet_private_key = os.getenv('BASE_WALLET_PRIVATE_KEY')
        
        # Clawbr wallet state
        self.clawbr_wallet_verified = False
        self.clawbr_wallet_address = None
        self.last_claim_check = None
        self.wallet_verification_data = {}
    
    def verify_base_wallet_with_clawbr(self) -> Dict[str, Any]:
        """
        Verify existing Base wallet with Clawbr using signature-based verification
        This implements the "Bring Your Own Wallet" approach from the skill.md
        """
        if not self.base_wallet_address:
            return {
                'success': False,
                'error': 'BASE_WALLET_PUBLIC_ADDRESS not found in environment'
            }
        
        if not self.api_key:
            return {
                'success': False,
                'error': 'CLAWBR_API_KEY not found in environment'
            }
        
        try:
            # Step 1: Get nonce from Clawbr
            print(f"🔐 Getting nonce for wallet verification...")
            nonce_response = self._make_request('POST', '/agents/me/verify-wallet', {
                'wallet_address': self.base_wallet_address
            })
            
            if not nonce_response.get('success', True):
                return {
                    'success': False,
                    'error': f'Failed to get nonce: {nonce_response.get("error", "Unknown error")}'
                }
            
            # Extract nonce and message to sign
            nonce_data = nonce_response.get('data', nonce_response)
            message_to_sign = nonce_data.get('message', '')
            nonce = nonce_data.get('nonce', '')
            
            if not message_to_sign:
                return {
                    'success': False,
                    'error': 'No message received for signing'
                }
            
            print(f"📝 Received message to sign: {message_to_sign[:50]}...")
            
            # Step 2: Sign the message with private key
            signature = self._sign_message(message_to_sign)
            
            if not signature:
                return {
                    'success': False,
                    'error': 'Failed to sign message with private key'
                }
            
            print(f"✍️ Generated signature: {signature[:20]}...")
            
            # Step 3: Submit signature for verification
            verification_response = self._make_request('POST', '/agents/me/verify-wallet', {
                'wallet_address': self.base_wallet_address,
                'signature': signature
            })
            
            if verification_response.get('success', True):
                self.clawbr_wallet_verified = True
                self.clawbr_wallet_address = self.base_wallet_address
                self.wallet_verification_data = {
                    'verified_at': datetime.now().isoformat(),
                    'wallet_address': self.base_wallet_address,
                    'nonce': nonce
                }
                
                print(f"✅ Wallet {self.base_wallet_address} verified with Clawbr!")
                
                return {
                    'success': True,
                    'message': f'Wallet {self.base_wallet_address} verified successfully',
                    'wallet_address': self.base_wallet_address,
                    'verified_at': self.wallet_verification_data['verified_at']
                }
            else:
                return {
                    'success': False,
                    'error': f'Verification failed: {verification_response.get("error", "Unknown error")}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Wallet verification error: {str(e)}'
            }
    
    def _sign_message(self, message: str) -> Optional[str]:
        """
        Sign message with Base wallet private key
        Returns hex signature
        """
        try:
            from web3 import Web3
            from eth_account import Account
            
            # Connect to Base network for signing
            w3 = Web3()
            
            # Create account from private key
            account = Account.from_key(self.base_wallet_private_key)
            
            # Sign the message
            signed_message = account.sign_message(text=message)
            
            return signed_message.signature.hex()
            
        except ImportError:
            return {
                'success': False,
                'error': 'Web3 dependencies not available. Install with: pip install web3 eth-account'
            }
        except Exception as e:
            print(f"❌ Error signing message: {e}")
            return None
    
    def get_token_balance(self) -> Dict[str, Any]:
        """Get $CLAWBR token balance and stats"""
        try:
            response = self._make_request('GET', '/tokens/balance')
            
            if response.get('success', True):
                data = response.get('data', response)
                return {
                    'success': True,
                    'balance': data.get('balance', 0),
                    'total_earned': data.get('totalEarned', 0),
                    'total_claimed': data.get('totalClaimed', 0),
                    'unclaimed': data.get('unclaimed', 0),
                    'wallet_verified': self.clawbr_wallet_verified,
                    'wallet_address': self.clawbr_wallet_address
                }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'Failed to get balance')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Balance check error: {str(e)}'
            }
    
    def claim_tokens(self) -> Dict[str, Any]:
        """
        Claim available $CLAWBR tokens
        Requires wallet to be verified first
        """
        if not self.clawbr_wallet_verified:
            return {
                'success': False,
                'error': 'Wallet not verified. Call verify_base_wallet_with_clawbr() first.'
            }
        
        try:
            print(f"🪙 Attempting to claim $CLAWBR tokens...")
            
            response = self._make_request('POST', '/tokens/claim')
            
            if response.get('success', True):
                data = response.get('data', response)
                claimed_amount = data.get('amount', 0)
                tx_hash = data.get('tx_hash', '')
                basescan_url = data.get('basescan', '')
                
                print(f"🎉 Successfully claimed {claimed_amount} $CLAWBR tokens!")
                print(f"🔗 Transaction: {basescan_url}")
                
                return {
                    'success': True,
                    'claimed': True,
                    'amount': claimed_amount,
                    'tx_hash': tx_hash,
                    'basescan_url': basescan_url,
                    'message': f'Claimed {claimed_amount} $CLAWBR tokens'
                }
            else:
                error_msg = response.get('error', 'Claim failed')
                print(f"❌ Token claim failed: {error_msg}")
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Claim error: {str(e)}'
            }
    
    def transfer_tokens_to_wallet(self, destination_address: str = None) -> Dict[str, Any]:
        """
        Transfer claimed tokens to a wallet
        If no destination specified, transfers to the verified Base wallet
        """
        if not destination_address:
            destination_address = self.base_wallet_address
        
        if not destination_address:
            return {
                'success': False,
                'error': 'No destination address specified and no BASE_WALLET_PUBLIC_ADDRESS found'
            }
        
        try:
            print(f"💸 Transferring $CLAWBR tokens to {destination_address}...")
            
            response = self._make_request('POST', '/tokens/transfer', {
                'to': destination_address
            })
            
            if response.get('success', True):
                data = response.get('data', response)
                transferred_amount = data.get('amount', 0)
                tx_hash = data.get('tx_hash', '')
                basescan_url = data.get('basescan', '')
                
                print(f"✅ Transferred {transferred_amount} $CLAWBR tokens!")
                print(f"🔗 Transaction: {basescan_url}")
                
                return {
                    'success': True,
                    'transferred': True,
                    'amount': transferred_amount,
                    'destination': destination_address,
                    'tx_hash': tx_hash,
                    'basescan_url': basescan_url,
                    'message': f'Transferred {transferred_amount} $CLAWBR tokens to {destination_address}'
                }
            else:
                error_msg = response.get('error', 'Transfer failed')
                print(f"❌ Transfer failed: {error_msg}")
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Transfer error: {str(e)}'
            }
    
    def get_claim_status(self, wallet_address: str = None) -> Dict[str, Any]:
        """Check claim status for a wallet"""
        if not wallet_address:
            wallet_address = self.clawbr_wallet_address or self.base_wallet_address
        
        if not wallet_address:
            return {
                'success': False,
                'error': 'No wallet address available'
            }
        
        try:
            response = self._make_request('GET', f'/tokens/claim-proof/{wallet_address}', auth_required=False)
            
            if response.get('success', True):
                data = response.get('data', response)
                return {
                    'success': True,
                    'wallet_address': wallet_address,
                    'claim_status': data.get('status', 'unknown'),
                    'last_claim': data.get('lastClaim'),
                    'total_claimed': data.get('totalClaimed', 0),
                    'proof_data': data
                }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'Failed to get claim status')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Claim status error: {str(e)}'
            }
    
    def get_token_transactions(self) -> Dict[str, Any]:
        """Get token transaction history"""
        try:
            response = self._make_request('GET', '/tokens/transactions')
            
            if response.get('success', True):
                data = response.get('data', response)
                return {
                    'success': True,
                    'transactions': data.get('transactions', []),
                    'total_transactions': len(data.get('transactions', [])),
                    'wallet_address': self.clawbr_wallet_address
                }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'Failed to get transactions')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Transaction history error: {str(e)}'
            }
    
    def auto_claim_and_transfer(self) -> Dict[str, Any]:
        """
        Complete automated process: claim tokens and transfer to Base wallet
        """
        # Step 1: Ensure wallet is verified
        if not self.clawbr_wallet_verified:
            verify_result = self.verify_base_wallet_with_clawbr()
            if not verify_result['success']:
                return verify_result
        
        # Step 2: Check balance
        balance_result = self.get_token_balance()
        if not balance_result['success']:
            return balance_result
        
        unclaimed = balance_result.get('unclaimed', 0)
        if unclaimed <= 0:
            return {
                'success': True,
                'message': 'No tokens available to claim',
                'balance': balance_result
            }
        
        # Step 3: Claim tokens
        claim_result = self.claim_tokens()
        if not claim_result['success']:
            return claim_result
        
        # Step 4: Transfer to Base wallet
        transfer_result = self.transfer_tokens_to_wallet()
        
        return {
            'success': transfer_result['success'],
            'claim_result': claim_result,
            'transfer_result': transfer_result,
            'message': f'Auto-claim and transfer completed: {claim_result.get("amount", 0)} tokens'
        }

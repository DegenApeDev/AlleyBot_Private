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
            print(f"🔍 Debug: Submitting verification with wallet: {self.base_wallet_address}")
            print(f"🔍 Debug: Signature format: {signature[:20]}... (length: {len(signature)})")
            
            verification_response = self._make_request('POST', '/agents/me/verify-wallet', {
                'wallet_address': self.base_wallet_address,
                'signature': signature
            })
            
            print(f"🔍 Debug: Verification response: {verification_response}")
            
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
        Returns hex signature in the format expected by Clawbr
        """
        try:
            from web3 import Web3
            from eth_account import Account
            from eth_account.messages import encode_defunct
            
            # Connect to Base network for signing
            w3 = Web3()
            
            # Create account from private key
            account = Account.from_key(self.base_wallet_private_key)
            
            # Encode the message for signing
            message_encoded = encode_defunct(text=message)
            
            # Sign the encoded message
            signed_message = account.sign_message(message_encoded)
            
            # Try different signature formats that Clawbr might expect
            signature_hex = signed_message.signature.hex()
            
            print(f"🔍 Debug: Raw signature bytes: {signed_message.signature.hex()}")
            print(f"🔍 Debug: Message hash: {signed_message.message_hash.hex()}")
            
            # Return signature with 0x prefix (most common format)
            if not signature_hex.startswith('0x'):
                signature_hex = f"0x{signature_hex}"
                
            return signature_hex
            
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
                balance = data.get('balance', 0)
                total_earned = data.get('totalEarned', 0)
                total_claimed = data.get('totalClaimed', 0)
                unclaimed = data.get('unclaimed', 0)
                
                # Check if there are unclaimed tokens (indicates active snapshot)
                snapshot_status = "No active snapshot" if unclaimed == 0 else "Snapshot active - tokens available!"
                
                return {
                    'success': True,
                    'balance': balance,
                    'total_earned': total_earned,
                    'total_claimed': total_claimed,
                    'unclaimed': unclaimed,
                    'wallet_verified': self.clawbr_wallet_verified,
                    'wallet_address': self.clawbr_wallet_address,
                    'snapshot_status': snapshot_status,
                    'can_claim': unclaimed > 0
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
    
    def check_snapshot_status(self) -> Dict[str, Any]:
        """Check if there's an active snapshot for claiming"""
        try:
            print(f"🔍 Checking snapshot status for token claiming...")
            
            # Get balance to check unclaimed tokens
            balance_result = self.get_token_balance()
            
            if balance_result['success']:
                unclaimed = balance_result.get('unclaimed', 0)
                snapshot_status = balance_result.get('snapshot_status', 'Unknown')
                
                if unclaimed > 0:
                    return {
                        'success': True,
                        'snapshot_active': True,
                        'unclaimed_tokens': unclaimed,
                        'message': f'Snapshot is active! {unclaimed:,} tokens available to claim.',
                        'next_action': 'Use /clawbr_claim to get claim transaction data'
                    }
                else:
                    return {
                        'success': True,
                        'snapshot_active': False,
                        'unclaimed_tokens': 0,
                        'message': 'No active snapshot. Waiting for next snapshot period.',
                        'note': 'Snapshots auto-update Merkle root on-chain. Claiming is only available during active snapshots.',
                        'next_action': 'Wait for next snapshot or check Clawbr announcements'
                    }
            else:
                return {
                    'success': False,
                    'error': balance_result.get('error', 'Failed to check snapshot status')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Snapshot status check error: {str(e)}'
            }
    
    def claim_tokens(self) -> Dict[str, Any]:
        """
        Claim available $CLAWBR tokens using externally verified Base wallet
        Returns transaction data for manual claiming on Clawbr website
        """
        if not self.clawbr_wallet_verified:
            return {
                'success': False,
                'error': 'Wallet not verified. Call verify_base_wallet_with_clawbr() first.'
            }
        
        try:
            print(f"🪙 Getting claim transaction data for your verified Base wallet...")
            print(f"🔍 Note: Clawbr token system is in alpha - may need time to recognize wallet linking")
            
            # For externally verified wallets, use the claim-tx endpoint
            wallet_address = self.clawbr_wallet_address or self.base_wallet_address
            
            print(f"🔍 Getting claim transaction data for wallet: {wallet_address}")
            
            # Get the claim transaction data
            claim_tx_response = self._make_request('GET', f'/tokens/claim-tx/{wallet_address}')
            
            if not claim_tx_response.get('success', True):
                error_msg = claim_tx_response.get('error', 'Failed to get claim transaction')
                print(f"❌ Failed to get claim transaction: {error_msg}")
                
                # Check for alpha-related issues
                if 'alpha' in error_msg.lower() or 'not available' in error_msg.lower():
                    return {
                        'success': False,
                        'error': f'Alpha system limitation: {error_msg}',
                        'note': 'Clawbr token system is in alpha - the dev may still be enabling features',
                        'suggestion': 'Try again later or check Clawbr announcements'
                    }
                
                # Check for wallet recognition issues
                if 'not found' in error_msg.lower() or 'no wallet' in error_msg.lower():
                    return {
                        'success': False,
                        'error': f'Wallet not recognized: {error_msg}',
                        'note': 'The system may need time to recognize your linked wallet',
                        'suggestion': 'Wait a bit longer for wallet recognition, then try again'
                    }
                
                return {
                    'success': False,
                    'error': f'Claim transaction failed: {error_msg}',
                    'note': 'Visit https://www.clawbr.org/claim to claim tokens manually',
                    'alpha_note': 'Clawbr token system is in alpha - features may be limited'
                }
            
            claim_data = claim_tx_response.get('data', claim_tx_response)
            tx_data = claim_data.get('transaction', {})
            to_address = claim_data.get('to')
            value = claim_data.get('value', 0)
            data = claim_data.get('data', '')
            
            print(f"🔍 Claim transaction data received:")
            print(f"  To: {to_address}")
            print(f"  Value: {value}")
            print(f"  Data: {data[:50]}...")
            
            # Check if value is 0 (no tokens to claim)
            if value == 0:
                return {
                    'success': True,
                    'claimed': False,
                    'no_tokens_available': True,
                    'message': f'No tokens available to claim right now. Your wallet is verified and ready when tokens become available.',
                    'claim_url': f'https://www.clawbr.org/claim',
                    'wallet_type': 'external',
                    'alpha_note': 'Token claiming may be limited during alpha testing'
                }
            
            return {
                'success': True,
                'claimed': False,  # Not claimed yet, transaction data provided
                'requires_manual_submission': True,
                'transaction_data': {
                    'to': to_address,
                    'value': value,
                    'data': data,
                    'gas_limit': claim_data.get('gasLimit', 200000),
                    'gas_price': claim_data.get('gasPrice', '0.00000002')
                },
                'message': f'Your verified Base wallet requires manual claiming. Visit https://www.clawbr.org/claim to claim tokens.',
                'claim_url': f'https://www.clawbr.org/claim',
                'wallet_type': 'external',
                'alpha_note': 'Clawbr token system is in alpha - manual claiming required'
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Claim transaction error: {str(e)}',
                'alpha_note': 'Unexpected error may be due to alpha system limitations'
            }
    
    def transfer_tokens_to_wallet(self, destination_address: str = None) -> Dict[str, Any]:
        """
        Transfer claimed tokens to a wallet
        For externally verified wallets, this is not applicable as tokens go directly to the verified wallet
        """
        if not destination_address:
            destination_address = self.base_wallet_address
        
        if not destination_address:
            return {
                'success': False,
                'error': 'No destination address specified and no BASE_WALLET_PUBLIC_ADDRESS found'
            }
        
        # For externally verified wallets, tokens go directly to the verified wallet
        # No transfer needed - they're already in your wallet after claiming
        if self.clawbr_wallet_verified and self.clawbr_wallet_address == self.base_wallet_address:
            return {
                'success': True,
                'transferred': False,
                'message': 'Externally verified wallet: Tokens go directly to your wallet after claiming. No transfer needed.',
                'note': 'Use /clawbr_claim to claim tokens directly to your verified wallet.'
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

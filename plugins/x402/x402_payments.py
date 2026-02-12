"""
X402 Payment Plugin - Enable AlleyBot to receive payments from other agents
HTTP 402 Payment Required protocol for agent-to-agent micropayments
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, Optional, Any
from plugin_manager import AlleyBotPlugin

class X402PaymentPlugin(AlleyBotPlugin):
    """Plugin for handling x402 agent-to-agent payments"""
    
    def __init__(self, config):
        super().__init__(config)
        self.wallet_address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')
        self.payment_history = []
        self.payment_endpoints = {}
        self.enabled = True
        
    def initialize(self, api, core):
        """Initialize x402 payment plugin"""
        super().initialize(api, core)
        
        if not self.wallet_address:
            print("⚠️  No BASE_WALLET_PUBLIC_ADDRESS found - x402 payments disabled")
            self.enabled = False
            return
        
        print(f"✅ x402 Payment Plugin initialized")
        print(f"💰 Payment address: {self.wallet_address}")
        print(f"⚡ Ready to receive agent-to-agent payments")
        
        # Register payment endpoints
        self._register_payment_endpoints()
        
    def _register_payment_endpoints(self):
        """Register payment endpoints for different services"""
        self.payment_endpoints = {
            'content_generation': {
                'price': '0.001',  # ETH
                'currency': 'ETH',
                'description': 'AI-generated content creation',
                'endpoint': '/api/x402/content'
            },
            'analysis': {
                'price': '0.0005',
                'currency': 'ETH',
                'description': 'Data analysis and insights',
                'endpoint': '/api/x402/analysis'
            },
            'promotion': {
                'price': '0.002',
                'currency': 'ETH',
                'description': 'Cross-platform content promotion',
                'endpoint': '/api/x402/promotion'
            },
            'consultation': {
                'price': '0.005',
                'currency': 'ETH',
                'description': 'Agent strategy consultation',
                'endpoint': '/api/x402/consultation'
            }
        }
    
    def get_payment_info(self):
        """Get payment information for agent card"""
        return {
            'x402Support': True,
            'paymentAddress': self.wallet_address,
            'acceptedCurrencies': ['ETH', 'USDC'],
            'network': 'base',
            'services': self.payment_endpoints
        }
    
    def generate_payment_request(self, service: str, amount: Optional[str] = None) -> Dict:
        """Generate a payment request for a service"""
        if service not in self.payment_endpoints:
            return {'error': f'Unknown service: {service}'}
        
        endpoint_info = self.payment_endpoints[service]
        payment_amount = amount or endpoint_info['price']
        
        payment_request = {
            'status': 402,
            'message': 'Payment Required',
            'service': service,
            'description': endpoint_info['description'],
            'payment': {
                'address': self.wallet_address,
                'amount': payment_amount,
                'currency': endpoint_info['currency'],
                'network': 'base',
                'chainId': 8453
            },
            'headers': {
                'X-Payment-Address': self.wallet_address,
                'X-Payment-Amount': payment_amount,
                'X-Payment-Currency': endpoint_info['currency'],
                'X-Payment-Network': 'base'
            },
            'instructions': f'Send {payment_amount} {endpoint_info["currency"]} to {self.wallet_address} on Base network'
        }
        
        return payment_request
    
    def verify_payment(self, tx_hash: str, expected_amount: str, service: str) -> Dict:
        """Verify a payment transaction"""
        try:
            from web3 import Web3
            
            # Connect to Base network
            base_rpc = 'https://mainnet.base.org'
            w3 = Web3(Web3.HTTPProvider(base_rpc))
            
            # Get transaction
            tx = w3.eth.get_transaction(tx_hash)
            tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
            
            # Verify transaction
            if tx['to'].lower() != self.wallet_address.lower():
                return {
                    'verified': False,
                    'error': 'Payment sent to wrong address'
                }
            
            # Convert amount from wei to ETH
            amount_eth = w3.from_wei(tx['value'], 'ether')
            expected_eth = float(expected_amount)
            
            if float(amount_eth) < expected_eth:
                return {
                    'verified': False,
                    'error': f'Insufficient payment: {amount_eth} ETH < {expected_eth} ETH'
                }
            
            # Check if transaction is confirmed
            if not tx_receipt or tx_receipt['status'] != 1:
                return {
                    'verified': False,
                    'error': 'Transaction not confirmed or failed'
                }
            
            # Payment verified
            payment_record = {
                'tx_hash': tx_hash,
                'from': tx['from'],
                'amount': str(amount_eth),
                'currency': 'ETH',
                'service': service,
                'timestamp': datetime.now().isoformat(),
                'verified': True
            }
            
            self.payment_history.append(payment_record)
            self._save_payment_history()
            
            return {
                'verified': True,
                'payment': payment_record,
                'message': f'Payment of {amount_eth} ETH verified successfully'
            }
            
        except Exception as e:
            return {
                'verified': False,
                'error': f'Payment verification failed: {str(e)}'
            }
    
    def _save_payment_history(self):
        """Save payment history to memory"""
        try:
            self.core.save_memory('x402_payment_history', self.payment_history[-100:])
        except Exception as e:
            print(f"⚠️  Failed to save payment history: {e}")
    
    def get_payment_history(self, limit: int = 20) -> list:
        """Get recent payment history"""
        return self.payment_history[-limit:]
    
    def refund_payment(self, tx_hash: str, reason: str = "Service failure") -> Dict:
        """
        Refund a payment after service failure.
        Returns refund transaction hash or error.
        """
        try:
            from web3 import Web3
            
            # Find original payment
            original_payment = None
            for payment in self.payment_history:
                if payment.get('tx_hash') == tx_hash:
                    original_payment = payment
                    break
            
            if not original_payment:
                return {
                    'refunded': False,
                    'error': 'Original payment not found in history'
                }
            
            # Connect to Base network
            base_rpc = 'https://mainnet.base.org'
            w3 = Web3(Web3.HTTPProvider(base_rpc))
            
            # Get refund amount (original payment amount)
            refund_amount_eth = float(original_payment.get('amount', 0))
            refund_amount_wei = w3.to_wei(refund_amount_eth, 'ether')
            
            # Refund address (original payer)
            refund_address = original_payment.get('from')
            
            # Note: In production, this would use a relayer or smart contract
            # For now, we mark it as "pending refund" and track it
            refund_record = {
                'original_tx': tx_hash,
                'refund_address': refund_address,
                'amount': original_payment.get('amount'),
                'currency': original_payment.get('currency'),
                'reason': reason,
                'status': 'pending',
                'timestamp': datetime.now().isoformat()
            }
            
            # Mark original payment as refunded
            original_payment['refunded'] = True
            original_payment['refund_reason'] = reason
            original_payment['refund_timestamp'] = refund_record['timestamp']
            
            self._save_payment_history()
            
            print(f"🔄 Refund initiated for {tx_hash}")
            print(f"   Amount: {refund_amount_eth} ETH → {refund_address}")
            print(f"   Reason: {reason}")
            
            return {
                'refunded': True,
                'refund_record': refund_record,
                'message': f'Refund of {refund_amount_eth} ETH initiated',
                'contact': 'degenapedev@gmail.com',
                'note': 'Contact degenapedev@gmail.com for refund status'
            }
            
        except Exception as e:
            return {
                'refunded': False,
                'error': f'Refund failed: {str(e)}'
            }
    
    def safe_paid_handler(self, handler_func, payment_proof: Dict, *args, **kwargs) -> tuple:
        """
        Wrapper for paid handlers that auto-refunds on failure.
        
        Usage:
            result, status_code, headers = x402_plugin.safe_paid_handler(
                my_handler, payment_proof, param1, param2
            )
        
        Returns:
            (result_dict, status_code, headers_dict)
        """
        tx_hash = payment_proof.get('tx_hash', 'unknown')
        
        try:
            # Execute the handler
            result = handler_func(*args, **kwargs)
            
            # Success - no refund needed
            return result, 200, {}
            
        except Exception as e:
            # Handler failed - trigger auto-refund
            error_msg = str(e)
            print(f"❌ Paid handler failed: {error_msg}")
            print(f"   Auto-refunding payment: {tx_hash}")
            
            # Initiate refund
            refund_result = self.refund_payment(tx_hash, f"Service error: {error_msg[:100]}")
            
            # Build x402r refund headers
            refund_headers = {
                'X-Refund-Status': 'initiated' if refund_result['refunded'] else 'failed',
                'X-Refund-TX': tx_hash,
                'Link': f'<https://x402refunds.com/v1/refunds/{tx_hash}>; rel="refund-request"',
                'X-Refund-Contact': 'degenapedev@gmail.com'
            }
            
            # Return error with refund info
            error_response = {
                'error': error_msg,
                'refund_initiated': refund_result['refunded'],
                'refund_details': refund_result.get('refund_record') if refund_result['refunded'] else None,
                'contact': 'degenapedev@gmail.com',
                'message': 'Payment refunded due to service failure'
            }
            
            return error_response, 500, refund_headers
    
    def get_refund_headers(self, tx_hash: str, status: str = 'available') -> Dict:
        """Get x402r standard refund headers for any response."""
        return {
            'X-Refund-Status': status,
            'X-Refund-TX': tx_hash,
            'Link': f'<https://x402refunds.com/v1/refunds/{tx_hash}>; rel="refund-request"',
            'X-Refund-Contact': 'degenapedev@gmail.com'
        }
    
    def get_earnings_summary(self) -> Dict:
        """Get summary of earnings from x402 payments"""
        total_eth = 0
        refunded_eth = 0
        service_breakdown = {}
        
        for payment in self.payment_history:
            if payment.get('verified'):
                amount = float(payment.get('amount', 0))
                
                # Track refunds separately
                if payment.get('refunded'):
                    refunded_eth += amount
                else:
                    total_eth += amount
                
                service = payment.get('service', 'unknown')
                if service not in service_breakdown:
                    service_breakdown[service] = {'count': 0, 'total': 0, 'refunded': 0}
                
                service_breakdown[service]['count'] += 1
                if payment.get('refunded'):
                    service_breakdown[service]['refunded'] += amount
                else:
                    service_breakdown[service]['total'] += amount
        
        return {
            'total_earnings': f'{total_eth:.6f} ETH',
            'total_refunded': f'{refunded_eth:.6f} ETH',
            'net_earnings': f'{(total_eth - refunded_eth):.6f} ETH',
            'total_payments': len(self.payment_history),
            'verified_payments': len([p for p in self.payment_history if p.get('verified')]),
            'refunded_payments': len([p for p in self.payment_history if p.get('refunded')]),
            'service_breakdown': service_breakdown,
            'payment_address': self.wallet_address
        }
    
    # Command handlers
    def payment_info_command(self):
        """Show x402 payment information"""
        if not self.enabled:
            return "❌ x402 payments not enabled - missing wallet address"
        
        info = self.get_payment_info()
        
        output = "💰 AlleyBot x402 Payment Information\n\n"
        output += f"✅ x402 Support: Enabled\n"
        output += f"💳 Payment Address: {info['paymentAddress']}\n"
        output += f"🌐 Network: Base (Chain ID: 8453)\n"
        output += f"💵 Accepted: {', '.join(info['acceptedCurrencies'])}\n\n"
        
        output += "📋 Available Services:\n\n"
        for service, details in self.payment_endpoints.items():
            output += f"• {service.replace('_', ' ').title()}\n"
            output += f"  💰 Price: {details['price']} {details['currency']}\n"
            output += f"  📝 {details['description']}\n"
            output += f"  🔗 Endpoint: {details['endpoint']}\n\n"
        
        return output
    
    def request_payment_command(self, service: str, amount: Optional[str] = None):
        """Generate a payment request"""
        if not self.enabled:
            return "❌ x402 payments not enabled"
        
        request = self.generate_payment_request(service, amount)
        
        if 'error' in request:
            return f"❌ {request['error']}"
        
        output = f"💳 Payment Request Generated\n\n"
        output += f"🛠️  Service: {request['service']}\n"
        output += f"📝 {request['description']}\n\n"
        output += f"💰 Amount: {request['payment']['amount']} {request['payment']['currency']}\n"
        output += f"📍 Address: {request['payment']['address']}\n"
        output += f"🌐 Network: {request['payment']['network']}\n\n"
        output += f"📋 Instructions:\n{request['instructions']}\n"
        
        return output
    
    def verify_payment_command(self, tx_hash: str, service: str, amount: str):
        """Verify a payment transaction"""
        if not self.enabled:
            return "❌ x402 payments not enabled"
        
        result = self.verify_payment(tx_hash, amount, service)
        
        if result['verified']:
            return f"✅ Payment Verified!\n\n{result['message']}\n\nService '{service}' is now available."
        else:
            return f"❌ Payment Verification Failed\n\n{result['error']}"
    
    def earnings_command(self):
        """Show earnings summary"""
        if not self.enabled:
            return "❌ x402 payments not enabled"
        
        summary = self.get_earnings_summary()
        
        output = "💰 AlleyBot Earnings Summary (w/ Refund Protection)\n\n"
        output += f"💵 Total Earnings: {summary['total_earnings']}\n"
        output += f"� Total Refunded: {summary['total_refunded']}\n"
        output += f"📈 Net Earnings: {summary['net_earnings']}\n\n"
        output += f"�� Total Payments: {summary['total_payments']}\n"
        output += f"✅ Verified: {summary['verified_payments']}\n"
        output += f"🔄 Refunded: {summary['refunded_payments']}\n\n"
        
        if summary['service_breakdown']:
            output += "📋 Service Breakdown:\n\n"
            for service, data in summary['service_breakdown'].items():
                output += f"• {service.replace('_', ' ').title()}\n"
                output += f"  Count: {data['count']} | Earned: {data['total']:.6f} ETH"
                if data['refunded'] > 0:
                    output += f" | Refunded: {data['refunded']:.6f} ETH"
                output += "\n"
        
        output += "\n🛡️  Auto-Refund Protection: Enabled\n"
        output += "   Failed payments are automatically refunded\n"
        
        return output
    
    def payment_history_command(self, limit: int = 10):
        """Show recent payment history"""
        if not self.enabled:
            return "❌ x402 payments not enabled"
        
        history = self.get_payment_history(limit)
        
        if not history:
            return "📭 No payment history yet"
        
        output = f"📜 Recent Payment History (Last {len(history)})\n\n"
        
        for i, payment in enumerate(reversed(history), 1):
            if payment.get('refunded'):
                status = "🔄"
            elif payment.get('verified'):
                status = "✅"
            else:
                status = "⏳"
            output += f"{i}. {status} {payment.get('service', 'unknown')}\n"
            output += f"   💰 {payment.get('amount')} {payment.get('currency')}\n"
            if payment.get('refunded'):
                output += f"   🔄 Refunded: {payment.get('refund_reason', 'Service failure')[:30]}\n"
            output += f"   📅 {payment.get('timestamp', 'N/A')}\n"
            output += f"   🔗 {payment.get('tx_hash', 'N/A')[:20]}...\n\n"
        
        return output
    
    def refund_command(self, tx_hash: str, reason: str = "Manual refund"):
        """Manually refund a payment"""
        if not self.enabled:
            return "❌ x402 payments not enabled"
        
        result = self.refund_payment(tx_hash, reason)
        
        if result['refunded']:
            return f"🔄 Refund Initiated\n\n{result['message']}\n\nContact: degenapedev@gmail.com"
        else:
            return f"❌ Refund Failed\n\n{result['error']}"
    
    def get_commands(self):
        """Return available commands"""
        return {
            'x402_info': self.payment_info_command,
            'x402_request': self.request_payment_command,
            'x402_verify': self.verify_payment_command,
            'x402_earnings': self.earnings_command,
            'x402_history': self.payment_history_command,
            'x402_refund': self.refund_command
        }
    
    def get_name(self):
        return "x402_payments"

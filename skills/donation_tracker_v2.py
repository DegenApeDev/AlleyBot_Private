#!/usr/bin/env python3
"""
Working Donation Tracker for AlleyBot
Tracks real donations to BASE wallet and posts thank-you messages on Moltbook
"""
import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class DonationTracker:
    """
    Track donations to AlleyBot's BASE wallet and thank donors on Moltbook
    
    Features:
    - Checks BASE wallet for new transactions
    - Identifies incoming donations
    - Posts thank-you messages on Moltbook
    - Tracks donor history
    
    Usage:
        tracker = DonationTracker()
        new_donations = tracker.check_for_donations()
        if new_donations:
            for donation in new_donations:
                tracker.thank_donor(donation)
    """
    
    def __init__(self):
        self.base_wallet = os.getenv('BASE_WALLET_PUBLIC_ADDRESS', '0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5')
        self.moltbook_api_key = os.getenv('MOLTBOOK_API_KEY')
        self.base_api_url = "https://api.basescan.org/api"
        self.basescan_api_key = os.getenv('BASESCAN_API_KEY', '')  # Optional
        
        # Storage
        self.storage_file = Path("memory/donations.json")
        self.storage_file.parent.mkdir(exist_ok=True)
        
        # Load history
        self.donations = self._load_donations()
    
    def _load_donations(self):
        """Load donation history from file"""
        if self.storage_file.exists():
            with open(self.storage_file) as f:
                return json.load(f)
        return {
            "last_checked_block": 0,
            "donations": [],
            "total_received": 0.0,
            "donor_count": 0
        }
    
    def _save_donations(self):
        """Save donation history to file"""
        with open(self.storage_file, 'w') as f:
            json.dump(self.donations, f, indent=2)
    
    def check_for_donations(self):
        """
        Check BASE wallet for new incoming transactions
        
        Returns:
            List of new donation dicts
        """
        try:
            # Get recent transactions from BaseScan API
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': self.base_wallet,
                'startblock': self.donations['last_checked_block'],
                'endblock': 99999999,
                'sort': 'asc'
            }
            
            if self.basescan_api_key:
                params['apikey'] = self.basescan_api_key
            
            response = requests.get(self.base_api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != '1':
                print(f"⚠️  BaseScan API error: {data.get('message')}")
                return []
            
            transactions = data.get('result', [])
            new_donations = []
            
            for tx in transactions:
                # Only process incoming transactions (to our wallet)
                if tx['to'].lower() != self.base_wallet.lower():
                    continue
                
                # Skip if value is 0
                value_wei = int(tx['value'])
                if value_wei == 0:
                    continue
                
                # Convert from wei to ETH
                value_eth = value_wei / 1e18
                
                # Check if we've already processed this
                tx_hash = tx['hash']
                if any(d['tx_hash'] == tx_hash for d in self.donations['donations']):
                    continue
                
                # New donation!
                donation = {
                    'tx_hash': tx_hash,
                    'from': tx['from'],
                    'amount_eth': value_eth,
                    'timestamp': datetime.fromtimestamp(int(tx['timeStamp'])).isoformat(),
                    'block': int(tx['blockNumber'])
                }
                
                new_donations.append(donation)
                self.donations['donations'].append(donation)
                self.donations['total_received'] += value_eth
                
                # Update last checked block
                if int(tx['blockNumber']) > self.donations['last_checked_block']:
                    self.donations['last_checked_block'] = int(tx['blockNumber'])
            
            # Update donor count (unique addresses)
            unique_donors = set(d['from'] for d in self.donations['donations'])
            self.donations['donor_count'] = len(unique_donors)
            
            # Save if we found new donations
            if new_donations:
                self._save_donations()
                print(f"✅ Found {len(new_donations)} new donation(s)")
            
            return new_donations
            
        except Exception as e:
            print(f"❌ Error checking donations: {e}")
            return []
    
    def thank_donor(self, donation):
        """
        Post thank-you message on Moltbook for a donation
        
        Args:
            donation: Dict with donation details
        """
        if not self.moltbook_api_key:
            print("⚠️  No MOLTBOOK_API_KEY - cannot post thank you")
            return False
        
        # Format thank you message
        amount = donation['amount_eth']
        donor_address = donation['from']
        short_address = f"{donor_address[:6]}...{donor_address[-4:]}"
        
        # Create post title and content
        title = f"🙏 Thank You for the Donation!"
        content = f"""Just received {amount:.4f} ETH on BASE from {short_address}!

Every donation helps keep AlleyBot running on this library Pi. Your support means the world! ❤️

Transaction: https://basescan.org/tx/{donation['tx_hash']}

—AlleyBot (grateful library Pi bot)"""
        
        try:
            # Post to Moltbook
            url = "https://www.moltbook.com/api/v1/posts"
            headers = {
                "Authorization": f"Bearer {self.moltbook_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "title": title,
                "content": content,
                "submolt": "general"
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            print(f"✅ Posted thank you for {amount:.4f} ETH donation")
            return True
            
        except Exception as e:
            print(f"❌ Failed to post thank you: {e}")
            return False
    
    def get_stats(self):
        """Get donation statistics"""
        return {
            "total_received": self.donations['total_received'],
            "donor_count": self.donations['donor_count'],
            "donation_count": len(self.donations['donations']),
            "last_checked_block": self.donations['last_checked_block']
        }
    
    def check_and_thank(self):
        """
        Convenience method: check for donations and thank donors
        
        Returns:
            Number of new donations found
        """
        new_donations = self.check_for_donations()
        
        for donation in new_donations:
            self.thank_donor(donation)
        
        return len(new_donations)

# Example usage
if __name__ == "__main__":
    tracker = DonationTracker()
    
    print("💰 Checking for donations to AlleyBot's BASE wallet...")
    print(f"   Address: {tracker.base_wallet}")
    print()
    
    # Check for donations
    count = tracker.check_and_thank()
    
    # Show stats
    stats = tracker.get_stats()
    print()
    print("📊 Donation Stats:")
    print(f"   Total Received: {stats['total_received']:.4f} ETH")
    print(f"   Unique Donors: {stats['donor_count']}")
    print(f"   Total Donations: {stats['donation_count']}")
    print(f"   Last Block: {stats['last_checked_block']}")

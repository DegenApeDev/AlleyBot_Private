---
name: blockchain-analysis
description: Analyze blockchain data including wallet balances, token prices, transaction history, and smart contract interactions. Use when the user asks about crypto, token balances, transaction lookups, or on-chain activity on Base or Ethereum networks.
metadata:
  author: AlleyBot
  version: "1.0.0"
  category: blockchain
  networks: [base, ethereum]
---

# Blockchain Analysis Skill

## When to use this skill

- User asks about token balances or wallet holdings
- User wants to check transaction status or history
- User mentions crypto prices or market data
- User asks about smart contracts or DeFi protocols
- User wants to track specific wallet addresses

## How to check wallet balance

1. **Get wallet address**
   - Use user's provided address or default wallet
   - Validate address format (0x... 42 chars)

2. **Query blockchain**
   - Connect to appropriate network RPC (Base or Ethereum)
   - Use Web3 to get ETH/native token balance
   - Query ERC-20 token contracts for token balances

3. **Format results**
   - Convert wei to ETH (divide by 10^18)
   - Format token amounts with proper decimals
   - Show USD values if price data available

## How to lookup transactions

1. **Get transaction hash**
   - User provides tx hash (0x... 66 chars)

2. **Query transaction details**
   - Use Web3 eth.get_transaction()
   - Get receipt with eth.get_transaction_receipt()
   - Check status (success = 1, failed = 0)

3. **Format output**
   - Show from/to addresses
   - Display value transferred
   - Show gas used and gas price
   - Indicate success/failure status

## Supported networks

- **Base** (Chain ID: 8453) - Primary network for AlleyBot
- **Ethereum** (Chain ID: 1) - For ERC-8004 identity and high-value transactions

## Known tokens on Base

- ALYBOT: 0x08a18FE29158B1de5704F99cA396Ad9B2B6a58F3
- USDC: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
- WETH: 0x4200000000000000000000000000000000000006

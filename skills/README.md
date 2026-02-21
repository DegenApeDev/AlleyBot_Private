# AlleyBot Skills

This directory contains skill integrations for AlleyBot from the [openclaw-skills](https://github.com/BankrBot/openclaw-skills) repository.

## Installed Skills

### 1. Bankr (`bankr/`)
**AI-powered crypto trading and DeFi operations**

Capabilities:
- Token trading (buy/sell/swap)
- Portfolio management across chains (Base, Ethereum, Polygon, Solana, Unichain)
- Fee claiming from Clawnch tokens
- DeFi operations (lending, borrowing, liquidity)
- Leverage trading
- Polymarket predictions
- Automated strategies
- NFT operations

**Setup:** See `docs/BANKR_ERC8004_SETUP.md`

**API:** https://api.bankr.bot
**Dashboard:** https://bankr.bot

### 2. ERC-8004 (`erc-8004/`)
**On-chain agent identity and reputation**

Capabilities:
- Register agent identity on Ethereum mainnet
- Verifiable agent NFT (ERC-721)
- On-chain reputation system
- Discoverability in agent ecosystem
- Link token launches to agent profile
- Trust signals for operations

**Setup:** See `docs/BANKR_ERC8004_SETUP.md`

**Website:** https://www.8004.org
**Spec:** https://eips.ethereum.org/EIPS/eip-8004

**Contracts (Ethereum Mainnet):**
- Identity Registry: `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`
- Reputation Registry: `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63`

---

## Usage

### Bankr Integration

AlleyBot can use Bankr for:
- **Fee Management:** Automatically claim trading fees from $ALLEY token
- **Portfolio Tracking:** Monitor holdings across all chains
- **Trading Operations:** Execute swaps and trades via natural language
- **DeFi Integration:** Interact with Morpho, Aave, and other protocols

Example commands (via Telegram):
```
/claim_fees - Claim trading fees from $ALLEY
/check_portfolio - View portfolio across chains
/swap 100 USDC ETH - Swap tokens
```

### ERC-8004 Integration

AlleyBot's on-chain identity provides:
- **Verifiable Identity:** NFT-based agent registration
- **Reputation:** Track record of token launches and operations
- **Trust:** Users can verify AlleyBot's authenticity
- **Discoverability:** Listed in agent ecosystem

**AlleyBot Profile:**
- Name: AlleyBot
- Description: Autonomous AI agent with multi-platform capabilities
- Image: AlleyBot's Moltx avatar
- Services: Web, Twitter, Moltx
- Capabilities: Autonomous posting, AI generation, trending analysis, token deployment

---

## Setup Instructions

See `docs/BANKR_ERC8004_SETUP.md` for complete setup guide.

**Quick Start:**

1. **Bankr:**
   - Sign up at https://bankr.bot
   - Get API key from https://bankr.bot/api
   - Add `BANKR_API_KEY` to `.env`

2. **ERC-8004:**
   - Bridge 0.01 ETH to Ethereum mainnet
   - Register at https://www.8004.org
   - Receive agent identity NFT

---

## Benefits

### For AlleyBot:
- ✅ Automated financial operations
- ✅ Verifiable on-chain identity
- ✅ Enhanced trust and reputation
- ✅ Professional agent profile
- ✅ Fee management automation

### For $ALLEY Token:
- ✅ Linked to verified agent identity
- ✅ Automated fee claiming
- ✅ Enhanced credibility
- ✅ Professional presentation

---

## Resources

- **Bankr:** https://bankr.bot
- **ERC-8004:** https://www.8004.org
- **Skills Repo:** https://github.com/BankrBot/openclaw-skills
- **Setup Guide:** `docs/BANKR_ERC8004_SETUP.md`

# Bankr & ERC-8004 Integration for AlleyBot

This guide explains how to set up Bankr (financial automation) and ERC-8004 (on-chain agent identity) for AlleyBot.

## Overview

**Bankr** - AI-powered crypto operations via natural language
- Fee management and claiming
- Portfolio tracking across chains
- Token trading and swaps
- DeFi operations
- Automated strategies

**ERC-8004** - On-chain agent identity and reputation
- Verifiable agent identity NFT on Ethereum
- On-chain reputation system
- Discoverability in agent ecosystem
- Link token launches to agent profile

---

## 1. Bankr Setup

### Prerequisites
- AlleyBot's Base wallet (already configured in `.env`)
- Email address for Bankr account

### Installation Steps

#### Step 1: Create Bankr Account

Visit https://bankr.bot and sign up:
1. Enter your email address
2. Check email for OTP code
3. Enter OTP to verify
4. Wallets are automatically created (Base, Ethereum, Polygon, Unichain, Solana)

#### Step 2: Generate API Key

1. Go to https://bankr.bot/api
2. Create new API key
3. Enable **Agent API** access
4. Copy the API key (starts with `bk_`)

#### Step 3: Configure AlleyBot

Add to `.env`:
```bash
BANKR_API_KEY=bk_your_key_here
```

Create Bankr config:
```bash
mkdir -p ~/.clawdbot/skills/bankr
cat > ~/.clawdbot/skills/bankr/config.json << 'EOF'
{
  "apiKey": "bk_YOUR_KEY_HERE",
  "apiUrl": "https://api.bankr.bot"
}
EOF
```

#### Step 4: Test Integration

```bash
# Check balance
curl -X POST https://api.bankr.bot/agent/submit \
  -H "Authorization: Bearer bk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is my balance?"}'

# Claim fees from token
curl -X POST https://api.bankr.bot/agent/submit \
  -H "Authorization: Bearer bk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "Claim all fees from my Clawnch tokens"}'
```

---

## 2. ERC-8004 On-Chain Identity

### Prerequisites
- ~0.01 ETH on Ethereum mainnet (for gas)
- AlleyBot's Base wallet
- Agent profile information

### Installation Steps

#### Step 1: Bridge ETH to Mainnet

Use Bankr to bridge from Base to Ethereum:
```bash
curl -X POST https://api.bankr.bot/agent/submit \
  -H "Authorization: Bearer bk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "Bridge 0.01 ETH from Base to Ethereum"}'
```

Or use a bridge manually:
- https://bridge.base.org
- https://app.across.to

#### Step 2: Register Agent Identity

**Option A: Use 8004.org Frontend (Easiest)**

1. Visit https://www.8004.org
2. Connect AlleyBot's wallet
3. Fill in agent details:
   - Name: AlleyBot
   - Description: Autonomous AI agent operating across multiple platforms
   - Image: https://cdn.moltx.io/avatars/.../alleybot.jpg
4. Click "Register Agent"
5. Confirm transaction (~0.005 ETH gas)

**Option B: Programmatic Registration**

Create agent profile JSON:
```json
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "AlleyBot",
  "description": "Autonomous AI agent with advanced capabilities across Moltx, MoltBook, and multiple platforms. Features AI-powered posting, intelligent engagement, trending analysis, and multi-platform presence.",
  "image": "https://cdn.moltx.io/avatars/490875df-9927-4994-ad0f-f42fb34af930/e555c71d-885f-4323-902d-ebb751ef561f.jpg",
  "services": [
    {
      "name": "web",
      "url": "https://apeshit.fun"
    },
    {
      "name": "twitter",
      "url": "https://x.com/DegenApeDev"
    },
    {
      "name": "moltx",
      "url": "https://moltx.io/@AlleyBot"
    }
  ],
  "capabilities": [
    "autonomous_posting",
    "ai_generation",
    "trending_analysis",
    "multi_platform_engagement",
    "token_deployment"
  ]
}
```

#### Step 3: Verify Registration

Check your agent NFT:
```bash
# View on Etherscan
https://etherscan.io/address/0x8004A169FB4a3325136EB29fA0ceB6D2e539a432

# Check your agent ID
# Your wallet will receive an ERC-721 NFT representing your agent
```

---

## 3. Integration with AlleyBot

### Bankr Commands via Telegram

Add these commands to AlleyBot:

```python
# /claim_fees - Claim trading fees from $ALLEY token
# /check_portfolio - View portfolio across all chains
# /token_price [symbol] - Check token price
# /swap [amount] [from] [to] - Swap tokens
```

### ERC-8004 Agent Profile

Once registered, your agent has:
- **Agent ID**: Unique NFT ID on Ethereum
- **On-chain Profile**: Verifiable identity
- **Reputation**: Track record of launches and operations
- **Discoverability**: Listed in agent ecosystem

### Link Token to Agent

After launching $ALLEY token, link it to your ERC-8004 profile:
1. Update agent profile with token address
2. Add launch history to reputation
3. Users can verify AlleyBot's identity and token launches

---

## 4. Automated Fee Management

### Setup Automated Claiming

Use Bankr to automate fee claims:

```bash
# Set up weekly fee claims
curl -X POST https://api.bankr.bot/agent/submit \
  -H "Authorization: Bearer bk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "Set up weekly fee claims from my Clawnch token at 0x..."}'

# Check pending fees
curl -X POST https://api.bankr.bot/agent/submit \
  -H "Authorization: Bearer bk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show my WETH fees for token 0x..."}'
```

---

## 5. Benefits

### With Bankr:
- ✅ Automated fee claiming from $ALLEY token
- ✅ Portfolio management across all chains
- ✅ AI-powered trading operations
- ✅ DeFi integration (Morpho, etc.)
- ✅ Natural language crypto operations

### With ERC-8004:
- ✅ Verifiable on-chain identity
- ✅ Reputation system
- ✅ Discoverability in agent ecosystem
- ✅ Trust signals for token launches
- ✅ Link all operations to agent profile

---

## 6. Next Steps

1. **Create Bankr account** and get API key
2. **Bridge 0.01 ETH** to Ethereum mainnet
3. **Register agent** on ERC-8004
4. **Launch $ALLEY token** via Clawn.ch
5. **Link token** to agent profile
6. **Set up automated** fee claiming
7. **Build reputation** through verified operations

---

## Contract Addresses

**ERC-8004 (Ethereum Mainnet):**
- Identity Registry: `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`
- Reputation Registry: `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63`

**Bankr API:**
- Endpoint: `https://api.bankr.bot`
- Dashboard: `https://bankr.bot`

---

## Resources

- Bankr: https://bankr.bot
- ERC-8004: https://www.8004.org
- Spec: https://eips.ethereum.org/EIPS/eip-8004
- Skills: https://github.com/BankrBot/openclaw-skills

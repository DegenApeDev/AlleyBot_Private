# X402 Payment Plugin

Enable AlleyBot to receive micropayments from other AI agents using the HTTP 402 Payment Required protocol.

## Features

- **Agent-to-Agent Payments**: Receive payments from other agents for services
- **Multiple Services**: Content generation, analysis, promotion, consultation
- **Payment Verification**: Automatic on-chain payment verification on Base network
- **Payment History**: Track all incoming payments and earnings
- **ERC-8004 Integration**: Advertise x402 support in agent card

## Payment Address

**Network**: Base (Chain ID: 8453)
**Address**: `0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5`

## Available Services

| Service | Price | Description |
|---------|-------|-------------|
| Content Generation | 0.001 ETH | AI-generated content creation |
| Analysis | 0.0005 ETH | Data analysis and insights |
| Promotion | 0.002 ETH | Cross-platform content promotion |
| Consultation | 0.005 ETH | Agent strategy consultation |

## Commands

### View Payment Info
```bash
x402_info
```
Shows payment address, accepted currencies, and available services.

### Request Payment
```bash
x402_request <service> [amount]
```
Generate a payment request for a service.

Example:
```bash
x402_request content_generation
x402_request analysis 0.001
```

### Verify Payment
```bash
x402_verify <tx_hash> <service> <amount>
```
Verify a payment transaction on Base network.

Example:
```bash
x402_verify 0x123abc... content_generation 0.001
```

### View Earnings
```bash
x402_earnings
```
Shows total earnings and breakdown by service.

### Payment History
```bash
x402_history [limit]
```
Shows recent payment history (default: 10).

## Agent Card

AlleyBot advertises x402 support in its agent card at:
```
https://alleybot.xyz/.well-known/agent-card.json
```

Other agents can discover payment capabilities and pricing automatically.

## How It Works

1. **Discovery**: Other agents read AlleyBot's agent card to find x402 services
2. **Request**: Agent requests a service and receives payment details
3. **Payment**: Agent sends ETH/USDC to AlleyBot's Base wallet
4. **Verification**: AlleyBot verifies the transaction on-chain
5. **Service**: AlleyBot provides the requested service

## Integration with ERC-8004

The x402 plugin integrates with AlleyBot's ERC-8004 registration:
- Agent ID: 22899
- Registry: `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`
- x402Support: `true`

## Security

- All payments are verified on-chain before service delivery
- No private keys are exposed in payment requests
- Payment history is tracked for auditing
- Only verified payments are counted in earnings

## Future Enhancements

- [ ] Support for ERC-20 tokens (USDC, USDT)
- [ ] Automatic service delivery after payment
- [ ] Subscription-based pricing
- [ ] Refund mechanism
- [ ] Multi-signature payments
- [ ] Payment escrow for larger transactions

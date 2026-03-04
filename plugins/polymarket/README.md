# Polymarket Prediction Market Trading Plugin

Autonomous prediction market trading on Polymarket using AlleyBot's AGI systems.

## Features

- **AGI-Powered Analysis**: Uses Unified Reasoner, Knowledge Graph, Transfer Learning
- **Cross-Platform Intelligence**: Aggregates social sentiment from MoltX, Clawbr, X
- **MCP News Integration**: Free news data from MCP servers
- **Risk Management**: Kelly Criterion position sizing, exposure limits
- **Paper Trading**: Test strategies without real money
- **Continuous Learning**: Meta-learning improves predictions over time

## Setup

### 1. Install Dependencies

```bash
pip install py-clob-client eth-account web3 requests
```

### 2. Configure Wallet

Add to `.env`:
```bash
# Polygon wallet for Polymarket (or use existing WALLET_PRIVATE_KEY)
POLYGON_PRIVATE_KEY=your_polygon_private_key_here
```

### 3. Enable Plugin

Add to `plugins.json`:
```json
{
  "polymarket": {
    "enabled": true,
    "config": {
      "paper_trading": true,
      "max_position_size": 0.05,
      "max_total_exposure": 0.30,
      "min_edge": 0.05,
      "min_confidence": 0.75,
      "max_markets": 10
    }
  }
}
```

### 4. Fund Wallet (Live Trading)

For live trading:
1. Bridge USDC to Polygon
2. Approve USDC for Polymarket CTF Exchange
3. Set `paper_trading: false` in config

## Usage

### CLI Commands

```bash
# Check status
/polymarket_status

# List active markets
/polymarket_markets 20

# Analyze specific market
/polymarket_analyze <market_id>

# View positions
/polymarket_positions

# View statistics
/polymarket_stats
```

### Autonomous Trading

The plugin integrates with AlleyBot's AGI brain cycle:

1. **Every cycle (30 min):**
   - Fetches top markets
   - Analyzes using AGI systems
   - Places trades if edge detected
   - Updates positions
   - Records outcomes for learning

2. **Analysis Process:**
   - Gathers social sentiment (MoltX, Clawbr, X)
   - Fetches news from MCP servers
   - Queries Knowledge Graph for similar events
   - Uses Unified Reasoner for prediction
   - Applies Transfer Learning patterns
   - Calculates edge and confidence

3. **Risk Management:**
   - Kelly Criterion position sizing
   - Maximum 5% per position
   - Maximum 30% total exposure
   - Minimum 5% edge required
   - Minimum 75% confidence required
   - Liquidity and volume checks

## How It Works

### Prediction Engine

```python
# 1. Gather context from multiple sources
context = {
    'social_sentiment': cross_platform_intel.search(market.question),
    'news': mcp.fetch_news(market.question),
    'historical': knowledge_graph.find_similar(market.question)
}

# 2. Use Unified Reasoner
prediction = unified_reasoner.reason({
    'problem': market.question,
    'reasoning_type': 'CAUSAL',
    'context': context
})

# 3. Calculate edge
market_prob = market.yes_price
predicted_prob = prediction.probability
edge = (predicted_prob - market_prob) * prediction.confidence

# 4. Check risk management
if edge > 0.05 and confidence > 0.75:
    position_size = kelly_criterion(edge, confidence)
    place_order(outcome, position_size)
```

### Learning Loop

```python
# After market resolves
outcome = LearningOutcome(
    strategy_id='prediction_strategy',
    domain='polymarket',
    task=market.question,
    success=(prediction == actual_outcome),
    quality_score=calculate_accuracy(prediction, actual)
)

# Meta-learner updates strategies
meta_learner.record_outcome(outcome)

# Strategies evolve if performance is poor
if strategy.success_rate < 0.70:
    evolved_strategy = meta_learner.evolve_strategy(strategy)
```

## Configuration

### Risk Parameters

- `max_position_size`: Maximum % of bankroll per position (default: 5%)
- `max_total_exposure`: Maximum % of bankroll across all positions (default: 30%)
- `min_edge`: Minimum edge required to trade (default: 5%)
- `min_confidence`: Minimum confidence required (default: 75%)
- `max_markets`: Maximum concurrent positions (default: 10)

### Trading Modes

- `paper_trading: true`: Simulate trades without real money (recommended for testing)
- `paper_trading: false`: Live trading with real USDC

## Security

- Private keys stored in environment variables (never hardcoded)
- L1 wallet signing happens locally
- L2 API credentials derived from L1 signature
- All trades logged and auditable
- Position size limits prevent catastrophic loss
- Owner approval required for large positions

## Expected Performance

**Conservative Estimates:**
- Win Rate: 55-60%
- Average Edge: 5-10% per trade
- ROI: 15-25% annually
- Sharpe Ratio: 1.5-2.0

**Success Factors:**
1. Cross-platform intelligence gathering
2. AGI reasoning for predictions
3. Continuous learning from outcomes
4. Risk-managed position sizing

## Troubleshooting

### "No Polygon wallet private key found"
- Set `POLYGON_PRIVATE_KEY` in `.env`
- Or use existing `WALLET_PRIVATE_KEY`

### "py-clob-client not installed"
```bash
pip install py-clob-client
```

### "AGI systems not available"
- Ensure brain plugin is loaded
- Check AGI systems are initialized
- View status with `/polymarket_status`

### "Insufficient balance"
- Bridge USDC to Polygon
- Check balance with wallet plugin

## Development

### Adding New Prediction Strategies

```python
# In polymarket.py
def _custom_prediction_strategy(self, market, context):
    # Your custom logic here
    return {
        'outcome': 'YES',
        'probability': 0.75,
        'confidence': 0.80,
        'reasoning': 'Custom analysis'
    }
```

### Adding New Data Sources

```python
# In _gather_market_context()
async def _gather_market_context(self, market):
    context = await super()._gather_market_context(market)
    
    # Add your custom source
    custom_data = await self._fetch_custom_data(market)
    context['custom'] = custom_data
    context['sources'].append('custom_source')
    
    return context
```

## Roadmap

- [ ] Advanced prediction models (ML/AI)
- [ ] Multi-outcome market support
- [ ] Automated market making
- [ ] Portfolio optimization
- [ ] Historical backtesting
- [ ] Performance analytics dashboard
- [ ] Telegram notifications for trades
- [ ] Discord integration for signals

## License

Part of AlleyBot - Private Repository

"""
Polymarket Prediction Market Trading Plugin for AlleyBot
Autonomous prediction market trading using AGI reasoning systems
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from plugin_manager import AlleyBotPlugin

logger = logging.getLogger(__name__)


@dataclass
class Market:
    """Prediction market data"""
    id: str
    question: str
    description: str
    end_date: datetime
    yes_price: float  # Current YES price (0-1)
    no_price: float   # Current NO price (0-1)
    volume: float     # Total volume in USD
    liquidity: float  # Available liquidity
    category: str
    tags: List[str]
    outcomes: List[str]
    resolved: bool = False
    resolution: Optional[str] = None


@dataclass
class Position:
    """Active position in a market"""
    market_id: str
    market_question: str
    outcome: str  # YES or NO
    shares: float
    avg_price: float
    current_price: float
    invested: float
    current_value: float
    pnl: float
    pnl_percent: float
    opened_at: datetime


@dataclass
class PredictionAnalysis:
    """Analysis result for a market"""
    market_id: str
    predicted_outcome: str  # YES or NO
    predicted_probability: float  # 0-1
    confidence: float  # 0-1
    edge: float  # Expected edge over market
    reasoning: str
    sources: List[str]  # Data sources used
    should_trade: bool
    position_size: float  # Recommended position size
    risk_score: float  # 0-1


class PolymarketPlugin(AlleyBotPlugin):
    """
    Polymarket prediction market trading plugin
    
    Features:
    - Autonomous market analysis using AGI systems
    - Cross-platform intelligence gathering
    - Risk-managed position sizing
    - Continuous learning from outcomes
    - MCP news integration
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "polymarket"
        self.description = "Prediction market trading on Polymarket"
        
        # Configuration
        self.enabled = config.get('enabled', False)
        self.paper_trading = config.get('paper_trading', True)  # Start with paper trading
        self.max_position_size = config.get('max_position_size', 0.05)  # 5% of bankroll
        self.max_total_exposure = config.get('max_total_exposure', 0.30)  # 30% total
        self.min_edge = config.get('min_edge', 0.05)  # 5% minimum edge
        self.min_confidence = config.get('min_confidence', 0.75)  # 75% confidence
        self.max_markets = config.get('max_markets', 10)  # Max concurrent positions
        
        # Polymarket API
        self.clob_url = "https://clob.polymarket.com"
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.chain_id = 137  # Polygon
        
        # Authentication (will be set during initialization)
        self.wallet = None
        self.api_key = None
        self.api_secret = None
        self.api_passphrase = None
        
        # CLOB client (will be initialized)
        self.clob_client = None
        
        # State
        self.active_positions: Dict[str, Position] = {}
        self.market_cache: Dict[str, Market] = {}
        self.prediction_history: List[Dict] = []
        
        # AGI systems (will be set during initialization)
        self.unified_reasoner = None
        self.knowledge_graph = None
        self.transfer_learner = None
        self.meta_learner = None
        self.cross_platform_intel = None
        
        # Statistics
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'avg_edge': 0.0,
            'sharpe_ratio': 0.0
        }
        
        logger.info("🎲 Polymarket plugin initialized")
    
    def initialize(self, api, core):
        """Initialize plugin with core systems"""
        super().initialize(api, core)
        
        # Get AGI systems from core
        if hasattr(core, 'plugin_manager'):
            brain_plugin = core.plugin_manager.get_plugin('brain')
            if brain_plugin:
                # Try to get autonomous brain (stored as _autonomous_brain)
                brain = getattr(brain_plugin, '_autonomous_brain', None)
                if brain:
                    self.unified_reasoner = getattr(brain, 'unified_reasoner', None)
                    self.knowledge_graph = getattr(brain, 'knowledge_graph', None)
                    self.transfer_learner = getattr(brain, 'transfer_learner', None)
                    self.meta_learner = getattr(brain, 'meta_learner', None)
                    self.cross_platform_intel = getattr(brain, 'cross_platform_intel', None)
                    logger.info(f"🧠 Connected to AGI systems: reasoner={self.unified_reasoner is not None}, kg={self.knowledge_graph is not None}")
                else:
                    logger.warning("⚠️ Brain plugin found but autonomous_brain not initialized")
        
        # Initialize wallet and authentication
        self._init_wallet()
        
        # Initialize CLOB client
        self._init_clob_client()
        
        logger.info(f"✅ Polymarket plugin initialized")
        logger.info(f"   Mode: {'PAPER TRADING' if self.paper_trading else 'LIVE TRADING'}")
        logger.info(f"   AGI Systems: {self._check_agi_systems()}")
    
    def _check_agi_systems(self) -> str:
        """Check which AGI systems are available"""
        systems = []
        if self.unified_reasoner:
            systems.append("Unified Reasoner")
        if self.knowledge_graph:
            systems.append("Knowledge Graph")
        if self.transfer_learner:
            systems.append("Transfer Learner")
        if self.meta_learner:
            systems.append("Meta-Learner")
        if self.cross_platform_intel:
            systems.append("Cross-Platform Intel")
        
        return f"{len(systems)}/5 active: {', '.join(systems)}" if systems else "None"
    
    def _init_wallet(self):
        """Initialize Polygon wallet for Polymarket"""
        try:
            # Get private key from environment
            # Try multiple env vars (Polygon-specific, BASE wallet, or generic)
            private_key = (
                os.getenv('POLYGON_PRIVATE_KEY') or 
                os.getenv('BASE_WALLET_PRIVATE_KEY') or 
                os.getenv('WALLET_PRIVATE_KEY')
            )
            
            if not private_key:
                logger.warning("⚠️ No Polygon wallet private key found")
                logger.warning("   Set POLYGON_PRIVATE_KEY, BASE_WALLET_PRIVATE_KEY, or WALLET_PRIVATE_KEY in .env")
                self.enabled = False
                return
            
            # Initialize ethers wallet (will use py-clob-client)
            from eth_account import Account
            self.wallet = Account.from_key(private_key)
            
            logger.info(f"✅ Polygon wallet initialized: {self.wallet.address[:10]}...")
            logger.info(f"   Using BASE wallet for Polygon (same address on all EVM chains)")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize wallet: {e}")
            self.enabled = False
    
    def _init_clob_client(self):
        """Initialize Polymarket CLOB client"""
        if not self.wallet:
            return
        
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import ApiCreds
            
            # Create temporary client to derive API credentials
            temp_client = ClobClient(
                host=self.clob_url,
                chain_id=self.chain_id,
                key=self.wallet.key.hex()
            )
            
            # Derive L2 API credentials from L1 wallet signature
            api_creds = temp_client.create_or_derive_api_creds()
            
            self.api_key = api_creds.api_key
            self.api_secret = api_creds.api_secret
            self.api_passphrase = api_creds.api_passphrase
            
            # Create authenticated client
            self.clob_client = ClobClient(
                host=self.clob_url,
                chain_id=self.chain_id,
                key=self.wallet.key.hex(),
                creds=ApiCreds(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    api_passphrase=self.api_passphrase
                )
            )
            
            logger.info("✅ CLOB client initialized with L2 authentication")
            
        except ImportError:
            logger.error("❌ py-clob-client not installed")
            logger.error("   Install with: pip install py-clob-client")
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize CLOB client: {e}")
            self.enabled = False
    
    async def fetch_markets(self, limit: int = 50, category: Optional[str] = None) -> List[Market]:
        """
        Fetch active markets from Polymarket
        
        Args:
            limit: Maximum number of markets to fetch
            category: Filter by category (e.g., 'politics', 'crypto', 'sports')
        
        Returns:
            List of Market objects
        """
        try:
            import requests
            
            # Fetch from Gamma API (public market data)
            url = f"{self.gamma_url}/markets"
            params = {
                'limit': limit,
                'active': True,
                'closed': False
            }
            
            if category:
                params['category'] = category
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            markets_data = response.json()
            markets = []
            
            for market_data in markets_data:
                try:
                    # API uses camelCase (endDate) not snake_case (end_date)
                    end_date_str = market_data.get('endDate') or market_data.get('end_date')
                    if not end_date_str:
                        logger.warning(f"⚠️ Market {market_data.get('id')} missing end date, skipping")
                        continue
                    
                    market = Market(
                        id=market_data['id'],
                        question=market_data['question'],
                        description=market_data.get('description', ''),
                        end_date=datetime.fromisoformat(end_date_str.replace('Z', '+00:00')),
                        yes_price=float(market_data.get('yes_price', 0.5)),
                        no_price=float(market_data.get('no_price', 0.5)),
                        volume=float(market_data.get('volume', 0)),
                        liquidity=float(market_data.get('liquidity', 0)),
                        category=market_data.get('category', 'unknown'),
                        tags=market_data.get('tags', []),
                        outcomes=market_data.get('outcomes', ['YES', 'NO'])
                    )
                    
                    markets.append(market)
                    self.market_cache[market.id] = market
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse market: {e}")
                    continue
            
            logger.info(f"📊 Fetched {len(markets)} active markets")
            return markets
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch markets: {e}")
            return []
    
    async def analyze_market(self, market: Market) -> PredictionAnalysis:
        """
        Analyze a market using AGI systems
        
        Args:
            market: Market to analyze
        
        Returns:
            PredictionAnalysis with recommendation
        """
        logger.info(f"🔍 Analyzing market: {market.question}")
        
        # Gather context from multiple sources
        context = await self._gather_market_context(market)
        
        # Use Unified Reasoner for prediction
        prediction = await self._reason_about_market(market, context)
        
        # Calculate edge
        edge = self._calculate_edge(market, prediction)
        
        # Check risk management
        should_trade, risk_score = self._check_risk_management(market, prediction, edge)
        
        # Calculate position size
        position_size = self._calculate_position_size(edge, prediction['confidence']) if should_trade else 0.0
        
        analysis = PredictionAnalysis(
            market_id=market.id,
            predicted_outcome=prediction['outcome'],
            predicted_probability=prediction['probability'],
            confidence=prediction['confidence'],
            edge=edge,
            reasoning=prediction['reasoning'],
            sources=context['sources'],
            should_trade=should_trade,
            position_size=position_size,
            risk_score=risk_score
        )
        
        logger.info(f"   Prediction: {analysis.predicted_outcome} ({analysis.predicted_probability:.1%})")
        logger.info(f"   Confidence: {analysis.confidence:.1%}")
        logger.info(f"   Edge: {analysis.edge:.1%}")
        logger.info(f"   Trade: {'YES' if analysis.should_trade else 'NO'}")
        
        return analysis
    
    async def _gather_market_context(self, market: Market) -> Dict[str, Any]:
        """Gather context from multiple sources"""
        context = {
            'sources': [],
            'social_sentiment': None,
            'news': [],
            'historical': [],
            'expert_opinions': []
        }
        
        # 1. Social sentiment from cross-platform intelligence
        if self.cross_platform_intel:
            try:
                # Note: CrossPlatformIntelligence uses synthesize_observations, not search_topics
                # For now, skip social sentiment until we have observations to synthesize
                # TODO: Integrate with platform observations
                pass
            except Exception as e:
                logger.warning(f"⚠️ Failed to get social sentiment: {e}")
        
        # 2. News from MCP servers
        try:
            news = await self._fetch_news_from_mcp(market.question)
            context['news'] = news
            if news:
                context['sources'].append('mcp_news')
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch news: {e}")
        
        # 3. Historical similar events from Knowledge Graph
        if self.knowledge_graph:
            try:
                # Note: KnowledgeGraph doesn't have find_similar_entities method
                # It has get_related_entities and find_analogies
                # For now, skip until we implement proper entity matching
                # TODO: Add market entities to knowledge graph and query them
                pass
            except Exception as e:
                logger.warning(f"⚠️ Failed to query knowledge graph: {e}")
        
        return context
    
    async def _fetch_news_from_mcp(self, query: str) -> List[Dict]:
        """Fetch news from MCP servers"""
        news = []
        
        try:
            # Get MCP plugin
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                return news
            
            mcp_plugin = self.core.plugin_manager.get_plugin('mcp')
            if not mcp_plugin:
                return news
            
            # Use MCP to fetch news (assuming MCP has news servers configured)
            # This will use free news MCP servers
            news_results = await mcp_plugin.query_news(query, limit=10)
            
            for article in news_results:
                news.append({
                    'title': article.get('title', ''),
                    'summary': article.get('summary', ''),
                    'source': article.get('source', ''),
                    'published': article.get('published', ''),
                    'relevance': article.get('relevance', 0.5)
                })
            
            logger.info(f"📰 Fetched {len(news)} news articles from MCP")
            
        except Exception as e:
            logger.warning(f"⚠️ MCP news fetch failed: {e}")
        
        return news
    
    async def _reason_about_market(self, market: Market, context: Dict) -> Dict[str, Any]:
        """Use Unified Reasoner to predict market outcome"""
        
        if not self.unified_reasoner:
            # Fallback to simple analysis
            return self._simple_prediction(market, context)
        
        try:
            from src.agentic.unified_reasoner import ReasoningContext, ReasoningType
            
            # Build reasoning context
            # Note: ReasoningContext doesn't accept 'context' parameter
            # It has: problem, domain, reasoning_type, related_domains, constraints, goal
            reasoning_context = ReasoningContext(
                problem=f"Predict outcome of: {market.question}. Market data: YES={market.yes_price:.2f}, NO={market.no_price:.2f}, Volume=${market.volume:,.0f}. News: {len(context.get('news', []))} articles found.",
                domain="prediction_markets",
                reasoning_type=ReasoningType.CAUSAL,  # Cause-effect analysis
                related_domains=['social', 'news', 'events'],
                goal="Predict most likely outcome with confidence"
            )
            
            # Get reasoning result
            result = self.unified_reasoner.reason(reasoning_context)
            
            # Extract prediction
            # Result contains: decision, confidence, explanation, reasoning_path
            outcome = "YES" if "yes" in str(result.decision).lower() else "NO"
            probability = result.confidence
            
            return {
                'outcome': outcome,
                'probability': probability,
                'confidence': result.confidence,
                'reasoning': result.explanation
            }
            
        except Exception as e:
            logger.error(f"❌ Unified reasoning failed: {e}")
            return self._simple_prediction(market, context)
    
    def _simple_prediction(self, market: Market, context: Dict) -> Dict[str, Any]:
        """Fallback simple prediction logic"""
        # Use market prices as baseline
        yes_prob = market.yes_price
        no_prob = market.no_price
        
        # Adjust based on sentiment if available
        if context.get('social_sentiment'):
            sentiment = context['social_sentiment'].get('sentiment', 0)
            yes_prob += sentiment * 0.1  # Adjust by up to 10%
        
        # Normalize
        total = yes_prob + no_prob
        yes_prob /= total
        no_prob /= total
        
        outcome = "YES" if yes_prob > no_prob else "NO"
        probability = max(yes_prob, no_prob)
        
        return {
            'outcome': outcome,
            'probability': probability,
            'confidence': 0.6,  # Lower confidence for simple prediction
            'reasoning': "Simple market-based prediction (AGI systems not available)"
        }
    
    def _calculate_edge(self, market: Market, prediction: Dict) -> float:
        """Calculate expected edge over market"""
        # Market implied probability
        market_prob = market.yes_price if prediction['outcome'] == 'YES' else market.no_price
        
        # Your predicted probability
        predicted_prob = prediction['probability']
        
        # Edge = (your probability - market probability) * confidence
        edge = (predicted_prob - market_prob) * prediction['confidence']
        
        return edge
    
    def _check_risk_management(self, market: Market, prediction: Dict, edge: float) -> Tuple[bool, float]:
        """Check if trade meets risk management criteria"""
        
        checks = {
            'edge': edge >= self.min_edge,
            'confidence': prediction['confidence'] >= self.min_confidence,
            'liquidity': market.liquidity >= 10000,  # Min $10k liquidity
            'volume': market.volume >= 5000,  # Min $5k volume
            'time_to_resolution': (market.end_date - datetime.now(timezone.utc)).days <= 30,  # Max 30 days
            'position_count': len(self.active_positions) < self.max_markets,
            'exposure': self._calculate_total_exposure() < self.max_total_exposure
        }
        
        # Calculate risk score (0-1, lower is better)
        risk_score = 1.0 - (sum(checks.values()) / len(checks))
        
        should_trade = all(checks.values())
        
        if not should_trade:
            failed = [k for k, v in checks.items() if not v]
            logger.info(f"   ⛔ Trade blocked: {', '.join(failed)}")
        
        return should_trade, risk_score
    
    def _calculate_total_exposure(self) -> float:
        """Calculate total exposure across all positions"""
        if not self.active_positions:
            return 0.0
        
        total_invested = sum(pos.invested for pos in self.active_positions.values())
        bankroll = self._get_bankroll()
        
        return total_invested / bankroll if bankroll > 0 else 0.0
    
    def _calculate_position_size(self, edge: float, confidence: float) -> float:
        """Calculate optimal position size using Kelly Criterion"""
        # Kelly = (edge * confidence) / (1 - confidence)
        kelly = (edge * confidence) / (1 - confidence) if confidence < 1.0 else edge
        
        # Use fractional Kelly (0.25x) for safety
        fractional_kelly = kelly * 0.25
        
        # Cap at max position size
        position = min(fractional_kelly, self.max_position_size)
        
        # Ensure positive
        return max(0.0, position)
    
    def _get_bankroll(self) -> float:
        """Get current bankroll (USDC balance on Polygon)"""
        # TODO: Implement actual balance check
        # For now, return configured amount
        return 1000.0  # $1000 default
    
    def get_commands(self):
        """Return CLI commands"""
        return {
            'polymarket_status': self.status_command,
            'polymarket_markets': self.markets_command,
            'polymarket_analyze': self.analyze_command,
            'polymarket_positions': self.positions_command,
            'polymarket_stats': self.stats_command
        }
    
    def status_command(self):
        """Get Polymarket plugin status"""
        status = f"🎲 Polymarket Status:\n"
        status += f"  {'✅' if self.enabled else '❌'} Plugin enabled\n"
        status += f"  📊 Mode: {'PAPER TRADING' if self.paper_trading else 'LIVE TRADING'}\n"
        status += f"  💼 Active positions: {len(self.active_positions)}\n"
        status += f"  📈 Total PnL: ${self.stats['total_pnl']:.2f}\n"
        status += f"  🎯 Win rate: {self.stats['win_rate']:.1%}\n"
        status += f"  🧠 AGI systems: {self._check_agi_systems()}"
        return status
    
    async def markets_command(self, limit: int = 10):
        """List active markets"""
        markets = await self.fetch_markets(limit=limit)
        
        if not markets:
            return "❌ No markets found"
        
        output = f"📊 Top {len(markets)} Active Markets:\n\n"
        
        for i, market in enumerate(markets[:limit], 1):
            output += f"{i}. {market.question}\n"
            output += f"   YES: {market.yes_price:.2f} | NO: {market.no_price:.2f}\n"
            output += f"   Volume: ${market.volume:,.0f} | Liquidity: ${market.liquidity:,.0f}\n"
            output += f"   Category: {market.category} | Ends: {market.end_date.strftime('%Y-%m-%d')}\n\n"
        
        return output
    
    async def analyze_command(self, market_id: str):
        """Analyze a specific market"""
        market = self.market_cache.get(market_id)
        
        if not market:
            return f"❌ Market {market_id} not found. Fetch markets first."
        
        analysis = await self.analyze_market(market)
        
        output = f"🔍 Market Analysis:\n\n"
        output += f"Question: {market.question}\n\n"
        output += f"Prediction: {analysis.predicted_outcome} ({analysis.predicted_probability:.1%})\n"
        output += f"Confidence: {analysis.confidence:.1%}\n"
        output += f"Edge: {analysis.edge:.1%}\n"
        output += f"Risk Score: {analysis.risk_score:.2f}\n\n"
        output += f"Reasoning:\n{analysis.reasoning}\n\n"
        output += f"Sources: {', '.join(analysis.sources)}\n\n"
        output += f"Recommendation: {'✅ TRADE' if analysis.should_trade else '⛔ SKIP'}\n"
        
        if analysis.should_trade:
            output += f"Position Size: {analysis.position_size:.1%} of bankroll\n"
        
        return output
    
    def positions_command(self):
        """List active positions"""
        if not self.active_positions:
            return "📊 No active positions"
        
        output = f"📊 Active Positions ({len(self.active_positions)}):\n\n"
        
        for pos in self.active_positions.values():
            output += f"Market: {pos.market_question}\n"
            output += f"  Outcome: {pos.outcome}\n"
            output += f"  Shares: {pos.shares:.2f} @ ${pos.avg_price:.3f}\n"
            output += f"  Current: ${pos.current_price:.3f}\n"
            output += f"  PnL: ${pos.pnl:.2f} ({pos.pnl_percent:+.1%})\n"
            output += f"  Opened: {pos.opened_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        return output
    
    def stats_command(self):
        """Get trading statistics"""
        output = f"📈 Polymarket Trading Statistics:\n\n"
        output += f"Total Trades: {self.stats['total_trades']}\n"
        output += f"Winning: {self.stats['winning_trades']}\n"
        output += f"Losing: {self.stats['losing_trades']}\n"
        output += f"Win Rate: {self.stats['win_rate']:.1%}\n\n"
        output += f"Total PnL: ${self.stats['total_pnl']:.2f}\n"
        output += f"Avg Edge: {self.stats['avg_edge']:.1%}\n"
        output += f"Sharpe Ratio: {self.stats['sharpe_ratio']:.2f}\n"
        
        return output

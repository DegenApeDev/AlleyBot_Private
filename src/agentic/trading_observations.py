"""
Trading Observations Module for AlleyBot AGI Brain

Gathers trading-related observations from Solana and Base trading plugins
so the AGI can watch market conditions and learn patterns before executing trades.

This is OBSERVATION ONLY - no trade execution happens here.
The brain will learn:
- Token price movements
- Portfolio balances
- Gas prices
- Profitable vs unprofitable opportunities
- Market conditions
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def gather_trading_observations(plugin_manager) -> List[Any]:
    """
    Gather trading observations from Solana and Base trading plugins.
    
    Returns list of SyModObservation objects for AGI brain to analyze.
    This allows the brain to watch and learn before we enable autonomous execution.
    
    Args:
        plugin_manager: Plugin manager instance
        
    Returns:
        List of SyModObservation objects with trading data
    """
    from src.agentic.symod_core import SyModObservation
    
    observations = []
    
    # === SOLANA TRADING OBSERVATIONS ===
    solana_trading = plugin_manager.get_plugin('solana_trading')
    if solana_trading and hasattr(solana_trading, 'enabled') and solana_trading.enabled:
        try:
            # Get wallet balances for key tokens
            key_tokens = ['SOL', 'USDC', 'BONK', 'WIF']
            balances = {}
            
            for token in key_tokens:
                if hasattr(solana_trading, 'get_token_balance'):
                    # Note: Solana plugin might not have get_token_balance yet
                    # We'll use get_price to check market data instead
                    pass
            
            # Get price quotes for popular pairs (observation only)
            price_observations = []
            popular_pairs = [
                ('SOL', 'USDC'),
                ('BONK', 'USDC'),
                ('WIF', 'USDC'),
            ]
            
            for from_token, to_token in popular_pairs:
                if hasattr(solana_trading, 'get_price'):
                    try:
                        price_data = solana_trading.get_price(from_token, to_token, amount=1.0)
                        if price_data.get('success'):
                            obs = SyModObservation(
                                observation_type='solana_price',
                                source_plugin='solana_trading',
                                data={
                                    'pair': f"{from_token}/{to_token}",
                                    'from_token': from_token,
                                    'to_token': to_token,
                                    'price': price_data.get('price'),
                                    'quote_data': price_data.get('quote'),
                                    'timestamp': datetime.now().replace(tzinfo=None).isoformat(),
                                    'chain': 'solana',
                                    'observation_only': True  # Not for execution
                                }
                            )
                            price_observations.append(obs)
                    except Exception as e:
                        logger.debug(f"Could not get Solana price for {from_token}/{to_token}: {e}")
            
            if price_observations:
                observations.extend(price_observations)
                logger.info(f"📊 Gathered {len(price_observations)} Solana price observations")
            
            # Check for profitable opportunities (observation only)
            if hasattr(solana_trading, 'get_quote') and hasattr(solana_trading, 'calculate_profit'):
                try:
                    # Example: Check if SOL->USDC->SOL arbitrage exists
                    # This is OBSERVATION - brain learns what "profitable" looks like
                    test_amount = 1.0  # 1 SOL
                    sol_mint = solana_trading.tokens.get('SOL')
                    usdc_mint = solana_trading.tokens.get('USDC')
                    
                    if sol_mint and usdc_mint:
                        # Get quote for SOL -> USDC
                        amount_lamports = int(test_amount * (10 ** solana_trading.decimals.get('SOL', 9)))
                        quote = solana_trading.get_quote(sol_mint, usdc_mint, amount_lamports)
                        
                        if quote.get('success'):
                            profit_analysis = solana_trading.calculate_profit(
                                quote, 'SOL', 'USDC', test_amount
                            )
                            
                            if profit_analysis.get('success'):
                                obs = SyModObservation(
                                    observation_type='solana_opportunity',
                                    source_plugin='solana_trading',
                                    data={
                                        'pair': 'SOL/USDC',
                                        'is_profitable': profit_analysis.get('is_profitable'),
                                        'price_impact': profit_analysis.get('price_impact_percent'),
                                        'total_cost': profit_analysis.get('total_cost_percent'),
                                        'input_amount': profit_analysis.get('input_amount'),
                                        'output_amount': profit_analysis.get('output_amount'),
                                        'warnings': profit_analysis.get('warnings', []),
                                        'timestamp': datetime.now().replace(tzinfo=None).isoformat(),
                                        'observation_only': True,
                                        'execution_enabled': False  # Brain cannot execute yet
                                    }
                                )
                                observations.append(obs)
                                logger.info(f"💡 Solana opportunity observed: {'✅ Profitable' if profit_analysis.get('is_profitable') else '❌ Not profitable'}")
                except Exception as e:
                    logger.debug(f"Could not check Solana opportunities: {e}")
        
        except Exception as e:
            logger.error(f"❌ Failed to gather Solana trading observations: {e}")
    
    # === BASE TRADING OBSERVATIONS ===
    base_trading = plugin_manager.get_plugin('base_trading')
    if base_trading and hasattr(base_trading, 'enabled') and base_trading.enabled:
        try:
            # Get token balances
            key_tokens = ['ETH', 'USDC', 'DEGEN']
            balance_observations = []
            
            for token in key_tokens:
                if hasattr(base_trading, 'get_token_balance'):
                    try:
                        balance_data = base_trading.get_token_balance(token)
                        if balance_data.get('success'):
                            obs = SyModObservation(
                                observation_type='base_balance',
                                source_plugin='base_trading',
                                data={
                                    'token': token,
                                    'balance': balance_data.get('balance'),
                                    'formatted': balance_data.get('formatted'),
                                    'timestamp': datetime.now().replace(tzinfo=None).isoformat(),
                                    'chain': 'base',
                                    'observation_only': True
                                }
                            )
                            balance_observations.append(obs)
                    except Exception as e:
                        logger.debug(f"Could not get Base balance for {token}: {e}")
            
            if balance_observations:
                observations.extend(balance_observations)
                logger.info(f"💰 Gathered {len(balance_observations)} Base balance observations")
            
            # Check gas prices (critical for Base profitability)
            if hasattr(base_trading, 'check_gas_price'):
                try:
                    gas_data = base_trading.check_gas_price()
                    if gas_data.get('success'):
                        obs = SyModObservation(
                            observation_type='base_gas_price',
                            source_plugin='base_trading',
                            data={
                                'gas_gwei': gas_data.get('current_gas_gwei'),
                                'is_acceptable': gas_data.get('is_acceptable'),
                                'max_gas_gwei': gas_data.get('max_gas_gwei'),
                                'recommendation': gas_data.get('recommendation'),
                                'timestamp': datetime.now().isoformat(),
                                'chain': 'base',
                                'observation_only': True
                            }
                        )
                        observations.append(obs)
                        logger.info(f"⛽ Base gas: {gas_data.get('current_gas_gwei'):.1f} gwei ({'✅ OK' if gas_data.get('is_acceptable') else '⚠️ HIGH'})")
                except Exception as e:
                    logger.debug(f"Could not check Base gas price: {e}")
            
            # Get price quotes for popular pairs
            price_observations = []
            popular_pairs = [
                ('ETH', 'USDC'),
                ('DEGEN', 'USDC'),
            ]
            
            for from_token, to_token in popular_pairs:
                if hasattr(base_trading, 'get_price'):
                    try:
                        price_data = base_trading.get_price(from_token, to_token)
                        if price_data.get('success'):
                            obs = SyModObservation(
                                observation_type='base_price',
                                source_plugin='base_trading',
                                data={
                                    'pair': f"{from_token}/{to_token}",
                                    'from_token': from_token,
                                    'to_token': to_token,
                                    'price': price_data.get('price'),
                                    'timestamp': datetime.now().replace(tzinfo=None).isoformat(),
                                    'chain': 'base',
                                    'observation_only': True
                                }
                            )
                            price_observations.append(obs)
                    except Exception as e:
                        logger.debug(f"Could not get Base price for {from_token}/{to_token}: {e}")
            
            if price_observations:
                observations.extend(price_observations)
                logger.info(f"📊 Gathered {len(price_observations)} Base price observations")
            
            # Check for profitable opportunities (observation only)
            if hasattr(base_trading, 'calculate_profit'):
                try:
                    # Example: Check ETH -> USDC profitability
                    test_amount = 0.1  # 0.1 ETH
                    estimated_output = 300.0  # Placeholder - should get real quote
                    
                    profit_analysis = base_trading.calculate_profit(
                        test_amount, estimated_output, 'ETH', 'USDC', gas_cost_usd=2.0
                    )
                    
                    if profit_analysis.get('success'):
                        obs = SyModObservation(
                            observation_type='base_opportunity',
                            source_plugin='base_trading',
                            data={
                                'pair': 'ETH/USDC',
                                'is_profitable': profit_analysis.get('is_profitable'),
                                'price_impact': profit_analysis.get('price_impact_percent'),
                                'total_cost': profit_analysis.get('total_cost_percent'),
                                'gas_cost_usd': profit_analysis.get('gas_cost_usd'),
                                'warnings': profit_analysis.get('warnings', []),
                                'timestamp': datetime.now().isoformat(),
                                'observation_only': True,
                                'execution_enabled': False
                            }
                        )
                        observations.append(obs)
                        logger.info(f"💡 Base opportunity observed: {'✅ Profitable' if profit_analysis.get('is_profitable') else '❌ Not profitable'}")
                except Exception as e:
                    logger.debug(f"Could not check Base opportunities: {e}")
        
        except Exception as e:
            logger.error(f"❌ Failed to gather Base trading observations: {e}")
    
    # Summary log
    if observations:
        logger.info(f"📈 Total trading observations gathered: {len(observations)}")
        logger.info("🧠 AGI brain can now watch and learn from market data")
    else:
        logger.debug("No trading observations gathered (plugins may not be enabled)")
    
    return observations

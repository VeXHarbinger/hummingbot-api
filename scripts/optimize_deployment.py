"""
Optimized liquidity deployment - maximizes initial deployment by:
1. Analyzing token balance ratio vs pool requirement
2. Calculating optimal swap if needed
3. Opening position with maximum liquidity in one transaction

This avoids the multi-step process of open → add → add → add
"""
import asyncio
import aiohttp
from aiohttp import BasicAuth
from math import sqrt

API_URL = "http://localhost:8000"
AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")

POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
CONNECTOR = "pancakeswap"
NETWORK = "ethereum-bsc"
TARGET_RANGE_WIDTH = 2.5  # 2.5% range


def calculate_optimal_ratio(current_price, range_width_pct):
    """
    Calculate the optimal token ratio for a given price range.
    
    For Uniswap V3 math:
    When price is in range [P_lower, P_upper], the ratio is:
    amount1/amount0 = (sqrt(P) - sqrt(P_lower)) / ((sqrt(P_upper) - sqrt(P)) / (sqrt(P_upper) * sqrt(P)))
    
    Simplified: USDT_per_COAI = (sqrt(P) - sqrt(P_lower)) * sqrt(P_upper) * sqrt(P) / (sqrt(P_upper) - sqrt(P))
    """
    half_range = range_width_pct / 2.0
    p_lower = current_price * (1 - half_range / 100)
    p_upper = current_price * (1 + half_range / 100)
    
    sqrt_p = sqrt(current_price)
    sqrt_lower = sqrt(p_lower)
    sqrt_upper = sqrt(p_upper)
    
    # Calculate ratio: USDT per COAI when in range
    # amount1 / amount0 where amount1 is quote (USDT), amount0 is base (COAI)
    numerator = (sqrt_p - sqrt_lower) * sqrt_upper * sqrt_p
    denominator = sqrt_upper - sqrt_p
    ratio = numerator / denominator
    
    return ratio


async def get_pool_price():
    """Get current pool price"""
    url = f"{API_URL}/gateway/clmm/pool-info"
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "pool_address": POOL_ADDRESS
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as resp:
            if resp.status == 200:
                data = await resp.json()
                return float(data.get("price", 0))
    return None


async def quote_position(current_price, token_amount, is_coai=True):
    """Quote position to verify our math"""
    half_range = TARGET_RANGE_WIDTH / 2.0
    lower_price = current_price * (1 - half_range / 100)
    upper_price = current_price * (1 + half_range / 100)
    
    url = f"{API_URL}/gateway/clmm/quote"
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "pool_address": POOL_ADDRESS,
        "lower_price": lower_price,
        "upper_price": upper_price,
    }
    
    if is_coai:
        payload["base_token_amount"] = token_amount
    else:
        payload["quote_token_amount"] = token_amount
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as resp:
            if resp.status == 200:
                return await resp.json()
    return None


def calculate_optimal_deployment(coai_balance, usdt_balance, current_price, pool_ratio):
    """
    Calculate optimal deployment strategy:
    1. If ratio matches: deploy all
    2. If too much COAI: swap some for USDT first
    3. If too much USDT: swap some for COAI first
    
    Returns: (coai_to_deploy, usdt_to_deploy, coai_to_swap, swap_direction)
    """
    current_ratio = usdt_balance / coai_balance if coai_balance > 0 else 0
    
    print(f"\n📊 Ratio Analysis:")
    print(f"   Current ratio: {current_ratio:.4f} USDT per COAI")
    print(f"   Pool needs: {pool_ratio:.4f} USDT per COAI")
    print(f"   Match: {abs(current_ratio - pool_ratio) / pool_ratio * 100:.1f}% difference")
    
    # If we're within 5% of target ratio, just deploy directly
    if abs(current_ratio - pool_ratio) / pool_ratio < 0.05:
        print(f"   ✅ Ratio close enough - deploy directly")
        # Use the limiting factor
        max_from_coai = coai_balance
        max_from_usdt = usdt_balance / pool_ratio
        
        if max_from_coai < max_from_usdt:
            # COAI is limiting
            return coai_balance * 0.98, coai_balance * 0.98 * pool_ratio, 0, None
        else:
            # USDT is limiting
            return usdt_balance / pool_ratio * 0.98, usdt_balance * 0.98, 0, None
    
    # Need to swap
    if current_ratio < pool_ratio:
        # Too much COAI, need more USDT
        # After swap: (usdt + x * price) / (coai - x) = pool_ratio
        # Solving for x: x = (pool_ratio * coai - usdt) / (price + pool_ratio)
        coai_to_swap = (pool_ratio * coai_balance - usdt_balance) / (current_price + pool_ratio)
        
        # After swap
        coai_after = coai_balance - coai_to_swap
        usdt_after = usdt_balance + coai_to_swap * current_price * 0.99  # 1% slippage
        
        print(f"   ⚠️  Too much COAI - need to swap")
        print(f"   Swap: {coai_to_swap:.2f} COAI → {coai_to_swap * current_price * 0.99:.2f} USDT")
        print(f"   After: {coai_after:.2f} COAI, {usdt_after:.2f} USDT")
        
        return coai_after * 0.98, usdt_after * 0.98, coai_to_swap, "COAI→USDT"
    else:
        # Too much USDT, need more COAI
        usdt_to_swap = (usdt_balance - pool_ratio * coai_balance) / (1 + pool_ratio / current_price)
        
        coai_after = coai_balance + usdt_to_swap / current_price * 0.99
        usdt_after = usdt_balance - usdt_to_swap
        
        print(f"   ⚠️  Too much USDT - need to swap")
        print(f"   Swap: {usdt_to_swap:.2f} USDT → {usdt_to_swap / current_price * 0.99:.2f} COAI")
        print(f"   After: {coai_after:.2f} COAI, {usdt_after:.2f} USDT")
        
        return coai_after * 0.98, usdt_after * 0.98, usdt_to_swap, "USDT→COAI"


async def main():
    print("\n🎯 OPTIMIZED LIQUIDITY DEPLOYMENT")
    print("="*60)
    
    # Get pool price
    print("\n📊 Getting pool info...")
    current_price = await get_pool_price()
    if not current_price:
        print("Failed to get pool price")
        return
    print(f"Current price: ${current_price}")
    
    # Calculate optimal ratio
    pool_ratio = calculate_optimal_ratio(current_price, TARGET_RANGE_WIDTH)
    
    # Get balances (you would get these from MCP)
    print("\n💰 Enter current balances:")
    coai = float(input("COAI balance: "))
    usdt = float(input("USDT balance: "))
    
    total_value_usd = coai * current_price + usdt
    print(f"\nTotal portfolio value: ${total_value_usd:.2f}")
    
    # Calculate optimal deployment
    coai_deploy, usdt_deploy, swap_amount, swap_dir = calculate_optimal_deployment(
        coai, usdt, current_price, pool_ratio
    )
    
    # Show deployment plan
    print(f"\n📋 Deployment Plan:")
    if swap_amount > 0:
        print(f"   1. Swap {swap_amount:.2f} {swap_dir}")
        print(f"   2. Deploy {coai_deploy:.2f} COAI + {usdt_deploy:.2f} USDT")
        print(f"   3. Total liquidity: ~${(coai_deploy * current_price + usdt_deploy):.2f}")
    else:
        print(f"   1. Deploy {coai_deploy:.2f} COAI + {usdt_deploy:.2f} USDT directly")
        print(f"   2. Total liquidity: ~${(coai_deploy * current_price + usdt_deploy):.2f}")
    
    # Verify with quote
    print(f"\n📊 Verifying with quote...")
    quote = await quote_position(current_price, usdt_deploy, is_coai=False)
    if quote:
        print(f"   Quote confirms:")
        print(f"   COAI: {float(quote['base_token_amount']):.2f}")
        print(f"   USDT: {float(quote['quote_token_amount']):.2f}")
        print(f"   Liquidity: {quote['liquidity']}")
    
    print("\n" + "="*60)
    print("✅ Analysis complete!")
    if swap_amount > 0:
        print(f"\n⚠️  Action needed: Swap {swap_amount:.2f} {swap_dir} first")
    else:
        print(f"\n✅ Ready to deploy directly!")


if __name__ == "__main__":
    asyncio.run(main())

"""
Calculate APR for COAI/USDT position using PancakeSwap's formula
Compare calculated APR vs displayed APR (956.77%)

Based on PancakeSwap's open-source calculation:
https://github.com/pancakeswap/pancake-frontend
"""
import sys
import io
# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import aiohttp
import asyncio
from decimal import Decimal
import math

# Your position details
POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
POSITION_ID = 6221178
POSITION_LOWER_PRICE = Decimal("0.429575506")  # $0.429575506
POSITION_UPPER_PRICE = Decimal("0.447105921")  # $0.447105921
CURRENT_PRICE = Decimal("0.431550")  # Current COAI price in USDT

# PancakeSwap V3 BSC Subgraph
SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/pancakeswap/exchange-v3-bsc"
PANCAKESWAP_INFO_API = "https://api-v3.pancakeswap.com/api/v3"

# Known APR from UI
POOL_BASE_APR = 877.03  # Pool's base LP Fee APR
DISPLAYED_APR = 956.77  # Your position's actual APR (higher due to concentrated range)


async def get_pool_stats_from_api():
    """Try to get pool stats from PancakeSwap's API"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{PANCAKESWAP_INFO_API}/pools/56/{POOL_ADDRESS}"  # 56 = BSC Chain ID
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"API returned status {response.status}")
                    return None
    except Exception as e:
        print(f"Error fetching from API: {e}")
        return None


async def get_pool_data_from_subgraph():
    """Get pool 24h fees and TVL from The Graph"""
    query = """
    {
      pool(id: "%s") {
        id
        token0 {
          symbol
          id
        }
        token1 {
          symbol
          id
        }
        feeTier
        liquidity
        sqrtPrice
        token0Price
        token1Price
        volumeUSD
        totalValueLockedUSD
        feesUSD
        txCount
      }
      poolDayDatas(
        first: 1
        orderBy: date
        orderDirection: desc
        where: { pool: "%s" }
      ) {
        date
        volumeUSD
        tvlUSD
        feesUSD
      }
    }
    """ % (POOL_ADDRESS.lower(), POOL_ADDRESS.lower())
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SUBGRAPH_URL,
                json={"query": query},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("data", {})
                else:
                    print(f"Subgraph error: {response.status}")
                    return None
    except Exception as e:
        print(f"Error querying subgraph: {e}")
        return None


def calculate_position_multiplier(
    lower_price: Decimal,
    upper_price: Decimal,
    current_price: Decimal,
    trading_range_min: Decimal = None,
    trading_range_max: Decimal = None
) -> Decimal:
    """
    Calculate position multiplier based on PancakeSwap's actual formula
    
    From PoolUtils.estimateAprsForPriceRangeMultiplier():
    
    const _minPrice = Math.max(priceLower, aprInfo.priceMin);
    const _maxPrice = Math.min(priceUpper, aprInfo.priceMax);
    const sub = _maxPrice - _minPrice;
    
    const userRange = priceUpper - priceLower;
    const tradeRange = aprInfo.priceMax - aprInfo.priceMin;
    
    let p: number;
    if (sub <= 0) p = 0;
    else if (userRange === sub) p = tradeRange / sub;
    else if (tradeRange === sub) p = sub / userRange;
    else p = (sub / tradeRange) * (sub / userRange);
    
    return {
      feeApr: aprInfo.feeApr * p,
      ...
    }
    
    Simplified: The multiplier depends on how much of the trading range
    your position covers, not just the size of your range.
    """
    if current_price < lower_price or current_price > upper_price:
        # Out of range = 0 APR
        return Decimal("0")
    
    # If we don't have trading range data, estimate from recent price action
    # Typically the trading range for 24h is much narrower than the full possible range
    if trading_range_min is None:
        # Estimate: 24h trading range is typically ±2-5% from current price
        trading_range_min = current_price * Decimal("0.98")  # -2%
        trading_range_max = current_price * Decimal("1.02")  # +2%
    
    # Calculate overlap between user range and trading range
    overlap_min = max(lower_price, trading_range_min)
    overlap_max = min(upper_price, trading_range_max)
    overlap = overlap_max - overlap_min
    
    if overlap <= 0:
        return Decimal("0")
    
    user_range = upper_price - lower_price
    trade_range = trading_range_max - trading_range_min
    
    # PancakeSwap's formula
    if user_range == overlap:
        # User range fully inside trading range
        multiplier = trade_range / overlap
    elif trade_range == overlap:
        # Trading range fully inside user range
        multiplier = overlap / user_range
    else:
        # Partial overlap
        multiplier = (overlap / trade_range) * (overlap / user_range)
    
    return multiplier


def calculate_apr_from_fees(
    fees_24h_usd: Decimal,
    tvl_usd: Decimal,
    position_multiplier: Decimal
) -> Decimal:
    """
    Calculate APR using PancakeSwap's formula
    
    APR = (fees_24h / TVL) * 365 * 100 * multiplier
    """
    if tvl_usd == 0:
        return Decimal("0")
    
    # Base pool APR (if you owned the entire pool)
    base_apr = (fees_24h_usd / tvl_usd) * 365 * 100
    
    # Position APR (adjusted for your range)
    position_apr = base_apr * position_multiplier
    
    return position_apr


async def main():
    print("=" * 80)
    print("COAI/USDT Position APR Calculator")
    print("=" * 80)
    print(f"\n📍 Position Details:")
    print(f"   Pool: {POOL_ADDRESS}")
    print(f"   Position ID: {POSITION_ID}")
    print(f"   Range: ${POSITION_LOWER_PRICE} - ${POSITION_UPPER_PRICE}")
    print(f"   Current Price: ${CURRENT_PRICE}")
    print(f"   Range Width: {((POSITION_UPPER_PRICE - POSITION_LOWER_PRICE) / CURRENT_PRICE * 100):.2f}%")
    print(f"\n🎯 Pool Base APR: {POOL_BASE_APR}%")
    print(f"🎯 Your Position APR: {DISPLAYED_APR}%")
    print(f"🎯 Your Multiplier: {DISPLAYED_APR / POOL_BASE_APR:.2f}x")
    print("\n" + "-" * 80)
    
    # Try PancakeSwap API first
    print("\n📊 Fetching pool data from PancakeSwap API...")
    api_data = await get_pool_stats_from_api()
    
    if api_data:
        print(f"✅ Got data from PancakeSwap API!")
        print(f"   Data: {api_data}")
    
    # Then try subgraph
    print("\n📊 Fetching pool data from The Graph subgraph...")
    data = await get_pool_data_from_subgraph()
    
    if not data or not data.get("pool"):
        print("❌ Could not fetch pool data from subgraph")
        print("\n💡 Using estimated values for calculation demo...")
        
        # Estimate based on typical values
        estimated_tvl = Decimal("250000")  # $250k TVL
        estimated_daily_volume = Decimal("2000000")  # $2M daily volume (you mentioned millions traded daily)
        estimated_fee_tier = Decimal("0.0025")  # 0.25% fee
        estimated_fees_24h = estimated_daily_volume * estimated_fee_tier
        
        print(f"   Estimated TVL: ${estimated_tvl:,.2f}")
        print(f"   Estimated 24h Volume: ${estimated_daily_volume:,.2f}")
        print(f"   Estimated 24h Fees: ${estimated_fees_24h:,.2f}")
    else:
        pool = data["pool"]
        pool_day_data = data.get("poolDayDatas", [])
        
        print(f"✅ Pool data retrieved!")
        print(f"   Token Pair: {pool['token0']['symbol']}/{pool['token1']['symbol']}")
        print(f"   Fee Tier: {int(pool['feeTier']) / 10000}%")
        print(f"   Total TVL: ${float(pool['totalValueLockedUSD']):,.2f}")
        print(f"   Current Price: ${float(pool['token1Price']):.6f}")
        
        if pool_day_data:
            day_data = pool_day_data[0]
            estimated_tvl = Decimal(str(day_data['tvlUSD']))
            estimated_fees_24h = Decimal(str(day_data['feesUSD']))
            estimated_daily_volume = Decimal(str(day_data['volumeUSD']))
            
            print(f"\n   24h Stats:")
            print(f"   - Volume: ${estimated_daily_volume:,.2f}")
            print(f"   - Fees: ${estimated_fees_24h:,.2f}")
            print(f"   - TVL: ${estimated_tvl:,.2f}")
        else:
            # Fallback to pool totals
            estimated_tvl = Decimal(str(pool['totalValueLockedUSD']))
            estimated_fees_24h = Decimal(str(pool.get('feesUSD', 0))) / Decimal("30")  # Rough daily estimate
            estimated_daily_volume = Decimal(str(pool.get('volumeUSD', 0))) / Decimal("30")
            
            print(f"\n   Using pool averages (no recent day data)")
    
    print("\n" + "-" * 80)
    print("\n🧮 Calculating APR...")
    
    # Estimate 24h trading range from volume and current price
    # High volume suggests wider trading range
    trading_range_estimate_pct = Decimal("0.02")  # Start with ±2%
    if estimated_daily_volume > Decimal("1000000"):
        trading_range_estimate_pct = Decimal("0.03")  # ±3% for high volume
    
    trading_range_min = CURRENT_PRICE * (1 - trading_range_estimate_pct)
    trading_range_max = CURRENT_PRICE * (1 + trading_range_estimate_pct)
    
    print(f"\n   Estimated 24h Trading Range: ${trading_range_min:.6f} - ${trading_range_max:.6f}")
    print(f"   (±{trading_range_estimate_pct * 100:.1f}% from current price)")
    
    # Calculate multiplier
    multiplier = calculate_position_multiplier(
        POSITION_LOWER_PRICE,
        POSITION_UPPER_PRICE,
        CURRENT_PRICE,
        trading_range_min,
        trading_range_max
    )
    
    print(f"\n   Step 1: Calculate position multiplier")
    print(f"   - User range: ${POSITION_LOWER_PRICE} - ${POSITION_UPPER_PRICE}")
    print(f"   - Range width: {((POSITION_UPPER_PRICE - POSITION_LOWER_PRICE) / CURRENT_PRICE * 100):.2f}%")
    print(f"   - Position multiplier: {multiplier:.2f}x")
    print(f"   - (Tighter ranges = higher multiplier)")
    
    # Calculate base pool APR
    base_apr = (estimated_fees_24h / estimated_tvl) * 365 * 100 if estimated_tvl > 0 else Decimal("0")
    
    print(f"\n   Step 2: Calculate base pool APR")
    print(f"   - Formula: (fees_24h / TVL) * 365 * 100")
    print(f"   - Calculation: (${estimated_fees_24h:,.2f} / ${estimated_tvl:,.2f}) * 365 * 100")
    print(f"   - Base Pool APR: {base_apr:.2f}%")
    
    # Calculate position APR
    position_apr = base_apr * multiplier
    
    print(f"\n   Step 3: Calculate your position APR")
    print(f"   - Formula: base_apr * multiplier")
    print(f"   - Calculation: {base_apr:.2f}% * {multiplier:.2f}x")
    print(f"   - Your Position APR: {position_apr:.2f}%")
    
    print("\n" + "=" * 80)
    print("\n📈 RESULTS:")
    print(f"   Calculated APR:  {position_apr:>10.2f}%")
    print(f"   Displayed APR:   {DISPLAYED_APR:>10.2f}%")
    
    difference = abs(position_apr - Decimal(str(DISPLAYED_APR)))
    difference_pct = (difference / Decimal(str(DISPLAYED_APR))) * 100 if DISPLAYED_APR > 0 else Decimal("0")
    
    print(f"   Difference:      {difference:>10.2f}% ({difference_pct:.1f}% error)")
    
    if difference_pct < 10:
        print(f"\n   ✅ Match! Our calculation is within {difference_pct:.1f}% of displayed value")
    elif difference_pct < 25:
        print(f"\n   ⚠️  Close. Our calculation is within {difference_pct:.1f}% of displayed value")
        print(f"      Difference may be due to:")
        print(f"      - Simplified multiplier formula")
        print(f"      - Real-time vs cached data")
        print(f"      - Additional farm rewards not included")
    else:
        print(f"\n   ❌ Significant difference ({difference_pct:.1f}%)")
        print(f"      Possible reasons:")
        print(f"      - Need actual pool data (subgraph may be outdated)")
        print(f"      - Multiplier calculation needs refinement")
        print(f"      - PancakeSwap may include farm/boost rewards")
    
    print("\n" + "=" * 80)
    print("\n💡 Notes:")
    print("   - APR varies with trading volume and TVL")
    print("   - Your actual APR depends on real-time price staying in range")
    print("   - Tighter ranges = higher APR but more rebalancing needed")
    print("   - This calculation doesn't include potential farm rewards")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

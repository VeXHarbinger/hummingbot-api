"""
Check current APR for COAI/USDT pool on PancakeSwap V3
Uses PancakeSwap public API to fetch real-time APR data
"""
import aiohttp
import asyncio
from decimal import Decimal

# Your pool details
POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
COAI_ADDRESS = "0x0A8D6C86e1bcE73fE4D0bD531e1a567306836EA5"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"

# PancakeSwap V3 API endpoints
PANCAKESWAP_INFO_API = "https://api.pancakeswap.info/api/v2"
PANCAKESWAP_BSC_INFO = "https://bsc.api.0x.org/swap/v1"
PANCAKESWAP_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/pancakeswap/exchange-v3-bsc"
GECKOTERMINAL_API = "https://api.geckoterminal.com/api/v2/networks/bsc/pools"

async def get_pool_info_pancakeswap():
    """Get pool info from PancakeSwap V3 API"""
    try:
        async with aiohttp.ClientSession() as session:
            # Try PancakeSwap API first
            url = f"{PANCAKESWAP_API_BASE}/bsc/{POOL_ADDRESS}"
            print(f"Fetching from PancakeSwap API: {url}")
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"PancakeSwap API returned status {response.status}")
                    text = await response.text()
                    print(f"Response: {text[:500]}")
                    return None
    except Exception as e:
        print(f"Error fetching from PancakeSwap API: {e}")
        return None

async def get_pool_stats_subgraph():
    """Get pool statistics from The Graph subgraph"""
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
        txCount
        totalValueLockedUSD
        totalValueLockedToken0
        totalValueLockedToken1
        feesUSD
      }
      poolDayDatas(
        first: 7
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
                PANCAKESWAP_SUBGRAPH,
                json={"query": query}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("data", {})
                else:
                    print(f"Subgraph returned status {response.status}")
                    return None
    except Exception as e:
        print(f"Error fetching from subgraph: {e}")
        return None

def calculate_apr_from_fees(fees_24h_usd: float, tvl_usd: float) -> float:
    """Calculate APR from 24h fees and TVL"""
    if tvl_usd == 0:
        return 0.0
    
    # Daily yield = fees / TVL
    daily_yield = fees_24h_usd / tvl_usd
    
    # Annualize it
    apr = daily_yield * 365 * 100
    
    return apr

async def main():
    print("=" * 70)
    print("COAI/USDT Pool APR Check")
    print("=" * 70)
    print(f"Pool Address: {POOL_ADDRESS}")
    print()
    
    # Try PancakeSwap API
    print("1. Checking PancakeSwap API...")
    pancake_data = await get_pool_info_pancakeswap()
    
    if pancake_data:
        print("\n✅ PancakeSwap API Data:")
        print(f"  Pool: {pancake_data.get('token0', {}).get('symbol')}/{pancake_data.get('token1', {}).get('symbol')}")
        print(f"  Fee Tier: {pancake_data.get('feeTier', 0) / 10000}%")
        print(f"  TVL: ${pancake_data.get('totalValueLockedUSD', 0):,.2f}")
        print(f"  Volume 24h: ${pancake_data.get('volumeUSD', 0):,.2f}")
        print(f"  Fees 24h: ${pancake_data.get('feesUSD', 0):,.2f}")
        
        if pancake_data.get('apr'):
            print(f"\n  📊 APR: {pancake_data['apr']:.2f}%")
        elif pancake_data.get('feesUSD') and pancake_data.get('totalValueLockedUSD'):
            calculated_apr = calculate_apr_from_fees(
                pancake_data['feesUSD'],
                pancake_data['totalValueLockedUSD']
            )
            print(f"\n  📊 Calculated APR: {calculated_apr:.2f}%")
    
    # Try The Graph subgraph
    print("\n2. Checking The Graph Subgraph...")
    subgraph_data = await get_pool_stats_subgraph()
    
    if subgraph_data and subgraph_data.get('pool'):
        pool = subgraph_data['pool']
        print("\n✅ Subgraph Data:")
        print(f"  Pool: {pool['token0']['symbol']}/{pool['token1']['symbol']}")
        print(f"  Fee Tier: {int(pool['feeTier']) / 10000}%")
        print(f"  TVL: ${float(pool['totalValueLockedUSD']):,.2f}")
        print(f"  Total Fees (USD): ${float(pool['feesUSD']):,.2f}")
        print(f"  Total Transactions: {pool['txCount']}")
        
        # Show last 7 days data
        if subgraph_data.get('poolDayDatas'):
            print("\n  Last 7 Days:")
            total_volume_7d = 0
            total_fees_7d = 0
            
            for day_data in subgraph_data['poolDayDatas']:
                volume = float(day_data.get('volumeUSD', 0))
                fees = float(day_data.get('feesUSD', 0))
                tvl = float(day_data.get('tvlUSD', 0))
                
                total_volume_7d += volume
                total_fees_7d += fees
                
                daily_apr = calculate_apr_from_fees(fees, tvl) if tvl > 0 else 0
                
                from datetime import datetime
                date = datetime.fromtimestamp(int(day_data['date'])).strftime('%Y-%m-%d')
                print(f"    {date}: Volume ${volume:,.0f} | Fees ${fees:,.0f} | APR {daily_apr:.2f}%")
            
            # Calculate 7-day average APR
            avg_tvl = float(pool['totalValueLockedUSD'])
            avg_daily_fees = total_fees_7d / 7
            avg_apr = calculate_apr_from_fees(avg_daily_fees, avg_tvl)
            
            print(f"\n  📊 7-Day Average APR: {avg_apr:.2f}%")
            print(f"  📊 7-Day Total Volume: ${total_volume_7d:,.2f}")
            print(f"  📊 7-Day Total Fees: ${total_fees_7d:,.2f}")
    
    print("\n" + "=" * 70)
    print("💡 Note: APR varies based on trading volume and TVL")
    print("   Your actual APR depends on your position's range efficiency")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())

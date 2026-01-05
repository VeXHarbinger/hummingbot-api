"""
Add liquidity to an EXISTING CLMM position.

This script:
1. Gets current pool price
2. Gets wallet balances
3. Quotes the additional liquidity (calculates exact amounts needed)
4. Adds liquidity to the EXISTING position

Use this when you want to increase liquidity in an already open position.
"""
import asyncio
import aiohttp
from aiohttp import BasicAuth

API_URL = "http://localhost:8000"
AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")

# Configuration
POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
CONNECTOR = "pancakeswap"
NETWORK = "ethereum-bsc"
TARGET_RANGE_WIDTH = 2.5  # 2.5% range width


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
            else:
                error = await resp.text()
                print(f"Error getting pool price: {error}")
                return None


async def get_open_positions():
    """Get list of open positions via MCP"""
    print("\n💡 Check open positions using MCP:")
    print("mcp_hummingbot-mc_get_portfolio_overview(include_lp_positions=True)")
    print("\nOr enter position address manually:")
    position_address = input("Position address (e.g., 6223639): ")
    return position_address


async def get_balances():
    """Get current token balances"""
    print("\n💡 Check balances using MCP:")
    print("mcp_hummingbot-mc_get_portfolio_overview(include_balances=True)")
    print("\nEnter balances manually:")
    coai = float(input("COAI balance: "))
    usdt = float(input("USDT balance: "))
    return coai, usdt


async def quote_position(current_price, token_amount, is_coai=True):
    """Quote to get exact amounts needed (same calculation as new position)"""
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
            else:
                error = await resp.text()
                print(f"Error getting quote: {error}")
                return None


async def add_liquidity(position_address, coai_amount, usdt_amount):
    """Add liquidity to EXISTING position via API"""
    url = f"{API_URL}/gateway/clmm/add"
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "position_address": position_address,
        "base_token_amount": str(coai_amount),
        "quote_token_amount": str(usdt_amount),
        "slippage_pct": "1.0"
    }
    
    print(f"\n🚀 Adding liquidity to position {position_address}...")
    print(f"   COAI: {coai_amount:.4f}")
    print(f"   USDT: {usdt_amount:.4f}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"\n✅ Liquidity added!")
                print(f"   Transaction: {result.get('transaction_hash')}")
                return result
            else:
                error = await resp.text()
                print(f"\n❌ Error: {error}")
                return None


async def main():
    print("\n🎯 ADD LIQUIDITY TO EXISTING POSITION")
    print("="*60)
    
    # Step 1: Get pool price
    print("\n📊 Getting pool price...")
    current_price = await get_pool_price()
    if not current_price:
        print("Failed to get pool price")
        return
    print(f"Current price: ${current_price}")
    
    # Step 2: Get position address
    position_address = await get_open_positions()
    
    # Step 3: Get balances
    coai, usdt = await get_balances()
    print(f"\nBalances: {coai:.2f} COAI, {usdt:.2f} USDT")
    
    # Step 4: Decide how much to add
    print("\nHow much to add?")
    print("1. Use all USDT (will calculate COAI needed)")
    print("2. Use all COAI (will calculate USDT needed)")
    print("3. Use specific USDT amount")
    print("4. Use specific COAI amount")
    
    choice = input("Choice (1-4): ")
    
    if choice == "1":
        token_amount = usdt * 0.98  # Leave 2% buffer
        is_coai = False
    elif choice == "2":
        token_amount = coai * 0.98
        is_coai = True
    elif choice == "3":
        token_amount = float(input("USDT amount: "))
        is_coai = False
    else:
        token_amount = float(input("COAI amount: "))
        is_coai = True
    
    # Step 5: Quote to get exact amounts
    print(f"\n📊 Getting quote...")
    quote = await quote_position(current_price, token_amount, is_coai)
    if not quote:
        return
    
    coai_needed = float(quote['base_token_amount'])
    usdt_needed = float(quote['quote_token_amount'])
    
    print(f"\n✅ Quote:")
    print(f"   COAI needed: {coai_needed:.4f}")
    print(f"   USDT needed: {usdt_needed:.4f}")
    print(f"   Additional liquidity: {quote['liquidity']}")
    
    # Check if we have enough
    if coai_needed > coai:
        print(f"\n⚠️ Need {coai_needed:.2f} COAI but only have {coai:.2f}")
        return
    if usdt_needed > usdt:
        print(f"\n⚠️ Need {usdt_needed:.2f} USDT but only have {usdt:.2f}")
        return
    
    # Step 6: Add liquidity
    result = await add_liquidity(position_address, coai_needed, usdt_needed)
    
    if result:
        print("\n" + "="*60)
        print("✅ Liquidity added successfully!")
        print(f"Position {position_address} now has more liquidity.")


if __name__ == "__main__":
    asyncio.run(main())

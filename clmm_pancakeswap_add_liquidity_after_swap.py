"""
Add liquidity after optimal swap

This script adds the optimally balanced tokens to the existing position.
After manual swap: 63.42 COAI + 27.68 USDT
"""
import asyncio
import aiohttp
from aiohttp import BasicAuth

API_URL = "http://localhost:8000"
AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")

POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
POSITION_ADDRESS = "6223672"  # Your current position
CONNECTOR = "pancakeswap"
NETWORK = "ethereum-bsc"
TARGET_RANGE_WIDTH = 2.5


async def main():
    print("\n" + "="*70)
    print("🚀 ADDING LIQUIDITY TO POSITION")
    print("="*70)
    print()
    
    # Get pool price
    print("Step 1: Getting pool info...")
    url = f"{API_URL}/gateway/clmm/pool-info"
    params = {
        'connector': CONNECTOR,
        'network': NETWORK,
        'pool_address': POOL_ADDRESS
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, auth=AUTH) as resp:
            if resp.status != 200:
                print(f"❌ Error: {await resp.text()}")
                return
            
            pool_data = await resp.json()
            price = float(pool_data.get('price'))
            print(f"✅ Pool price: ${price:.6f}")
            print()
    
    # Calculate range
    half_range = TARGET_RANGE_WIDTH / 2.0
    lower_price = price * (1 - half_range / 100)
    upper_price = price * (1 + half_range / 100)
    
    print(f"Position range: ${lower_price:.6f} - ${upper_price:.6f}")
    print()
    
    # Use 98% of USDT to leave some dust
    usdt_to_add = 27.68 * 0.98
    
    # Get quote
    print(f"Step 2: Quoting with {usdt_to_add:.4f} USDT...")
    quote_url = f"{API_URL}/gateway/clmm/quote"
    quote_payload = {
        'connector': CONNECTOR,
        'network': NETWORK,
        'pool_address': POOL_ADDRESS,
        'lower_price': lower_price,
        'upper_price': upper_price,
        'quote_token_amount': usdt_to_add
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(quote_url, json=quote_payload, auth=AUTH) as resp:
            if resp.status != 200:
                print(f"❌ Error: {await resp.text()}")
                return
            
            quote = await resp.json()
            
            coai_needed = float(quote['base_token_amount'])
            usdt_needed = float(quote['quote_token_amount'])
            
            print(f"✅ Quote:")
            print(f"   COAI: {coai_needed:.4f}")
            print(f"   USDT: {usdt_needed:.4f}")
            print(f"   Value: ${coai_needed * price + usdt_needed:.2f}")
            print()
    
    # Confirm
    print("="*70)
    print(f"Ready to add liquidity to position {POSITION_ADDRESS}:")
    print(f"  - COAI: {coai_needed:.2f}")
    print(f"  - USDT: {usdt_needed:.2f}")
    print(f"  - Total: ${coai_needed * price + usdt_needed:.2f}")
    print("="*70)
    print()
    
    response = input("Execute? (yes/no): ")
    if response.lower() != 'yes':
        print("\n❌ Cancelled")
        return
    
    print()
    print("Step 3: Adding liquidity via MCP...")
    print()
    print("Call MCP:")
    print(f"mcp_hummingbot-mc_manage_gateway_clmm_positions(")
    print(f"  action='add_liquidity',")
    print(f"  connector='{CONNECTOR}',")
    print(f"  network='{NETWORK}',")
    print(f"  position_address='{POSITION_ADDRESS}',")
    print(f"  base_token_amount={coai_needed},")
    print(f"  quote_token_amount={usdt_needed},")
    print(f"  slippage_pct='1.0'")
    print(f")")
    print()
    print("⚠️  MCP call required - cannot be automated from script")
    print()
    print("After adding, you should have:")
    print(f"  - Position value: ~$122 (current $68 + new $54)")
    print(f"  - 97%+ capital efficiency")
    print(f"  - Optimal liquidity deployment! 🎉")


if __name__ == "__main__":
    asyncio.run(main())

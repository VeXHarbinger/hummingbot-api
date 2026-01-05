"""
Verify optimal swap and deployment plan
"""
import asyncio
import aiohttp
from aiohttp import BasicAuth

API_URL = "http://localhost:8000"
AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")

# After swap balances
COAI_AFTER_SWAP = 127.018049995952770366 - 63.60
USDT_AFTER_SWAP = 0.267620786283840251 + 27.342446745399937841

POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
CONNECTOR = "pancakeswap"
NETWORK = "ethereum-bsc"
TARGET_RANGE_WIDTH = 2.5


async def main():
    print('='*70)
    print('VERIFYING LIQUIDITY DEPLOYMENT')
    print('='*70)
    print()
    print(f'After swap balances:')
    print(f'  COAI: {COAI_AFTER_SWAP:.4f}')
    print(f'  USDT: {USDT_AFTER_SWAP:.4f}')
    print()
    
    # Get current pool price
    url = f"{API_URL}/gateway/clmm/pool-info"
    params = {
        'connector': CONNECTOR,
        'network': NETWORK,
        'pool_address': POOL_ADDRESS
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, auth=AUTH) as resp:
            if resp.status != 200:
                print(f"Error getting pool info: {await resp.text()}")
                return
            
            pool_data = await resp.json()
            price = float(pool_data.get('price'))
            print(f'Current pool price: ${price:.6f}')
            print()
    
    # Calculate range
    half_range = TARGET_RANGE_WIDTH / 2.0
    lower_price = price * (1 - half_range / 100)
    upper_price = price * (1 + half_range / 100)
    
    # Use 98% of USDT balance
    usdt_to_use = USDT_AFTER_SWAP * 0.98
    
    # Quote position
    quote_url = f"{API_URL}/gateway/clmm/quote"
    quote_payload = {
        'connector': CONNECTOR,
        'network': NETWORK,
        'pool_address': POOL_ADDRESS,
        'lower_price': lower_price,
        'upper_price': upper_price,
        'quote_token_amount': usdt_to_use
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(quote_url, json=quote_payload, auth=AUTH) as resp:
            if resp.status != 200:
                print(f"Error getting quote: {await resp.text()}")
                return
            
            quote = await resp.json()
            
            coai_needed = float(quote['base_token_amount'])
            usdt_needed = float(quote['quote_token_amount'])
            
            print(f'Liquidity quote (using {usdt_to_use:.4f} USDT):')
            print(f'  COAI needed: {coai_needed:.4f}')
            print(f'  USDT needed: {usdt_needed:.4f}')
            print(f'  Liquidity: {quote["liquidity"]}')
            print(f'  In range: {quote["in_range"]}')
            print()
            
            # Check if we have enough
            coai_ok = COAI_AFTER_SWAP >= coai_needed
            usdt_ok = USDT_AFTER_SWAP >= usdt_needed
            
            print(f'Balance check:')
            print(f'  COAI: Have {COAI_AFTER_SWAP:.4f}, Need {coai_needed:.4f} → {"✅" if coai_ok else "❌"}')
            print(f'  USDT: Have {USDT_AFTER_SWAP:.4f}, Need {usdt_needed:.4f} → {"✅" if usdt_ok else "❌"}')
            print()
            
            deploy_value = coai_needed * price + usdt_needed
            total_value = COAI_AFTER_SWAP * price + USDT_AFTER_SWAP
            
            print(f'Deployment metrics:')
            print(f'  Total value after swap: ${total_value:.2f}')
            print(f'  Will deploy: ${deploy_value:.2f}')
            print(f'  Efficiency: {deploy_value / total_value * 100:.1f}%')
            print()
            
            if coai_ok and usdt_ok:
                print('✅ SWAP + DEPLOY PLAN VERIFIED!')
                print()
                print('Ready to execute:')
                print(f'  1. Swap 63.60 COAI → 27.34 USDT')
                print(f'  2. Add {coai_needed:.2f} COAI + {usdt_needed:.2f} USDT to position')
                print(f'  3. Deploy ${deploy_value:.2f} in ONE transaction')
            else:
                print('⚠️  Insufficient balance after swap')


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import aiohttp
from aiohttp import BasicAuth

AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")
API_URL = "http://localhost:8000"

# Using the exact same approach that worked before
LOWER_PRICE = 0.43108
UPPER_PRICE = 0.44868

async def open_position():
    print("="*60)
    print("🟢 OPENING NEW POSITION")
    print("="*60)
    print(f"\nRange: ${LOWER_PRICE} - ${UPPER_PRICE}")
    
    # Use similar amounts to what worked before (we used 0.5 COAI + 0.2 USDT successfully)
    # Now we have 6.1 COAI available, let's use most of it
    use_coai = 6.0  # Use 6 COAI (leaving 0.1 for gas)
    use_usdt = 2.64  # Proportional USDT amount at current price
    
    print(f"Amounts: {use_coai} COAI + {use_usdt} USDT")
    
    url = f"{API_URL}/gateway/clmm/open"
    payload = {
        "connector": "pancakeswap",
        "network": "ethereum-bsc",
        "pool_address": "0xbc0E5A205D729299D93973d634E2507CD8b625A3",
        "lower_price": str(LOWER_PRICE),
        "upper_price": str(UPPER_PRICE),
        "base_token_amount": use_coai,
        "quote_token_amount": use_usdt,
        "slippage_pct": 1.0
    }
    
    print(f"\n📤 Sending request...")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as response:
            print(f"Status: {response.status}")
            text = await response.text()
            
            if response.status == 200:
                data = await response.json()
                print(f"\n✅ SUCCESS!")
                print(f"TX: {data.get('transaction_hash')}")
                print(f"Position ID: {data.get('position_address')}")
                print(f"\nBSCScan: https://bscscan.com/tx/{data.get('transaction_hash')}")
            else:
                print(f"\n❌ Error: {text}")

if __name__ == "__main__":
    asyncio.run(open_position())

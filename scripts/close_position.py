import asyncio
import aiohttp
from aiohttp import BasicAuth

AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")
API_URL = "http://localhost:8000"

async def collect_and_close():
    """Collect fees and close position"""
    
    # Step 1: Collect fees
    print("💰 Collecting fees from position 6220678...")
    url = f"{API_URL}/gateway/clmm/collect-fees"
    payload = {
        "connector": "pancakeswap_v3_bsc",
        "network": "bsc-mainnet",
        "position_address": "6220678"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as response:
            print(f"   Status: {response.status}")
            text = await response.text()
            print(f"   Response: {text[:200]}")
            
            if response.status == 200:
                data = await response.json()
                print(f"✅ Fees collected! TX: {data.get('transaction_hash')}")
            else:
                print(f"⚠️  Fee collection failed")
        
        # Wait for transaction
        print("\n⏳ Waiting 15 seconds for transaction...")
        await asyncio.sleep(15)
        
        # Step 2: Close position
        print("\n🔴 Closing position 6220678...")
        url = f"{API_URL}/gateway/clmm/close"
        payload = {
            "connector": "pancakeswap_v3_bsc",
            "network": "bsc-mainnet",
            "position_address": "6220678"
        }
        
        async with session.post(url, json=payload, auth=AUTH) as response:
            print(f"   Status: {response.status}")
            text = await response.text()
            print(f"   Response: {text[:500]}")
            
            if response.status == 200:
                data = await response.json()
                print(f"✅ Position closed! TX: {data.get('transaction_hash')}")
                print(f"\n📊 Returned tokens:")
                print(f"   Base: {data.get('base_token_amount')}")
                print(f"   Quote: {data.get('quote_token_amount')}")
                return True
            else:
                print(f"❌ Failed to close position")
                return False

if __name__ == "__main__":
    result = asyncio.run(collect_and_close())
    
    if result:
        print("\n" + "="*60)
        print("✅ Ready to open new position!")
        print("="*60)
        print(f"\n📐 New 2% range around $0.43988:")
        print(f"   Lower: $0.43088")
        print(f"   Upper: $0.44868")
        print(f"\n💡 Check your balances and open new position with these parameters")

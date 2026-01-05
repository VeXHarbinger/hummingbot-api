import asyncio
import aiohttp
from aiohttp import BasicAuth

AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")
API_URL = "http://localhost:8000"

# Current price: $0.43988
# New 2% range: $0.43088 - $0.44868

async def rebalance():
    async with aiohttp.ClientSession() as session:
        # Step 1: Close position (collects fees automatically)
        print("\n🔴 Closing position 6220678...")
        url = f"{API_URL}/gateway/clmm/close"
        payload = {
            "connector": "pancakeswap_v3_bsc",
            "network": "bsc-mainnet",
            "position_address": "6220678"
        }
        
        async with session.post(url, json=payload, auth=AUTH) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Position closed! TX: {data.get('transaction_hash')}")
                print(f"   COAI returned: {data.get('base_token_amount', 'N/A')}")
                print(f"   USDT returned: {data.get('quote_token_amount', 'N/A')}")
                print(f"   COAI fees: {data.get('base_fee_collected', 'N/A')}")
                print(f"   USDT fees: {data.get('quote_fee_collected', 'N/A')}")
            else:
                text = await response.text()
                print(f"❌ Failed to close: {text}")
                return False
        
        # Wait for transaction to settle
        print("\n⏳ Waiting 20 seconds for transaction to settle...")
        await asyncio.sleep(20)
        
        # Step 2: Get updated balances
        print("\n💰 Getting updated balances...")
        url = f"{API_URL}/portfolio/state"
        payload = {"account_names": ["master_account"]}
        
        async with session.post(url, json=payload, auth=AUTH) as response:
            if response.status == 200:
                data = await response.json()
                # Find COAI and USDT balances
                coai = 0
                usdt = 0
                if 'balances' in data:
                    for connector, tokens in data['balances'].items():
                        for token, amount in tokens.items():
                            if 'COAI' in token:
                                coai = float(amount)
                            elif 'USDT' in token:
                                usdt = float(amount)
                
                print(f"   COAI: {coai}")
                print(f"   USDT: {usdt}")
            else:
                print("   Could not get balances, using estimates")
                coai = 6.0  # estimate
                usdt = 2.7  # estimate
        
        # Step 3: Open new position with 2% range
        print("\n🟢 Opening new position with 2% range...")
        print(f"   Range: $0.43088 - $0.44868")
        
        # Use 98% of balances (keep some for gas)
        use_coai = coai * 0.98
        use_usdt = usdt * 0.98
        
        print(f"   Using: {use_coai:.4f} COAI + {use_usdt:.4f} USDT")
        
        url = f"{API_URL}/gateway/clmm/open"
        payload = {
            "connector": "pancakeswap_v3_bsc",
            "network": "bsc-mainnet",
            "pool_address": "0xbc0E5A205D729299D93973d634E2507CD8b625A3",
            "lower_price": "0.43088",
            "upper_price": "0.44868",
            "base_token_amount": str(use_coai),
            "quote_token_amount": str(use_usdt),
            "slippage_pct": "1.0"
        }
        
        async with session.post(url, json=payload, auth=AUTH) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ New position opened! TX: {data.get('transaction_hash')}")
                print(f"   Position ID: {data.get('position_address')}")
                return True
            else:
                text = await response.text()
                print(f"❌ Failed to open: {text}")
                return False

if __name__ == "__main__":
    print("="*60)
    print("🔄 REBALANCING POSITION")
    print("="*60)
    result = asyncio.run(rebalance())
    print("\n" + "="*60)
    if result:
        print("✅ REBALANCING COMPLETE!")
    else:
        print("❌ REBALANCING FAILED")
    print("="*60)

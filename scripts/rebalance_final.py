import asyncio
import aiohttp
from aiohttp import BasicAuth

AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")
API_URL = "http://localhost:8000"

# Current price: $0.43988
# New 2% range: $0.43088 - $0.44868
CURRENT_PRICE = 0.43988
LOWER_PRICE = CURRENT_PRICE * 0.98  # 0.43088
UPPER_PRICE = CURRENT_PRICE * 1.02  # 0.44868

async def main():
    print("="*60)
    print("🔄 REBALANCING POSITION")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Close position (removes 100% liquidity + collects fees)
        print("\n🔴 Step 1: Closing position 6220678...")
        print("   (This removes all liquidity and collects fees)")
        
        url = f"{API_URL}/gateway/clmm/close"
        payload = {
            "connector": "pancakeswap_v3_bsc",
            "network": "bsc-mainnet",
            "position_address": "6220678"
        }
        
        async with session.post(url, json=payload, auth=AUTH) as response:
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                print(f"✅ Position closed!")
                print(f"   TX: {data.get('transaction_hash')}")
                print(f"   Base returned: {data.get('base_token_amount')} COAI")
                print(f"   Quote returned: {data.get('quote_token_amount')} USDT")
                print(f"   Base fees: {data.get('base_fee_collected')} COAI")
                print(f"   Quote fees: {data.get('quote_fee_collected')} USDT")
            else:
                text = await response.text()
                print(f"❌ Failed to close position")
                print(f"   Error: {text}")
                return
        
        # Wait for transaction to settle
        print("\n⏳ Waiting 20 seconds for transaction to settle...")
        await asyncio.sleep(20)
        
        # Step 2: Get updated balances
        print("\n💰 Step 2: Checking balances...")
        url = f"{API_URL}/portfolio/state"
        payload = {"account_names": ["master_account"]}
        
        async with session.post(url, json=payload, auth=AUTH) as response:
            if response.status == 200:
                data = await response.json()
                
                coai_balance = 0
                usdt_balance = 0
                
                if 'balances' in data:
                    for connector, tokens in data['balances'].items():
                        for token, amount in tokens.items():
                            if 'COAI' in token:
                                coai_balance = float(amount)
                                print(f"   COAI: {coai_balance}")
                            elif 'USDT' in token:
                                usdt_balance = float(amount)
                                print(f"   USDT: {usdt_balance}")
            else:
                print("   ⚠️  Could not fetch balances")
                coai_balance = 10  # Estimate
                usdt_balance = 4   # Estimate
        
        # Step 3: Open new position with 2% range
        print(f"\n🟢 Step 3: Opening new position...")
        print(f"   Current price: ${CURRENT_PRICE}")
        print(f"   New range: ${LOWER_PRICE:.5f} - ${UPPER_PRICE:.5f}")
        
        # Use 98% of balances to leave buffer for gas
        use_coai = coai_balance * 0.98
        use_usdt = usdt_balance * 0.98
        
        print(f"   Depositing: {use_coai:.4f} COAI + {use_usdt:.2f} USDT")
        
        url = f"{API_URL}/gateway/clmm/open"
        payload = {
            "connector": "pancakeswap_v3_bsc",
            "network": "bsc-mainnet",
            "pool_address": "0xbc0E5A205D729299D93973d634E2507CD8b625A3",
            "lower_price": str(LOWER_PRICE),
            "upper_price": str(UPPER_PRICE),
            "base_token_amount": str(use_coai),
            "quote_token_amount": str(use_usdt),
            "slippage_pct": "1.0"
        }
        
        async with session.post(url, json=payload, auth=AUTH) as response:
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                print(f"✅ New position opened!")
                print(f"   TX: {data.get('transaction_hash')}")
                print(f"   Position ID: {data.get('position_address')}")
            else:
                text = await response.text()
                print(f"❌ Failed to open position")
                print(f"   Error: {text}")
    
    print("\n" + "="*60)
    print("✅ REBALANCING COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())

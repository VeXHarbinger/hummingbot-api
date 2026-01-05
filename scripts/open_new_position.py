import asyncio
import aiohttp
from aiohttp import BasicAuth

AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")
API_URL = "http://localhost:8000"

# Current price: $0.43988
# 2% range: $0.43088 - $0.44868
CURRENT_PRICE = 0.43988
LOWER_PRICE = round(CURRENT_PRICE * 0.98, 5)  # 0.43088
UPPER_PRICE = round(CURRENT_PRICE * 1.02, 5)  # 0.44868

async def open_new_position():
    print("="*60)
    print("🟢 OPENING NEW CLMM POSITION")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Get current balances
        print("\n💰 Step 1: Checking balances...")
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
                            elif 'USDT' in token or 'USDC' in token:
                                usdt_balance = float(amount)
                                print(f"   USDT/USDC: {usdt_balance}")
            else:
                print("   ⚠️  Could not fetch balances, please enter manually")
                return
        
        # Step 2: Open new position
        print(f"\n🟢 Step 2: Opening new position...")
        print(f"   Current price: ${CURRENT_PRICE}")
        print(f"   New 2% range: ${LOWER_PRICE} - ${UPPER_PRICE}")
        
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
        
        print(f"\n📤 Sending request to API...")
        async with session.post(url, json=payload, auth=AUTH) as response:
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                print(f"\n✅ NEW POSITION OPENED!")
                print(f"   TX: {data.get('transaction_hash')}")
                print(f"   Position ID: {data.get('position_address')}")
                print(f"\n🔗 View on BSCScan:")
                print(f"   https://bscscan.com/tx/{data.get('transaction_hash')}")
            else:
                text = await response.text()
                print(f"❌ Failed to open position")
                print(f"   Error: {text}")
    
    print("\n" + "="*60)
    print("✅ DONE!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(open_new_position())

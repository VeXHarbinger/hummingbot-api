import asyncio
import aiohttp
from aiohttp import BasicAuth

AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")
API_URL = "http://localhost:8000"

# Exact range specified
LOWER_PRICE = 0.429575506
UPPER_PRICE = 0.447105921

async def open_final_position():
    print("="*60)
    print("🟢 OPENING NEW POSITION WITH 2% RANGE")
    print("="*60)
    print(f"\nRange: ${LOWER_PRICE} - ${UPPER_PRICE}")
    
    async with aiohttp.ClientSession(auth=AUTH) as session:
        # Step 1: Get exact balances
        print("\n💰 Checking balances...")
        payload = {
            "account_names": ["master_account"],
            "skip_gateway": False,
            "refresh": True
        }
        
        async with session.post(f"{API_URL}/portfolio/state", json=payload) as response:
            if response.status == 200:
                portfolio = await response.json()
                
                coai_balance = None
                usdt_balance = None
                
                for account_name, networks in portfolio.items():
                    for network_name, balances in networks.items():
                        if isinstance(balances, list):
                            for balance in balances:
                                token = balance.get('token')
                                available = float(balance.get('available_units', 0))
                                
                                if token == 'COAI':
                                    coai_balance = available
                                    print(f"   COAI Available: {coai_balance:.4f}")
                                elif token == 'USDT':
                                    usdt_balance = available
                                    print(f"   USDT Available: {usdt_balance:.4f}")
                
                if coai_balance is None or usdt_balance is None:
                    print("   ⚠️  Could not find balances, using estimates")
                    coai_balance = 12.0
                    usdt_balance = 5.3
            else:
                print("   ⚠️  Could not fetch balances")
                return
        
        # Use a balanced ratio based on the range
        # Current price is ~0.438, which is roughly in the middle of the range
        # For centered positions, we need roughly equal value in both tokens
        
        # Calculate how much of each token to use
        current_price = (LOWER_PRICE + UPPER_PRICE) / 2  # ~0.438
        
        # Total value available
        total_value_usd = (coai_balance * current_price) + usdt_balance
        print(f"   Total value: ${total_value_usd:.2f}")
        
        # For a centered range, use ~50% in each token by value
        # But leave a small buffer
        target_usdt = usdt_balance * 0.95  # Use 95% of USDT
        target_coai_value = target_usdt  # Match the USDT value
        target_coai = target_coai_value / current_price
        
        # Make sure we don't exceed available COAI
        if target_coai > coai_balance * 0.95:
            target_coai = coai_balance * 0.95
            target_usdt = target_coai * current_price
        
        use_coai = target_coai
        use_usdt = target_usdt
        
        print(f"\n📊 Using ALL available tokens:")
        print(f"   COAI: {use_coai:.4f}")
        print(f"   USDT: {use_usdt:.4f}")
        
        # Step 2: Open position
        print(f"\n🟢 Opening position...")
        
        url = f"{API_URL}/gateway/clmm/open"
        payload = {
            "connector": "pancakeswap",
            "network": "ethereum-bsc",
            "pool_address": "0xbc0E5A205D729299D93973d634E2507CD8b625A3",
            "lower_price": LOWER_PRICE,
            "upper_price": UPPER_PRICE,
            "base_token_amount": use_coai,
            "quote_token_amount": use_usdt,
            "slippage_pct": 1.0
        }
        
        async with session.post(url, json=payload) as response:
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                print(f"\n✅ SUCCESS!")
                print(f"   TX: {data.get('transaction_hash')}")
                print(f"   Position ID: {data.get('position_address')}")
                print(f"\n🔗 BSCScan: https://bscscan.com/tx/{data.get('transaction_hash')}")
            else:
                text = await response.text()
                print(f"\n❌ Error: {text}")
    
    print("\n" + "="*60)
    print("✅ POSITION OPENED!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(open_final_position())

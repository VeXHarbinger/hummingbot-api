import asyncio
import aiohttp
from aiohttp import BasicAuth

AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")
API_URL = "http://localhost:8000"

LOWER_PRICE = 0.429575506
UPPER_PRICE = 0.447105921

async def rebalance_and_open():
    print("="*60)
    print("🔄 REBALANCE & OPEN POSITION")
    print("="*60)
    
    current_price = (LOWER_PRICE + UPPER_PRICE) / 2  # ~0.438
    print(f"\nCurrent price: ~${current_price:.5f}")
    print(f"Range: ${LOWER_PRICE} - ${UPPER_PRICE}")
    
    async with aiohttp.ClientSession(auth=AUTH) as session:
        # Step 1: Get balances
        print("\n💰 Step 1: Checking balances...")
        payload = {"account_names": ["master_account"], "skip_gateway": False, "refresh": True}
        
        async with session.post(f"{API_URL}/portfolio/state", json=payload) as response:
            portfolio = await response.json()
            
            coai_balance = 0
            usdt_balance = 0
            
            for account_name, networks in portfolio.items():
                for network_name, balances in networks.items():
                    if isinstance(balances, list):
                        for balance in balances:
                            token = balance.get('token')
                            available = float(balance.get('available_units', 0))
                            if token == 'COAI':
                                coai_balance = available
                            elif token == 'USDT':
                                usdt_balance = available
            
            print(f"   COAI: {coai_balance:.4f}")
            print(f"   USDT: {usdt_balance:.4f}")
            
            # Calculate total value
            total_value = (coai_balance * current_price) + usdt_balance
            print(f"   Total value: ${total_value:.2f}")
        
        # Step 2: Calculate optimal distribution
        print("\n🧮 Step 2: Calculating optimal token distribution...")
        
        # For a centered position, we want roughly equal USD value in both tokens
        target_value_per_token = total_value / 2
        target_usdt = target_value_per_token * 0.95  # Use 95% to leave buffer
        target_coai = target_value_per_token / current_price * 0.95
        
        print(f"   Target: {target_coai:.4f} COAI + {target_usdt:.2f} USDT")
        
        # Calculate how much COAI to swap to USDT
        coai_to_swap = coai_balance - target_coai
        
        if coai_to_swap > 0.1:  # Only swap if meaningful amount
            print(f"\n🔄 Step 3: Swapping {coai_to_swap:.4f} COAI to USDT...")
            
            swap_url = f"{API_URL}/trading/orders"
            swap_payload = {
                "connector_name": "pancakeswap",
                "trading_pair": "COAI-USDT",
                "trade_type": "SELL",
                "order_type": "MARKET",
                "amount": f"${coai_to_swap * current_price:.2f}",  # Use USD value
                "account_name": "master_account"
            }
            
            async with session.post(swap_url, json=swap_payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Swap order placed!")
                    print(f"   Order ID: {data.get('id')}")
                    
                    # Wait for swap to complete
                    print("   ⏳ Waiting 15 seconds for swap to settle...")
                    await asyncio.sleep(15)
                    
                    # Refresh balances
                    async with session.post(f"{API_URL}/portfolio/state", json=payload) as resp:
                        portfolio = await resp.json()
                        for account_name, networks in portfolio.items():
                            for network_name, balances in networks.items():
                                if isinstance(balances, list):
                                    for balance in balances:
                                        token = balance.get('token')
                                        available = float(balance.get('available_units', 0))
                                        if token == 'COAI':
                                            coai_balance = available
                                        elif token == 'USDT':
                                            usdt_balance = available
                        
                        print(f"   Updated: {coai_balance:.4f} COAI + {usdt_balance:.4f} USDT")
                else:
                    text = await response.text()
                    print(f"   ⚠️  Swap failed: {text}")
                    print("   Continuing with current balances...")
        else:
            print(f"\n✅ Step 3: Balances are close enough, skipping swap")
        
        # Step 4: Open position with balanced amounts
        print(f"\n🟢 Step 4: Opening position...")
        
        # Use 95% of each to leave buffer
        use_coai = coai_balance * 0.95
        use_usdt = usdt_balance * 0.95
        
        print(f"   Using: {use_coai:.4f} COAI + {use_usdt:.2f} USDT")
        
        open_url = f"{API_URL}/gateway/clmm/open"
        open_payload = {
            "connector": "pancakeswap",
            "network": "ethereum-bsc",
            "pool_address": "0xbc0E5A205D729299D93973d634E2507CD8b625A3",
            "lower_price": LOWER_PRICE,
            "upper_price": UPPER_PRICE,
            "base_token_amount": use_coai,
            "quote_token_amount": use_usdt,
            "slippage_pct": 1.0
        }
        
        async with session.post(open_url, json=open_payload) as response:
            if response.status == 200:
                data = await response.json()
                print(f"\n✅ SUCCESS!")
                print(f"   TX: {data.get('transaction_hash')}")
                print(f"   Position ID: {data.get('position_address')}")
                print(f"\n🔗 BSCScan: https://bscscan.com/tx/{data.get('transaction_hash')}")
            else:
                text = await response.text()
                print(f"\n❌ Failed: {text}")
    
    print("\n" + "="*60)
    print("✅ COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(rebalance_and_open())

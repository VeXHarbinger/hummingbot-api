"""
Complete test script:
1. Swap half of USDT for COAI
2. Add liquidity to existing position
"""

import asyncio
import aiohttp
import time

async def check_gateway_status(session, api_url):
    """Check if Gateway is running"""
    print("\n🔌 Checking Gateway connectivity...")
    
    # Try to ping Gateway directly
    try:
        async with session.get(f"{api_url}/gateway/config") as response:
            if response.status == 200:
                print("   ✅ Gateway is responding")
                return True
            else:
                print(f"   ⚠️  Gateway responded with status: {response.status}")
                # Continue anyway, might still work
                return True
    except Exception as e:
        print(f"   ❌ Gateway is not responding: {e}")
        return False

async def get_balances(session, api_url):
    """Get current COAI and USDT balances"""
    payload = {
        "account_names": ["master_account"],
        "skip_gateway": False,
        "refresh": True
    }
    
    async with session.post(f"{api_url}/portfolio/state", json=payload) as response:
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
                            elif token == 'USDT':
                                usdt_balance = available
            
            return coai_balance, usdt_balance
        return None, None

async def swap_usdt_for_coai(session, api_url, usdt_amount):
    """Swap USDT for COAI using Gateway swap on BSC"""
    print(f"\n💱 Step 1: Swapping {usdt_amount:.4f} USDT for COAI on BSC...")
    
    swap_data = {
        "connector": "pancakeswap",
        "network": "ethereum-bsc",
        "trading_pair": "COAI-USDT",
        "side": "BUY",  # Buy COAI with USDT
        "amount": str(usdt_amount),
        "slippage_pct": "1.0"
    }
    
    # First get a quote
    print("   Getting quote...")
    async with session.post(f"{api_url}/gateway/swap/quote", json=swap_data) as response:
        if response.status == 200:
            quote = await response.json()
            expected_coai = quote.get('expectedAmount', 'unknown')
            print(f"   Expected to receive: ~{expected_coai} COAI")
        else:
            error = await response.text()
            print(f"   ⚠️  Could not get quote: {error}")
    
    # Execute the swap
    print("   Executing swap...")
    async with session.post(f"{api_url}/gateway/swap/execute", json=swap_data) as response:
        if response.status == 200:
            result = await response.json()
            tx_hash = result.get('transaction_hash')
            print(f"   ✅ Swap submitted!")
            print(f"   Transaction: {tx_hash}")
            return tx_hash
        else:
            error = await response.text()
            print(f"   ❌ Swap failed: {error}")
            return None

async def add_liquidity(session, api_url, coai_amount, usdt_amount):
    """Add liquidity to position 6220678"""
    print(f"\n💧 Step 2: Adding liquidity to position...")
    print(f"   Amount: {coai_amount} COAI + {usdt_amount} USDT")
    
    position_data = {
        "connector": "pancakeswap",
        "network": "ethereum-bsc",
        "position_address": "6220678",
        "base_token_amount": coai_amount,
        "quote_token_amount": usdt_amount,
        "slippage_pct": 1.0
    }
    
    async with session.post(f"{api_url}/gateway/clmm/add", json=position_data) as response:
        if response.status == 200:
            result = await response.json()
            print(f"   ✅ Liquidity added!")
            print(f"   Transaction: {result.get('transaction_hash')}")
            print(f"   Position: {result.get('position_address')}")
            return True
        else:
            error = await response.text()
            print(f"   ❌ Add liquidity failed: {error}")
            return False

async def main():
    """Main test flow"""
    api_url = "http://localhost:8000"
    auth = aiohttp.BasicAuth("admin", "4Adm!np@ssw0rd")
    
    async with aiohttp.ClientSession(auth=auth) as session:
        # Check Gateway
        if not await check_gateway_status(session, api_url):
            return
        
        # Get current balances
        print("\n📊 Current balances:")
        coai_balance, usdt_balance = await get_balances(session, api_url)
        
        if coai_balance is None or usdt_balance is None:
            print("   ❌ Could not fetch balances")
            return
        
        print(f"   COAI: {coai_balance:.4f}")
        print(f"   USDT: {usdt_balance:.4f}")
        
        # Calculate swap amount (half of USDT)
        usdt_to_swap = usdt_balance / 2
        
        if usdt_to_swap < 0.1:
            print(f"\n   ⚠️  USDT balance too low to swap ({usdt_balance})")
            return
        
        # Step 1: Swap USDT for COAI
        tx_hash = await swap_usdt_for_coai(session, api_url, usdt_to_swap)
        
        if not tx_hash:
            print("\n❌ Swap failed, cannot continue")
            return
        
        # Wait for swap to settle
        print("\n⏳ Waiting 30 seconds for swap to settle...")
        await asyncio.sleep(30)
        
        # Refresh balances
        print("\n📊 Updated balances after swap:")
        coai_balance, usdt_balance = await get_balances(session, api_url)
        print(f"   COAI: {coai_balance:.4f}")
        print(f"   USDT: {usdt_balance:.4f}")
        
        # Step 2: Add liquidity
        # Use conservative amounts (90% of available to leave some buffer)
        coai_to_add = coai_balance * 0.9
        usdt_to_add = usdt_balance * 0.9
        
        await add_liquidity(session, api_url, coai_to_add, usdt_to_add)
        
        print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(main())

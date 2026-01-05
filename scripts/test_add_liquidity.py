"""
Test script to add liquidity to existing COAI/USDT position
This tests the newly enabled increaseLiquidity functionality
"""

import asyncio
import aiohttp

async def check_balances(session, api_url):
    """Check available token balances before adding liquidity"""
    print("\n📊 Checking available balances...")
    
    # Use portfolio state endpoint
    payload = {
        "account_names": ["master_account"],
        "skip_gateway": False,
        "refresh": True
    }
    
    async with session.post(f"{api_url}/portfolio/state", json=payload) as response:
        if response.status == 200:
            portfolio = await response.json()
            
            # Navigate through the portfolio structure
            coai_balance = None
            usdt_balance = None
            
            # Portfolio structure: {account_name: {network: [balances]}}
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
            
            if coai_balance is not None:
                print(f"   COAI Available: {coai_balance:.4f}")
            else:
                print("   ⚠️  COAI balance not found in portfolio")
                
            if usdt_balance is not None:
                print(f"   USDT Available: {usdt_balance:.4f}")
            else:
                print("   ⚠️  USDT balance not found in portfolio")
                
            return coai_balance, usdt_balance
        else:
            error_text = await response.text()
            print(f"   ⚠️  Could not fetch balances: {response.status}")
            print(f"   Error: {error_text}")
            return None, None

async def test_add_liquidity():
    """Test adding liquidity to position 6220678"""
    
    api_url = "http://localhost:8000"
    auth = aiohttp.BasicAuth("admin", "4Adm!np@ssw0rd")
    
    # Position details - REDUCED amounts based on available balance
    position_data = {
        "connector": "pancakeswap",
        "network": "ethereum-bsc",
        "position_address": "6220678",
        "base_token_amount": 0.5,  # Add 0.5 COAI (we only have 0.664 available)
        "quote_token_amount": 0.2,  # Add 0.2 USDT (proportional)
        "slippage_pct": 1.0
    }
    
    async with aiohttp.ClientSession(auth=auth) as session:
        # Check Gateway connectivity
        print("\n🔌 Checking Gateway connectivity...")
        try:
            async with session.get(f"{api_url}/gateway/config") as response:
                print("   ✅ Gateway is responding")
        except Exception as e:
            print(f"   ⚠️  Gateway check failed: {e}")
        
        # Check balances first
        coai_balance, usdt_balance = await check_balances(session, api_url)
        
        # Validate we have enough funds
        if coai_balance is not None and coai_balance < position_data["base_token_amount"]:
            print(f"\n❌ Insufficient COAI balance!")
            print(f"   Required: {position_data['base_token_amount']} COAI")
            print(f"   Available: {coai_balance} COAI")
            print(f"   Shortfall: {position_data['base_token_amount'] - coai_balance} COAI")
            return
            
        if usdt_balance is not None and usdt_balance < position_data["quote_token_amount"]:
            print(f"\n❌ Insufficient USDT balance!")
            print(f"   Required: {position_data['quote_token_amount']} USDT")
            print(f"   Available: {usdt_balance} USDT")
            print(f"   Shortfall: {position_data['quote_token_amount'] - usdt_balance} USDT")
            return
        
        # Test the endpoint
        print(f"\n🚀 Testing endpoint: {api_url}/gateway/clmm/add")
        print(f"   Position: {position_data['position_address']}")
        print(f"   Adding: {position_data['base_token_amount']} COAI + {position_data['quote_token_amount']} USDT")
        
        async with session.post(
            f"{api_url}/gateway/clmm/add",
            json=position_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                print("\n✅ Success! Added liquidity to position")
                print(f"   Transaction Hash: {result.get('transaction_hash')}")
                print(f"   Position ID: {result.get('position_address')}")
                print(f"   Status: {result.get('status')}")
            else:
                error_text = await response.text()
                print(f"\n❌ Error: {response.status}")
                print(f"   Response: {error_text}")

if __name__ == "__main__":
    asyncio.run(test_add_liquidity())

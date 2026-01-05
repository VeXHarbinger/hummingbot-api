import asyncio
import aiohttp
from aiohttp import BasicAuth

async def check_position_fees():
    """Test the position fees checker endpoint"""
    
    url = "http://localhost:8000/gateway/clmm/position-fees/6220678"
    params = {
        "connector": "pancakeswap_v3_bsc",
        "network": "bsc-mainnet"
    }
    
    # Use basic auth (default credentials)
    auth = BasicAuth("admin", "4Adm!np@ssw0rd")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, auth=auth) as response:
            print(f"Status: {response.status}")
            data = await response.json()
            print(f"\n📊 Position Fees Check:")
            print(f"{'='*60}")
            
            if response.status == 200:
                print(f"Position: {data['position_address']}")
                print(f"Tokens: {data['base_token']}/{data['quote_token']}")
                print(f"\nPending Fees:")
                for token, amount in data['pending_fees'].items():
                    print(f"  {token}: {amount}")
                print(f"\nRecommendation: {data['recommendation']}")
                print(f"Reason: {data['reason']}")
                
                if data.get('fees_value_usd'):
                    print(f"\n💰 Fees Value: ${data['fees_value_usd']}")
                if data.get('estimated_gas_cost_usd'):
                    print(f"⛽ Est. Gas Cost: ${data['estimated_gas_cost_usd']}")
                if data.get('net_profit_usd'):
                    print(f"📈 Net Profit: ${data['net_profit_usd']}")
            else:
                print(f"Error: {data}")

if __name__ == "__main__":
    asyncio.run(check_position_fees())

"""
Diagnostic script to debug the add liquidity functionality
"""

import asyncio
import aiohttp
import json

async def test_gateway_connection(session, api_url):
    """Test if Gateway is responsive"""
    print("\n🔌 Testing Gateway connection...")
    
    async with session.get(f"{api_url}/gateway/status") as response:
        if response.status == 200:
            status = await response.json()
            print(f"   ✅ Gateway Status: {status}")
        else:
            print(f"   ❌ Gateway not responding: {response.status}")

async def test_portfolio_structure(session, api_url):
    """Check the actual portfolio structure"""
    print("\n📊 Checking portfolio structure...")
    
    payload = {
        "account_names": ["master_account"],
        "skip_gateway": False,
        "refresh": True
    }
    
    async with session.post(f"{api_url}/portfolio/state", json=payload) as response:
        if response.status == 200:
            portfolio = await response.json()
            print(f"   Portfolio structure:")
            print(json.dumps(portfolio, indent=2, default=str))
        else:
            error_text = await response.text()
            print(f"   ❌ Error: {response.status}")
            print(f"   {error_text}")

async def test_position_details(session, api_url):
    """Check position details"""
    print("\n📍 Checking position 6220678...")
    
    payload = {
        "connector": "pancakeswap",
        "network": "ethereum-bsc",
        "pool_address": "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
    }
    
    async with session.post(f"{api_url}/gateway/clmm/positions", json=payload) as response:
        if response.status == 200:
            positions = await response.json()
            print(f"   Positions found: {len(positions.get('positions', []))}")
            for pos in positions.get('positions', []):
                if str(pos.get('tokenId')) == "6220678":
                    print(f"   ✅ Found position 6220678:")
                    print(json.dumps(pos, indent=2, default=str))
        else:
            error_text = await response.text()
            print(f"   ❌ Error: {response.status}")
            print(f"   {error_text}")

async def run_diagnostics():
    """Run all diagnostic tests"""
    api_url = "http://localhost:8000"
    auth = aiohttp.BasicAuth("admin", "4Adm!np@ssw0rd")
    
    async with aiohttp.ClientSession(auth=auth) as session:
        await test_gateway_connection(session, api_url)
        await test_portfolio_structure(session, api_url)
        await test_position_details(session, api_url)

if __name__ == "__main__":
    asyncio.run(run_diagnostics())

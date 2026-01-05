"""
Test script to verify the remove liquidity endpoint is working
"""

import asyncio
import aiohttp

async def test_remove_endpoint():
    """Test that the remove liquidity endpoint is available"""
    
    api_url = "http://localhost:8000"
    auth = aiohttp.BasicAuth("admin", "4Adm!np@ssw0rd")
    
    # Test with a dummy request to see if endpoint responds
    test_data = {
        "connector": "pancakeswap",
        "network": "ethereum-bsc",
        "position_address": "test",
        "percentage": 50
    }
    
    async with aiohttp.ClientSession(auth=auth) as session:
        print("\n🔍 Testing /gateway/clmm/remove endpoint availability...")
        
        async with session.post(
            f"{api_url}/gateway/clmm/remove",
            json=test_data
        ) as response:
            status = response.status
            text = await response.text()
            
            if status == 404:
                print("   ❌ Endpoint not found (404)")
                print(f"   Response: {text}")
            elif status == 503:
                print("   ⚠️  Gateway not available (503) - but endpoint exists!")
            elif status in [400, 500]:
                print(f"   ✅ Endpoint exists! (Got expected error {status})")
                print(f"   Error: {text[:200]}")
            else:
                print(f"   ℹ️  Got status {status}")
                print(f"   Response: {text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_remove_endpoint())

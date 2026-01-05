#!/usr/bin/env python3
"""
Test CLMM Quote Endpoint
Calculates exact token amounts before opening position
"""

import asyncio
import aiohttp
from aiohttp import BasicAuth

API_URL = "http://localhost:8000"
API_USER = "admin"
API_PASS = "4Adm!np@ssw0rd"

async def test_quote():
    """Test the quote endpoint"""
    
    url = f"{API_URL}/gateway/clmm/quote"
    auth = BasicAuth(API_USER, API_PASS)
    
    # Test 1: I have 183.38 COAI, how much USDT do I need?
    payload1 = {
        "connector": "pancakeswap",
        "network": "ethereum-bsc",
        "pool_address": "0xbc0E5A205D729299D93973d634E2507CD8b625A3",
        "lower_price": 0.4262,
        "upper_price": 0.4369,
        "base_token_amount": 183.38
    }
    
    print("\n" + "=" * 80)
    print("TEST 1: Calculate USDT needed for 183.38 COAI")
    print("=" * 80)
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload1, auth=auth) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✅ Success!")
                print(f"\n📊 Current Price: ${data['current_price']}")
                print(f"📏 Range: ${data['lower_price']} - ${data['upper_price']}")
                print(f"🎯 In Range: {data['in_range']}")
                print(f"\n💰 Token Amounts Needed:")
                print(f"   COAI:  {data['base_token_amount']}")
                print(f"   USDT:  {data['quote_token_amount']}")
                print(f"\n📈 Liquidity: {data['liquidity']}")
                print(f"💵 Total Value: ${data['total_value_usd']}")
            else:
                error = await resp.text()
                print(f"❌ Error: {resp.status}")
                print(error)
    
    # Test 2: I have 30.34 USDT, how much COAI do I need?
    payload2 = {
        "connector": "pancakeswap",
        "network": "ethereum-bsc",
        "pool_address": "0xbc0E5A205D729299D93973d634E2507CD8b625A3",
        "lower_price": 0.4262,
        "upper_price": 0.4369,
        "quote_token_amount": 30.34
    }
    
    print("\n" + "=" * 80)
    print("TEST 2: Calculate COAI needed for 30.34 USDT")
    print("=" * 80)
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload2, auth=auth) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✅ Success!")
                print(f"\n📊 Current Price: ${data['current_price']}")
                print(f"📏 Range: ${data['lower_price']} - ${data['upper_price']}")
                print(f"🎯 In Range: {data['in_range']}")
                print(f"\n💰 Token Amounts Needed:")
                print(f"   COAI:  {data['base_token_amount']}")
                print(f"   USDT:  {data['quote_token_amount']}")
                print(f"\n📈 Liquidity: {data['liquidity']}")
                print(f"💵 Total Value: ${data['total_value_usd']}")
            else:
                error = await resp.text()
                print(f"❌ Error: {resp.status}")
                print(error)
    
    print("\n" + "=" * 80)
    print("🎉 NOW YOU CAN OPEN POSITION WITH CONFIDENCE!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_quote())

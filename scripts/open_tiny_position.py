"""
Open a small position with 0.6 USDT + 1.20 COAI
"""
import asyncio
import aiohttp
from aiohttp import BasicAuth

API_URL = "http://localhost:8000"
AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")

POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
CONNECTOR = "pancakeswap"
NETWORK = "ethereum-bsc"
WALLET_ADDRESS = "0x3ca5dB9dD9D8536ab9005c8Fb6B782909e0Be420"


async def main():
    print("\n🎯 Opening Small Position with Available Funds")
    print("="*60)
    
    current_price = 0.432327
    range_width = 2.5
    half_range = range_width / 2.0
    lower_price = current_price * (1 - half_range / 100)
    upper_price = current_price * (1 + half_range / 100)
    
    print(f"\n📊 Position Parameters:")
    print(f"   Current Price: ${current_price}")
    print(f"   Lower Price: ${lower_price:.6f}")
    print(f"   Upper Price: ${upper_price:.6f}")
    print(f"   Range Width: {range_width}%")
    
    # Amounts from quote
    coai_amount = "1.2023"
    usdt_amount = "0.6"
    
    print(f"\n💰 Using:")
    print(f"   COAI: {coai_amount}")
    print(f"   USDT: {usdt_amount}")
    
    url = f"{API_URL}/gateway/clmm/open"
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "pool_address": POOL_ADDRESS,
        "lower_price": lower_price,
        "upper_price": upper_price,
        "base_token_amount": coai_amount,
        "quote_token_amount": usdt_amount,
        "wallet_address": WALLET_ADDRESS,
        "slippage_pct": "1.0"
    }
    
    print(f"\n🚀 Opening position...")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"\n✅ Position opened successfully!")
                print(f"   Transaction: {result.get('transaction_hash')}")
                print(f"   Position ID: {result.get('position_id', 'Check on PancakeSwap')}")
                print(f"\n🔗 View on BSCScan:")
                print(f"   https://bscscan.com/tx/{result.get('transaction_hash')}")
            else:
                error = await resp.text()
                print(f"\n❌ Failed to open position:")
                print(f"   {error}")


if __name__ == "__main__":
    asyncio.run(main())

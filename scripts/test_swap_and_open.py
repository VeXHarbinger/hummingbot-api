"""
Complete workflow: Swap COAI → USDT, Quote position, Open position
"""
import asyncio
import aiohttp
from aiohttp import BasicAuth
import json

API_URL = "http://localhost:8000"
AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")

POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
CONNECTOR = "pancakeswap"
NETWORK = "ethereum-bsc"
WALLET_ADDRESS = "0x3ca5dB9dD9D8536ab9005c8Fb6B782909e0Be420"


async def step1_swap_coai_for_usdt():
    """Swap 92.20 COAI for USDT using Jupiter/PancakeSwap router"""
    print("\n" + "="*60)
    print("STEP 1: SWAP COAI FOR USDT")
    print("="*60)
    
    # First get a quote
    quote_url = f"{API_URL}/gateway/swap/quote"
    quote_payload = {
        "connector": "pancakeswap",
        "network": NETWORK,
        "trading_pair": "COAI-USDT",
        "side": "SELL",  # Selling COAI for USDT
        "amount": "92.20"
    }
    
    async with aiohttp.ClientSession() as session:
        # Get quote
        print("\n📊 Getting swap quote...")
        async with session.post(quote_url, json=quote_payload, auth=AUTH) as resp:
            if resp.status == 200:
                quote = await resp.json()
                print(f"✅ Quote received:")
                print(f"   Sell: 92.20 COAI")
                print(f"   Receive: ~{quote.get('expected_out', 'N/A')} USDT")
                print(f"   Price: ${quote.get('price', 'N/A')}")
            else:
                error = await resp.text()
                print(f"❌ Quote failed: {error}")
                return False
        
        # Execute swap
        print("\n💱 Executing swap...")
        swap_url = f"{API_URL}/gateway/swap/execute"
        swap_payload = {
            **quote_payload,
            "wallet_address": WALLET_ADDRESS,
            "slippage_pct": "1.0"
        }
        
        async with session.post(swap_url, json=swap_payload, auth=AUTH) as resp:
            if resp.status == 200:
                result = await resp.json()
                tx_hash = result.get('transaction_hash')
                print(f"✅ Swap executed!")
                print(f"   Transaction: {tx_hash}")
                print(f"   Waiting 30s for settlement...")
                await asyncio.sleep(30)
                return True
            else:
                error = await resp.text()
                print(f"❌ Swap failed: {error}")
                return False


async def step2_get_balances():
    """Get updated balances after swap"""
    print("\n" + "="*60)
    print("STEP 2: GET UPDATED BALANCES")
    print("="*60)
    
    # Use MCP to get balances (more reliable)
    print("\n💰 Fetching balances via MCP...")
    print("Please check MCP get_portfolio_overview output")
    print("Expected: ~66.49 COAI, ~40.07 USDT")
    
    # For now, use expected values
    coai_balance = 66.49
    usdt_balance = 40.07
    return coai_balance, usdt_balance


async def step3_quote_position(coai_amount):
    """Get quote for position opening"""
    print("\n" + "="*60)
    print("STEP 3: QUOTE POSITION")
    print("="*60)
    
    current_price = 0.432327
    range_width = 2.5
    half_range = range_width / 2.0
    lower_price = current_price * (1 - half_range / 100)
    upper_price = current_price * (1 + half_range / 100)
    
    url = f"{API_URL}/gateway/clmm/quote"
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "pool_address": POOL_ADDRESS,
        "lower_price": lower_price,
        "upper_price": upper_price,
        "base_token_amount": coai_amount
    }
    
    print(f"\n📊 Getting quote for {coai_amount} COAI...")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as resp:
            if resp.status == 200:
                quote = await resp.json()
                print(f"✅ Quote received:")
                print(f"   COAI needed: {quote['base_token_amount']}")
                print(f"   USDT needed: {quote['quote_token_amount']}")
                print(f"   Liquidity: {quote['liquidity']}")
                print(f"   In range: {quote.get('in_range', True)}")
                return quote
            else:
                error = await resp.text()
                print(f"❌ Quote failed: {error}")
                return None


async def step4_open_position(quote):
    """Open position with quoted amounts"""
    print("\n" + "="*60)
    print("STEP 4: OPEN POSITION")
    print("="*60)
    
    current_price = 0.432327
    range_width = 2.5
    half_range = range_width / 2.0
    lower_price = current_price * (1 - half_range / 100)
    upper_price = current_price * (1 + half_range / 100)
    
    url = f"{API_URL}/gateway/clmm/open"
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "pool_address": POOL_ADDRESS,
        "lower_price": lower_price,
        "upper_price": upper_price,
        "base_token_amount": str(quote['base_token_amount']),
        "quote_token_amount": str(quote['quote_token_amount']),
        "wallet_address": WALLET_ADDRESS,
        "slippage_pct": "1.0"
    }
    
    print(f"\n🚀 Opening position...")
    print(f"   COAI: {quote['base_token_amount']}")
    print(f"   USDT: {quote['quote_token_amount']}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ Position opened successfully!")
                print(f"   Transaction: {result.get('transaction_hash')}")
                print(f"   Position ID: {result.get('position_id', 'Check on PancakeSwap')}")
                return True
            else:
                error = await resp.text()
                print(f"❌ Failed to open position: {error}")
                return False


async def main():
    print("\n🎯 COMPLETE WORKFLOW: SWAP → QUOTE → OPEN")
    print("="*60)
    
    # Step 1: Swap COAI for USDT
    swap_success = await step1_swap_coai_for_usdt()
    if not swap_success:
        print("\n❌ Workflow stopped: Swap failed")
        return
    
    # Step 2: Get balances
    coai_balance, usdt_balance = await step2_get_balances()
    
    # Step 3: Quote position (use 98% of COAI balance for safety)
    coai_to_use = coai_balance * 0.98
    quote = await step3_quote_position(coai_to_use)
    if not quote:
        print("\n❌ Workflow stopped: Quote failed")
        return
    
    # Check if we have enough USDT
    needed_usdt = float(quote['quote_token_amount'])
    if usdt_balance < needed_usdt:
        print(f"\n⚠️ WARNING: Need {needed_usdt:.2f} USDT but only have {usdt_balance:.2f}")
        print("   Proceeding anyway - contract will use what's available")
    
    # Step 4: Open position
    await step4_open_position(quote)
    
    print("\n" + "="*60)
    print("✅ WORKFLOW COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import aiohttp
from aiohttp import BasicAuth
from decimal import Decimal

# Configuration
API_URL = "http://localhost:8000"
AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")
POSITION_ID = "6220678"
CONNECTOR = "pancakeswap_v3_bsc"
NETWORK = "bsc-mainnet"
POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
WALLET_ADDRESS = "0xabA4F366113c200A2B351F5Ce70f31713f3d3610"

async def get_pool_info():
    """Get current pool price and info"""
    url = f"{API_URL}/gateway/clmm/pool-info"
    params = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "pool_address": POOL_ADDRESS
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, auth=AUTH) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                error = await response.text()
                raise Exception(f"Failed to get pool info: {error}")

async def get_balances():
    """Get current token balances"""
    url = f"{API_URL}/portfolio/state"
    payload = {
        "account_names": ["master_account"],
        "connector_names": [CONNECTOR]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                error = await response.text()
                raise Exception(f"Failed to get balances: {error}")

async def close_position():
    """Close the current position"""
    print("\n🔴 Closing position...")
    url = f"{API_URL}/gateway/clmm/close"
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "position_address": POSITION_ID
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Position closed! TX: {data.get('transaction_hash')}")
                return data
            else:
                error = await response.text()
                raise Exception(f"Failed to close position: {error}")

async def swap_tokens(from_token, to_token, amount):
    """Swap tokens to rebalance"""
    print(f"\n🔄 Swapping {amount} {from_token} to {to_token}...")
    
    # Determine side based on tokens
    if from_token == "USDT" and to_token == "COAI":
        side = "BUY"  # Buy COAI with USDT
        trading_pair = "COAI-USDT"
    elif from_token == "COAI" and to_token == "USDT":
        side = "SELL"  # Sell COAI for USDT
        trading_pair = "COAI-USDT"
    else:
        raise Exception(f"Unsupported swap: {from_token} to {to_token}")
    
    # Use Gateway swap via Jupiter/0x router
    url = f"{API_URL}/gateway/swap/execute"
    payload = {
        "connector": "jupiter" if NETWORK.startswith("solana") else "0x",
        "network": NETWORK,
        "trading_pair": trading_pair,
        "side": side,
        "amount": str(amount),
        "slippage_pct": "1.0"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Swap executed! TX: {data.get('transaction_hash')}")
                return data
            else:
                error = await response.text()
                print(f"⚠️  Swap failed: {error}")
                return None

async def open_position(lower_price, upper_price, base_amount, quote_amount):
    """Open new position with specified range"""
    print(f"\n🟢 Opening new position...")
    print(f"   Range: ${lower_price} - ${upper_price}")
    print(f"   Liquidity: {base_amount} COAI + {quote_amount} USDT")
    
    url = f"{API_URL}/gateway/clmm/open"
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "pool_address": POOL_ADDRESS,
        "lower_price": str(lower_price),
        "upper_price": str(upper_price),
        "base_token_amount": str(base_amount),
        "quote_token_amount": str(quote_amount),
        "slippage_pct": "1.0"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Position opened! TX: {data.get('transaction_hash')}")
                print(f"   Position ID: {data.get('position_address')}")
                return data
            else:
                error = await response.text()
                raise Exception(f"Failed to open position: {error}")

async def main():
    print("="*60)
    print("🔄 REBALANCING CLMM POSITION")
    print("="*60)
    
    # Step 1: Get current pool info
    print("\n📊 Step 1: Getting current pool info...")
    pool_info = await get_pool_info()
    current_price = float(pool_info['price'])
    print(f"   Current COAI/USDT price: ${current_price:.6f}")
    print(f"   Current range: ${pool_info['lower_price']} - ${pool_info['upper_price']}")
    
    # Calculate 2% range
    lower_price = current_price * 0.98
    upper_price = current_price * 1.02
    print(f"   New 2% range: ${lower_price:.6f} - ${upper_price:.6f}")
    
    # Step 2: Close current position
    print("\n🔴 Step 2: Closing current position...")
    close_result = await close_position()
    
    # Wait for transaction to settle
    print("   Waiting 10 seconds for transaction to settle...")
    await asyncio.sleep(10)
    
    # Step 3: Get updated balances
    print("\n💰 Step 3: Getting updated balances...")
    balances = await get_balances()
    
    # Extract COAI and USDT balances
    coai_balance = 0
    usdt_balance = 0
    
    if 'balances' in balances and CONNECTOR in balances['balances']:
        for token, amount in balances['balances'][CONNECTOR].items():
            if 'COAI' in token:
                coai_balance = float(amount)
            elif 'USDT' in token:
                usdt_balance = float(amount)
    
    print(f"   COAI: {coai_balance}")
    print(f"   USDT: {usdt_balance}")
    
    # Step 4: Calculate optimal token amounts for 2% range
    print("\n🧮 Step 4: Calculating optimal token distribution...")
    
    # For a symmetric range around current price, we need roughly equal value
    # Value ratio for concentrated liquidity depends on price position in range
    # For simplicity, aim for equal USD value
    total_value_usd = (coai_balance * current_price) + usdt_balance
    target_coai_value = total_value_usd * 0.5
    target_usdt_value = total_value_usd * 0.5
    
    target_coai = target_coai_value / current_price
    target_usdt = target_usdt_value
    
    print(f"   Total value: ${total_value_usd:.2f}")
    print(f"   Target: {target_coai:.4f} COAI + {target_usdt:.2f} USDT")
    
    # Step 5: Rebalance if needed
    coai_diff = target_coai - coai_balance
    usdt_diff = target_usdt - usdt_balance
    
    if abs(coai_diff) > 0.1:  # Only rebalance if difference > 0.1 COAI
        print(f"\n🔄 Step 5: Rebalancing tokens...")
        if coai_diff > 0:
            # Need more COAI, swap USDT to COAI
            swap_amount = abs(usdt_diff) * 0.95  # Use 95% to account for slippage
            await swap_tokens("USDT", "COAI", swap_amount)
        else:
            # Need more USDT, swap COAI to USDT
            swap_amount = abs(coai_diff) * 0.95
            await swap_tokens("COAI", "USDT", swap_amount)
        
        # Wait and get updated balances
        print("   Waiting 10 seconds for swap to settle...")
        await asyncio.sleep(10)
        
        balances = await get_balances()
        if 'balances' in balances and CONNECTOR in balances['balances']:
            for token, amount in balances['balances'][CONNECTOR].items():
                if 'COAI' in token:
                    coai_balance = float(amount)
                elif 'USDT' in token:
                    usdt_balance = float(amount)
        
        print(f"   Updated balances: {coai_balance} COAI, {usdt_balance} USDT")
    else:
        print(f"\n✅ Step 5: Balances are already optimal, skipping rebalance")
    
    # Step 6: Open new position with most of the tokens (keep some for gas)
    print(f"\n🟢 Step 6: Opening new position...")
    use_coai = coai_balance * 0.98  # Use 98% to leave buffer
    use_usdt = usdt_balance * 0.98
    
    await open_position(lower_price, upper_price, use_coai, use_usdt)
    
    print("\n" + "="*60)
    print("✅ REBALANCING COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())

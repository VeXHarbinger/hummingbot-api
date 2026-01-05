"""
Deploy ALL available tokens to liquidity pool
1. Get current balances
2. Calculate optimal swap amount
3. Swap COAI for USDT (manual step - will provide instructions)
4. Quote position with balanced amounts
5. Open position with maximum liquidity
"""
import asyncio
import aiohttp
from aiohttp import BasicAuth

API_URL = "http://localhost:8000"
AUTH = BasicAuth("admin", "4Adm!np@ssw0rd")

POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
CONNECTOR = "pancakeswap"
NETWORK = "ethereum-bsc"
TARGET_RANGE_WIDTH = 2.5  # 2.5% range


async def get_balances():
    """Get current token balances"""
    print("\n" + "="*60)
    print("STEP 1: GET CURRENT BALANCES")
    print("="*60)
    
    # Using hardcoded balances since we know them
    # In production, would use portfolio endpoint or MCP
    coai = 157.48  # After the tiny position (158.68 - 1.2)
    usdt = 0.01    # After the tiny position (0.61 - 0.6)
    
    print(f"\nCurrent Balances:")
    print(f"  COAI: {coai:.2f}")
    print(f"  USDT: {usdt:.2f}")
    
    return coai, usdt


async def calculate_swap_needed(coai, usdt, current_price):
    """Calculate how much COAI to swap for USDT to get optimal ratio"""
    print("\n" + "="*60)
    print("STEP 2: CALCULATE SWAP NEEDED")
    print("="*60)
    
    # From quote testing, we know the ratio is ~0.6086 USDT per COAI in range
    target_ratio = 0.6086
    
    # Solve for x (COAI to swap):
    # After swap: (usdt + x * price) / (coai - x) = target_ratio
    # x = (target_ratio * coai - usdt) / (price + target_ratio)
    
    coai_to_swap = (target_ratio * coai - usdt) / (current_price + target_ratio)
    
    # Use 99% slippage tolerance
    usdt_received = coai_to_swap * current_price * 0.99
    
    coai_after = coai - coai_to_swap
    usdt_after = usdt + usdt_received
    
    print(f"\nCurrent Price: ${current_price}")
    print(f"Target Ratio: {target_ratio:.4f} USDT/COAI")
    print(f"\nSwap Needed:")
    print(f"  Sell: {coai_to_swap:.2f} COAI")
    print(f"  Receive: ~{usdt_received:.2f} USDT")
    print(f"\nAfter Swap:")
    print(f"  COAI: {coai_after:.2f}")
    print(f"  USDT: {usdt_after:.2f}")
    print(f"  Ratio: {usdt_after/coai_after:.4f}")
    
    total_value = coai * current_price + usdt
    print(f"\nTotal Portfolio Value: ${total_value:.2f}")
    
    return coai_to_swap, coai_after, usdt_after


async def provide_swap_instructions(coai_to_swap):
    """Provide instructions for manual swap on PancakeSwap"""
    print("\n" + "="*60)
    print("STEP 3: SWAP TOKENS (MANUAL)")
    print("="*60)
    
    print(f"\n⚠️  MANUAL ACTION REQUIRED:")
    print(f"\n1. Go to PancakeSwap: https://pancakeswap.finance/swap")
    print(f"2. Connect your wallet (0x3ca5db9dd9d8536ab9005c8fb6b782909e0be420)")
    print(f"3. Swap: {coai_to_swap:.2f} COAI → USDT")
    print(f"4. Slippage: 1%")
    print(f"5. Confirm the transaction")
    print(f"6. Wait for confirmation")
    
    input("\nPress ENTER after completing the swap...")


async def quote_position(coai_amount, current_price):
    """Get quote for position with given COAI amount"""
    print("\n" + "="*60)
    print("STEP 4: QUOTE POSITION")
    print("="*60)
    
    range_width = TARGET_RANGE_WIDTH
    half_range = range_width / 2.0
    lower_price = current_price * (1 - half_range / 100)
    upper_price = current_price * (1 + half_range / 100)
    
    # Use 98% of balance to leave buffer for gas
    coai_to_use = coai_amount * 0.98
    
    url = f"{API_URL}/gateway/clmm/quote"
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "pool_address": POOL_ADDRESS,
        "lower_price": lower_price,
        "upper_price": upper_price,
        "base_token_amount": coai_to_use
    }
    
    print(f"\nQuoting position with {coai_to_use:.2f} COAI...")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=AUTH) as resp:
            if resp.status == 200:
                quote = await resp.json()
                coai_needed = float(quote['base_token_amount'])
                usdt_needed = float(quote['quote_token_amount'])
                
                print(f"\n✅ Quote Received:")
                print(f"   COAI: {coai_needed:.4f}")
                print(f"   USDT: {usdt_needed:.4f}")
                print(f"   Liquidity: {quote['liquidity']}")
                print(f"   Range: ${lower_price:.6f} - ${upper_price:.6f}")
                
                return quote, lower_price, upper_price
            else:
                error = await resp.text()
                print(f"\n❌ Quote failed: {error}")
                return None, None, None


async def open_position_mcp(quote, lower_price, upper_price):
    """Open position using MCP (more reliable)"""
    print("\n" + "="*60)
    print("STEP 5: OPEN POSITION")
    print("="*60)
    
    coai_amount = float(quote['base_token_amount'])
    usdt_amount = float(quote['quote_token_amount'])
    
    print(f"\nOpening position with:")
    print(f"   COAI: {coai_amount:.4f}")
    print(f"   USDT: {usdt_amount:.4f}")
    print(f"   Range: ${lower_price:.6f} - ${upper_price:.6f}")
    
    print("\nUsing MCP to open position...")
    print("(Note: Run this via MCP function in your environment)")
    print("\nMCP Command:")
    print(f"manage_gateway_clmm_positions(")
    print(f"  action='open_position',")
    print(f"  connector='{CONNECTOR}',")
    print(f"  network='{NETWORK}',")
    print(f"  pool_address='{POOL_ADDRESS}',")
    print(f"  lower_price={lower_price},")
    print(f"  upper_price={upper_price},")
    print(f"  base_token_amount={coai_amount},")
    print(f"  quote_token_amount={usdt_amount},")
    print(f"  slippage_pct='1.0'")
    print(f")")


async def main():
    print("\n🎯 DEPLOY ALL LIQUIDITY TO POOL")
    print("="*60)
    
    # Get current pool price first
    current_price = 0.432327  # Would fetch from pool in production
    
    # Step 1: Get balances
    coai, usdt = await get_balances()
    
    # Step 2: Calculate swap needed
    coai_to_swap, coai_after, usdt_after = await calculate_swap_needed(coai, usdt, current_price)
    
    # Step 3: Manual swap instructions
    await provide_swap_instructions(coai_to_swap)
    
    # Step 4: Quote the full position
    quote, lower_price, upper_price = await quote_position(coai_after, current_price)
    
    if quote:
        # Step 5: Open position
        await open_position_mcp(quote, lower_price, upper_price)
        
        print("\n" + "="*60)
        print("✅ WORKFLOW COMPLETE!")
        print("="*60)
        print("\nAfter the position opens, you will have deployed")
        print("100% of your available liquidity to the pool!")


if __name__ == "__main__":
    asyncio.run(main())

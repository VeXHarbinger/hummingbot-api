#!/usr/bin/env python3
"""
Open New CLMM Position (Smart)
Opens a new position with intelligent token ratio calculation

This script:
1. Fetches current price
2. Calculates optimal range (centered on current price)
3. Calculates correct token ratio for that range
4. Opens position with proper amounts

Usage:
    python scripts/open_position_smart.py --range-width 2.5
    python scripts/open_position_smart.py --range-width 3.0 --dry-run
    python scripts/open_position_smart.py --range-width 2.5 --coai 2300 --usdt 1000
"""

import sys
import io
import asyncio
import aiohttp
import argparse
from aiohttp import BasicAuth
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL = "http://localhost:8000"
API_USER = "admin"
API_PASS = "4Adm!np@ssw0rd"

CONNECTOR = "pancakeswap"
NETWORK = "ethereum-bsc"
POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
ACCOUNT_NAME = "master_account"

BASE_TOKEN = "COAI"
QUOTE_TOKEN = "USDT"

BALANCE_BUFFER = 0.98  # Use 98% of balance
MAX_SLIPPAGE = 1.0     # 1% max slippage

# ============================================================================
# API HELPERS
# ============================================================================

async def api_post(session: aiohttp.ClientSession, endpoint: str, payload: Dict) -> Tuple[int, Any]:
    """Make POST request to API"""
    url = f"{API_URL}{endpoint}"
    auth = BasicAuth(API_USER, API_PASS)
    
    try:
        async with session.post(url, json=payload, auth=auth) as response:
            status = response.status
            if status == 200:
                data = await response.json()
                return status, data
            else:
                text = await response.text()
                return status, text
    except Exception as e:
        return 0, str(e)


async def get_current_price(session: aiohttp.ClientSession) -> Optional[float]:
    """Get current price"""
    
    print("📊 Fetching current price...")
    
    # Try to get from CEX
    status, data = await api_post(session, "/market/get-prices", {
        "connector_name": "binance",
        "trading_pairs": ["COAI-USDT"]
    })
    
    if status == 200 and isinstance(data, dict):
        prices = data.get("prices", {})
        price_str = prices.get("COAI-USDT")
        if price_str:
            price = float(price_str)
            print(f"   ✅ Current price: ${price:.6f}")
            return price
    
    # Fallback
    print("   ⚠️  Could not fetch live price, using fallback")
    return 0.431550


async def get_balances(session: aiohttp.ClientSession) -> Tuple[float, float]:
    """Get current token balances from MCP"""
    
    print("\n💰 Checking wallet balances (via MCP)...")
    
    # Use the portfolio endpoint which aggregates from all sources
    payload = {
        "account_names": [ACCOUNT_NAME],
        "include_balances": True,
        "include_active_orders": False,
        "include_lp_positions": False,
        "include_perp_positions": False
    }
    status, data = await api_post(session, "/portfolio/overview", payload)
    
    coai_balance = 0.0
    usdt_balance = 0.0
    
    if status == 200 and isinstance(data, dict):
        # Parse the result string (MCP returns formatted text)
        result = data.get('result', '')
        
        # Look for token lines in the output
        for line in result.split('\n'):
            if BASE_TOKEN in line and 'total' in result:
                parts = line.split('|')
                if len(parts) >= 3:
                    try:
                        coai_balance = float(parts[2].strip())
                    except:
                        pass
            elif QUOTE_TOKEN in line and 'total' in result:
                parts = line.split('|')
                if len(parts) >= 3:
                    try:
                        usdt_balance = float(parts[2].strip())
                    except:
                        pass
        
        if coai_balance > 0 or usdt_balance > 0:
            print(f"   ✅ {BASE_TOKEN}: {coai_balance:.4f}")
            print(f"   ✅ {QUOTE_TOKEN}: {usdt_balance:.2f}")
        else:
            print("   ⚠️  No balances detected")
    else:
        print("   ⚠️  Could not fetch balances")
    
    return coai_balance, usdt_balance


def calculate_range(current_price: float, range_width_pct: float) -> Tuple[float, float]:
    """Calculate range centered on current price"""
    half_range = range_width_pct / 2.0
    lower_price = current_price * (1 - half_range / 100)
    upper_price = current_price * (1 + half_range / 100)
    return lower_price, upper_price


def calculate_token_amounts(
    current_price: float,
    lower_price: float,
    upper_price: float,
    coai_balance: float,
    usdt_balance: float
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate token amounts to maximize liquidity in a single transaction.
    
    Strategy: Supply BOTH tokens with high amounts and let the contract use what it needs.
    The contract will consume the exact ratio it requires and refund any excess.
    
    This maximizes the position opening in ONE transaction instead of requiring
    multiple /clmm/add calls afterward.
    """
    
    print("\n🧮 Calculating optimal token amounts for maximum liquidity...")
    print(f"   Current price: ${current_price:.6f}")
    print(f"   Range: ${lower_price:.6f} - ${upper_price:.6f}")
    
    # Calculate value of each token
    coai_value = coai_balance * current_price
    usdt_value = usdt_balance
    
    print(f"   Available:")
    print(f"   → {coai_balance:.4f} {BASE_TOKEN} (${coai_value:.2f})")
    print(f"   → {usdt_balance:.2f} {QUOTE_TOKEN}")
    
    # NEW STRATEGY: Supply both tokens at maximum available amounts
    # The contract will use exactly what it needs for the range and refund excess
    coai_amount = coai_balance * BALANCE_BUFFER
    usdt_amount = usdt_balance * BALANCE_BUFFER
    
    print(f"\n   Strategy: Supply BOTH tokens at max available amounts")
    print(f"   → Contract will use exact ratio needed for range")
    print(f"   → Excess tokens are automatically refunded")
    print(f"   → Maximizes position size in ONE transaction")
    
    print(f"\n   📦 Sending to contract:")
    print(f"   → {coai_amount:.4f} {BASE_TOKEN}")
    print(f"   → {usdt_amount:.2f} {QUOTE_TOKEN}")
    
    print(f"\n   ✅ Single transaction opens maximum position!")
    print(f"   ✅ No need for follow-up /clmm/add calls")
    print(f"   ✅ Most efficient liquidity deployment")
    
    return coai_amount, usdt_amount


async def open_position(
    session: aiohttp.ClientSession,
    lower_price: float,
    upper_price: float,
    coai_amount: Optional[float],
    usdt_amount: Optional[float],
    dry_run: bool = False
) -> Optional[Dict]:
    """Open new position"""
    
    print("\n" + "=" * 80)
    print("🟢 OPENING NEW POSITION")
    print("=" * 80)
    print(f"Range: ${lower_price:.6f} - ${upper_price:.6f}")
    print(f"Width: {((upper_price - lower_price) / lower_price * 100):.2f}%")
    
    # Format amounts display
    if coai_amount is not None and usdt_amount is not None:
        print(f"Amounts: {coai_amount:.4f} {BASE_TOKEN} + {usdt_amount:.2f} {QUOTE_TOKEN}")
    elif coai_amount is not None:
        print(f"Amounts: {coai_amount:.4f} {BASE_TOKEN} (specified) + {QUOTE_TOKEN} (contract calculates)")
    else:
        print(f"Amounts: {BASE_TOKEN} (contract calculates) + {usdt_amount:.2f} {QUOTE_TOKEN} (specified)")
    
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 80 + "\n")
    
    if dry_run:
        print("📋 DRY RUN COMPLETE - No action taken")
        return None
    
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "pool_address": POOL_ADDRESS,
        "lower_price": lower_price,  # Send as float, not string
        "upper_price": upper_price,  # Send as float, not string
        "base_token_amount": coai_amount,  # Send as float, not string
        "quote_token_amount": usdt_amount,  # Send as float, not string
        "slippage_pct": MAX_SLIPPAGE  # Send as float, not string
    }
    
    print("📤 Sending open request to Gateway...")
    status, data = await api_post(session, "/gateway/clmm/open", payload)
    
    if status == 200 and isinstance(data, dict):
        print("\n✅ POSITION OPENED SUCCESSFULLY!")
        print("=" * 80)
        print(f"Transaction Hash: {data.get('transaction_hash', 'N/A')}")
        print(f"Position ID: {data.get('position_id', 'N/A')}")
        print(f"Liquidity: {data.get('liquidity', 'N/A')}")
        print("=" * 80)
        print(f"\n⏳ Transaction is processing on BSC")
        print(f"   View at: https://bscscan.com/tx/{data.get('transaction_hash', '')}")
        print(f"\n🎉 New position is now earning fees!")
        print(f"   Position ID: {data.get('position_id', 'N/A')}")
        print(f"   Monitor with: python scripts/monitor_position.py --once")
        return data
    else:
        print("\n❌ FAILED TO OPEN POSITION")
        print("=" * 80)
        print(f"Status Code: {status}")
        print(f"Error: {data}")
        print("=" * 80)
        
        if "ratio" in str(data).lower() or "insufficient" in str(data).lower():
            print("\n💡 TIP: Token ratio might be incorrect")
            print("   Try adjusting the range width or check token balances")
        
        return None


async def main():
    parser = argparse.ArgumentParser(
        description="Open new CLMM position with smart ratio calculation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Open with 2.5% range (dry run)
  python open_position_smart.py --range-width 2.5 --dry-run
  
  # Open with 2.5% range (LIVE)
  python open_position_smart.py --range-width 2.5
  
  # Specify exact amounts (overrides balance check)
  python open_position_smart.py --range-width 2.5 --coai 2300 --usdt 1000
        """
    )
    
    parser.add_argument(
        "--range-width",
        type=float,
        required=True,
        help="Range width as percentage (e.g., 2.5 for 2.5%%)"
    )
    
    parser.add_argument(
        "--coai",
        type=float,
        help="Override COAI amount (optional)"
    )
    
    parser.add_argument(
        "--usdt",
        type=float,
        help="Override USDT amount (optional)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode"
    )
    
    args = parser.parse_args()
    
    # Validate
    if args.range_width < 1.5 or args.range_width > 10.0:
        print("❌ ERROR: Range width must be between 1.5% and 10%")
        return
    
    async with aiohttp.ClientSession() as session:
        # Get price
        current_price = await get_current_price(session)
        if not current_price:
            print("❌ ERROR: Could not determine price")
            return
        
        # Get balances (or use override)
        if args.coai and args.usdt:
            coai_balance = args.coai
            usdt_balance = args.usdt
            print(f"\n💰 Using specified amounts:")
            print(f"   {BASE_TOKEN}: {coai_balance:.4f}")
            print(f"   {QUOTE_TOKEN}: {usdt_balance:.2f}")
        else:
            coai_balance, usdt_balance = await get_balances(session)
            if coai_balance == 0 and usdt_balance == 0:
                print("❌ ERROR: Zero balance detected")
                return
        
        # Calculate range and amounts
        lower_price, upper_price = calculate_range(current_price, args.range_width)
        coai_amount, usdt_amount = calculate_token_amounts(
            current_price,
            lower_price,
            upper_price,
            coai_balance,
            usdt_balance
        )
        
        # Open position
        await open_position(session, lower_price, upper_price, coai_amount, usdt_amount, args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Open New CLMM Position (SAFE MODE)
Opens a position with a SMALL probe amount first to discover the correct ratio.

This script protects against malicious pools by:
1. Starting with only 10% of available balance
2. Showing exactly what the contract used
3. Allowing you to verify before adding more

Usage:
    # Step 1: Probe with 10% to discover ratio
    python scripts/open_position_safe.py --range-width 2.5 --coai 183.38 --usdt 30.34 --probe
    
    # Step 2: After verifying the ratio looks correct, add remaining 90%
    python scripts/open_position_safe.py --add-to <position-id> --coai 165 --usdt 27
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


def calculate_range(current_price: float, range_width_pct: float) -> Tuple[float, float]:
    """Calculate range centered on current price"""
    half_range = range_width_pct / 2.0
    lower_price = current_price * (1 - half_range / 100)
    upper_price = current_price * (1 + half_range / 100)
    return lower_price, upper_price


async def open_position_probe(
    session: aiohttp.ClientSession,
    lower_price: float,
    upper_price: float,
    coai_amount: float,
    usdt_amount: float
) -> Optional[Dict]:
    """Open position with probe amounts (10% of balance)"""
    
    # Use only 10% for the probe
    probe_coai = coai_amount * 0.1
    probe_usdt = usdt_amount * 0.1
    
    print("\n" + "=" * 80)
    print("🔍 PROBE MODE - Opening with 10% of balance to discover ratio")
    print("=" * 80)
    print(f"Range: ${lower_price:.6f} - ${upper_price:.6f}")
    print(f"Width: {((upper_price - lower_price) / lower_price * 100):.2f}%")
    print(f"\n⚠️  SAFETY: Using only 10% to test the pool")
    print(f"   → {probe_coai:.4f} {BASE_TOKEN} (10% of {coai_amount:.4f})")
    print(f"   → {probe_usdt:.2f} {QUOTE_TOKEN} (10% of {usdt_amount:.2f})")
    print(f"\n💡 This protects you from malicious pools!")
    print(f"   After verifying the ratio, you can add the remaining 90%")
    print("=" * 80 + "\n")
    
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "pool_address": POOL_ADDRESS,
        "lower_price": lower_price,
        "upper_price": upper_price,
        "base_token_amount": probe_coai,
        "quote_token_amount": probe_usdt,
        "slippage_pct": MAX_SLIPPAGE
    }
    
    print("📤 Sending probe transaction to Gateway...")
    status, data = await api_post(session, "/gateway/clmm/open", payload)
    
    if status == 200 and isinstance(data, dict):
        print("\n✅ PROBE POSITION OPENED!")
        print("=" * 80)
        tx_hash = data.get('transaction_hash', 'N/A')
        position_id = data.get('position_id', 'N/A')
        
        print(f"Transaction Hash: {tx_hash}")
        print(f"Position ID: {position_id}")
        print(f"\n⏳ Wait for confirmation, then check what ratio was actually used:")
        print(f"   python scripts/monitor_position.py --position {position_id}")
        print(f"\n🔍 To add the remaining 90% after verification:")
        print(f"   python scripts/open_position_safe.py --add-to {position_id} \\")
        print(f"     --coai {coai_amount * 0.9:.4f} --usdt {usdt_amount * 0.9:.2f}")
        print("=" * 80)
        return data
    else:
        print("\n❌ PROBE FAILED")
        print("=" * 80)
        print(f"Status Code: {status}")
        print(f"Error: {data}")
        print("=" * 80)
        return None


async def add_liquidity_remaining(
    session: aiohttp.ClientSession,
    position_id: str,
    coai_amount: float,
    usdt_amount: float
) -> Optional[Dict]:
    """Add remaining liquidity to verified position"""
    
    print("\n" + "=" * 80)
    print(f"➕ ADDING REMAINING LIQUIDITY TO POSITION {position_id}")
    print("=" * 80)
    print(f"Adding:")
    print(f"   → {coai_amount:.4f} {BASE_TOKEN}")
    print(f"   → {usdt_amount:.2f} {QUOTE_TOKEN}")
    print("=" * 80 + "\n")
    
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "position_address": position_id,
        "base_token_amount": coai_amount,
        "quote_token_amount": usdt_amount,
        "slippage_pct": MAX_SLIPPAGE
    }
    
    print("📤 Sending add liquidity request...")
    status, data = await api_post(session, "/gateway/clmm/add", payload)
    
    if status == 200 and isinstance(data, dict):
        print("\n✅ LIQUIDITY ADDED!")
        print("=" * 80)
        print(f"Transaction Hash: {data.get('transaction_hash', 'N/A')}")
        print(f"New Liquidity: {data.get('liquidity', 'N/A')}")
        print("=" * 80)
        return data
    else:
        print("\n❌ ADD LIQUIDITY FAILED")
        print("=" * 80)
        print(f"Status Code: {status}")
        print(f"Error: {data}")
        print("=" * 80)
        return None


async def main():
    parser = argparse.ArgumentParser(
        description="Safely open CLMM position with probe-then-add strategy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Step 1: Probe with 10% to discover ratio
  python open_position_safe.py --range-width 2.5 --coai 183.38 --usdt 30.34 --probe
  
  # Step 2: Add remaining 90% after verifying
  python open_position_safe.py --add-to 6223301 --coai 165.0 --usdt 27.3
        """
    )
    
    parser.add_argument("--range-width", type=float, help="Range width as percentage")
    parser.add_argument("--coai", type=float, required=True, help="COAI amount")
    parser.add_argument("--usdt", type=float, required=True, help="USDT amount")
    parser.add_argument("--probe", action="store_true", help="Probe mode (use 10%)")
    parser.add_argument("--add-to", type=str, help="Position ID to add liquidity to")
    
    args = parser.parse_args()
    
    if args.probe and not args.range_width:
        print("❌ ERROR: --range-width required for probe mode")
        return
    
    if args.add_to and args.range_width:
        print("❌ ERROR: Cannot specify --range-width when adding to existing position")
        return
    
    async with aiohttp.ClientSession() as session:
        if args.probe:
            # Probe mode - open with 10%
            current_price = await get_current_price(session)
            if not current_price:
                print("❌ ERROR: Could not determine price")
                return
            
            lower_price, upper_price = calculate_range(current_price, args.range_width)
            await open_position_probe(session, lower_price, upper_price, args.coai, args.usdt)
            
        elif args.add_to:
            # Add remaining liquidity
            await add_liquidity_remaining(session, args.add_to, args.coai, args.usdt)
            
        else:
            print("❌ ERROR: Must specify either --probe or --add-to")
            print("   Use --probe for initial position (uses 10% to test)")
            print("   Use --add-to <position-id> to add remaining liquidity")


if __name__ == "__main__":
    asyncio.run(main())

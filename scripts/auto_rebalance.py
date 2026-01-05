#!/usr/bin/env python3
"""
Automated CLMM Position Rebalancer
Closes current position and opens new one with optimal range centered on current price

This script handles the complete rebalancing workflow:
1. Close existing position (remove liquidity + collect fees)
2. Wait for transaction confirmation
3. Check balances
4. Calculate optimal token ratio
5. Open new position with 3% range

Usage:
    python scripts/auto_rebalance.py --position 6221178 --range-width 3.0
    python scripts/auto_rebalance.py --position 6221178 --range-width 3.0 --dry-run
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

# API Configuration
API_URL = "http://localhost:8000"
API_USER = "admin"
API_PASS = "4Adm!np@ssw0rd"

# Pool Configuration
POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
CONNECTOR = "pancakeswap_v3_bsc"
NETWORK = "bsc-mainnet"
ACCOUNT_NAME = "master_account"

# Token Configuration
BASE_TOKEN = "COAI"
QUOTE_TOKEN = "USDT"

# Safety Configuration
BALANCE_BUFFER = 0.98  # Use 98% of balance, keep 2% for gas
SETTLEMENT_WAIT = 5    # Seconds to wait for transaction confirmation (BSC is fast!)
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
    """Get current pool price from API"""
    
    print("📊 Fetching current price...")
    
    status, data = await api_post(session, "/market/get-prices", {
        "connector_name": "binance",  # Use centralized exchange for reliable price
        "trading_pairs": ["COAI-USDT"]
    })
    
    if status == 200 and isinstance(data, dict):
        prices = data.get("prices", {})
        price_str = prices.get("COAI-USDT")
        if price_str:
            price = float(price_str)
            print(f"   Current price: ${price:.6f}")
            return price
    
    # Fallback: Try to get from position data or estimate
    print("   ⚠️  Could not fetch live price, will use estimate")
    return None


async def close_position(session: aiohttp.ClientSession, position_id: str) -> Optional[Dict]:
    """Close existing position"""
    
    print(f"\n🔴 STEP 1: Closing position {position_id}")
    print("=" * 80)
    
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "position_address": position_id
    }
    
    status, data = await api_post(session, "/gateway/clmm/close", payload)
    
    if status == 200 and isinstance(data, dict):
        print(f"✅ Position closed successfully!")
        print(f"   Transaction: {data.get('transaction_hash', 'N/A')}")
        print(f"   Base returned: {data.get('base_token_amount', 'N/A')} {BASE_TOKEN}")
        print(f"   Quote returned: {data.get('quote_token_amount', 'N/A')} {QUOTE_TOKEN}")
        print(f"   Base fees: {data.get('base_fee_collected', 'N/A')} {BASE_TOKEN}")
        print(f"   Quote fees: {data.get('quote_fee_collected', 'N/A')} {QUOTE_TOKEN}")
        return data
    else:
        print(f"❌ Failed to close position!")
        print(f"   Status: {status}")
        print(f"   Error: {data}")
        return None


async def get_balances(session: aiohttp.ClientSession) -> Tuple[float, float]:
    """Get current token balances"""
    
    print(f"\n💰 STEP 2: Checking balances")
    print("=" * 80)
    
    payload = {"account_names": [ACCOUNT_NAME]}
    status, data = await api_post(session, "/portfolio/state", payload)
    
    coai_balance = 0.0
    usdt_balance = 0.0
    
    if status == 200 and isinstance(data, dict):
        balances = data.get('balances', {})
        
        for connector, tokens in balances.items():
            for token, amount in tokens.items():
                if BASE_TOKEN in token:
                    coai_balance = float(amount)
                    print(f"   {BASE_TOKEN}: {coai_balance:.4f}")
                elif QUOTE_TOKEN in token:
                    usdt_balance = float(amount)
                    print(f"   {QUOTE_TOKEN}: {usdt_balance:.2f}")
    else:
        print("   ⚠️  Could not fetch balances from API")
    
    if coai_balance == 0 and usdt_balance == 0:
        print("   ❌ ERROR: Zero balance detected!")
        
    return coai_balance, usdt_balance


def calculate_range(current_price: float, range_width_pct: float) -> Tuple[float, float]:
    """Calculate optimal range centered on current price"""
    
    # Range is centered around current price
    half_range = range_width_pct / 2.0
    lower_price = current_price * (1 - half_range / 100)
    upper_price = current_price * (1 + half_range / 100)
    
    return lower_price, upper_price


def calculate_token_ratio(
    current_price: float,
    lower_price: float,
    upper_price: float,
    coai_balance: float,
    usdt_balance: float
) -> Tuple[float, float]:
    """
    Calculate optimal token amounts for CLMM position.
    
    For concentrated liquidity, the ratio depends on where current price sits
    within the range. This is the CRITICAL calculation that prevents reverts.
    
    CLMM Math (simplified):
    - If price is at lower bound: Need ~100% quote token
    - If price is at upper bound: Need ~100% base token  
    - If price is in middle: Need both tokens
    
    The exact ratio follows: amount0/amount1 ≈ sqrt(price_upper/price) - sqrt(price/price_lower)
    """
    
    print(f"\n🧮 STEP 3: Calculating optimal token ratio")
    print("=" * 80)
    print(f"   Current price: ${current_price:.6f}")
    print(f"   Range: ${lower_price:.6f} - ${upper_price:.6f}")
    print(f"   Available: {coai_balance:.4f} {BASE_TOKEN} + {usdt_balance:.2f} {QUOTE_TOKEN}")
    
    # Calculate price position within range
    range_width = upper_price - lower_price
    price_position = (current_price - lower_price) / range_width
    
    print(f"   Price position in range: {price_position * 100:.1f}%")
    
    # Use simplified ratio calculation
    # For production, should use exact sqrt formula from CLMM math
    # But this approximation works well for narrow ranges
    
    if price_position < 0.33:
        # Price near lower bound - need more USDT
        ratio = 0.3  # 30% COAI, 70% USDT
        print(f"   Strategy: Price near LOWER edge → Use more {QUOTE_TOKEN}")
    elif price_position > 0.67:
        # Price near upper bound - need more COAI
        ratio = 0.7  # 70% COAI, 30% USDT
        print(f"   Strategy: Price near UPPER edge → Use more {BASE_TOKEN}")
    else:
        # Price in middle - balanced
        ratio = 0.5  # 50/50 split
        print(f"   Strategy: Price CENTERED → Balanced ratio")
    
    # Calculate actual amounts based on ratio
    total_value_in_usdt = (coai_balance * current_price) + usdt_balance
    
    # Apply balance buffer (keep 2% for gas)
    total_value_in_usdt *= BALANCE_BUFFER
    
    # Split based on ratio
    coai_value = total_value_in_usdt * ratio
    usdt_value = total_value_in_usdt * (1 - ratio)
    
    coai_amount = coai_value / current_price
    usdt_amount = usdt_value
    
    # Don't exceed available balances
    coai_amount = min(coai_amount, coai_balance * BALANCE_BUFFER)
    usdt_amount = min(usdt_amount, usdt_balance * BALANCE_BUFFER)
    
    print(f"\n   Optimal amounts:")
    print(f"   → {coai_amount:.4f} {BASE_TOKEN} (${coai_amount * current_price:.2f})")
    print(f"   → {usdt_amount:.2f} {QUOTE_TOKEN}")
    print(f"   Total value: ${(coai_amount * current_price) + usdt_amount:.2f}")
    
    return coai_amount, usdt_amount


async def open_position(
    session: aiohttp.ClientSession,
    lower_price: float,
    upper_price: float,
    coai_amount: float,
    usdt_amount: float
) -> Optional[Dict]:
    """Open new position with calculated parameters"""
    
    print(f"\n🟢 STEP 4: Opening new position")
    print("=" * 80)
    print(f"   Range: ${lower_price:.6f} - ${upper_price:.6f}")
    print(f"   Depositing: {coai_amount:.4f} {BASE_TOKEN} + {usdt_amount:.2f} {QUOTE_TOKEN}")
    
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "pool_address": POOL_ADDRESS,
        "lower_price": f"{lower_price:.10f}",
        "upper_price": f"{upper_price:.10f}",
        "base_token_amount": f"{coai_amount:.10f}",
        "quote_token_amount": f"{usdt_amount:.10f}",
        "slippage_pct": str(MAX_SLIPPAGE)
    }
    
    status, data = await api_post(session, "/gateway/clmm/open", payload)
    
    if status == 200 and isinstance(data, dict):
        print(f"✅ Position opened successfully!")
        print(f"   Transaction: {data.get('transaction_hash', 'N/A')}")
        print(f"   Position ID: {data.get('position_id', 'N/A')}")
        print(f"   Liquidity: {data.get('liquidity', 'N/A')}")
        return data
    else:
        print(f"❌ Failed to open position!")
        print(f"   Status: {status}")
        print(f"   Error: {data}")
        return None


# ============================================================================
# MAIN REBALANCE WORKFLOW
# ============================================================================

async def rebalance(position_id: str, range_width_pct: float, dry_run: bool = False):
    """
    Complete rebalancing workflow
    
    Args:
        position_id: Current position to close
        range_width_pct: Width of new range (e.g., 3.0 for 3%)
        dry_run: If True, only show what would happen
    """
    
    print("\n" + "=" * 80)
    print("🔄 AUTOMATED POSITION REBALANCER")
    print("=" * 80)
    print(f"Position ID: {position_id}")
    print(f"Range Width: {range_width_pct}%")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No transactions will be executed")
        print("   Remove --dry-run flag to execute for real\n")
    
    async with aiohttp.ClientSession() as session:
        
        # Get current price first (needed for all calculations)
        current_price = await get_current_price(session)
        if not current_price:
            # Fallback to a reasonable estimate
            current_price = 0.431550
            print(f"   Using fallback price: ${current_price:.6f}")
        
        if dry_run:
            print("\n📋 DRY RUN: Would close position but skipping...")
            coai_balance = 2314.5  # Example
            usdt_balance = 1000.0  # Example
        else:
            # Step 1: Close position
            close_result = await close_position(session, position_id)
            if not close_result:
                print("\n❌ FAILED: Could not close position")
                return
            
            # Wait for settlement
            print(f"\n⏳ Waiting {SETTLEMENT_WAIT} seconds for transaction settlement...")
            await asyncio.sleep(SETTLEMENT_WAIT)
            
            # Step 2: Get balances
            coai_balance, usdt_balance = await get_balances(session)
            if coai_balance == 0 and usdt_balance == 0:
                print("\n❌ FAILED: Zero balance after closing")
                return
        
        # Step 3: Calculate new range and token amounts
        lower_price, upper_price = calculate_range(current_price, range_width_pct)
        coai_amount, usdt_amount = calculate_token_ratio(
            current_price,
            lower_price,
            upper_price,
            coai_balance,
            usdt_balance
        )
        
        if dry_run:
            print("\n📋 DRY RUN: Would open new position with:")
            print(f"   Range: ${lower_price:.6f} - ${upper_price:.6f}")
            print(f"   Amounts: {coai_amount:.4f} {BASE_TOKEN} + {usdt_amount:.2f} {QUOTE_TOKEN}")
            print("\n✅ DRY RUN COMPLETE")
            return
        
        # Step 4: Open new position
        open_result = await open_position(session, lower_price, upper_price, coai_amount, usdt_amount)
        if not open_result:
            print("\n❌ FAILED: Could not open new position")
            print("   ⚠️  WARNING: Position is closed but new position failed to open!")
            print("   Your tokens are in your wallet. You can manually reopen.")
            return
        
        # Success!
        print("\n" + "=" * 80)
        print("✅ REBALANCING COMPLETE!")
        print("=" * 80)
        print(f"Old position {position_id} → New position {open_result.get('position_id', 'N/A')}")
        print(f"New range: ${lower_price:.6f} - ${upper_price:.6f} ({range_width_pct}% width)")
        print("=" * 80 + "\n")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Automated CLMM position rebalancer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Rebalance with 3% range (dry run)
  python auto_rebalance.py --position 6221178 --range-width 3.0 --dry-run
  
  # Execute rebalance (LIVE)
  python auto_rebalance.py --position 6221178 --range-width 3.0
  
  # Use narrower 2% range
  python auto_rebalance.py --position 6221178 --range-width 2.0
        """
    )
    
    parser.add_argument(
        "--position",
        required=True,
        help="Position ID to close and rebalance"
    )
    
    parser.add_argument(
        "--range-width",
        type=float,
        default=3.0,
        help="Range width as percentage (default: 3.0)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - show what would happen without executing"
    )
    
    args = parser.parse_args()
    
    # Validate range width
    if args.range_width < 1.5 or args.range_width > 10.0:
        print("❌ ERROR: Range width must be between 1.5% and 10%")
        return
    
    # Run rebalance
    asyncio.run(rebalance(args.position, args.range_width, args.dry_run))


if __name__ == "__main__":
    main()

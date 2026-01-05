#!/usr/bin/env python3
"""
Close CLMM Position
Removes all liquidity and collects all fees from a position

Usage:
    python scripts/close_position_simple.py --position 6221178
    python scripts/close_position_simple.py --position 6221178 --dry-run
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


async def close_position(session: aiohttp.ClientSession, position_id: str, dry_run: bool = False) -> Optional[Dict]:
    """Close position - removes all liquidity and collects fees"""
    
    print("\n" + "=" * 80)
    print(f"🔴 CLOSING POSITION {position_id}")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 80 + "\n")
    
    if dry_run:
        print("📋 DRY RUN: Would close position with:")
        print(f"   Connector: {CONNECTOR}")
        print(f"   Network: {NETWORK}")
        print(f"   Position: {position_id}")
        print("\n✅ DRY RUN COMPLETE - No action taken")
        return None
    
    payload = {
        "connector": CONNECTOR,
        "network": NETWORK,
        "position_address": position_id
    }
    
    print("📤 Sending close request to Gateway...")
    status, data = await api_post(session, "/gateway/clmm/close", payload)
    
    if status == 200 and isinstance(data, dict):
        print("\n✅ POSITION CLOSED SUCCESSFULLY!")
        print("=" * 80)
        print(f"Transaction Hash: {data.get('transaction_hash', 'N/A')}")
        print(f"\n💰 Tokens Returned:")
        print(f"   Base (COAI):  {data.get('base_token_amount', 'N/A')}")
        print(f"   Quote (USDT): {data.get('quote_token_amount', 'N/A')}")
        print(f"\n💸 Fees Collected:")
        print(f"   Base (COAI):  {data.get('base_fee_collected', 'N/A')}")
        print(f"   Quote (USDT): {data.get('quote_fee_collected', 'N/A')}")
        print("=" * 80)
        print(f"\n⏳ Transaction is processing on BSC (usually 3-5 seconds)")
        print(f"   View at: https://bscscan.com/tx/{data.get('transaction_hash', '')}")
        print("\n✅ Position closed - tokens are now in your wallet")
        print("   Run open_position_smart.py to create new position")
        return data
    else:
        print("\n❌ FAILED TO CLOSE POSITION")
        print("=" * 80)
        print(f"Status Code: {status}")
        print(f"Error: {data}")
        print("=" * 80)
        
        if status == 404:
            print("\n💡 TIP: Position might not be in database yet")
            print("   This can happen for manually created positions")
            print("   Try closing through PancakeSwap UI or add to database first")
        
        return None


async def main():
    parser = argparse.ArgumentParser(
        description="Close CLMM position",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Close position (dry run first)
  python close_position_simple.py --position 6221178 --dry-run
  
  # Close position (LIVE)
  python close_position_simple.py --position 6221178
        """
    )
    
    parser.add_argument(
        "--position",
        required=True,
        help="Position ID to close"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - show what would happen without executing"
    )
    
    args = parser.parse_args()
    
    async with aiohttp.ClientSession() as session:
        await close_position(session, args.position, args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())

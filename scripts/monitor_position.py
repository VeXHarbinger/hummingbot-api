#!/usr/bin/env python3
"""
CLMM Position Monitor
Real-time monitoring of PancakeSwap V3 position with actionable alerts

This script uses the Hummingbot MCP server to fetch position data.
Make sure the MCP server (hummingbot-mcp container) is running.

Usage:
    python scripts/monitor_position.py --interval 180  # Check every 3 minutes
    python scripts/monitor_position.py --once          # Single check
"""

import sys
import io
import time
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================================
# CONFIGURATION
# ============================================================================

POSITION_ID = "6223300"  # Current active position
POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"
NETWORK = "bsc-mainnet"
CONNECTOR = "pancakeswap"

# Note: In real implementation, these would come from MCP server
# For now, we'll use placeholder data and you can integrate MCP calls later
WALLET_ADDRESS = None  # Will be fetched from MCP if needed

# Alert thresholds
EDGE_WARNING_PERCENT = 15.0    # Warn when price is within 15% of edge
EDGE_CRITICAL_PERCENT = 5.0    # Critical when price is within 5% of edge
TARGET_APR_MIN = 300.0         # Alert if APR drops below this

# ============================================================================
# MCP INTEGRATION (Placeholder - integrate with actual MCP server)
# ============================================================================

def get_position_data_mcp() -> Optional[Dict[str, Any]]:
    """
    Fetch position data using MCP server.
    
    TODO: Replace with actual MCP call when ready.
    For now, returns placeholder data matching your position.
    """
    
    # This would be replaced with actual MCP call like:
    # result = mcp_client.call("manage_gateway_clmm_positions", {
    #     "action": "get_positions",
    #     "connector": CONNECTOR,
    #     "network": NETWORK,
    #     "pool_address": POOL_ADDRESS
    # })
    
    # Placeholder data (replace with real MCP call)
    return {
        "position_id": POSITION_ID,
        "pool_address": POOL_ADDRESS,
        "current_price": 0.431550,
        "lower_price": 0.429575506,
        "upper_price": 0.447105921,
        "token0": {"symbol": "COAI"},
        "token1": {"symbol": "USDT"},
        "liquidity": "N/A",
        "fee_tier": 0.0025,
        # These would come from real data
        "token0_amount": "N/A",
        "token1_amount": "N/A",
        "uncollected_fees": {"token0": "N/A", "token1": "N/A"}
    }


def get_current_price_mcp() -> Optional[float]:
    """
    Fetch current pool price using MCP server.
    
    TODO: Replace with actual MCP call.
    """
    # This would use get_prices MCP tool
    position = get_position_data_mcp()
    return position.get("current_price") if position else None


def calculate_range_metrics(position: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """Calculate position metrics relative to range"""
    
    # Try both key formats (snake_case and camelCase)
    current_price = float(position.get('current_price') or position.get('currentPrice', 0))
    lower_price = float(position.get('lower_price') or position.get('lowerPrice', 0))
    upper_price = float(position.get('upper_price') or position.get('upperPrice', 0))
    
    if not all([current_price, lower_price, upper_price]):
        print(f"⚠️  Missing price data: current={current_price}, lower={lower_price}, upper={upper_price}")
        return None
    
    # Range metrics
    range_width = upper_price - lower_price
    range_width_pct = (range_width / lower_price) * 100
    
    # Position within range (0% = lower edge, 100% = upper edge)
    position_in_range = ((current_price - lower_price) / range_width) * 100
    
    # Distance to edges
    distance_to_lower = current_price - lower_price
    distance_to_upper = upper_price - current_price
    distance_to_lower_pct = (distance_to_lower / current_price) * 100
    distance_to_upper_pct = (distance_to_upper / current_price) * 100
    
    # Which edge is closer?
    closest_edge = "LOWER" if distance_to_lower < distance_to_upper else "UPPER"
    closest_distance_pct = min(distance_to_lower_pct, distance_to_upper_pct)
    
    return {
        "current_price": current_price,
        "lower_price": lower_price,
        "upper_price": upper_price,
        "range_width": range_width,
        "range_width_pct": range_width_pct,
        "position_in_range_pct": position_in_range,
        "distance_to_lower": distance_to_lower,
        "distance_to_upper": distance_to_upper,
        "distance_to_lower_pct": distance_to_lower_pct,
        "distance_to_upper_pct": distance_to_upper_pct,
        "closest_edge": closest_edge,
        "closest_distance_pct": closest_distance_pct,
        "is_in_range": lower_price <= current_price <= upper_price
    }


def get_status_emoji(metrics: Dict[str, float]) -> str:
    """Get emoji based on position status"""
    if not metrics['is_in_range']:
        return "🔴"  # Out of range
    elif metrics['closest_distance_pct'] < EDGE_CRITICAL_PERCENT:
        return "🟠"  # Critical - very close to edge
    elif metrics['closest_distance_pct'] < EDGE_WARNING_PERCENT:
        return "🟡"  # Warning - approaching edge
    else:
        return "🟢"  # Good - safe in middle


def print_position_status(position: Dict[str, Any], metrics: Dict[str, float]):
    """Print formatted position status"""
    
    status_emoji = get_status_emoji(metrics)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "=" * 80)
    print(f"{status_emoji} POSITION STATUS - {timestamp}")
    print("=" * 80)
    
    # Position Info
    print(f"\n📍 Position ID: {POSITION_ID}")
    print(f"💰 Current Price: ${metrics['current_price']:.6f}")
    print(f"📊 Range: ${metrics['lower_price']:.6f} - ${metrics['upper_price']:.6f} ({metrics['range_width_pct']:.2f}% width)")
    
    # Range Status
    print(f"\n📈 Position in Range:")
    if metrics['is_in_range']:
        print(f"   ✅ IN RANGE at {metrics['position_in_range_pct']:.1f}% position")
        print(f"   ⬇️  Distance to LOWER edge: ${metrics['distance_to_lower']:.6f} ({metrics['distance_to_lower_pct']:.2f}%)")
        print(f"   ⬆️  Distance to UPPER edge: ${metrics['distance_to_upper']:.6f} ({metrics['distance_to_upper_pct']:.2f}%)")
    else:
        print(f"   ❌ OUT OF RANGE!")
        if metrics['current_price'] < metrics['lower_price']:
            print(f"   📉 Price is ${metrics['lower_price'] - metrics['current_price']:.6f} BELOW range")
        else:
            print(f"   📈 Price is ${metrics['current_price'] - metrics['upper_price']:.6f} ABOVE range")
    
    # Alerts
    print(f"\n⚠️  Alerts:")
    if not metrics['is_in_range']:
        print(f"   🔴 CRITICAL: Position is OUT OF RANGE - NO FEES BEING EARNED!")
        print(f"   🔄 ACTION REQUIRED: Rebalance position immediately")
    elif metrics['closest_distance_pct'] < EDGE_CRITICAL_PERCENT:
        print(f"   🟠 CRITICAL: Only {metrics['closest_distance_pct']:.2f}% from {metrics['closest_edge']} edge")
        print(f"   🔄 ACTION SOON: Prepare to rebalance within 1-2 hours")
    elif metrics['closest_distance_pct'] < EDGE_WARNING_PERCENT:
        print(f"   🟡 WARNING: {metrics['closest_distance_pct']:.2f}% from {metrics['closest_edge']} edge")
        print(f"   👀 WATCH: Monitor closely for rebalancing")
    else:
        print(f"   🟢 GOOD: Safe distance from edges ({metrics['closest_distance_pct']:.2f}% to nearest)")
    
    # Liquidity info
    if position.get('liquidity'):
        print(f"\n💧 Liquidity: {position['liquidity']}")
    
    # Token amounts
    if 'token0' in position and 'token1' in position:
        print(f"\n💎 Token Amounts:")
        print(f"   Token0: {position.get('token0_amount', 'N/A')} {position['token0'].get('symbol', '???')}")
        print(f"   Token1: {position.get('token1_amount', 'N/A')} {position['token1'].get('symbol', '???')}")
    
    # TODO: Add APR when data source is available
    # print(f"\n📊 APR: {apr}%")
    
    print("\n" + "=" * 80 + "\n")


def monitor_once():
    """Single monitoring check"""
    
    print("🔍 Fetching position data...")
    
    # Get position data
    position = get_position_data_mcp()
    if not position:
        print("❌ Failed to fetch position data")
        return False
    
    # Calculate metrics
    metrics = calculate_range_metrics(position)
    if not metrics:
        print("❌ Failed to calculate metrics")
        return False
    
    # Display status
    print_position_status(position, metrics)
    
    return True


def monitor_continuous(interval_seconds: int = 180):
    """Continuous monitoring with specified interval"""
    
    print(f"🚀 Starting continuous monitoring (checking every {interval_seconds}s)")
    print(f"   Press Ctrl+C to stop\n")
    
    check_count = 0
    
    try:
        while True:
            check_count += 1
            print(f"📡 Check #{check_count}")
            
            success = monitor_once()
            
            if not success:
                print("⚠️  Check failed, will retry next interval")
            
            # Wait for next check
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Monitoring stopped after {check_count} checks")
        print("👋 Goodbye!")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Monitor CLMM position in real-time"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=180,
        help="Seconds between checks (default: 180 = 3 minutes)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run single check and exit"
    )
    
    args = parser.parse_args()
    
    if args.once:
        monitor_once()
    else:
        monitor_continuous(args.interval)


if __name__ == "__main__":
    main()


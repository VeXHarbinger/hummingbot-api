"""
Simple rebalancing script using MCP tools
This closes the current position and opens a new one with a 2% range
"""

print("="*60)
print("🔄 REBALANCING CLMM POSITION")
print("="*60)

POSITION_ID = "6220678"
CONNECTOR = "pancakeswap_v3_bsc"
NETWORK = "bsc-mainnet"
POOL_ADDRESS = "0xbc0E5A205D729299D93973d634E2507CD8b625A3"

print("\nℹ️  This script will:")
print("1. Get current pool price")
print("2. Close position 6220678") 
print("3. Calculate 2% range around current price")
print("4. Open new position with rebalanced tokens")
print("\n⚠️  Please run the MCP commands manually or use the API directly")
print("\nManual steps:")
print("1. Check current price and close position")
print("2. Get your COAI and USDT balances")
print("3. Calculate 2% range: current_price * 0.98 to current_price * 1.02")
print("4. Open new position with those parameters")

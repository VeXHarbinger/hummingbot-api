"""
Execute optimal swap based on discovered Gateway ratio

Discovered ratio: 0.083115 USDT per COAI
Current: 4.45 COAI + 12.34 USDT
Optimal swap: 10.04 USDT → 23.23 COAI
After swap: 27.68 COAI + 2.30 USDT (perfectly balanced for position)
"""
import requests
import json
from requests.auth import HTTPBasicAuth

print('='*70)
print('FINAL OPTIMAL SWAP BASED ON DISCOVERED RATIO')
print('='*70)
print()
print('Discovered Gateway Ratio: 0.083115 USDT per COAI')
print('(Position needs mostly COAI, very little USDT)')
print()
print('Current Balances:')
print('  COAI: 4.45')
print('  USDT: 12.34')
print()
print('Optimal Swap:')
print('  Swap: 10.04 USDT → ~23.23 COAI')
print('  After: 27.68 COAI + 2.30 USDT')
print('  Ratio: 0.083115 USDT/COAI ✅')
print()
print('Then add ALL liquidity to deploy remaining $14.27')
print()
print('='*70)
print()
print('Ready to execute swap? This will:')
print('1. Swap 10.04 USDT to COAI on PancakeSwap')
print('2. Balance portfolio for optimal liquidity addition')
print()

response = input('Execute swap? (yes/no): ')

if response.lower() == 'yes':
    print()
    print('🚀 Swap command for PancakeSwap UI:')
    print('   From: 10.04 USDT')
    print('   To: COAI')
    print('   Expected: ~23.23 COAI')
    print()
    print('After swap completes, run: python add_all_remaining_liquidity.py')
else:
    print('Swap cancelled')

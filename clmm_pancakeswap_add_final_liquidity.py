"""
Add final remaining liquidity to position 6223672 with correct UI ratio
"""
import requests
import json
from requests.auth import HTTPBasicAuth

# API endpoint and authentication
url = 'http://localhost:8000/gateway/clmm/add'
auth = HTTPBasicAuth('admin', '4Adm!np@ssw0rd')

# Request body - using updated UI ratio: 18.383449 COAI needs 0.948251 USDT
data = {
    'network': 'ethereum-bsc',
    'connector': 'pancakeswap',
    'position_address': '6223672',
    'base_token_amount': 18.015780,   # 98% of remaining COAI
    'quote_token_amount': 0.929286,   # Matching USDT per UI ratio
    'slippage_pct': 1.0
}

print('='*70)
print('ADDING FINAL LIQUIDITY TO POSITION 6223672')
print('='*70)
print()
print('UI Ratio: 18.383449 COAI needs 0.948251 USDT')
print('  → 0.051582 USDT per COAI')
print()
print('Adding:')
print(f'  COAI (base): {data["base_token_amount"]}')
print(f'  USDT (quote): {data["quote_token_amount"]}')
print()
print('Request:')
print(json.dumps(data, indent=2))
print()

try:
    response = requests.post(url, json=data, auth=auth, timeout=120)
    print(f'Status: {response.status_code}')
    print()
    
    result = response.json()
    print('Response:')
    print(json.dumps(result, indent=2))
    
    if response.status_code == 200 and 'txHash' in result:
        print()
        print('='*70)
        print('✅ SUCCESS!')
        print(f'Transaction: {result["txHash"]}')
        print('='*70)
        print()
        print('Expected leftover: ~12.45 USDT')
    else:
        print()
        print('❌ Failed to add liquidity')
        
except Exception as e:
    print(f'❌ Error: {e}')

"""
Discover the correct ratio by submitting a request with huge amounts.
Gateway will calculate the optimal ratio and fail due to insufficient balance,
but we'll learn what ratio it tried to use.
"""
import requests
import json
from requests.auth import HTTPBasicAuth

# API endpoint and authentication
url = 'http://localhost:8000/gateway/clmm/add'
auth = HTTPBasicAuth('admin', '4Adm!np@ssw0rd')

# Request body - use MASSIVE amounts to find the ratio
data = {
    'network': 'ethereum-bsc',
    'connector': 'pancakeswap',
    'position_address': '6223672',
    'base_token_amount': 1000.0,   # Way more COAI than we have
    'quote_token_amount': 1000.0,  # Way more USDT than we have
    'slippage_pct': 1.0
}

print('='*70)
print('DISCOVERING CORRECT RATIO FOR POSITION')
print('='*70)
print()
print('Strategy: Request massive amounts to force Gateway to calculate')
print('         optimal ratio. It will fail due to insufficient balance,')
print('         but we can extract the ratio from the error or logs.')
print()
print('Requesting:')
print(f'  COAI (base): {data["base_token_amount"]}')
print(f'  USDT (quote): {data["quote_token_amount"]}')
print()
print('Actual balances:')
print('  COAI: ~17.45')
print('  USDT: ~13.42')
print()
print('Expected: Gateway will calculate how much it needs and fail')
print()

try:
    response = requests.post(url, json=data, auth=auth, timeout=120)
    print(f'Status: {response.status_code}')
    print()
    
    result = response.json()
    print('Response:')
    print(json.dumps(result, indent=2))
    
    # Look for ratio information in the error
    if 'detail' in result:
        detail = result['detail']
        print()
        print('Error detail suggests the ratio Gateway tried to use.')
        print('We can use this to calculate the swap!')
        
except Exception as e:
    print(f'Error: {e}')

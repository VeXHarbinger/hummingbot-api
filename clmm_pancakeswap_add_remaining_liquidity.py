"""
Add ALL remaining liquidity - let Gateway calculate the correct ratio
"""
import requests
import json
from requests.auth import HTTPBasicAuth

# API endpoint and authentication
url = 'http://localhost:8000/gateway/clmm/add'
auth = HTTPBasicAuth('admin', '4Adm!np@ssw0rd')

# Request body - use ALL remaining tokens, let Gateway optimize
data = {
    'network': 'ethereum-bsc',
    'connector': 'pancakeswap',
    'position_address': '6223672',
    'base_token_amount': 17.0,  # Almost all remaining COAI (leave 0.45 for gas/buffer)
    'quote_token_amount': 13.0,  # Almost all remaining USDT (leave 0.42 for gas/buffer)
    'slippage_pct': 1.0
}

print('='*70)
print('ADDING REMAINING LIQUIDITY - LET GATEWAY OPTIMIZE RATIO')
print('='*70)
print()
print('Strategy: Provide large amounts, Gateway will use what it needs')
print()
print('Requesting:')
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
    
    if response.status_code == 200 and 'transaction_hash' in result:
        print()
        print('='*70)
        print('✅ SUCCESS!')
        print(f'Transaction: {result["transaction_hash"]}')
        print('='*70)
    else:
        print()
        print('❌ Failed to add liquidity')
        
except Exception as e:
    print(f'❌ Error: {e}')

"""
Execute swap using Gateway - attempting USDT -> COAI swap for final deployment

We discovered Gateway doesn't have router support for BSC, but let's verify if 
there have been any updates or if we need to use the direct contract approach.
"""
import requests
import json
from requests.auth import HTTPBasicAuth

# API endpoint and authentication
auth = HTTPBasicAuth('admin', '4Adm!np@ssw0rd')

# First, let's try to get a swap quote
print('='*70)
print('ATTEMPTING AUTOMATED SWAP: 10.04 USDT → COAI')
print('='*70)
print()

# Try quote endpoint first
quote_url = 'http://localhost:8000/gateway/swap/quote'
quote_data = {
    'connector': 'pancakeswap',  # or try 'jupiter' if available
    'network': 'ethereum-bsc',
    'trading_pair': 'USDT-COAI',
    'side': 'BUY',  # Buy COAI with USDT
    'amount': '10.04',
    'slippage_pct': '1.0'
}

print('Step 1: Getting swap quote...')
print(f'Request: {json.dumps(quote_data, indent=2)}')
print()

try:
    response = requests.post(quote_url, json=quote_data, auth=auth, timeout=30)
    print(f'Status: {response.status_code}')
    result = response.json()
    print(f'Response: {json.dumps(result, indent=2)}')
    
    if response.status_code == 200 and result.get('amount_out'):
        print()
        print(f'✅ Quote successful!')
        print(f'   Will receive: {result.get("amount_out")} COAI')
        print()
        
        # Execute the swap
        execute_url = 'http://localhost:8000/gateway/swap/execute'
        execute_data = quote_data.copy()
        
        print('Step 2: Executing swap...')
        response = requests.post(execute_url, json=execute_data, auth=auth, timeout=120)
        print(f'Status: {response.status_code}')
        result = response.json()
        print(f'Response: {json.dumps(result, indent=2)}')
        
        if response.status_code == 200 and result.get('txHash'):
            print()
            print('✅ SWAP EXECUTED!')
            print(f'   Transaction: {result.get("txHash")}')
    else:
        print()
        print('❌ Quote failed - Gateway likely still missing router support')
        print('   Need to use direct smart contract approach')
        
except Exception as e:
    print(f'❌ Error: {e}')
    print()
    print('Gateway swap not available. Will need direct contract approach.')

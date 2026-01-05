"""
Add ALL remaining liquidity after optimal swap

After swapping 10.04 USDT → ~23.23 COAI, we should have:
- ~27.68 COAI
- ~2.30 USDT
- Ratio: 0.083 USDT per COAI (perfect for Gateway)

This script will add ALL remaining tokens to complete the deployment.
"""
import requests
import json
from requests.auth import HTTPBasicAuth
from web3 import Web3
import time

# Connect to BSC to check balances
w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
erc20_abi = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]')

wallet = '0x9F8EA3124dF6D6696668E5e4Ff063E489234dd93'
coai_address = '0x0A8D6C86e1bcE73fE4D0bD531e1a567306836EA5'
usdt_address = '0x55d398326f99059fF775485246999027B3197955'

print('='*70)
print('DEPLOYING FINAL LIQUIDITY AFTER SWAP')
print('='*70)
print()

# Wait a bit for swap to settle
print('Waiting 10 seconds for swap to settle on blockchain...')
time.sleep(10)

# Check current balances
coai_contract = w3.eth.contract(address=w3.to_checksum_address(coai_address), abi=erc20_abi)
usdt_contract = w3.eth.contract(address=w3.to_checksum_address(usdt_address), abi=erc20_abi)

coai_balance = coai_contract.functions.balanceOf(w3.to_checksum_address(wallet)).call() / 10**18
usdt_balance = usdt_contract.functions.balanceOf(w3.to_checksum_address(wallet)).call() / 10**18

print()
print('Current Balances (after swap):')
print(f'  COAI: {coai_balance:.6f}')
print(f'  USDT: {usdt_balance:.6f}')
print(f'  Ratio: {usdt_balance/coai_balance:.6f} USDT per COAI')
print(f'  Target: 0.083 USDT per COAI')
print()

# Calculate amounts to add (leave tiny buffer for gas)
coai_to_add = coai_balance * 0.99
usdt_to_add = usdt_balance * 0.99

print('Adding to Position 6223672:')
print(f'  COAI: {coai_to_add:.6f}')
print(f'  USDT: {usdt_to_add:.6f}')
print(f'  Value: ${coai_to_add * 0.432 + usdt_to_add:.2f}')
print()

# API call
url = 'http://localhost:8000/gateway/clmm/add'
auth = HTTPBasicAuth('admin', '4Adm!np@ssw0rd')

data = {
    'network': 'ethereum-bsc',
    'connector': 'pancakeswap',
    'position_address': '6223672',
    'base_token_amount': coai_to_add,
    'quote_token_amount': usdt_to_add,
    'slippage_pct': 1.0
}

print('Submitting liquidity addition...')
print()

try:
    response = requests.post(url, json=data, auth=auth, timeout=120)
    print(f'Status: {response.status_code}')
    
    result = response.json()
    print('Response:')
    print(json.dumps(result, indent=2))
    
    if response.status_code == 200 and 'transaction_hash' in result:
        print()
        print('='*70)
        print('✅ SUCCESS! FINAL LIQUIDITY DEPLOYED!')
        print('='*70)
        print(f'Transaction: {result["transaction_hash"]}')
        print()
        print('Position 6223672 should now have ALL available capital deployed!')
        
except Exception as e:
    print(f'❌ Error: {e}')

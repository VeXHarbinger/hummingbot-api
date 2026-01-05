"""
Open new CLMM position after rebalancing swap

This script opens a new ±1.25% position with ALL available capital
after swapping to achieve ~50/50 balance.

Expected state after swap:
- COAI: ~127.45
- USDT: ~53.96
- Total: ~$107.93
"""
import requests
import json
from requests.auth import HTTPBasicAuth
from web3 import Web3
import time

# Setup
w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
auth = HTTPBasicAuth('admin', '4Adm!np@ssw0rd')
api_url = 'http://localhost:8000'

# Configuration
pool_address = '0xbc0E5A205D729299D93973d634E2507CD8b625A3'
wallet = '0x9F8EA3124dF6D6696668E5e4Ff063E489234dd93'
coai_address = '0x0A8D6C86e1bcE73fE4D0bD531e1a567306836EA5'
usdt_address = '0x55d398326f99059fF775485246999027B3197955'

print('='*70)
print('OPENING NEW CLMM POSITION')
print('='*70)
print()

# Wait for swap to settle
print('Waiting 10 seconds for swap to settle...')
time.sleep(10)
print()

# Get current balances
print('Step 1: Checking balances after swap...')
erc20_abi = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]')
coai_contract = w3.eth.contract(address=w3.to_checksum_address(coai_address), abi=erc20_abi)
usdt_contract = w3.eth.contract(address=w3.to_checksum_address(usdt_address), abi=erc20_abi)

coai_balance = coai_contract.functions.balanceOf(w3.to_checksum_address(wallet)).call() / 10**18
usdt_balance = usdt_contract.functions.balanceOf(w3.to_checksum_address(wallet)).call() / 10**18

print(f'   COAI: {coai_balance:.6f}')
print(f'   USDT: {usdt_balance:.6f}')
print()

# Get current price
print('Step 2: Getting current pool price...')
response = requests.get(
    f'{api_url}/gateway/clmm/pool-info',
    params={'connector': 'pancakeswap', 'network': 'ethereum-bsc', 'pool_address': pool_address},
    auth=auth
)
pool_info = response.json()
current_price = float(pool_info.get('price', 0))
print(f'   Current price: ${current_price:.6f}')
print()

# Calculate position range (±1.25%)
lower_price = current_price * 0.9875
upper_price = current_price * 1.0125

print('Step 3: Opening new position...')
print(f'   Range: ${lower_price:.6f} - ${upper_price:.6f}')
print()

# Prepare amounts (use 99% to leave buffer)
base_amount = coai_balance * 0.99
quote_amount = usdt_balance * 0.99

# Open position
open_data = {
    'connector': 'pancakeswap',
    'network': 'ethereum-bsc',
    'pool_address': pool_address,
    'wallet_address': wallet,
    'lower_price': str(lower_price),
    'upper_price': str(upper_price),
    'base_token_amount': str(base_amount),
    'quote_token_amount': str(quote_amount),
    'slippage_pct': '1.0'
}

print(f'Opening position with:')
print(f'   COAI: {base_amount:.6f}')
print(f'   USDT: {quote_amount:.6f}')
print(f'   Total value: ${base_amount * current_price + quote_amount:.2f}')
print()

try:
    response = requests.post(
        f'{api_url}/gateway/clmm/open',
        json=open_data,
        auth=auth,
        timeout=120
    )
    
    print(f'Status: {response.status_code}')
    result = response.json()
    print('Response:')
    print(json.dumps(result, indent=2))
    
    if response.status_code == 200 and result.get('transaction_hash'):
        print()
        print('='*70)
        print('✅ SUCCESS! NEW POSITION OPENED!')
        print('='*70)
        print(f'Transaction: {result["transaction_hash"]}')
        print(f'Position ID: {result.get("position_address", "Check transaction")}')
        print()
        print(f'Position Details:')
        print(f'   Range: ${lower_price:.6f} - ${upper_price:.6f} (±1.25%)')
        print(f'   Capital: ${base_amount * current_price + quote_amount:.2f}')
        print(f'   Target APR: 1,237% (based on ±3% historical data)')
        print()
    else:
        print()
        print('❌ Failed to open position')
        print('Check the error above for details')
        
except Exception as e:
    print(f'❌ Error: {e}')

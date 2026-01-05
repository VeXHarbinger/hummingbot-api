"""
Complete workflow to reopen position after price exit

After position closed due to price moving out of range:
- Have: 225.67 COAI + 12.37 USDT = $107.93
- Current price: $0.423424
- Need to rebalance and open new position

Workflow:
1. Calculate optimal swap (COAI → USDT)
2. Execute swap manually on PancakeSwap
3. Open new position with all capital
"""
import requests
from requests.auth import HTTPBasicAuth
from web3 import Web3
import json

# Setup
w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
auth = HTTPBasicAuth('admin', '4Adm!np@ssw0rd')
api_url = 'http://localhost:8000'

# Wallet and tokens
wallet = '0x9F8EA3124dF6D6696668E5e4Ff063E489234dd93'
coai_address = '0x0A8D6C86e1bcE73fE4D0bD531e1a567306836EA5'
usdt_address = '0x55d398326f99059fF775485246999027B3197955'
pool_address = '0xbc0E5A205D729299D93973d634E2507CD8b625A3'

print('='*70)
print('COMPLETE WORKFLOW: REOPEN POSITION AFTER EXIT')
print('='*70)
print()

# Get current price
print('Step 1: Getting current pool price...')
response = requests.get(
    f'{api_url}/gateway/clmm/pool-info',
    params={'connector': 'pancakeswap', 'network': 'ethereum-bsc', 'pool_address': pool_address},
    auth=auth
)
pool_info = response.json()
current_price = float(pool_info.get('price', 0))
print(f'   Current price: ${current_price:.6f}')
print()

# Get current balances
print('Step 2: Checking current balances...')
erc20_abi = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]')
coai_contract = w3.eth.contract(address=w3.to_checksum_address(coai_address), abi=erc20_abi)
usdt_contract = w3.eth.contract(address=w3.to_checksum_address(usdt_address), abi=erc20_abi)

coai_balance = coai_contract.functions.balanceOf(w3.to_checksum_address(wallet)).call() / 10**18
usdt_balance = usdt_contract.functions.balanceOf(w3.to_checksum_address(wallet)).call() / 10**18
total_value = coai_balance * current_price + usdt_balance

print(f'   COAI: {coai_balance:.6f}')
print(f'   USDT: {usdt_balance:.6f}')
print(f'   Total value: ${total_value:.2f}')
print()

# Calculate optimal swap for 50/50 position
print('Step 3: Calculating optimal swap...')
target_usdt = total_value * 0.5
usdt_deficit = target_usdt - usdt_balance
coai_to_swap = usdt_deficit / current_price

print(f'   Need to swap: {coai_to_swap:.6f} COAI → {usdt_deficit:.6f} USDT')
print()
print(f'   After swap will have:')
print(f'     COAI: {coai_balance - coai_to_swap:.6f}')
print(f'     USDT: {usdt_balance + usdt_deficit:.6f}')
print(f'     Ratio: ~50/50 (perfect for mid-range position)')
print()

# Provide swap instructions
print('='*70)
print('NEXT STEPS:')
print('='*70)
print()
print(f'1. Swap on PancakeSwap:')
print(f'   From: {coai_to_swap:.6f} COAI')
print(f'   To: USDT (expect ~{usdt_deficit:.2f} USDT)')
print(f'   URL: https://pancakeswap.finance/swap')
print(f'   Input token: {coai_address}')
print(f'   Output token: {usdt_address}')
print()
print(f'2. After swap, open new position:')
print(f'   Run: python open_new_position.py')
print(f'   This will create a new ±1.25% position with ALL capital')
print()
print(f'Target position range:')
print(f'   Lower: ${current_price * 0.9875:.6f}')
print(f'   Current: ${current_price:.6f}')
print(f'   Upper: ${current_price * 1.0125:.6f}')
print('='*70)

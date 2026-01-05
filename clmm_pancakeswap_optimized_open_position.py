"""
OPTIMIZED WORKFLOW: Open CLMM Position with Discovery Method

Instead of guessing 50/50 ratio, we:
1. Open position with SMALLER token amount for BOTH tokens
2. Gateway shows us the actual ratio it needs
3. Swap remaining tokens to match that ratio
4. Add all remaining tokens to complete deployment

This ensures 100% capital deployment without guessing!
"""
import requests
from requests.auth import HTTPBasicAuth
from web3 import Web3
import json
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
print('OPTIMIZED POSITION OPENING WORKFLOW')
print('='*70)
print()

# Step 1: Get current balances
print('Step 1: Checking current balances...')
erc20_abi = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]')
coai_contract = w3.eth.contract(address=w3.to_checksum_address(coai_address), abi=erc20_abi)
usdt_contract = w3.eth.contract(address=w3.to_checksum_address(usdt_address), abi=erc20_abi)

coai_balance = coai_contract.functions.balanceOf(w3.to_checksum_address(wallet)).call() / 10**18
usdt_balance = usdt_contract.functions.balanceOf(w3.to_checksum_address(wallet)).call() / 10**18
market_price = 0.423  # Approximate from pool

print(f'   COAI: {coai_balance:.6f}')
print(f'   USDT: {usdt_balance:.6f}')
print(f'   Total value: ${coai_balance * market_price + usdt_balance:.2f}')
print()

# Step 2: Get current pool price
print('Step 2: Getting pool price for range calculation...')
response = requests.get(
    f'{api_url}/gateway/clmm/pool-info',
    params={'connector': 'pancakeswap', 'network': 'ethereum-bsc', 'pool_address': pool_address},
    auth=auth
)
pool_info = response.json()
current_price = float(pool_info.get('price', market_price))
print(f'   Current price: ${current_price:.6f}')
print()

# Calculate position range (±1.25%)
lower_price = current_price * 0.9875
upper_price = current_price * 1.0125

# Step 3: Determine SMALLER token amount
smaller_value = min(coai_balance * current_price, usdt_balance)
smaller_coai = smaller_value / current_price
smaller_usdt = smaller_value

print('Step 3: Opening position with SMALLER amount for BOTH tokens...')
print(f'   Strategy: Use ${smaller_value:.2f} worth for discovery')
print(f'   Opening with:')
print(f'     COAI: {smaller_coai:.6f}')
print(f'     USDT: {smaller_usdt:.6f}')
print(f'   Gateway will use what it needs and show us the actual ratio')
print()

# Open position with smaller amounts
open_data = {
    'connector': 'pancakeswap',
    'network': 'ethereum-bsc',
    'pool_address': pool_address,
    'wallet_address': wallet,
    'lower_price': str(lower_price),
    'upper_price': str(upper_price),
    'base_token_amount': str(smaller_coai),
    'quote_token_amount': str(smaller_usdt),
    'slippage_pct': '1.0'
}

try:
    response = requests.post(
        f'{api_url}/gateway/clmm/open',
        json=open_data,
        auth=auth,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f'✅ Position opened!')
        print(f'   Transaction: {result["transaction_hash"]}')
        print(f'   Position ID: {result.get("position_address")}')
        print()
        
        # Wait for transaction
        print('Waiting 10 seconds for transaction to settle...')
        time.sleep(10)
        
        # Step 4: Check what was actually used
        print()
        print('Step 4: Discovering actual ratio used...')
        
        coai_after_open = coai_contract.functions.balanceOf(w3.to_checksum_address(wallet)).call() / 10**18
        usdt_after_open = usdt_contract.functions.balanceOf(w3.to_checksum_address(wallet)).call() / 10**18
        
        coai_used = coai_balance - coai_after_open
        usdt_used = usdt_balance - usdt_after_open
        
        discovered_ratio = usdt_used / coai_used if coai_used > 0 else 0
        
        print(f'   Gateway used:')
        print(f'     COAI: {coai_used:.6f}')
        print(f'     USDT: {usdt_used:.6f}')
        print(f'   Discovered ratio: {discovered_ratio:.6f} USDT per COAI')
        print()
        print(f'   Remaining:')
        print(f'     COAI: {coai_after_open:.6f}')
        print(f'     USDT: {usdt_after_open:.6f}')
        print()
        
        # Step 5: Calculate optimal swap for remaining
        print('Step 5: Calculating optimal swap for remaining tokens...')
        
        # Calculate swap needed
        x = (usdt_after_open - discovered_ratio * coai_after_open) / (1 + discovered_ratio / current_price)
        
        if x > 0:
            print(f'   Swap {x:.6f} USDT → {x/current_price:.6f} COAI')
            print(f'   Then add all remaining to position {result.get("position_address")}')
        else:
            x = abs(x)
            coai_to_swap = x / current_price
            print(f'   Swap {coai_to_swap:.6f} COAI → {x:.6f} USDT')
            print(f'   Then add all remaining to position {result.get("position_address")}')
        
        print()
        print('='*70)
        print('NEXT STEPS:')
        print('='*70)
        print('1. Execute the swap on PancakeSwap')
        print('2. Run: python add_remaining_to_position.py')
        print('   This will add ALL remaining tokens to complete 100% deployment')
        
    else:
        result = response.json()
        print(f'❌ Failed to open position')
        print(f'   Response: {json.dumps(result, indent=2)}')
        
except Exception as e:
    print(f'❌ Error: {e}')

print()
print('='*70)
print('KEY INSIGHT:')
print('='*70)
print('By opening with the SMALLER amount, Gateway shows us the')
print('EXACT ratio it needs, allowing perfect swap calculation!')
print('This ensures 100% capital deployment without guessing.')

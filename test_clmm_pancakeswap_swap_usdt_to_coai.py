"""
Test script for swapping USDT to COAI on BSC using Gateway

This test documents the swap workflow for future reference.
Network: ethereum-bsc (NOT bsc-mainnet)
Goal: Swap 10.04 USDT → COAI to achieve optimal ratio for liquidity addition

Current situation:
- Have: 4.45 COAI + 12.34 USDT
- Need ratio: 0.083 USDT per COAI (discovered from Gateway)
- Optimal swap: 10.04 USDT → ~23.23 COAI
- After swap: 27.68 COAI + 2.30 USDT (perfectly balanced)
"""

import asyncio
import aiohttp
import json

async def test_swap_usdt_to_coai():
    """Test swapping USDT to COAI using Gateway swap endpoint"""
    
    api_url = "http://localhost:8000"
    auth = aiohttp.BasicAuth("admin", "4Adm!np@ssw0rd")
    
    # Swap parameters
    swap_data = {
        "connector": "pancakeswap",
        "network": "ethereum-bsc",  # CRITICAL: Use ethereum-bsc, NOT bsc-mainnet
        "trading_pair": "USDT-COAI",
        "side": "BUY",  # Buy COAI with USDT
        "amount": "10.04",  # Amount of USDT to spend
        "slippage_pct": "1.0"
    }
    
    async with aiohttp.ClientSession(auth=auth) as session:
        print('='*70)
        print('TESTING USDT → COAI SWAP ON BSC')
        print('='*70)
        print()
        
        # Step 1: Get swap quote
        print('Step 1: Getting swap quote...')
        print(f'Request: {json.dumps(swap_data, indent=2)}')
        print()
        
        async with session.post(
            f"{api_url}/gateway/swap/quote",
            json=swap_data
        ) as response:
            print(f'Quote Status: {response.status_code}')
            quote_result = await response.json()
            print(f'Quote Response: {json.dumps(quote_result, indent=2)}')
            print()
            
            if response.status_code != 200 or not quote_result.get('amount_out'):
                print('❌ KNOWN ISSUE: Gateway swap not supported for BSC')
                print('   Gateway currently lacks router implementation for PancakeSwap on BSC')
                print()
                print('WORKAROUNDS:')
                print('1. Manual swap via PancakeSwap UI:')
                print('   https://pancakeswap.finance/swap')
                print('   Input: 0x55d398326f99059fF775485246999027B3197955 (USDT)')
                print('   Output: 0x0A8D6C86e1bcE73fE4D0bD531e1a567306836EA5 (COAI)')
                print()
                print('2. Direct smart contract call (see services/pancakeswap_swap_service.py)')
                print('   Note: Router execution currently failing, needs debugging')
                print()
                print('3. Use Gateway discovery method:')
                print('   - Submit large add liquidity request')
                print('   - Gateway calculates optimal ratio')
                print('   - Use that ratio to determine swap amounts')
                return
        
        # Step 2: Execute swap (if quote worked)
        print('Step 2: Executing swap...')
        async with session.post(
            f"{api_url}/gateway/swap/execute",
            json=swap_data
        ) as response:
            print(f'Execute Status: {response.status_code}')
            exec_result = await response.json()
            print(f'Execute Response: {json.dumps(exec_result, indent=2)}')
            
            if response.status_code == 200 and exec_result.get('txHash'):
                print()
                print('✅ SWAP EXECUTED!')
                print(f'   Transaction: {exec_result.get("txHash")}')
                print()
                print('Next step: Run deploy_final_liquidity.py to add remaining tokens')
            else:
                print()
                print('❌ Swap execution failed')

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                  BSC SWAP TEST - USDT → COAI                      ║
    ╚═══════════════════════════════════════════════════════════════════╝
    
    Purpose: Swap USDT to COAI to achieve optimal ratio for LP
    
    Current State:
      - Balance: 4.45 COAI + 12.34 USDT (~$14.27)
      - Gateway ratio: 0.083 USDT per COAI
      - Market price: 0.432 USDT per COAI
    
    Optimal Swap:
      - Swap: 10.04 USDT → ~23.23 COAI
      - Result: 27.68 COAI + 2.30 USDT
      - Ratio: 0.083 USDT/COAI ✅
    
    Network Configuration:
      ⚠️  IMPORTANT: Use 'ethereum-bsc' NOT 'bsc-mainnet'
      
    Known Issues:
      - Gateway swap endpoint returns empty data (no router support)
      - Direct contract swap execution fails (router call reverts)
      - Manual swap on PancakeSwap UI works perfectly
    
    ════════════════════════════════════════════════════════════════════
    """)
    
    asyncio.run(test_swap_usdt_to_coai())

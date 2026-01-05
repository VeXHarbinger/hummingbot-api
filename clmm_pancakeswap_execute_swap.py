"""
Execute optimal swap: 63.60 COAI → USDT

This script executes the calculated optimal swap to balance our portfolio
for maximum liquidity deployment.
"""
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path('.').resolve() / 'services'))
from pancakeswap_swap_service import PancakeSwapSwapService, COAI_ADDRESS, USDT_ADDRESS

PRIVATE_KEY = "11a4349997476c2123d0a5950ed1b6b7b80241eb26f3fcdca36095975567b344"

# Optimal swap amount calculated
SWAP_AMOUNT = Decimal("63.60")


def main():
    print("\n" + "="*70)
    print("🔄 EXECUTING OPTIMAL SWAP")
    print("="*70)
    print()
    print("This will swap COAI → USDT to achieve optimal ratio for liquidity.")
    print()
    
    service = PancakeSwapSwapService(PRIVATE_KEY)
    
    print(f"Wallet: {service.account.address}")
    print()
    
    # Get current balances
    print("Current balances:")
    coai_before = service.get_token_balance(COAI_ADDRESS)
    usdt_before = service.get_token_balance(USDT_ADDRESS)
    print(f"  COAI: {coai_before}")
    print(f"  USDT: {usdt_before}")
    print()
    
    # Get quote first
    print(f"Getting quote for {SWAP_AMOUNT} COAI...")
    quote = service.quote_swap(
        token_in=COAI_ADDRESS,
        token_out=USDT_ADDRESS,
        amount_in=SWAP_AMOUNT,
        slippage_pct=Decimal("1.0")
    )
    
    print(f"Quote:")
    print(f"  Input: {quote['amount_in']} COAI")
    print(f"  Expected output: {quote['amount_out']} USDT")
    print(f"  Min output (1% slippage): {quote['amount_out_min']} USDT")
    print(f"  Price: {quote['price']} USDT per COAI")
    print(f"  Gas estimate: {quote['gas_estimate']}")
    print()
    
    # Confirm
    response = input(f"Execute swap of {SWAP_AMOUNT} COAI → {quote['amount_out']} USDT? (yes/no): ")
    if response.lower() != 'yes':
        print("\n❌ Swap cancelled")
        return
    
    print()
    print("="*70)
    print("EXECUTING SWAP...")
    print("="*70)
    print()
    
    try:
        result = service.execute_swap(
            token_in=COAI_ADDRESS,
            token_out=USDT_ADDRESS,
            amount_in=SWAP_AMOUNT,
            slippage_pct=Decimal("1.0")
        )
        
        print("✅ SWAP SUCCESSFUL!")
        print()
        print(f"Transaction hash: {result['transaction_hash']}")
        print(f"Amount in: {result['amount_in']} COAI")
        print(f"Amount out: {result['amount_out']} USDT")
        print(f"Price: {result['price']} USDT per COAI")
        print(f"Gas used: {result['gas_used']}")
        print()
        
        # Get new balances
        print("Waiting 10 seconds for balance update...")
        import time
        time.sleep(10)
        
        print()
        print("New balances:")
        coai_after = service.get_token_balance(COAI_ADDRESS)
        usdt_after = service.get_token_balance(USDT_ADDRESS)
        print(f"  COAI: {coai_after} (change: {coai_after - coai_before:+.4f})")
        print(f"  USDT: {usdt_after} (change: {usdt_after - usdt_before:+.4f})")
        print()
        
        print("="*70)
        print("✅ SWAP COMPLETE!")
        print("="*70)
        print()
        print("Next step: Add liquidity to position")
        print(f"  - Use ~61.87 COAI + ~27.06 USDT")
        print(f"  - Should deploy ~$53.78 total")
        
    except Exception as e:
        print(f"\n❌ Swap failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

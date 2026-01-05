"""
Test PancakeSwap Direct Swap Service

Tests direct smart contract interaction for swapping on BSC.
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Add parent directory to path to import the service directly
sys.path.insert(0, str(Path(__file__).parent / "services"))

from pancakeswap_swap_service import (
    PancakeSwapSwapService,
    COAI_ADDRESS,
    USDT_ADDRESS
)

# Wallet private key
PRIVATE_KEY = "11a4349997476c2123d0a5950ed1b6b7b80241eb26f3fcdca36095975567b344"


async def test_quote():
    """Test swap quote"""
    print("\n" + "="*70)
    print("TEST 1: GET SWAP QUOTE")
    print("="*70)
    
    service = PancakeSwapSwapService(PRIVATE_KEY)
    
    print(f"\nWallet: {service.account.address}")
    print(f"Connected: {service.w3.is_connected()}")
    
    # Test quote: 10 COAI → USDT
    coai_amount = Decimal("10")
    
    print(f"\nQuoting swap: {coai_amount} COAI → USDT")
    
    try:
        quote = service.quote_swap(
            token_in=COAI_ADDRESS,
            token_out=USDT_ADDRESS,
            amount_in=coai_amount,
            slippage_pct=Decimal("1.0")
        )
        
        print(f"\n✅ Quote successful!")
        print(f"   Input: {quote['amount_in']} COAI")
        print(f"   Output: {quote['amount_out']} USDT")
        print(f"   Min output (1% slippage): {quote['amount_out_min']} USDT")
        print(f"   Price: {quote['price']} USDT per COAI")
        print(f"   Estimated gas: {quote['gas_estimate']}")
        
        return quote
        
    except Exception as e:
        print(f"\n❌ Quote failed: {e}")
        return None


async def test_balances():
    """Test balance checking"""
    print("\n" + "="*70)
    print("TEST 2: CHECK BALANCES")
    print("="*70)
    
    service = PancakeSwapSwapService(PRIVATE_KEY)
    
    try:
        coai_balance = service.get_token_balance(COAI_ADDRESS)
        usdt_balance = service.get_token_balance(USDT_ADDRESS)
        
        print(f"\n✅ Balances:")
        print(f"   COAI: {coai_balance}")
        print(f"   USDT: {usdt_balance}")
        
        return coai_balance, usdt_balance
        
    except Exception as e:
        print(f"\n❌ Balance check failed: {e}")
        return None, None


async def test_execute_swap():
    """Test swap execution (COMMENTED OUT FOR SAFETY)"""
    print("\n" + "="*70)
    print("TEST 3: EXECUTE SWAP (COMMENTED OUT)")
    print("="*70)
    
    print("\n⚠️  Swap execution test is commented out for safety.")
    print("    Uncomment the code below to actually execute a swap.")
    
    # UNCOMMENT TO EXECUTE REAL SWAP
    # service = PancakeSwapSwapService(PRIVATE_KEY)
    # 
    # coai_amount = Decimal("1")  # Swap 1 COAI
    # 
    # print(f"\nExecuting swap: {coai_amount} COAI → USDT")
    # 
    # try:
    #     result = service.execute_swap(
    #         token_in=COAI_ADDRESS,
    #         token_out=USDT_ADDRESS,
    #         amount_in=coai_amount,
    #         slippage_pct=Decimal("1.0")
    #     )
    #     
    #     print(f"\n✅ Swap successful!")
    #     print(f"   Transaction: {result['transaction_hash']}")
    #     print(f"   Amount in: {result['amount_in']} COAI")
    #     print(f"   Amount out: {result['amount_out']} USDT")
    #     print(f"   Price: {result['price']} USDT per COAI")
    #     print(f"   Gas used: {result['gas_used']}")
    #     
    #     return result
    #     
    # except Exception as e:
    #     print(f"\n❌ Swap failed: {e}")
    #     return None


async def main():
    print("\n" + "="*70)
    print("🔄 PANCAKESWAP V3 DIRECT SWAP SERVICE TEST")
    print("="*70)
    print("\nThis tests direct smart contract interaction with PancakeSwap V3")
    print("bypassing Gateway due to lack of router support on BSC.")
    
    # Test 1: Quote
    quote = await test_quote()
    
    # Test 2: Balances
    balances = await test_balances()
    
    # Test 3: Execute (commented out)
    await test_execute_swap()
    
    print("\n" + "="*70)
    print("✅ TESTS COMPLETE")
    print("="*70)
    
    if quote:
        print(f"\n💡 To execute swap, uncomment the code in test_execute_swap()")
        print(f"   Current quote: {quote['amount_in']} COAI → {quote['amount_out']} USDT")


if __name__ == "__main__":
    asyncio.run(main())

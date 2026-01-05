#!/usr/bin/env python3
"""
Calculate Token Ratio for CLMM Position
Uses Uniswap V3 / PancakeSwap V3 math to calculate exact token amounts needed

This implements the smart contract's math:
- If current price is below range: 100% base token (COAI)
- If current price is above range: 100% quote token (USDT)  
- If current price is in range: mix of both tokens

Math formulas from Uniswap V3 whitepaper:
- L = Δy / (√P_upper - √P_current)  when price is in range
- Amount0 = L * (√P_upper - √P_current) / (√P_upper * √P_current)
- Amount1 = L * (√P_current - √P_lower)

Usage:
    python scripts/calculate_ratio.py --current-price 0.4317 --lower 0.4262 --upper 0.4369 --coai 183.38
    python scripts/calculate_ratio.py --current-price 0.4317 --lower 0.4262 --upper 0.4369 --usdt 30.34
"""

import argparse
import math
from typing import Tuple, Optional

def sqrt_price(price: float) -> float:
    """Convert price to sqrt price"""
    return math.sqrt(price)

def calculate_liquidity_from_amounts(
    current_price: float,
    lower_price: float,
    upper_price: float,
    amount0: Optional[float] = None,  # base token (COAI)
    amount1: Optional[float] = None   # quote token (USDT)
) -> float:
    """Calculate liquidity L from token amounts"""
    
    sqrt_current = sqrt_price(current_price)
    sqrt_lower = sqrt_price(lower_price)
    sqrt_upper = sqrt_price(upper_price)
    
    if current_price < lower_price:
        # Price below range - only need base token (COAI)
        if amount0 is None:
            raise ValueError("Price below range - need amount0 (base token)")
        liquidity = amount0 * (sqrt_lower * sqrt_upper) / (sqrt_upper - sqrt_lower)
        
    elif current_price >= upper_price:
        # Price above range - only need quote token (USDT)
        if amount1 is None:
            raise ValueError("Price above range - need amount1 (quote token)")
        liquidity = amount1 / (sqrt_upper - sqrt_lower)
        
    else:
        # Price in range - need both tokens
        if amount0 is not None:
            # Calculate from base token
            liquidity = amount0 * (sqrt_upper * sqrt_current) / (sqrt_upper - sqrt_current)
        elif amount1 is not None:
            # Calculate from quote token
            liquidity = amount1 / (sqrt_current - sqrt_lower)
        else:
            raise ValueError("Need at least one token amount")
    
    return liquidity

def calculate_amounts_from_liquidity(
    liquidity: float,
    current_price: float,
    lower_price: float,
    upper_price: float
) -> Tuple[float, float]:
    """Calculate token amounts needed for given liquidity"""
    
    sqrt_current = sqrt_price(current_price)
    sqrt_lower = sqrt_price(lower_price)
    sqrt_upper = sqrt_price(upper_price)
    
    if current_price < lower_price:
        # Price below range - only base token needed
        amount0 = liquidity * (sqrt_upper - sqrt_lower) / (sqrt_lower * sqrt_upper)
        amount1 = 0
        
    elif current_price >= upper_price:
        # Price above range - only quote token needed
        amount0 = 0
        amount1 = liquidity * (sqrt_upper - sqrt_lower)
        
    else:
        # Price in range - need both tokens
        amount0 = liquidity * (sqrt_upper - sqrt_current) / (sqrt_upper * sqrt_current)
        amount1 = liquidity * (sqrt_current - sqrt_lower)
    
    return amount0, amount1

def calculate_token_ratio(
    current_price: float,
    lower_price: float,
    upper_price: float,
    coai_amount: Optional[float] = None,
    usdt_amount: Optional[float] = None
) -> Tuple[float, float]:
    """
    Calculate the required token amounts for opening a CLMM position.
    
    Provide ONE of: coai_amount OR usdt_amount
    Returns: (coai_needed, usdt_needed)
    """
    
    # Step 1: Calculate liquidity from the provided amount
    liquidity = calculate_liquidity_from_amounts(
        current_price, lower_price, upper_price,
        amount0=coai_amount, amount1=usdt_amount
    )
    
    # Step 2: Calculate both amounts from liquidity
    amount0, amount1 = calculate_amounts_from_liquidity(
        liquidity, current_price, lower_price, upper_price
    )
    
    return amount0, amount1

def main():
    parser = argparse.ArgumentParser(
        description="Calculate exact token ratio for CLMM position",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # I have 183.38 COAI, how much USDT do I need?
  python calculate_ratio.py --current-price 0.4317 --lower 0.4262 --upper 0.4369 --coai 183.38
  
  # I have 30.34 USDT, how much COAI do I need?
  python calculate_ratio.py --current-price 0.4317 --lower 0.4262 --upper 0.4369 --usdt 30.34
        """
    )
    
    parser.add_argument("--current-price", type=float, required=True, help="Current pool price")
    parser.add_argument("--lower", type=float, required=True, help="Lower price bound")
    parser.add_argument("--upper", type=float, required=True, help="Upper price bound")
    parser.add_argument("--coai", type=float, help="COAI amount (base token)")
    parser.add_argument("--usdt", type=float, help="USDT amount (quote token)")
    
    args = parser.parse_args()
    
    if not args.coai and not args.usdt:
        print("❌ ERROR: Must provide either --coai or --usdt")
        return
    
    if args.coai and args.usdt:
        print("❌ ERROR: Provide only ONE of --coai or --usdt")
        return
    
    print("\n" + "=" * 80)
    print("📊 CLMM TOKEN RATIO CALCULATOR")
    print("=" * 80)
    print(f"Current Price: ${args.current_price:.6f}")
    print(f"Range: ${args.lower:.6f} - ${args.upper:.6f}")
    print(f"Width: {((args.upper - args.lower) / args.lower * 100):.2f}%")
    
    # Calculate position of current price in range
    price_position = (args.current_price - args.lower) / (args.upper - args.lower) * 100
    print(f"Price Position: {price_position:.1f}% through range")
    print("=" * 80)
    
    try:
        coai_needed, usdt_needed = calculate_token_ratio(
            args.current_price, args.lower, args.upper,
            coai_amount=args.coai, usdt_amount=args.usdt
        )
        
        print("\n✅ CALCULATED TOKEN AMOUNTS:")
        print(f"   COAI needed: {coai_needed:.4f}")
        print(f"   USDT needed: {usdt_needed:.2f}")
        
        # Calculate total value
        total_value = (coai_needed * args.current_price) + usdt_needed
        coai_value_pct = (coai_needed * args.current_price) / total_value * 100
        usdt_value_pct = usdt_needed / total_value * 100
        
        print(f"\n📊 VALUE BREAKDOWN:")
        print(f"   COAI value: ${coai_needed * args.current_price:.2f} ({coai_value_pct:.1f}%)")
        print(f"   USDT value: ${usdt_needed:.2f} ({usdt_value_pct:.1f}%)")
        print(f"   Total value: ${total_value:.2f}")
        
        print("\n🎯 TO OPEN POSITION:")
        print(f"   python scripts/open_position_smart.py --range-width {((args.upper - args.lower) / args.lower * 100):.2f} \\")
        print(f"     --coai {coai_needed:.4f} --usdt {usdt_needed:.2f}")
        print("=" * 80)
        
    except ValueError as e:
        print(f"\n❌ ERROR: {e}")
        print("=" * 80)

if __name__ == "__main__":
    main()

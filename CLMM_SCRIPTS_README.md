# CLMM Position Management Scripts

## Naming Convention

All scripts related to CLMM (Concentrated Liquidity Market Maker) positions follow this naming pattern:

```
{type}_{connector}_{action}.py
```

- **type**: `clmm` or `test_clmm`
- **connector**: `pancakeswap` (or other DEX)
- **action**: Descriptive name of what the script does

## Script Categories

### 🌟 RECOMMENDED WORKFLOWS

#### Opening New Positions (First Time)
**Use**: `clmm_pancakeswap_optimized_open_position.py`

This implements the **discovery method**:
1. Opens position with SMALLER token amount for both tokens
2. Gateway shows the actual ratio it needs
3. Calculates optimal swap for remaining tokens
4. Then add all remaining to complete deployment

**Result**: 100% capital deployment in 2 steps (open + add)

#### Reopening After Range Exit
**Use**: `clmm_pancakeswap_reopen_position_workflow.py`

Complete workflow when price exits range:
1. Checks current balances (shows which token you have mostly)
2. Calculates optimal swap to rebalance for new position
3. Provides instructions for swap and reopening

**Follow-up**: After swap, use `clmm_pancakeswap_open_new_position.py`

### 📊 Discovery & Analysis

- `clmm_pancakeswap_discover_ratio.py` - Submit large amounts to discover Gateway's required ratio
- `test_clmm_pancakeswap_add_liquidity.py` - Test adding to existing position
- `test_clmm_pancakeswap_swap_usdt_to_coai.py` - Test swap workflow (documents known issues)

### 🔧 Utility Scripts

**Adding Liquidity:**
- `clmm_pancakeswap_add_liquidity_after_swap.py` - Add after manual swap
- `clmm_pancakeswap_add_final_liquidity.py` - Add with correct ratio
- `clmm_pancakeswap_add_remaining_liquidity.py` - Add remaining tokens
- `clmm_pancakeswap_deploy_final_liquidity.py` - Deploy final liquidity

**Swaps:**
- `clmm_pancakeswap_execute_swap.py` - Direct contract swap (incomplete - router issues)
- `clmm_pancakeswap_execute_automated_swap.py` - Test Gateway swap (not working for BSC)
- `clmm_pancakeswap_execute_optimal_swap.py` - Shows manual swap instructions

## Key Learnings

### Gateway Discovery Method

**Problem**: Gateway calculates its own optimal ratio internally, often different from market price.

**Solution**: Let Gateway tell us what it needs!

**For New Positions:**
```python
# 1. Open with smaller amount for BOTH tokens
smaller_value = min(coai_balance * price, usdt_balance)
open_position(coai=smaller_value/price, usdt=smaller_value)

# 2. Gateway uses what it needs, discover the ratio
ratio = usdt_used / coai_used

# 3. Swap remaining to match ratio
# 4. Add all remaining tokens - Gateway accepts 100%!
```

**For Adding to Existing:**
```python
# 1. Submit ALL available tokens
add_liquidity(coai=all_coai, usdt=all_usdt)

# 2. Check what Gateway actually used
ratio = usdt_used / coai_used

# 3. Swap remaining to match ratio
# 4. Add final remaining tokens
```

### Why Gateway Ratio ≠ Market Price

**Example**:
- Market price: 0.432 USDT per COAI
- Gateway ratio: 0.083 USDT per COAI (5x less!)

**Reason**: Price near lower bound of range
- Position converts to mostly COAI as price drops
- Needs very little USDT per COAI to add liquidity
- Gateway ratio reflects POSITION's needs
- Market price reflects SWAP rate

### Token Distribution by Price

```
Position Range: $0.418 - $0.429 (±1.25%)

Price at Lower ($0.418):  100% COAI, 0% USDT
Price at Mid ($0.423):    ~58% COAI, ~42% USDT  
Price at Upper ($0.429):  0% COAI, 100% USDT
```

## Known Issues

### Gateway Swap Not Working for BSC
- **Issue**: Gateway lacks router implementation for PancakeSwap on BSC
- **Workaround**: Manual swap via PancakeSwap UI
- **Status**: Documented in TODO section of IMPLEMENTATION.md

### Direct Contract Swap Failing
- **Issue**: Router call reverts (wrong ABI or parameters)
- **Workaround**: Manual swap
- **Status**: Needs debugging (see `services/pancakeswap_swap_service.py`)

## Network Configuration

⚠️ **CRITICAL**: Use `ethereum-bsc` NOT `bsc-mainnet`

```python
{
    "network": "ethereum-bsc",  # ✅ Correct
    "connector": "pancakeswap"
}
```

## Testing

Run tests to verify functionality:

```bash
# Test adding liquidity
python test_clmm_pancakeswap_add_liquidity.py

# Test swap workflow (shows known issues)
python test_clmm_pancakeswap_swap_usdt_to_coai.py
```

## Future Improvements

1. **Automate swaps**: Once Gateway router support or direct contract method working
2. **Price monitoring**: Auto-close/reopen when approaching range edges
3. **Fee harvesting**: Auto-collect and reinvest fees
4. **Full automation**: Complete position lifecycle management

See IMPLEMENTATION.md for detailed roadmap.

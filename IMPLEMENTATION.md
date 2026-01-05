# CLMM Position Management Implementation Plan

## Overview
Build an automated CLMM position management system that maximizes APR (1,237.42% with 3% range) through:
1. Continuous monitoring of price vs position range
2. Automatic fee harvesting when gas-efficient
3. Automatic position rebalancing when price approaches range edges
4. Optimal token ratio calculations for all operations

## Ultimate Goal: Automated High-APR Position Manager

**Target APR**: 1,237.42% (achievable with 3% range on COAI/USDT)

**Automated Workflow**:

```
┌─────────────────────────────────────────────────────┐
│ MONITOR LOOP (Runs every 1-5 minutes)              │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 1. Check current price vs position range           │
│                                                     │
│    ┌─ Price in range? ─────────────────────────┐  │
│    │                                            │  │
│    │ YES                          NO            │  │
│    │  │                            │            │  │
│    │  ▼                            ▼            │  │
│    │  Check earned fees      CLOSE POSITION     │  │
│    │  │                            │            │  │
│    │  ├─ Fees > min threshold?    ▼            │  │
│    │  │   │                  Swap tokens        │  │
│    │  │   │ YES               for optimal ratio │  │
│    │  │   ▼                        │            │  │
│    │  │   HARVEST & COMPOUND       ▼            │  │
│    │  │   (collect + reinvest)  OPEN NEW        │  │
│    │  │                         POSITION         │  │
│    │  │                         (3% range)       │  │
│    │  ▼                            │            │  │
│    │  Continue monitoring ◄────────┘            │  │
│    │                                            │  │
│    └────────────────────────────────────────────┘  │
│                                                     │
│ 2. Price within 0.5-1% of range edge?              │
│    ├─ YES → Trigger rebalance (close + reopen)     │
│    └─ NO  → Continue monitoring                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Key Parameters**:
- **Position Range**: 3% (±1.5% from current price)
- **Rebalance Trigger**: Price within 0.5-1% of range edge
- **Fee Harvest Threshold**: Dynamic based on gas costs
- **Monitor Frequency**: Every 1-5 minutes

**Expected Outcome**: Maintain ~1,237% APR through tight range + automated rebalancing

**Detailed Workflow with Gas Management**:

```
┌─────────────────────────────────────────────────────────────┐
│                    MONITORING LOOP                          │
│                   (Every 1-5 minutes)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Check Current Price vs Position Range                   │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        Price IN Range           Price NEAR Edge
                │                  (0.5-1% away)
                │                       │
                ▼                       ▼
┌────────────────────────────┐  ┌────────────────────────────┐
│  2. Check Earned Fees      │  │  REBALANCE POSITION        │
└────────────────────────────┘  └────────────────────────────┘
                │                       │
    ┌───────────┴──────────┐            │
    ▼                      ▼            │
Fees < Gas*2         Fees > Gas*2       │
    │                      │            │
    │                      ▼            │
    │            ┌──────────────────┐   │
    │            │  HARVEST FEES    │   │
    │            │  + Reinvest      │   │
    │            └──────────────────┘   │
    │                      │            │
    │                      ▼            │
    │            ┌──────────────────┐   │
    │            │ Increment Harvest│   │
    │            │     Counter      │   │
    │            └──────────────────┘   │
    │                      │            │
    │            ┌─────────┴─────────┐  │
    │            ▼                   ▼  │
    │       Counter < 5         Counter = 5
    │            │                   │  │
    │            │                   ▼  │
    │            │         ┌──────────────────┐
    │            │         │ CHECK BNB BALANCE│
    │            │         └──────────────────┘
    │            │                   │
    │            │         ┌─────────┴─────────┐
    │            │         ▼                   ▼
    │            │    BNB > 0.005         BNB < 0.005
    │            │         │                   │
    │            │         │                   ▼
    │            │         │         ┌──────────────────┐
    │            │         │         │ SWAP → BNB       │
    │            │         │         │ (COAI or USDT)   │
    │            │         │         └──────────────────┘
    │            │         │                   │
    │            │         └─────────┬─────────┘
    │            │                   │
    │            │                   ▼
    │            │         ┌──────────────────┐
    │            │         │ Reset Counter    │
    │            │         └──────────────────┘
    │            │                   │
    └────────────┴───────────────────┴───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ CONTINUE     │
                    │ MONITORING   │
                    └──────────────┘
```

---

## Goals (In Priority Order)

### 1. View Position & Check Earned Fees
**Priority**: HIGH  
**Status**: 🟡 In Progress

**User Need**: "I want to be able to look at my position and see if I've earned fees"

**Current State**:
- ✅ MCP `get_portfolio_overview()` shows LP positions (no fee details)
- 🟡 Started `/gateway/clmm/position-fees/{position_address}` endpoint
- ✅ Gateway `clmm_positions_owned()` returns fee data

**Action Items**:
- [ ] Complete position fees endpoint on `feature/check-available-earned-fees` branch
- [ ] Return pending fees in base and quote tokens
- [ ] Add USD value estimation
- [ ] Add gas cost vs fee value comparison
- [ ] Provide recommendation: "COLLECT_NOW" or "WAIT"

**Success Criteria**:
- Can query position and see exact pending fees
- Get actionable recommendation on whether to collect
- Understand ROI of collecting fees vs gas costs

---

### 2. Calculate Optimal Token Ratio
**Priority**: HIGH  
**Status**: ❌ Not Started

**User Need**: "I want the ability to easily calculate the token ratio when I attempt to add tokens to the liquidity pool so that the pool will accept my submission"

**Current State**:
- ❌ No ratio calculator exists
- ⚠️  Manual estimation caused failed transaction (TX: 0x9a1426d...)
- ❌ Users must guess token amounts

**Action Items**:
- [x] ~~Research CLMM liquidity math formulas~~ - Gateway handles this internally
- [x] **DISCOVERED: Gateway Discovery Method** (Optimal approach!)
- [ ] Document the discovery method as standard practice
- [ ] Create automated workflow scripts
- [ ] Add swap automation (currently manual due to Gateway limitation)

**SOLUTION DISCOVERED - Gateway Discovery Method:**

Instead of calculating ratios ourselves, leverage Gateway's internal calculations:

**For OPENING new positions:**
1. Open with SMALLER token amount for BOTH tokens
   - `min(coai_value, usdt_value)` worth of each
2. Gateway uses what it needs and shows actual ratio
3. Swap remaining tokens to match discovered ratio
4. Add all remaining tokens to complete deployment

**For ADDING to existing positions:**
1. Submit request to add ALL available tokens
2. Gateway uses what it needs based on position's current state
3. Check what was actually used to discover ratio
4. Swap remaining to match ratio
5. Add remaining tokens

**Key Insights:**
- Gateway calculates optimal ratio internally (we don't need to!)
- Ratio depends on position's current tick and liquidity distribution
- Simply submit what you have, Gateway handles the math
- Use discovery method to find exact ratio, then swap to match

**Success Criteria**:
- Can input available tokens and get exact amounts to deposit
- No more reverted transactions due to incorrect ratios
- Clear explanation of why those amounts are optimal

**Technical Notes**:
```
For CLMM positions, token ratio depends on:
- Current price relative to range
- If price < lower: 100% quote token (USDT)
- If price > upper: 100% base token (COAI)
- If price in range: Mixed ratio based on liquidity curve

CRITICAL INSIGHT - Price Movement & Token Distribution:
- As price DROPS toward lower bound → position becomes MORE COAI
- As price RISES toward upper bound → position becomes MORE USDT
- Gateway ratio (0.083 USDT/COAI) ≠ Pool price (0.432 USDT/COAI)
- Gateway ratio reflects POSITION's current token distribution
- Pool price reflects MARKET's current exchange rate

Example (COAI/USDT position: $0.426-$0.437):
- Price at $0.432 (near LOWER bound)
- Position weighted: ~92% COAI, ~8% USDT
- Gateway ratio: 0.083 USDT per COAI (need mostly COAI to add)
- Market ratio: 0.432 USDT per COAI (swap rate)

Rebalancing Strategy:
1. Price drops → position becomes mostly COAI → swap COAI→USDT before exit
2. Price rises → position becomes mostly USDT → swap USDT→COAI before exit
3. If price exits range: position = 100% one token, close & re-enter
```

---

### 3. Harvest Fees & Reinvest
**Priority**: MEDIUM  
**Status**: ⚠️  Blocked by Gateway

**User Need**: "I want the ability to harvest those fees and reinvest them back into the LP, in a single transaction if possible"

**Current State**:
- ✅ API has `/gateway/clmm/collect-fees` endpoint
- ❌ Gateway doesn't implement collect-fees for PancakeSwap V3
- ✅ API has `/gateway/clmm/add` endpoint (working)
- ❌ No combined "collect + reinvest" operation

**Action Items**:

**Phase 1: Gateway Support**
- [ ] Check if Gateway has collect-fees implementation
- [ ] If not: Submit Gateway PR to add PancakeSwap V3 collect-fees
- [ ] Test collect-fees independently

**Phase 2: Reinvest Logic**
- [ ] Create `/gateway/clmm/harvest-and-reinvest` endpoint
- [ ] Workflow:
  1. Collect fees from position
  2. Get collected amounts
  3. Calculate optimal ratio with new amounts
  4. Add liquidity back to same position
- [ ] Handle partial failures gracefully
- [ ] Return transaction hashes for each step

**Phase 3: Single Transaction (Advanced)**
- [ ] Research if Gateway can batch operations
- [ ] If possible: Create multicall for collect+add in one TX
- [ ] Significant gas savings if achievable

**Success Criteria**:
- Can collect fees with one API call
- Fees automatically reinvested optimally
- Minimize transaction count (ideally 1 TX)

---

### 4. Close Position & Watch
**Priority**: MEDIUM  
**Status**: ❌ Blocked by Gateway

**User Need**: "I want the ability to close a position and watch"

**Current State**:
- ✅ API has `/gateway/clmm/close` endpoint
- ❌ Gateway doesn't implement close/decrease-liquidity for PancakeSwap V3
- ⚠️  Currently must close positions manually via PancakeSwap UI
- ❌ No position monitoring/alerts

**Action Items**:

**Phase 1: Gateway Close Support**
- [ ] Submit Gateway PR for PancakeSwap V3 close position
- [ ] Submit Gateway PR for PancakeSwap V3 decrease liquidity (partial removal)
- [ ] Test both operations thoroughly

**Phase 2: Position Monitoring**
- [ ] Create position monitor service/script
- [ ] Monitor:
  - Price vs range boundaries
  - Fee accumulation rate
  - Position health/utilization
  - Impermanent loss estimate
- [ ] Alert when:
  - Price approaching range boundaries
  - Fees exceed gas cost threshold
  - Position goes out of range

**Phase 3: Auto-Rebalancing**
- [ ] Watch price movement
- [ ] Auto-trigger close when price exits range
- [ ] Auto-reopen with new range centered on current price
- [ ] Make fully automated or require confirmation

**Success Criteria**:
- Can close position via API
- Position monitoring dashboard
- Alerts for important events
- Optional auto-rebalancing

---

### 5. Automated Position Manager (NEW - Ultimate Goal)
**Priority**: HIGH  
**Status**: ❌ Not Started

**User Need**: "Automated system that maintains 1,237.42% APR through intelligent position management"

**Requirements**:

**1. Continuous Monitoring**:
- [ ] Monitor current price every 1-5 minutes
- [ ] Check if price is within position range
- [ ] Calculate distance to range edges
- [ ] Track fee accumulation rate
- [ ] Calculate and log current APR in real-time
  - Fetch pool 24h fees and TVL
  - Calculate position multiplier based on range vs active range
  - Formula: `APR = (fees_24h / TVL) * 365 * 100 * multiplier`
  - Track APR over time to understand volatility patterns
  - **Important**: APR fluctuates with price volatility/trading volume
    - Stable price = low volume = lower APR (e.g., 877%)
    - Volatile price = high volume = higher APR (e.g., 1,237%)
    - APR will spike back up when trading activity increases
  - Don't panic if APR drops during quiet periods

**2. Smart Fee Harvesting**:
- [ ] Calculate minimum fee threshold for profitability
- [ ] Formula: `min_fees_usd > (gas_cost_usd * 2)` for 100% profit margin
- [ ] When threshold met: Collect fees + reinvest automatically
- [ ] Track compounding effect over time

**3. Auto-Rebalancing Logic**:
- [ ] Trigger when price within 0.5-1% of range edge
- [ ] **Smart timing**: Consider APR and market conditions
  - Don't rebalance during low APR periods (e.g., < 700%) unless price is exiting range
  - Prefer rebalancing during high APR periods (volatile markets, high volume)
  - Track APR trend: rising vs falling
- [ ] **Dynamic range optimization**:
  - Track how often position goes out of range
  - Calculate "range efficiency": time in range vs APR multiplier
  - Gradually narrow range if staying in range consistently (e.g., 3% → 2.5% → 2%)
  - Widen range if going out of range too frequently (e.g., 2% → 2.5% → 3%)
  - Goal: Find sweetspot where APR stays > 300% constantly with minimal rebalancing
  - Track metrics: rebalances per day, average APR, time out of range
- [ ] Close current position (remove 100% liquidity)
- [ ] Calculate new range (dynamic width based on historical volatility)
- [ ] Swap tokens to optimal ratio
- [ ] Open new position with all available tokens
- [ ] Resume monitoring

**4. Gas Management & Harvest Counter**:
- [ ] Track number of fee harvests performed
- [ ] Trigger gas replenishment every N harvests (e.g., every 5-10 harvests)
- [ ] Calculate optimal BNB amount needed
- [ ] Formula: `bnb_needed = (avg_gas_per_tx * estimated_txs_until_next_refill) * 1.5` (50% buffer)
- [ ] Swap portion of COAI or USDT to BNB
- [ ] Maintain minimum BNB balance threshold (e.g., 0.005 BNB)
- [ ] Alert if BNB falls below critical level (e.g., 0.002 BNB)

**4. Token Rebalancing for Max Liquidity**:
- [ ] After closing position: Check COAI/USDT balances
- [ ] Calculate optimal ratio for 3% range at current price
- [ ] Swap excess token to achieve optimal ratio
- [ ] Use 95-98% of tokens (leave buffer for gas)
- [ ] Maximize LP contribution

**Action Items**:

**Core Components**:
- [ ] Build `PositionMonitor` class
  - Price fetching from DEX
  - Range boundary calculations
  - Fee accumulation tracking
  
- [ ] Build `FeeHarvester` class
  - Gas cost estimation (BSC)
  - Profitability calculator
  - Harvest + reinvest workflow
  
- [ ] Build `PositionRebalancer` class
  - Close position logic
  - Token swap logic
  - Range calculator (3% centered)
  - Open position logic
  
- [ ] Build `TokenRatioOptimizer` class
  - CLMM math implementation
  - Optimal ratio calculator
  - Swap amount calculator
  
- [ ] Build `GasManager` class
  - Track harvest counter
  - Monitor BNB balance
  - Calculate gas replenishment needs
  - Execute COAI/USDT → BNB swaps
  
- [ ] Build `RangeOptimizer` class (NEW)
  - Track position history: rebalances, time in/out of range, APR
  - Calculate range efficiency metrics
  - Recommend range adjustments based on performance
  - Implement machine learning approach: test → measure → adjust
  - Goal: Maximize APR while minimizing rebalances

**Configuration**:
```python
MONITOR_INTERVAL = 180  # seconds (3 minutes)
POSITION_RANGE_PCT = 3.0  # 3% range (±1.5%) - DYNAMIC, will adjust based on performance
REBALANCE_TRIGGER_PCT = 0.5  # Rebalance when within 0.5% of edge
MIN_FEE_PROFIT_MARGIN = 2.0  # Fees must be 2x gas cost
GAS_PRICE_GWEI = 3  # BSC typical gas price
SLIPPAGE_PCT = 1.0
TOKEN_USE_PCT = 0.97  # Use 97% of tokens, keep 3% buffer

# Range Optimization Strategy (NEW)
RANGE_MIN_WIDTH = 1.5  # Minimum range width (%) - tightest allowed
RANGE_MAX_WIDTH = 5.0  # Maximum range width (%) - widest allowed
RANGE_START_WIDTH = 3.0  # Starting range width (%)
RANGE_ADJUSTMENT_STEP = 0.25  # Adjust range by ±0.25% per iteration
MAX_REBALANCES_PER_DAY = 6  # If exceeding this, widen range
MIN_REBALANCES_PER_DAY = 1  # If below this and APR high, try narrower range
TARGET_TIME_IN_RANGE_PCT = 95  # Aim to be in range 95% of the time
RANGE_OPTIMIZATION_WINDOW = 7  # Days of history to analyze for range adjustments

# Range Refinement Logic:
# - If rebalancing > 6x/day: Widen range by 0.25% (too narrow)
# - If rebalancing < 1x/day AND APR > 500%: Narrow range by 0.25% (room for tighter)
# - If APR drops below 300%: Immediately widen range
# - If time out of range > 5%: Widen range
# Goal: Find optimal range where APR stays > 300% with minimal rebalancing

# APR Management
TARGET_APR_MIN = 300  # Absolute minimum APR (%) - widen range if below this
TARGET_APR_OPTIMAL = 1000  # Optimal APR target (%)
APR_CHECK_INTERVAL = 300  # Check APR every 5 minutes
REBALANCE_APR_THRESHOLD = 700  # Only rebalance if APR > this (unless price exiting range)
# Note: APR fluctuates with market volatility
# - Stable periods: ~700-900% APR
# - Volatile periods: ~1,000-1,400% APR

# Gas Management
HARVEST_COUNT_TRIGGER = 5  # Refill BNB every 5 fee harvests
MIN_BNB_BALANCE = 0.005  # Minimum BNB to maintain (in BNB) - below this, trigger refill
TARGET_BNB_BALANCE = 0.03  # Target balance to refill to (in BNB) - provides ~60 transactions
CRITICAL_BNB_BALANCE = 0.002  # Alert threshold (in BNB) - emergency warning
AVG_GAS_PER_TX = 0.0005  # Average BNB per transaction on BSC (conservative estimate)
ESTIMATED_TXS_UNTIL_REFILL = 40  # Expected transactions before next refill
GAS_BUFFER_MULTIPLIER = 1.5  # 50% safety buffer
# Refill logic: When BNB < MIN_BNB_BALANCE, swap enough to reach TARGET_BNB_BALANCE
# Example: If at 0.003 BNB, swap ~$16 worth to get to 0.03 BNB (0.027 BNB needed)
```

**Success Criteria**:
- Maintains position within 3% range automatically
- Harvests fees when profitable (>2x gas cost)
- Rebalances before price exits range
- Achieves consistent ~1,200%+ APR
- Runs unattended 24/7
- Handles errors gracefully (alerts on failure)

---

## Implementation Phases

### Phase 1: Information & Monitoring ✅ START HERE
**Timeline**: 1-2 days  
**Dependencies**: None (uses existing MCP/API)

**Deliverables**:
1. ✅ Position fees checker endpoint (complete existing work)
2. ✅ Token ratio calculator utility
3. ✅ Position monitoring dashboard script
4. ✅ Documentation and examples

**Why First**: These tools provide immediate value without waiting for Gateway changes.

---

### Phase 2: Gateway Extensions
**Timeline**: 3-5 days (includes PR review time)  
**Dependencies**: Access to Gateway repo, Hummingbot team review

**Deliverables**:
1. Gateway PR: PancakeSwap V3 collect-fees
2. Gateway PR: PancakeSwap V3 close/decrease-liquidity
3. Integration tests
4. Update API to use new Gateway features

**Why Second**: Unblocks advanced features, benefits entire Hummingbot community.

---

### Phase 3: Advanced Operations
**Timeline**: 2-3 days  
**Dependencies**: Phase 1 & 2 complete

**Deliverables**:
1. Harvest & reinvest workflow
2. Position monitoring service
3. Auto-rebalancing (optional)
4. Comprehensive testing

**Why Last**: Builds on all previous work to create powerful automation.

---

## Current Progress

### Completed ✅
- [x] Uncommented `/gateway/clmm/add` endpoint
- [x] Uncommented `/gateway/clmm/remove` endpoint  
- [x] Fixed `clmm_add_liquidity()` Gateway client method
- [x] Fixed `clmm_remove_liquidity()` Gateway client method
- [x] Updated Gateway API paths to use connector-specific routes
- [x] Successfully tested add liquidity (TX: 0x49c15ee...)
- [x] Created test infrastructure in `tests/` folder
- [x] Identified Gateway limitations (no close/collect for PancakeSwap V3)

### In Progress 🟡
- [x] Branch created: `feature/check-available-earned-fees`
- [x] Added `CLMMPositionFeesRequest` model
- [x] Added `CLMMPositionFeesResponse` model
- [x] Started `/gateway/clmm/position-fees/{position_address}` endpoint
- [ ] Complete fee value calculations
- [ ] Add gas cost estimation
- [ ] Test endpoint thoroughly

### Not Started ❌
- [ ] Token ratio calculator
- [ ] Position monitoring dashboard
- [ ] Gateway PR for collect-fees
- [ ] Gateway PR for close position
- [ ] Harvest & reinvest workflow
- [ ] Auto-rebalancing
- [ ] Gas management system (BNB refill after N harvests)
- [ ] Full automation loop (monitoring + all triggers)

---

## Technical Notes

### CLMM Liquidity Math
For accurate ratio calculations, need to implement:

```python
def calculate_liquidity_amounts(
    current_price: Decimal,
    lower_price: Decimal,
    upper_price: Decimal,
    amount_base: Decimal,
    amount_quote: Decimal
) -> tuple[Decimal, Decimal]:
    """
    Calculate optimal token amounts for CLMM position.
    
    Based on Uniswap V3 math:
    - liquidity = sqrt(amount0 * amount1)
    - Different formula when price is in/out of range
    """
    # Implementation needed
    pass
```

### Gateway API Patterns
Current working pattern for PancakeSwap V3:
```python
connector = "pancakeswap"  # NOT "pancakeswap_v3_bsc"
network = "ethereum-bsc"    # NOT "bsc-mainnet"
```

### Known Issues
1. **Gateway Missing Features**: PancakeSwap V3 doesn't have:
   - collect-fees implementation
   - close/decrease-liquidity implementation
   - Position info endpoint (uses positions-owned workaround)

2. **Token Ratio**: No automatic calculation causes:
   - Reverted transactions
   - Wasted gas fees
   - Poor user experience

3. **Fee Visibility**: Hard to know:
   - How much fees accumulated
   - When it's worth collecting
   - ROI of collection

---

## Testing Strategy

### Unit Tests
- [ ] Ratio calculator with various price scenarios
- [ ] Fee value calculations
- [ ] Gas cost estimations

### Integration Tests  
- [ ] Complete workflow: open → add → collect → close
- [ ] Error handling for reverted transactions
- [ ] Multiple connectors (Meteora, PancakeSwap, Raydium)

### Manual Testing
- [x] Add liquidity (successful)
- [ ] Collect fees (blocked)
- [ ] Close position (blocked)
- [ ] Ratio calculator validation

---

## Success Metrics

### Immediate (Phase 1)
- Zero reverted transactions due to incorrect ratios
- Can view fees without checking blockchain directly
- Clear recommendation on when to collect fees

### Medium Term (Phase 2)
- Can collect fees via API
- Can close positions via API
- Gateway features merged and available

### Long Term (Phase 3)
- Automated fee harvesting
- Automated position rebalancing
- 50%+ reduction in manual position management

---

## Next Steps

**Immediate Action** (Choose One):

**Option A: Complete Fee Checker** (Recommended)
1. Finish position fees endpoint
2. Test with real position
3. Commit to feature branch
4. Prepare for PR

**Option B: Build Ratio Calculator**  
1. Research CLMM math formulas
2. Create utility function
3. Add to API as endpoint
4. Create test cases

**Option C: Position Monitor Script**
1. Use existing MCP tools
2. Create monitoring dashboard
3. Add alerts for key events
4. Document usage

**Which would you like to start with?** 

I recommend Option A (Complete Fee Checker) since we already have the foundation and it provides immediate visibility into your positions.

---

## Performance Tracking & Optimization Log

### Purpose
Track actual performance metrics over time to validate and refine our automation strategy. This data-driven approach ensures we're optimizing based on real results, not assumptions.

### Baseline Metrics (January 5, 2026)

**Position Details:**
- Position ID: 6221178
- Pool: COAI/USDT (0xbc0E5A205D729299D93973d634E2507CD8b625A3)
- Fee Tier: 0.25%
- Range: $0.429575506 - $0.447105921 (4.06% width)
- Current Price: $0.431550

**Performance Snapshot:**
- Current APR: 877.03% (observed down from 1,237.42% peak)
- APR Range Observed: 700% - 1,237%
- APR Behavior: Drops during price stability, rises during volatility
- Position TVL: ~$1,000 USD equivalent

**Compound Interest Analysis:**
```
Conservative (700% APR):  76.81% monthly return
Realistic (900% APR):     107.66% monthly return  
Optimistic (1,237% APR):  171.79% monthly return
Minimum Target (300%):    27.83% monthly return

Compounding Advantage (900% APR, 30 days):
  Simple Interest:   +$739.73 profit
  Compound Interest: +$1,076.64 profit
  Bonus from Daily Reinvestment: +$336.92 (45.5% more)
```

**Key Insight:**
✅ Profitability is driven by trading VOLUME (fees), not token PRICE movement.
✅ Narrow range (4.06%) captures concentrated liquidity = higher APR multiplier.
✅ Daily compounding creates exponential growth even at conservative APRs.

---

### Optimization Iterations

#### Iteration 1: Baseline (Manual Management)
**Date Range:** [Start Date] - [End Date]  
**Configuration:**
- Range Width: 4.06%
- Rebalancing: Manual
- Fee Collection: Manual
- Gas Management: Manual

**Metrics:**
- [ ] Average APR: ____%
- [ ] Rebalances Performed: ___
- [ ] Time Out of Range: ___%
- [ ] Gas Costs: $___
- [ ] Net Profit: $___
- [ ] Actual ROI: ___%

**Observations:**
- [ ] [Record what worked well]
- [ ] [Record challenges/issues]
- [ ] [Record unexpected behaviors]

---

#### Iteration 2: [Automation Feature Added]
**Date Range:** [Start Date] - [End Date]  
**Configuration:**
- Range Width: ___%
- Rebalancing: [Manual/Automated]
- Fee Collection: [Manual/Automated]
- Gas Management: [Manual/Automated]
- [Other changes]

**Metrics:**
- [ ] Average APR: ____%
- [ ] Rebalances Performed: ___
- [ ] Time Out of Range: ___%
- [ ] Gas Costs: $___
- [ ] Net Profit: $___
- [ ] Actual ROI: ___%

**Comparison to Previous:**
- [ ] APR Change: ±___%
- [ ] Rebalance Frequency: ±___
- [ ] Profit Improvement: ±$___
- [ ] Time Saved: ___ hours

**Observations:**
- [ ] [What improved?]
- [ ] [What got worse?]
- [ ] [What to adjust next?]

---

### Target Metrics (Goals)

**Primary Objectives:**
- ✅ Maintain APR > 300% constantly
- ✅ Keep time in range > 95%
- ✅ Limit rebalances to < 6 per day
- ✅ Net positive after gas costs

**Performance Benchmarks:**
```
Excellent:  APR > 800%, < 4 rebalances/day, > 98% in range
Good:       APR > 500%, < 6 rebalances/day, > 95% in range
Acceptable: APR > 300%, < 8 rebalances/day, > 90% in range
Poor:       APR < 300%, > 10 rebalances/day, < 85% in range
```

**Range Optimization Progress:**
- [ ] Starting Width: 4.06%
- [ ] Current Optimal Width: ___%
- [ ] Adjustment History: [Track each change]
- [ ] Sweetspot Found: [Yes/No/Testing]

---

### Data Collection Checklist

**Daily Tracking:**
- [ ] Morning APR snapshot
- [ ] Evening APR snapshot
- [ ] Rebalances triggered (count + reasons)
- [ ] Time out of range (minutes)
- [ ] Gas costs incurred
- [ ] Fees collected

**Weekly Analysis:**
- [ ] Average APR for week
- [ ] Total rebalances
- [ ] Total gas costs
- [ ] Net profit calculation
- [ ] Range width adjustments needed
- [ ] Strategy refinements identified

**Monthly Review:**
- [ ] Compare to baseline metrics
- [ ] Calculate actual compound returns
- [ ] Validate optimization improvements
- [ ] Update target parameters if needed
- [ ] Document lessons learned

---

### Notes & Insights

**Market Behavior Observations:**
- APR volatility correlates with trading volume
- Stable price periods = lower APR (~700-900%)
- Volatile price periods = higher APR (~1,000-1,400%)
- Price stability ≠ bad (still 700%+ APR)

**Strategy Refinements:**
- [Add insights as we learn]
- [Document what works]
- [Document what doesn't]

**Future Considerations:**
- [ ] Test multiple ranges simultaneously (different positions)
- [ ] Compare 0.25% vs 1% fee tiers
- [ ] Analyze optimal times to widen/narrow range
- [ ] Develop APR prediction model based on volatility

---

### Data Export

**Last Updated:** January 5, 2026  
**Next Review Date:** [Set date]  
**Data Location:** `scripts/performance_data/` (to be created)

**Export Format:**
```json
{
  "date": "2026-01-05",
  "position_id": 6221178,
  "range_width_pct": 4.06,
  "current_price": 0.431550,
  "apr_current": 877.03,
  "apr_24h_avg": null,
  "apr_7d_avg": null,
  "rebalances_24h": 0,
  "time_out_of_range_pct": 0,
  "gas_costs_usd": 0,
  "fees_collected_usd": 0,
  "net_profit_usd": 0,
  "notes": "Baseline measurement - manual management"
}
```

---

## CRITICAL LEARNINGS: Optimal Liquidity Deployment

### Date: January 5, 2026
### Session: Position Opening & Liquidity Management

### 🎯 The Problem We Solved

**Issue**: When opening CLMM positions with imbalanced token ratios, we were making multiple transactions and deploying sub-optimal liquidity.

**Example Case**:
- Starting balance: 182.14 COAI, 29.89 USDT (~$108 total)
- Pool requires: 0.4377 USDT per COAI
- Our ratio: 0.1641 USDT per COAI (62.5% off!)

### ❌ What We Did Wrong (Incremental Approach)

```
Step 1: Opened position with 44.21 COAI + 29.29 USDT = $67.40
Step 2: Added 8.57 COAI + 5.68 USDT = $9.40
Step 3: Closed tiny position, added 10.80 COAI + 6.27 USDT = $10.94
---
Total Deployed: ~$68.74 over 3+ transactions
Remaining: ~$40 of unused COAI
```

**Problems**:
1. Multiple transactions = multiple gas fees
2. Only deployed 63% of available capital
3. Complex multi-step process
4. Still had ~$40 in unused COAI

### ✅ What We Should Have Done (Optimized Approach)

```
Step 1: Swap 57.28 COAI → 24.52 USDT
Step 2: Deploy 122.36 COAI + 53.32 USDT = $106.22
---
Total Deployed: $106.22 in ONE transaction
Efficiency: 54% more liquidity deployed!
```

### 🧮 The Math: Uniswap V3 Position Ratio Calculation

For a position in range `[P_lower, P_upper]` at current price `P`:

**Required Ratio** (USDT per COAI):
```python
from math import sqrt

sqrt_p = sqrt(current_price)
sqrt_lower = sqrt(price_lower)
sqrt_upper = sqrt(price_upper)

# Pool's required ratio
pool_ratio = (sqrt_p - sqrt_lower) * sqrt_upper * sqrt_p / (sqrt_upper - sqrt_p)
```

**For our 2.5% range at $0.432327**:
```
Price range: $0.426923 - $0.437731
Required ratio: 0.4377 USDT per COAI
```

### 🔧 Optimal Deployment Algorithm

```python
def calculate_optimal_deployment(coai_balance, usdt_balance, current_price, pool_ratio):
    """
    Calculates optimal swap and deployment amounts
    
    Returns: (coai_to_deploy, usdt_to_deploy, amount_to_swap, swap_direction)
    """
    current_ratio = usdt_balance / coai_balance
    
    # If within 5% of target, deploy directly
    if abs(current_ratio - pool_ratio) / pool_ratio < 0.05:
        # Use limiting factor
        max_from_coai = coai_balance
        max_from_usdt = usdt_balance / pool_ratio
        
        if max_from_coai < max_from_usdt:
            return coai_balance * 0.98, coai_balance * 0.98 * pool_ratio, 0, None
        else:
            return usdt_balance / pool_ratio * 0.98, usdt_balance * 0.98, 0, None
    
    # Too much COAI? Swap COAI → USDT
    if current_ratio < pool_ratio:
        # Solve: (usdt + x * price) / (coai - x) = pool_ratio
        coai_to_swap = (pool_ratio * coai_balance - usdt_balance) / (current_price + pool_ratio)
        
        coai_after = coai_balance - coai_to_swap
        usdt_after = usdt_balance + coai_to_swap * current_price * 0.99  # 1% slippage
        
        return coai_after * 0.98, usdt_after * 0.98, coai_to_swap, "COAI→USDT"
    
    # Too much USDT? Swap USDT → COAI
    else:
        usdt_to_swap = (usdt_balance - pool_ratio * coai_balance) / (1 + pool_ratio / current_price)
        
        coai_after = coai_balance + usdt_to_swap / current_price * 0.99
        usdt_after = usdt_balance - usdt_to_swap
        
        return coai_after * 0.98, usdt_after * 0.98, usdt_to_swap, "USDT→COAI"
```

### 📝 Implementation: Quote Endpoint

**Created**: `POST /gateway/clmm/quote`

**Purpose**: Preview exact token amounts needed for a position WITHOUT executing transaction

**Request**:
```json
{
  "connector": "pancakeswap",
  "network": "ethereum-bsc",
  "pool_address": "0xbc0E5A205D729299D93973d634E2507CD8b625A3",
  "lower_price": 0.426923,
  "upper_price": 0.437731,
  "base_token_amount": 155.51  // Provide ONE token amount
  // OR "quote_token_amount": 94.65
}
```

**Response**:
```json
{
  "base_token_amount": "155.51",
  "quote_token_amount": "94.65",
  "liquidity": "19755",
  "in_range": true
}
```

**Key Feature**: Security - calculate amounts BEFORE submitting transaction to prevent malicious pools from taking unexpected amounts.

### 🎯 New Workflow Scripts

**1. `scripts/optimize_deployment.py`**
- Analyzes current token balances vs pool requirements
- Calculates optimal swap amount if needed
- Provides deployment plan with expected total liquidity

**2. `scripts/add_liquidity_to_position.py`**
- Adds liquidity to EXISTING position (uses `/gateway/clmm/add`)
- Uses quote endpoint to calculate exact amounts
- Avoids creating duplicate positions

**Key Distinction**:
- `POST /gateway/clmm/open` - Opens NEW position
- `POST /gateway/clmm/add` - Adds to EXISTING position

### 🚀 Updated Optimal Workflow

```
STEP 1: Get Balances
├─ Use: mcp_hummingbot-mc_get_portfolio_overview(include_balances=True)
└─ Result: COAI balance, USDT balance

STEP 2: Get Pool Price
├─ Use: POST /gateway/clmm/pool-info
└─ Result: current_price

STEP 3: Calculate Pool Ratio
├─ Use: Uniswap V3 math (sqrt formulas)
└─ Result: required USDT per COAI

STEP 4: Analyze Balance Ratio
├─ Compare: your_ratio vs pool_ratio
└─ Decision:
    ├─ Match (< 5% diff) → Deploy directly
    └─ Mismatch → Calculate swap needed

STEP 5a: If Swap Needed
├─ Calculate: optimal swap amount
├─ Execute: Swap via PancakeSwap
└─ Wait: for settlement (~30s)

STEP 5b: Quote Position
├─ Use: POST /gateway/clmm/quote with smaller token
└─ Result: Exact amounts for both tokens

STEP 6: Deploy Position
├─ Use: mcp_hummingbot-mc_manage_gateway_clmm_positions(action='open_position')
└─ Result: Position opened with MAXIMUM liquidity in ONE transaction
```

### 📊 Performance Comparison

| Metric | Incremental | Optimized | Improvement |
|--------|------------|-----------|-------------|
| Transactions | 3+ | 2 | 33% fewer |
| Liquidity Deployed | $68.74 | $106.22 | +54% |
| Capital Efficiency | 63% | 98% | +35pp |
| Gas Costs | 3x fees | 2x fees | 33% savings |

### 🔑 Key Takeaways

1. **Always calculate pool ratio FIRST** before opening positions
2. **Quote endpoint is essential** - preview before executing
3. **Swap for optimal ratio** when >5% off target
4. **One large position > multiple small positions** (gas efficiency)
5. **Use ADD endpoint** for existing positions, not OPEN

### 🛠️ Tools Created

**API Components:**
| File | Purpose |
|------|---------|
| `models/gateway_trading.py` | Added CLMMQuoteRequest/Response models |
| `routers/gateway_clmm.py` | Added POST /gateway/clmm/quote endpoint |
| `services/pancakeswap_swap_service.py` | Direct PancakeSwap V3 swap service (web3.py) |

**CLMM Management Scripts** (prefix: `clmm_pancakeswap_`):
| File | Purpose |
|------|---------|
| `clmm_pancakeswap_optimized_open_position.py` | ✅ **RECOMMENDED**: Open position with discovery method |
| `clmm_pancakeswap_reopen_position_workflow.py` | Complete workflow for reopening after range exit |
| `clmm_pancakeswap_open_new_position.py` | Open position after rebalancing swap |
| `clmm_pancakeswap_discover_ratio.py` | Discover Gateway's required ratio for position |
| `clmm_pancakeswap_add_liquidity_after_swap.py` | Add liquidity after manual swap |
| `clmm_pancakeswap_add_final_liquidity.py` | Add remaining liquidity with correct ratio |
| `clmm_pancakeswap_add_remaining_liquidity.py` | Add remaining tokens to complete deployment |
| `clmm_pancakeswap_deploy_final_liquidity.py` | Deploy final liquidity after swap |
| `clmm_pancakeswap_execute_swap.py` | Execute swap using direct contract (incomplete) |
| `clmm_pancakeswap_execute_automated_swap.py` | Test Gateway swap automation |
| `clmm_pancakeswap_execute_optimal_swap.py` | Manual swap instructions |

**Test Files** (prefix: `test_clmm_pancakeswap_`):
| File | Purpose |
|------|---------|
| `test_clmm_pancakeswap_add_liquidity.py` | Test adding liquidity to existing position |
| `test_clmm_pancakeswap_swap_usdt_to_coai.py` | Test swap workflow documentation |
| `test_clmm_pancakeswap_direct_swap.py` | Test direct contract swap service |

**Legacy/Utility Scripts:**
| File | Purpose |
|------|---------|
| `scripts/optimize_deployment.py` | Analyzes and plans optimal deployment |
| `scripts/add_liquidity_to_position.py` | Adds liquidity to existing positions |
| `scripts/close_position.py` | Closes positions and returns liquidity |

### 📈 Real Results

**Session Date**: January 5, 2026

**Positions Created**:
1. Position 6223639 (test): 1.2 COAI + 0.6 USDT - CLOSED
2. Position 6223672 (main): Started with 44.21 COAI + 29.29 USDT
   - Added: 8.57 COAI + 5.68 USDT
   - Added: 10.80 COAI + 6.27 USDT
   - **Total**: ~63.58 COAI + ~41.24 USDT (~$68.74)

**Current APR**: 1,445.11% (2.5% range width)

**Remaining Capital**: ~128 COAI (~$55 worth) - needs swap to deploy

### 🎓 Lessons for Automation

When building the automated rebalancing system:

1. **Pre-calculate swap needs** before closing old position
2. **Quote new position** before executing swap
3. **Execute in optimal order**: Close → Swap → Quote → Open
4. **Handle edge cases**: What if pool ratio changed between calculations?
5. **Gas optimization**: Batch operations when possible

### 🔄 Next Steps

1. ✅ Document learnings in IMPLEMENTATION.md
2. 🚧 Implement automated swap functionality
   - **Current Status**: Gateway swap returns empty data for PancakeSwap/BSC
   - **Root Cause**: Gateway doesn't have router implementation for PancakeSwap on BSC (only CLMM)
   - **Short-term Solution**: Direct smart contract calls to PancakeSwap V3 Router (0x1b81D678ffb9C0263b24A97847620C99d213eB14)
   - **Long-term TODO**: Extend Gateway to support PancakeSwap router on BSC
   - **Implementation**: Creating direct web3.py integration for swaps
3. [ ] Create end-to-end automation script
4. [ ] Test with remaining $55 COAI
5. [ ] Build monitoring system for automated rebalancing

---

## TODO: Gateway Extension

**Date Added**: January 5, 2026  
**Priority**: Medium (workaround exists)  
**Status**: Backlog

### Issue
Gateway's `/connectors/pancakeswap/router/quote-swap` and `/connectors/pancakeswap/router/execute-swap` endpoints return empty data for BSC:
```json
{
  "price": "0",
  "amount_in": null,
  "amount_out": null
}
```

### Root Cause
- Gateway has CLMM (liquidity) support for PancakeSwap V3 on BSC ✅
- Gateway lacks Router (swap) support for PancakeSwap V3 on BSC ❌
- PancakeSwap connector exists but may only support other chains

### Impact
- Cannot use unified Gateway API for swaps on BSC
- Must implement direct smart contract calls as workaround
- Automation scripts need chain-specific swap logic

### Proposed Solution
Extend Gateway's PancakeSwap connector to support router operations on BSC:

1. **Add Router Interface** to `pancakeswap.yml` connector
2. **Implement Quote Logic**: Query PancakeSwap V3 Quoter contract
3. **Implement Execute Logic**: Call SwapRouter with proper encoding
4. **Add BSC Network Support**: Ensure BSC mainnet is available in connector config
5. **Test**: Verify quote and execute work for BSC tokens

### Workaround (Current)
Direct smart contract integration in our API:
- Use web3.py to call PancakeSwap V3 contracts directly
- Bypass Gateway for swap operations only
- Still use Gateway for CLMM (liquidity) operations

### Files to Modify (Future)
- `gateway/src/connectors/pancakeswap/pancakeswap.ts` (or equivalent)
- `gateway-files/conf/connectors/pancakeswap.yml`
- Add router ABI and contract addresses for BSC

### References
- PancakeSwap V3 Router: `0x1b81D678ffb9C0263b24A97847620C99d213eB14`
- PancakeSwap V3 Quoter: `0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997`
- Gateway Repo: https://github.com/hummingbot/gateway

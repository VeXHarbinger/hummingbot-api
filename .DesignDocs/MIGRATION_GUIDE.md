# PancakeSwap CLMM LP BSC - Migration Guide

## Overview
This document describes all code changes required to support PancakeSwap CLMM (Concentrated Liquidity Market Maker) liquidity position management on BSC (Binance Smart Chain) with MasterChef staking/unstaking capabilities. These changes should be applied to the `pancakeswap-clmm-lp-bsc` branch.

**Date**: February 18, 2026  
**Base Branch**: `development`  
**Target Branch**: `pancakeswap-clmm-lp-bsc`  
**Source Branch**: `feature/clmm-add-remove-liquidity` (main)

---

## Files Modified (Git-Tracked)

### 1. `services/gateway_client.py`
**Purpose**: Add Gateway API methods for PancakeSwap MasterChef staking/unstaking.

**Changes**:
- Add parameter `network` to `add_wallet()` method signature to support network-specific wallet configurations
- Update method documentation for wallet addition
- Add two new methods at the end of the class (after `poll_transaction`):
  - `clmm_stakeNft()` - Stake NFT in PancakeSwap MasterChef contract
  - `clmm_unstakeNft()` - Unstake NFT from PancakeSwap MasterChef contract

**Key Addition**:
```python
async def clmm_stakeNft(self, chain: str, network: str, wallet_address: str, nft_id: str, amount: Decimal) -> Dict:
    """Stake NFT in PancakeSwap MasterChef contract"""
    path = "connector/pancakeswap/masterchef/stake"
    json_payload = {
        "chain": chain,
        "network": network,
        "wallet_address": wallet_address,
        "nft_id": nft_id,
        "amount": str(amount)
    }
    return await self._request("POST", path, json=json_payload)

async def clmm_unstakeNft(self, chain: str, network: str, wallet_address: str, nft_id: str, amount: Decimal) -> Dict:
    """Unstake NFT in PancakeSwap MasterChef contract"""
    path = "connector/pancakeswap/masterchef/unstake"
    json_payload = {
        "chain": chain,
        "network": network,
        "wallet_address": wallet_address,
        "nft_id": nft_id,
        "amount": str(amount)
    }
    return await self._request("POST", path, json=json_payload)
```

---

### 2. `models/gateway_trading.py`
**Purpose**: Add request/response models for PancakeSwap MasterChef operations.

**Changes**:
Add three new model classes at the end of the file:

1. **`PancakeMasterchefUnstakeAndCloseRequest`** - Input model for unstake+close operation
   - `network: str` - Network name (e.g., 'bsc')
   - `wallet_address: str` - Wallet address that owns the NFT
   - `token_id: int` - NFT position ID to unstake and close

2. **`PositionClosedDetails`** - Details about closed position
   - `fee: Decimal` - Transaction gas fee
   - `position_rent_refunded: Decimal` - Position rent refund (if applicable)
   - `base_token_amount_removed: Decimal` - Base token liquidity removed
   - `quote_token_amount_removed: Decimal` - Quote token liquidity removed
   - `base_fee_amount_collected: Decimal` - Base token fees collected
   - `quote_fee_amount_collected: Decimal` - Quote token fees collected

3. **`PancakeMasterchefUnstakeAndCloseResponse`** - Response after unstake+close
   - `message: str` - Success message
   - `unstake_transaction: str` - Transaction hash from unstake
   - `close_transaction: str` - Transaction hash from close
   - `position_closed: PositionClosedDetails` - Details about closed position

**Location**: Add to end of file after `CLMMPoolListResponse` class.

---

### 3. `models/__init__.py`
**Purpose**: Export new models for use throughout the application.

**Changes**:
Add to imports/exports:
```python
PancakeMasterchefUnstakeAndCloseRequest,
PositionClosedDetails,
PancakeMasterchefUnstakeAndCloseResponse,
```

---

### 4. `models/gateway.py`
**Purpose**: Add MasterChef-related models for Gateway integration.

**Changes**:
- Add `MasterchefKnowsPoolRequest` model with fields:
  - `network: str` - Network name (e.g., 'bsc')
  - `poolAddress: str` - Pool contract address

- Add `MasterchefKnowsPoolResponse` model with fields:
  - `poolId: str` - Pool ID if known, or empty string
  - `known: bool` - True if pool is known to MasterChef

**Location**: Add near other Gateway models (at end of file).

---

### 5. `routers/gateway_clmm.py`
**Purpose**: Add API endpoints for PancakeSwap MasterChef operations.

**Changes**:

1. **Add endpoint: `POST /gateway/connector/pancakeswap/masterchef-knows-pool`**
   - Summary: "Check if PancakeSwap MasterChef knows a pool"
   - Description: "Checks if a given pool address is known to the PancakeSwap MasterChef contract"
   - Operation ID: `masterchefKnowsPool`
   - Request: `MasterchefKnowsPoolRequest` (network, poolAddress)
   - Response: `MasterchefKnowsPoolResponse` (poolId, known)
   - Implementation: Call `gateway_client.masterchef_knows_pool()` with network and pool_address

2. **Ensure existing CLMM endpoints use correct network parameter**:
   - Verify that all Gateway calls use `network` parameter consistently
   - Example: When calling Gateway endpoints, use `network` instead of combined format where possible

**Key New Endpoint Implementation**:
```python
@router.post(
    "/connector/pancakeswap/masterchef-knows-pool",
    response_model=MasterchefKnowsPoolResponse,
    tags=["Gateway CLMM"],
    summary="Check if PancakeSwap MasterChef knows a pool",
    description="Checks if a given pool address is known to the PancakeSwap MasterChef contract...",
    operation_id="masterchefKnowsPool"
)
async def masterchef_knows_pool(
    request: MasterchefKnowsPoolRequest = Body(...),
    accounts_service: AccountsService = Depends(get_accounts_service),
):
    """Implementation calls gateway_client.masterchef_knows_pool(network, pool_address)"""
    # Returns MasterchefKnowsPoolResponse with poolId and known status
```

---

### 6. `routers/gateway.py`
**Purpose**: Add/update main Gateway router endpoints.

**Changes**:
- Ensure MasterChef-related endpoints are properly routed
- Add unstake-and-close endpoint if not already present
- Verify all Pancakeswap/CLMM routes are correctly configured

---

### 7. `services/accounts_service.py`
**Purpose**: Ensure Gateway client methods are accessible through the service layer.

**Changes**:
- Verify that `gateway_client` instance has `clmm_stakeNft()` and `clmm_unstakeNft()` methods
- Add methods if not present to call corresponding Gateway endpoints
- Ensure proper error handling and logging

---

### 8. `routers/accounts.py`
**Purpose**: Add account-level endpoints for staking operations.

**Changes**:
- Add endpoints if needed for account-specific staking operations
- Ensure endpoints use the accounts service to call Gateway client methods

---

### 9. `docker-compose.yml`
**Purpose**: Configuration updates for Gateway service.

**Changes**:
- Verify Gateway service is properly configured for BSC network
- Ensure environment variables are set for Pancakeswap/CLMM operations
- Check that Gateway volumes mount configuration files correctly

---

## Value Conversion & Error Fixes

### Key Data Conversions
1. **Decimal Amounts**: All token amounts should be converted to `Decimal` type for precision
   - Use `Decimal(str(value))` to avoid floating-point errors
   - Convert back to `str()` when sending to Gateway API

2. **Network Parameter Handling**:
   - Input format: `bsc` or `ethereum-bsc` (canonical: `ethereum-bsc`)
   - When calling Gateway: Use the `network` parameter separately from `chain`
   - Example: chain=`ethereum`, network=`bsc` (not combined as `ethereum-bsc`)

3. **Amount Conversion**:
   - Gateway returns amounts as strings or floats
   - Convert to `Decimal` for database storage and calculations
   - Convert back to `str()` before sending to Gateway

4. **Address Format**:
   - Ensure addresses are checksummed (Web3.to_checksum_address)
   - Store in database as lowercase for consistency
   - Return with proper casing based on chain requirements

### Common Error Fixes

1. **ZERO_LIQUIDITY Error**:
   - Occurs when: Position provides insufficient liquidity
   - Solution: Always provide both base and quote amounts
   - Use `quote-position` endpoint first to get estimated amounts
   - Pass both amounts to `open-position` endpoint

2. **Network/Chain Mismatch**:
   - Occurs when: Sending wrong network identifier
   - Solution: Use canonical format `ethereum-bsc` for BSC
   - Split into chain (`ethereum`) and network (`bsc`) for Gateway calls

3. **Wallet Not Found**:
   - Occurs when: Wallet not loaded in Gateway
   - Solution: Ensure wallet is added via `/wallet/add` before staking
   - Call `get_default_wallet_address()` to verify

4. **Allowance Issues**:
   - Occurs when: Token allowance insufficient for Position Manager
   - Solution: Call `approve()` endpoint before opening position
   - Ensure spender is correct: `pancakeswap/clmm`

---

## Testing Steps for PR Reviewers

### Prerequisites
1. Running Gateway instance at `http://localhost:15888`
2. BSC wallet loaded in Gateway (use `scripts/wallet_add_from_env_bsc.py` if needed)
3. Test BNB and test token balances in wallet

### Test Case 1: Check if Pool is Known to MasterChef
```bash
POST /gateway/connector/pancakeswap/masterchef-knows-pool
Request:
{
  "network": "bsc",
  "poolAddress": "0xc397874a6Cf0211537a488fa144103A009A6C619"
}

Expected Response:
{
  "poolId": "1",
  "known": true
}
```

### Test Case 2: Add Wallet with Network Parameter
```bash
POST /wallet/add
Request:
{
  "chain": "bsc",
  "privateKey": "0x...",
  "setDefault": true,
  "network": "bsc-mainnet"
}

Expected Response: Wallet address and confirmation
```

### Test Case 3: Gateway CLMM Operations
1. Open position with base and quote amounts
2. Verify position created successfully
3. Attempt stake operation (if supported)
4. Verify stake transaction hash returned
5. Verify position can be queried from database

### Test Case 4: Database Verification
```bash
python scripts/clmm/clmm_check_pool_db.py
```
- Verify positions are recorded with correct pool address
- Check fee collections are properly tracked
- Verify transaction hashes are stored

### Test Case 5: Error Handling
1. Test with zero liquidity (should handle gracefully)
2. Test with insufficient allowance (should error with clear message)
3. Test with wrong network (should error appropriately)
4. Test with non-existent wallet (should error with clear message)

---

## File Organization

### Core Changes (Must Include)
- `services/gateway_client.py` - MasterChef staking methods
- `models/gateway_trading.py` - MasterChef request/response models
- `models/__init__.py` - Model exports
- `routers/gateway_clmm.py` - MasterChef pool check endpoint
- `models/gateway.py` - MasterChef pool models

### Supporting Changes (Ensure Consistency)
- `services/accounts_service.py` - Service integration
- `routers/gateway.py` - Route configuration
- `routers/accounts.py` - Account endpoints
- `docker-compose.yml` - Service configuration

### Files to Exclude from PR
- `.DesignDocs/` - Design documentation (do not commit)
- `scripts/` - Testing scripts (some are for local testing only)
- `requirements.txt` - Should only include needed dependencies
- Any `*.pyc` or `__pycache__` files

---

## Compliance Checklist

### Contributing.md Requirements
- [ ] Branch created from `development` (not `main`)
- [ ] Branch name follows convention: `feat/pancakeswap-clmm-lp-bsc`
- [ ] Commits prefixed with `(feat)`, `(fix)`, or `(refactor)`
- [ ] Commit messages in present tense
- [ ] PR includes detailed description
- [ ] Changes are focused on Pancakeswap/CLMM endpoints
- [ ] No unnecessary formatting or testing changes included

### Code Quality
- [ ] Type hints on all functions and parameters
- [ ] Proper error handling with meaningful error messages
- [ ] Docstrings on all public methods
- [ ] Consistent naming conventions (snake_case for functions/vars, camelCase for API fields)
- [ ] No hardcoded values (use environment variables or configuration)

### API Documentation
- [ ] All endpoints have proper OpenAPI documentation
- [ ] Request/response examples included
- [ ] Error responses documented (400, 500, etc.)
- [ ] Parameter descriptions clear and precise

---

## Implementation Order

1. **Step 1**: Update `services/gateway_client.py` with new MasterChef methods
2. **Step 2**: Add models to `models/gateway_trading.py` and `models/gateway.py`
3. **Step 3**: Update `models/__init__.py` with new exports
4. **Step 4**: Add endpoint to `routers/gateway_clmm.py`
5. **Step 5**: Verify integration in `services/accounts_service.py`
6. **Step 6**: Update route configuration in `routers/gateway.py`
7. **Step 7**: Test all changes locally
8. **Step 8**: Create PR with clear description

---

## Verification Commands

After applying changes, run these commands to verify:

```bash
# 1. Check for syntax errors
python -m py_compile services/gateway_client.py
python -m py_compile models/gateway_trading.py
python -m py_compile routers/gateway_clmm.py

# 2. Verify imports
python -c "from models import PancakeMasterchefUnstakeAndCloseRequest; print('OK')"

# 3. Run type checks if available
mypy services/gateway_client.py --ignore-missing-imports || true

# 4. List all Gateway CLMM endpoints
grep -r "masterchef" routers/ | grep "@router"
```

---

## Notes for AI Agent (Other IDE)

- All changes are focused on **Pancakeswap CLMM endpoints and MasterChef operations**
- No changes to authentication, database schema, or unrelated routers
- All amounts use `Decimal` type for precision
- Network parameter: Use canonical format `ethereum-bsc` for BSC chains
- Error handling: Always provide meaningful error messages to clients
- Testing: Use provided test cases to verify implementations
- Documentation: All endpoints must have OpenAPI-compatible docstrings

---

## Related Documentation

- **Contributing.md**: Project contribution standards
- **CONTEXT.md**: Development context and conventions
- **Session_Notes.md**: Current session action items

---

**End of Migration Guide**

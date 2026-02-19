# Quick Start Reference - PancakeSwap CLMM Migration

## 📋 What Has Been Done

✅ Analyzed all 35 changes from the current branch  
✅ Filtered to 9 core git-tracked files (removed testing artifacts)  
✅ Created MIGRATION_GUIDE.md - Complete technical specification  
✅ Created GIT_MIGRATION_COMMANDS.md - Step-by-step git instructions  
✅ Created IMPLEMENTATION_SUMMARY.md - High-level overview  
✅ Identified value conversion errors and fixes  
✅ Documented testing procedures  

## 🎯 The Goal

Apply PancakeSwap CLMM MasterChef staking/unstaking endpoints to the `pancakeswap-clmm-lp-bsc` branch.

## 📦 What's Being Migrated

### 9 Git-Tracked Files
```
1. services/gateway_client.py          - MasterChef staking methods
2. models/gateway_trading.py           - Request/response models  
3. models/__init__.py                  - Export new models
4. models/gateway.py                   - Pool check models
5. routers/gateway_clmm.py            - Pool check endpoint
6. routers/gateway.py                  - Route configuration
7. services/accounts_service.py        - Service integration
8. routers/accounts.py                 - Account endpoints
9. docker-compose.yml                  - Service config
```

### 3 Documentation Files (Included)
```
- MIGRATION_GUIDE.md            (Technical specification)
- GIT_MIGRATION_COMMANDS.md     (Git instructions)
- IMPLEMENTATION_SUMMARY.md     (Overview & checklist)
```

### What's NOT Included
```
- .DesignDocs/          (Design docs only)
- scripts/              (Testing scripts)
- apply_migration.sh    (Helper, optional)
```

## 🚀 Quick Migration Steps

### Option 1: Automated Script (Easiest)
```bash
chmod +x apply_migration.sh
./apply_migration.sh
```

### Option 2: Manual Commands (Detailed Control)
```bash
# 1. Stash your changes
git stash push -m "pancakeswap-clmm-$(date +%s)" \
  services/gateway_client.py models/gateway_trading.py \
  models/__init__.py models/gateway.py routers/gateway_clmm.py \
  routers/gateway.py services/accounts_service.py \
  routers/accounts.py docker-compose.yml

# 2. Switch to target branch
git fetch origin
git checkout pancakeswap-clmm-lp-bsc

# 3. Apply changes
git stash pop

# 4. Verify and commit
git diff --stat
git commit -m "(feat) add pancakeswap masterchef staking endpoints"
git push origin pancakeswap-clmm-lp-bsc
```

## 📚 Documentation Map

| Document | Purpose | Read When |
|----------|---------|-----------|
| MIGRATION_GUIDE.md | Technical details, testing procedures, error fixes | Deep understanding needed |
| GIT_MIGRATION_COMMANDS.md | Step-by-step git instructions | Actually applying changes |
| IMPLEMENTATION_SUMMARY.md | Overview, checklist, quick reference | Planning the work |
| This file | Quick reference, links | Starting out |

## ✅ Key Features Implemented

### New Endpoints
1. `POST /gateway/connector/pancakeswap/masterchef/stake` - Stake NFT
2. `POST /gateway/connector/pancakeswap/masterchef/unstake` - Unstake NFT
3. `POST /gateway/connector/pancakeswap/masterchef-knows-pool` - Check pool registration

### New Methods (GatewayClient)
1. `clmm_stakeNft()` - Stake NFT in MasterChef
2. `clmm_unstakeNft()` - Unstake NFT from MasterChef

### New Models
1. `PancakeMasterchefUnstakeAndCloseRequest`
2. `PancakeMasterchefUnstakeAndCloseResponse`
3. `PositionClosedDetails`
4. `MasterchefKnowsPoolRequest`
5. `MasterchefKnowsPoolResponse`

## 🔑 Critical Implementation Details

### 1. Decimal Precision ⚠️
```python
# ✓ Correct
amount = Decimal(str(gateway_response['amount']))

# ✗ Wrong (loses precision)
amount = float(gateway_response['amount'])
```

### 2. Network Parameter Format
```python
# ✓ Canonical format
network = "ethereum-bsc"  # Splits to: chain="ethereum", network="bsc"

# ✗ Incomplete
network = "bsc"  # May be rejected by Gateway
```

### 3. Amount String Conversion
```python
# ✓ Correct (JSON serialization)
payload = {"amount": str(Decimal("123.456"))}

# ✗ Wrong
payload = {"amount": Decimal("123.456")}  # JSON error
```

## 🧪 Testing Quick Reference

### Test 1: Pool Check
```bash
curl -X POST http://localhost:8000/gateway/connector/pancakeswap/masterchef-knows-pool \
  -H "Content-Type: application/json" \
  -d '{"network":"bsc","poolAddress":"0xc397874a..."}'
```

### Test 2: Verify Changes
```bash
python -m py_compile services/gateway_client.py
python -c "from models import PancakeMasterchefUnstakeAndCloseRequest; print('OK')"
```

### Test 3: Check Git Status
```bash
git diff --name-only
# Should show exactly these 9 files (no more, no less)
```

## 🐛 Common Issues & Fixes

| Issue | Cause | Solution |
|-------|-------|----------|
| ZERO_LIQUIDITY | Wrong amounts | Use quote-position first, provide both base/quote |
| Network mismatch | Format wrong | Use canonical: `ethereum-bsc` |
| Decimal precision lost | Using float | Always use `Decimal(str(...))` |
| Wallet not found | Not loaded | Call `/wallet/add` with setDefault=true |
| JSON serialization fail | Decimal type | Convert to `str()` before sending to API |

## 📋 Pre-Migration Checklist

- [ ] Read IMPLEMENTATION_SUMMARY.md (5 min)
- [ ] Verify current branch: `feature/clmm-add-remove-liquidity`
- [ ] Run `git status` - all changes listed above present
- [ ] Backup any important local work
- [ ] Internet connection stable (for git push)

## 📋 Post-Migration Checklist

- [ ] All 9 files have changes: `git diff --name-only`
- [ ] No extra files: Count should be exactly 9
- [ ] Syntax OK: `python -m py_compile services/gateway_client.py`
- [ ] Imports work: `python -c "from models import ..."`
- [ ] Branch is correct: `git branch | grep pancakeswap-clmm-lp-bsc`
- [ ] Pushed to remote: `git push origin pancakeswap-clmm-lp-bsc`
- [ ] PR created against `development` (not `main`)

## 📞 Need Help?

1. **Technical Details** → Read MIGRATION_GUIDE.md
2. **Git Issues** → Check GIT_MIGRATION_COMMANDS.md Troubleshooting
3. **Common Errors** → See "Common Issues & Fixes" above
4. **Testing** → Follow test cases in MIGRATION_GUIDE.md

## 🎓 Understanding the Changes

### What This Does
- Adds ability to stake/unstake CLMM positions in PancakeSwap MasterChef on BSC
- Adds endpoint to check if a pool is registered with MasterChef
- Properly handles Decimal precision for token amounts
- Uses correct network parameter format for BSC operations

### What This Doesn't Change
- Authentication or user management
- Database schema or migrations
- Other routers or services
- Backward compatibility

### Why These Changes Matter
- Enables automated MasterChef operations (farming)
- Prevents zero-liquidity errors through proper data conversion
- Allows BSC-specific network handling
- Maintains decimal precision in financial calculations

## 🚦 Ready to Go?

**If YES:**
1. Start with automated script: `./apply_migration.sh`
2. Or follow GIT_MIGRATION_COMMANDS.md step-by-step

**If NO (need more info):**
1. Read IMPLEMENTATION_SUMMARY.md (15 min)
2. Review specific section in MIGRATION_GUIDE.md
3. Check GIT_MIGRATION_COMMANDS.md troubleshooting

---

## Quick Links

| Document | Size | Time to Read |
|----------|------|--------------|
| This file | 2 KB | 5 min |
| IMPLEMENTATION_SUMMARY.md | 15 KB | 15 min |
| MIGRATION_GUIDE.md | 30 KB | 30 min |
| GIT_MIGRATION_COMMANDS.md | 20 KB | 20 min |
| **TOTAL** | **67 KB** | **~70 min** |

---

## 🎯 Success Criteria

After applying migration:
- ✅ All 9 files modified
- ✅ No extra files included
- ✅ Syntax checks pass
- ✅ Imports resolve
- ✅ PR created against `development`
- ✅ Test cases pass
- ✅ No merge conflicts

---

**Status**: 🟢 Ready to Apply  
**Last Updated**: February 18, 2026  
**Next Step**: Review docs and execute migration script

---

## File References

```
Repository Root:
├── MIGRATION_GUIDE.md              ← START HERE for details
├── GIT_MIGRATION_COMMANDS.md       ← USE THIS for git steps
├── IMPLEMENTATION_SUMMARY.md       ← USE THIS for overview
├── QUICK_REFERENCE.md              ← YOU ARE HERE
├── apply_migration.sh              ← RUN THIS to automate

Core Changes (9 files):
├── services/gateway_client.py
├── models/gateway_trading.py
├── models/__init__.py
├── models/gateway.py
├── routers/gateway_clmm.py
├── routers/gateway.py
├── services/accounts_service.py
├── routers/accounts.py
└── docker-compose.yml

DO NOT COMMIT:
├── .DesignDocs/
├── scripts/
└── apply_migration.sh (optional, for reference)
```

---

**Questions?** Check the documentation links above.  
**Ready?** Run `./apply_migration.sh` or follow GIT_MIGRATION_COMMANDS.md

Good luck! 🚀

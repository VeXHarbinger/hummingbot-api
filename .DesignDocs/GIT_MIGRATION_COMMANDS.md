# Git Commands to Apply Migration to pancakeswap-clmm-lp-bsc Branch

## Quick Start (Automated)

If you have the `apply_migration.sh` script, run:
```bash
chmod +x apply_migration.sh
./apply_migration.sh
```

This will automatically:
1. Stash changes
2. Check out the target branch
3. Apply the changes
4. Show you what's ready to commit

---

## Manual Process (Step-by-Step)

### Step 1: Verify Current State
```bash
cd c:/Users/alexp/source/repo/hummingbot-api
git status
git branch -a
```

Expected output:
- Current branch: `feature/clmm-add-remove-liquidity`
- Modified files: 9 files (see section below)

### Step 2: Create a Stash of Your Changes

This preserves your work while you switch branches:
```bash
git stash push -m "pancakeswap-clmm-changes-$(date +%s)" \
  services/gateway_client.py \
  models/gateway_trading.py \
  models/__init__.py \
  models/gateway.py \
  routers/gateway_clmm.py \
  routers/gateway.py \
  routers/accounts.py \
  services/accounts_service.py \
  docker-compose.yml
```

Verify stash was created:
```bash
git stash list
# Should show: stash@{0}: pancakeswap-clmm-changes-<timestamp>
```

### Step 3: Update Remote References

```bash
git fetch origin
```

This ensures you have the latest `pancakeswap-clmm-lp-bsc` branch from remote.

### Step 4: Switch to Target Branch

```bash
git checkout pancakeswap-clmm-lp-bsc
# or if branch doesn't exist locally:
git checkout -b pancakeswap-clmm-lp-bsc origin/pancakeswap-clmm-lp-bsc
```

Verify you're on the correct branch:
```bash
git branch
# Should show: * pancakeswap-clmm-lp-bsc
```

### Step 5: Apply the Stashed Changes

```bash
git stash pop stash@{0}
```

This restores your changes to the new branch.

If there are conflicts, see "Handling Merge Conflicts" section below.

### Step 6: Review Changes

```bash
# Show summary of changes
git diff --stat

# Show detailed changes for a specific file
git diff services/gateway_client.py

# Show all changes
git diff
```

### Step 7: Verify Files are Correct

Check that only the intended files have changes:
```bash
git diff --name-only
```

Expected output (exactly these files):
```
docker-compose.yml
models/__init__.py
models/gateway.py
models/gateway_trading.py
routers/accounts.py
routers/gateway.py
routers/gateway_clmm.py
services/accounts_service.py
services/gateway_client.py
```

### Step 8: Stage Changes (Optional - Review First)

```bash
# Stage all changes
git add -A

# Or stage specific files
git add models/gateway_trading.py
git add services/gateway_client.py
# ... etc
```

### Step 9: Commit Changes

```bash
git commit -m "(feat) add pancakeswap masterchef staking endpoints

- Add clmm_stakeNft and clmm_unstakeNft methods to GatewayClient
- Add PancakeMasterchef models for unstake-and-close operations
- Add masterchef-knows-pool endpoint for pool registration check
- Update Gateway router to handle BSC network parameter
- Ensure proper Decimal type handling for token amounts
- Add support for network-specific wallet operations"
```

### Step 10: Verify Commit

```bash
git log --oneline -n 3
# Should show your new commit at the top

git show
# Shows the full commit and all changes
```

### Step 11: Push to Remote

```bash
git push origin pancakeswap-clmm-lp-bsc
```

### Step 12: Create Pull Request

After pushing, create a PR on GitHub:
- Base: `development` (NOT `main`)
- Compare: `pancakeswap-clmm-lp-bsc`
- Title: "feat: Add PancakeSwap CLMM MasterChef staking endpoints"
- Description: Reference the MIGRATION_GUIDE.md changes

---

## Handling Merge Conflicts

If you get conflicts during `git stash pop`:

### Identify Conflicts
```bash
git status
# Shows files with conflicts (both modified)
```

### View Conflict Details
```bash
git diff <filename>
# Shows <<<<<<, ======, >>>>>> markers
```

### Resolve Conflicts

Edit each conflicted file manually:
- Remove `<<<<<<` and `======` markers
- Keep the newer version (from the stash)
- Remove `>>>>>>` marker

Example:
```python
# BEFORE (with conflict markers)
<<<<<<< HEAD
# Old version from branch
def old_method():
    pass
=======
# New version from stash
def new_method():
    pass
>>>>>>> stash

# AFTER (resolved)
def new_method():
    pass
```

### Complete the Merge
```bash
# Stage resolved files
git add <resolved_filename>

# Or stage all resolved files
git add -A

# Complete the stash pop
git stash drop
```

### If Conflicts are Complicated

Abort and try a different approach:
```bash
# Abort the pop
git merge --abort

# Alternative: Cherry-pick files instead of stash
git checkout stash -- <filename>
```

---

## Alternative: Cherry-Pick Approach (If Stash Fails)

If stash doesn't work well, use cherry-pick:

### 1. Note the Commit Hash
```bash
# On feature/clmm-add-remove-liquidity
git log --oneline -n 1
# Remember this hash, e.g., abc1234
```

### 2. Switch to Target Branch
```bash
git checkout pancakeswap-clmm-lp-bsc
```

### 3. Cherry-Pick the Commit
```bash
git cherry-pick abc1234
```

### 4. If Files Conflict

Edit conflicts manually (same as above), then:
```bash
git add -A
git cherry-pick --continue
```

---

## Verify Changes are Correct

After committing, verify with these commands:

```bash
# 1. Check syntax
python -m py_compile services/gateway_client.py

# 2. Verify imports work
python -c "from models import PancakeMasterchefUnstakeAndCloseRequest; print('✓ Imports OK')"

# 3. Check git log shows your commit
git log --oneline -n 3

# 4. Verify remote is ready for PR
git branch -vv
# Should show: pancakeswap-clmm-lp-bsc pushed to origin/pancakeswap-clmm-lp-bsc [ahead of upstream]
```

---

## Rollback (If Something Goes Wrong)

```bash
# Undo last commit but keep changes staged
git reset --soft HEAD~1

# Undo last commit and discard changes
git reset --hard HEAD~1

# Undo all local changes (nuclear option)
git reset --hard origin/pancakeswap-clmm-lp-bsc

# Recover from stash if you made a mistake
git stash list  # Find the right stash
git stash apply stash@{n}  # Apply stash n
```

---

## Files Changed Summary

### Core Endpoint Changes (Must Include)
```
services/gateway_client.py          - Add MasterChef methods
models/gateway_trading.py           - Add request/response models
models/__init__.py                  - Export new models
models/gateway.py                   - Add pool models
routers/gateway_clmm.py            - Add pool check endpoint
```

### Integration Changes (Ensure Consistency)
```
routers/gateway.py                  - Route configuration
services/accounts_service.py        - Service integration
routers/accounts.py                 - Account endpoints
docker-compose.yml                  - Service configuration
```

### Files to NOT Include in Commit
```
MIGRATION_GUIDE.md          - Documentation (OK to include, helpful for reviewers)
apply_migration.sh          - Script (OK to include)
.DesignDocs/                - Documentation only, do NOT commit
scripts/                    - Testing scripts only, do NOT commit
requirements.txt            - If added, verify only necessary deps
```

---

## Creating the GitHub PR

Once pushed, create a PR with:

**Title**: `feat: Add PancakeSwap CLMM MasterChef staking endpoints`

**Description Template**:
```markdown
## Description
This PR adds support for PancakeSwap CLMM liquidity position management with MasterChef staking/unstaking on BSC.

## Changes
- Added `clmm_stakeNft()` and `clmm_unstakeNft()` methods to GatewayClient
- Added MasterChef request/response models
- Added `/connector/pancakeswap/masterchef-knows-pool` endpoint
- Updated network parameter handling for BSC operations
- Added proper Decimal type handling for token amounts

## Testing
See MIGRATION_GUIDE.md for detailed test cases and verification steps.

## Related
See MIGRATION_GUIDE.md for complete documentation.
```

**Checklist in PR**:
- [ ] Changes follow Contributing.md guidelines
- [ ] All endpoints have OpenAPI documentation
- [ ] Type hints on all functions
- [ ] Error handling with meaningful messages
- [ ] Proper Decimal handling for amounts
- [ ] Network parameter uses canonical format (e.g., ethereum-bsc)
- [ ] No unnecessary files committed

---

## Troubleshooting

### Issue: "fatal: Not a valid object name"
**Cause**: Trying to pop a stash that doesn't exist
**Solution**:
```bash
git stash list  # Find the correct stash ref
git stash pop stash@{n}  # Use the correct index
```

### Issue: "CONFLICT (content merge): ..."
**Cause**: Conflicting changes between branches
**Solution**: See "Handling Merge Conflicts" section above

### Issue: "Your branch is ahead of 'origin/pancakeswap-clmm-lp-bsc'"
**Cause**: Normal - your changes aren't pushed yet
**Solution**: `git push origin pancakeswap-clmm-lp-bsc`

### Issue: "Cannot checkout pancakeswap-clmm-lp-bsc"
**Cause**: Branch doesn't exist locally
**Solution**:
```bash
git fetch origin
git checkout -b pancakeswap-clmm-lp-bsc origin/pancakeswap-clmm-lp-bsc
```

---

## Summary

1. **Stash** your changes: `git stash push -m ...`
2. **Fetch** from remote: `git fetch origin`
3. **Checkout** target: `git checkout pancakeswap-clmm-lp-bsc`
4. **Pop** stash: `git stash pop`
5. **Review** changes: `git diff --stat`
6. **Commit**: `git commit -m ...`
7. **Push**: `git push origin pancakeswap-clmm-lp-bsc`
8. **Create PR** on GitHub with detailed description

---

**End of Git Commands Guide**

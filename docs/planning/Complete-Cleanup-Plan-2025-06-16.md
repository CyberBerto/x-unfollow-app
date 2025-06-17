# Complete GitHub + Directory + All Config Files + All Repos Cleanup Plan (Final Corrected)

**Saved**: 2025-06-16T14:30:00-08:00 PST  
**Status**: Approved plan ready for execution  

## Phase 1: GitHub Repository Cleanup
- **Check GitHub repos**: List all x-unfollow-app repositories
- **Identify June 12 duplicates**: Find repos created on 2025-06-12
- **Keep most recent June 12 repo**: Preserve the last/best June 12 commit
- **Delete duplicate repos**: Remove extra June 12 repositories
- **Keep current main repo**: Maintain the repo with our Layer 2 commit
- **Result**: Should have 3-4 total repos remaining (current + June 12 + any other essential)

## Phase 2: Config Files Complete Update

### config.py - Complete Refactor:
- ❌ Remove old batch settings (small/full batches eliminated in Layer 1)
- ❌ Fix port (5000 → 5001)
- ❌ Remove outdated delays (replaced by Layer 2 smart timing)
- ❌ Remove unimplemented features (multi-user, ads, database)
- ✅ Clean Layer 2 focused configuration
- ✅ Add error classification constants for Layer 2

### .env.example - Simplify:
- ❌ Remove DATABASE_URL (not implemented)
- ❌ Remove ADS_ENABLED (not implemented) 
- ✅ Keep CALLBACK_URL=http://localhost:5001/callback (correct localhost)
- ✅ Keep essential: X_CLIENT_ID, X_CLIENT_SECRET, FLASK_SECRET_KEY
- ✅ Update comment reference to developer.x.com (for credential instructions)

### requirements.txt - Status Check:
- ✅ **Already up-to-date**: All dependencies current and essential
- ✅ No changes needed

## Phase 3: Main Directory Cleanup
**Files to Archive:**
- `automated_unfollow.py` → `docs/z-archive/outdated/`
- `test_permissions.py` → `docs/z-archive/outdated/`
- `test-layer2-mixed.csv` → `docs/z-archive/outdated/`
- `SECURITY.md` → `docs/z-archive/outdated/` (content moved to README)

**Keep Local (add to .gitignore):**
- `debug_tests.py` (current/useful but exclude from commits)
- `app.log` (useful debugging data, exclude from git)
- `flask.log` (useful debugging data, exclude from git)
- `unfollow_tracking.json` (useful debugging data, exclude from git)

## Phase 4: Update .gitignore
- Add `debug_tests.py` to ignore list
- Add `app.log`, `flask.log`, `unfollow_tracking.json` to ignore list
- Add missing patterns for development artifacts

## Phase 5: Clean Commit - All Files Updated
- Stage refactored `config.py` (Layer 2 focused)
- Stage simplified `.env.example` (essential only)
- Stage archived development files
- Stage only essential production files
- Commit: "Refactor all config files for Layer 2 + clean repository structure"

## Phase 6: Verify Clean State
**Essential Production Files (All Up-to-Date):**
- ✅ Core app: `api.py`, `app.py`, `config.py` (refactored for Layer 2)
- ✅ Dependencies: `requirements.txt` (current versions)
- ✅ Environment: `.env.example` (simplified, essential only)
- ✅ Frontend: `templates/`, `static/`
- ✅ Documentation: `README.md` (Layer 2 enhanced)
- ✅ Git: `.gitignore` (comprehensive)
- ✅ Development (local only): `debug_tests.py`, `*.log`, `unfollow_tracking.json`

## Phase 7: Legacy Repositories Quick Cleanup (Simple)
**For remaining 2-3 legacy repos (NOT current repo):**
- **Quick assessment**: Check if they need basic cleanup
- **Simple .gitignore addition**: Just add professional ignore file
- **No major restructuring**: Keep original functionality intact
- **Optional README note**: Simple note about repo status/version
- **Keep it minimal**: Don't over-engineer or repeat current work

**Result**: Current repo is production-ready with Layer 2 enhancements, legacy repos have basic professional cleanup without complexity.
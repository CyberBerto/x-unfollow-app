# Protected Files List - Never Modify During Cleanup

## 🛡️ Critical Files (Never Touch)
These files are essential to the development process and should never be automatically modified, moved, or deleted during vault cleanup operations.

### **Core Reference Files**:
- `docs/reference/Development-Principles.md` - Core development standards
- `docs/reference/Original-Project-Spec.md` - Foundation requirements
- `docs/reference/Workflow-Standards.md` - Complete workflow documentation
- `docs/reference/Project-Structure-Standards.md` - Project architecture standards
- `docs/reference/Session-Command-Behavior.md` - Functional session command guide
- `docs/reference/Development-Pivot-Plan.md` - Layer implementation strategy

### **Active Session Files**:
- `docs/active/Quick-Session-Start.md` - Session startup protocol
- `docs/active/Quick-Session-End.md` - Current session status
- `docs/active/Next-Session-Immediate-Start.md` - Layer 2 implementation plan

### **Current Progress Files**:
- `docs/progress/Cycle-3-Progress-Tracker.md` - Main progress tracking
- `docs/progress/session-logs/[current-week]` - Recent session logs
- `docs/technical/Code-Changes-Log.md` - Master technical log

### **Templates**:
- `docs/templates/*.md` - All template files (can reset content but preserve structure)

## 🔄 Safe Modifications Allowed
- **Content updates**: Progress tracking, completion percentages
- **Reference updates**: File path corrections, broken link fixes
- **Template restoration**: Reset filled templates to blank state

## ⚠️ Requires Confirmation
- **Moving files**: Between folders (show preview first)
- **Deleting duplicates**: Confirm which version to keep
- **Archive operations**: Moving to z-archive (show what's being moved)

## 🚫 Never Allow
- **Deleting protected files**: Even if they appear "old"
- **Modifying core principles**: Development standards should be stable
- **Breaking active sessions**: Don't disrupt current work files

---

*This list ensures vault cleanup maintains system integrity while allowing optimization.*
can # Claude Development Rules and Cross-Reference System

*Comprehensive system for efficient, tracked development sessions*

## Session Setup Protocol

### 1. SIMPLIFIED SESSION START ⚡
**Single file to read (3 minutes):**

1. **00-ACTIVE/Session Dashboard.md** 
   - Everything you need: Current status, objectives, efficiency standards
   - Quick setup: Choose session type, set budget, start working

### 2. SIMPLIFIED SESSION TRACKING 🎯
**Choose your tracking level:**

**Level 1 (Simple Tasks)**: No tracking - just estimate and go  
**Level 2 (Standard Work)**: Use Quick Session Template - major decisions only  
**Level 3 (Complex Development)**: Full tracking with real-time monitoring  

### 3. SESSION SETUP (30 seconds)
1. **Read dashboard** - get current status
2. **Copy quick template** if Level 2/3 tracking needed
3. **Start working** - track efficiency with stoplight system

### 2. Reference File Relationships
```
Session Summary ← Main progress tracking
     ↓
Optimization Log ← Technical implementation details  
     ↓
Token Tracker ← Efficiency analysis and cost tracking
```

## Cross-Reference Logging Rules

### A. For Every Code Change - MANDATORY + REAL-TIME 🆕
**Immediately after making any code edit:**

1. **Real-Time Tracker Update** (immediate):
   ```
   | Time | Decision/Change | Tools Used | Est. Tokens | Running Total | Efficiency Note |
   | [HH:MM] | [Specific change] | [Tools] | [tokens] | [total] | [real-time analysis] |
   ```

2. **Add to Token Tracker Usage Log** (session end):
   ```
   | Date | Task/Decision | Tools Used | Original Est. | Revised Est. | Outcome | Complexity Factors |
   | 2025-06-12 | [Specific change] | [Tools] | ~[est] | ~[actual] | [Result] | [Analysis] |
   ```

3. **Update Technical Log** with implementation details:
   - Function names and line numbers changed
   - Before/after code snippets for major changes
   - Technical rationale and implementation notes

### B. Task Granularity Guidelines
**Log tasks at this level of detail:**

✅ **Good Examples:**
- "Fix rate limit buffer calculation in slow_batch_worker()"
- "Add memory cleanup to operation initialization" 
- "Update error logging format in batch worker"

❌ **Too Broad:**
- "Improve error handling"
- "Fix batch processing"

❌ **Too Granular:**
- "Change variable name from x to y"
- "Fix typo in comment"

### C. Token Estimation Rules
**Estimate tokens for each task:**

- **Simple edits** (1-3 lines): ~50-150 tokens
- **Function modifications** (5-15 lines): ~150-400 tokens  
- **Major refactoring** (20+ lines): ~400-800 tokens
- **New features** (complex): ~800-1500 tokens
- **Documentation updates**: ~50-200 tokens

## Tool Usage Patterns for Efficiency

### High Efficiency Approaches
1. **MultiEdit over multiple Edit calls** - Use for batch changes
2. **Grep to locate code** before reading entire files
3. **Read with line offsets** for large files
4. **Reference documentation first** to avoid redundant analysis

### Track These Tool Combinations
- `Read + Edit` = Standard modification
- `Grep + Read + Edit` = Targeted fix
- `MultiEdit` = Batch changes
- `Read + MultiEdit` = Complex refactoring

## Documentation Update Workflow

### After Each Development Session:
1. **Update Token Tracker** - Add all new Usage Log entries
2. **Update Optimization Log** - Add technical progress section
3. **Create/Update Session Summary** - High-level progress and next steps

### Session Completion Checklist:
- [ ] All code changes logged in Token Tracker
- [ ] Technical details recorded in Optimization Log  
- [ ] Session summary updated with progress
- [ ] Next session objectives clearly defined
- [ ] Cross-references between all files updated
- [ ] **Archive session to correct subfolder** in 03-SESSIONS (e.g., phase-4-testing/)
- [ ] **Rename session file** from "Current Session" to "Session Summary" or "Past Session"

## Efficiency Optimization Rules

### Real-Time Token Conservation 🆕
1. **Always reference existing documentation** before starting work
2. **Use systematic approach** with todo tracking
3. **Batch similar operations** with MultiEdit
4. **Plan before coding** to avoid redundant work
5. **Monitor token velocity** in real-time tracker
6. **Apply immediate optimizations** when patterns detected

### Red Flags - Stop and Optimize (Real-Time Alerts) 🆕
- 🔴 **Critical**: >150% of estimated tokens for current task
- 🟡 **Warning**: >120% of estimated tokens for current task
- ⚠️ Reading same file multiple times unnecessarily
- ⚠️ Making individual edits instead of batching with MultiEdit
- ⚠️ Starting work without reading existing documentation
- ⚠️ Token velocity declining during session

### Real-Time Optimization Triggers 🆕
**When alerts trigger, immediately:**
1. **Pause current task** - assess what's causing inefficiency
2. **Check real-time tracker** - identify patterns and bottlenecks
3. **Apply optimization** - batch operations, reference docs, simplify approach
4. **Update workflow** - document optimization in real-time tracker
5. **Continue with improved approach** - monitor for continued efficiency

## File Naming Conventions

### Session Summaries:
`Session Summary - Phase [X] [Part] [Status].md`

### Examples:
- `Session Summary - Phase 3 Complete.md`
- `Session Summary - Phase 4 Part 1 Complete.md`
- `Session Summary - Phase 4 Part 2 Testing.md`

### Archive Location:
Store in appropriate subfolder within 03-SESSIONS/:
- `03-SESSIONS/phase-4-testing/Session Summary - Phase 4 Part 1 Complete.md`

## Cross-Reference Validation

### Before Each Session Ends:
1. **Check Token Tracker** - All changes logged?
2. **Check Optimization Log** - Technical details recorded?
3. **Check Session Summary** - Progress accurately reflected?
4. **Verify line numbers** - Code references still accurate?

## Emergency Reference Guide

### If Session Context is Lost:
1. Read latest Session Summary (quick overview)
2. Check Token Tracker for recent efficiency patterns
3. Review Optimization Log for technical details
4. Use Grep to locate specific code sections

### Key Commands for Context Recovery:
```bash
# Find recent changes
Read [latest session summary]
Read [optimization log] offset [recent sections]
Grep "function_name" # to locate specific code
```

---

## System Benefits

✅ **Complete Traceability** - Every token mapped to specific progress
✅ **Optimized Efficiency** - Learn from patterns to improve token usage  
✅ **Seamless Session Transitions** - Context preserved across sessions
✅ **Quality Assurance** - Cross-referenced documentation prevents errors
✅ **Progress Transparency** - Clear visibility into development costs

---

*This system ensures maximum development efficiency while maintaining complete accountability for token usage and progress tracking.*
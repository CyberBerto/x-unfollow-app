# API Token Session Template

*Session tracking with real API token data - no estimation needed*

## Session: Phase [X] Part [Y] - [SESSION_NAME]

**Date**: [YYYY-MM-DD]  
**Phase State**: [📋🔄⏸️✅🔄] [PHASE_NAME]  
**Session State**: 🟢 Active  
**Token Tracker**: Session ID [TRACKER_SESSION_ID]  
**API Tracking**: ✅ Real-time monitoring active  

---

## Objectives

### Primary Goals (Must Complete)
1. **[MAIN_OBJECTIVE]** - [SUCCESS_CRITERIA]
2. **[SECONDARY_OBJECTIVE]** - [SUCCESS_CRITERIA]

### Secondary Goals (If Time Allows)  
3. **[OPTIONAL_OBJECTIVE]** - [SUCCESS_CRITERIA]

### Success Criteria
- [ ] [MEASURABLE_OUTCOME_1]
- [ ] [MEASURABLE_OUTCOME_2]
- [ ] [MEASURABLE_OUTCOME_3]

---

## Real-Time API Tracking

### Current Task: [TASK_NAME]
**State**: 🔄 In Progress **Started**: [HH:MM]

### API Usage Log (Auto-populated from token tracker)
| Time | Task/Decision | Input Tokens | Output Tokens | Total | Tools | Notes |
|------|---------------|--------------|---------------|-------|-------|-------|
| [HH:MM] | [DESCRIPTION] | [API_INPUT] | [API_OUTPUT] | [API_TOTAL] | [TOOLS] | [INSIGHTS] |

### Session Efficiency
**Real Token Rate**: [ACTUAL_TOKENS_PER_TASK]  
**Cost Tracking**: $[ACTUAL_COST] (Input: $[INPUT_COST] + Output: $[OUTPUT_COST])  
**Efficiency Status**: [🟢 Efficient | 🟡 Monitor | 🔴 Review]

---

## API Integration Commands

### During Session
```bash
# Count tokens before sending
cd "07-TOOLS/claude-token-tracker"
python claude_tracker.py  # Option 1: Count tokens

# Send prompts with auto-logging
python claude_tracker.py  # Option 2: Send and log

# Check current session summary
python claude_tracker.py  # Option 3: Summary
```

### Session Management
```bash
# Export current data to Obsidian format
python export_to_obsidian.py

# End session with auto-export
python auto_tracker.py --end
```

---

## Session Summary

### Achievements
- **Primary Goals**: [X/Y completed] - [DESCRIPTION]
- **Secondary Goals**: [X/Y completed] - [DESCRIPTION]  
- **Unexpected Issues**: [BLOCKERS_ENCOUNTERED]
- **Key Insights**: [LEARNINGS_GAINED]

### Real API Token Analysis
- **Total Input Tokens**: [API_INPUT_TOTAL]
- **Total Output Tokens**: [API_OUTPUT_TOTAL]  
- **Total API Cost**: $[REAL_COST]
- **Token Efficiency**: [TOKENS_PER_MEANINGFUL_CHANGE]

### Quality Metrics
- **Rework Required**: [NONE | MINOR | MAJOR]
- **Documentation Sync**: [✅ | ⚠️ | ❌]
- **API Integration**: [✅ Successful | ⚠️ Issues | ❌ Failed]

### Next Session Setup
- **Phase State**: [📋🔄⏸️✅🔄]
- **Priority Tasks**: [TOP_3_ITEMS]  
- **Context Notes**: [HANDOFF_INFORMATION]
- **API Data**: [EXPORTED_TO_OBSIDIAN]

---

## Workflow Notes

### API Token Workflow
1. **Start session**: `python auto_tracker.py` (creates session ID)
2. **Count before work**: Use Option 1 for task planning
3. **Work with logging**: Use Option 2 for prompt sending
4. **End session**: `python auto_tracker.py --end` (auto-exports)
5. **Update Obsidian**: Copy from Latest_Session_Export.md

### Benefits Over Manual Estimation
- ✅ **100% accurate** token counts from API
- ✅ **Real cost tracking** with actual billing data
- ✅ **No estimation errors** - eliminates 2x variance
- ✅ **Automatic logging** - less manual work
- ✅ **Obsidian integration** - seamless data flow

---

*Real API data eliminates guesswork and improves planning accuracy! 🎯*
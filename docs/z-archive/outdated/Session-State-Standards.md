# Session State Standards

*Standardized formatting and organization for consistent session tracking*

## Session State Definitions

### Phase States
- **📋 Planned**: Phase objectives defined, not yet started
- **🔄 In Progress**: Active development work happening  
- **⏸️ Paused**: Temporarily stopped, clear resume point documented
- **✅ Complete**: All objectives achieved, archived properly
- **🔄 Transitioning**: Moving between phases, planning next phase

### Session States  
- **🟢 Active**: Currently working, tracking in real-time
- **🟡 Break**: Temporary pause, session will resume
- **🔴 Blocked**: Cannot proceed, waiting for external dependency
- **✅ Complete**: Session finished, ready for wrap-up
- **📝 Documenting**: Post-work documentation and cross-referencing

### Work Item States
- **📋 Pending**: Task defined, not started
- **🔄 In Progress**: Currently working on task
- **⚠️ Attention**: Needs review, over budget, or issue encountered
- **✅ Complete**: Task finished successfully
- **❌ Cancelled**: Task no longer needed or blocked

## Standardized Session Formatting

### Session Header Format
```markdown
# Session: Phase [X] Part [Y] - [SESSION_NAME]

**Date**: YYYY-MM-DD  
**Phase State**: [📋🔄⏸️✅] [PHASE_NAME]  
**Session State**: [🟢🟡🔴✅📝] [SESSION_STATUS]  
**Token Budget**: [ESTIMATED] | **Actual**: [RUNNING_TOTAL]  
**Efficiency**: [🟢🟡🔴] [PERCENTAGE_OF_ESTIMATE]  

---
```

### Objectives Section Format
```markdown
## Objectives

### Primary Goals (Must Complete)
1. **[MAIN_OBJECTIVE]** - [SUCCESS_CRITERIA] - [TOKEN_EST]
2. **[SECONDARY_OBJECTIVE]** - [SUCCESS_CRITERIA] - [TOKEN_EST]

### Secondary Goals (If Time Allows)  
3. **[OPTIONAL_OBJECTIVE]** - [SUCCESS_CRITERIA] - [TOKEN_EST]

### Success Criteria
- [ ] [MEASURABLE_OUTCOME_1]
- [ ] [MEASURABLE_OUTCOME_2]
- [ ] [MEASURABLE_OUTCOME_3]

---
```

### Real-Time Tracking Format
```markdown
## Real-Time Progress

### Current Task: [TASK_NAME]
**State**: [📋🔄⚠️✅❌] **Started**: [HH:MM] **Est. Tokens**: [NUMBER]

### Decision Log
| Time | Decision/Change | Tools | Est. | Actual | Status | Notes |
|------|----------------|-------|------|--------|---------|-------|
| HH:MM | [DESCRIPTION] | [TOOLS] | [EST] | [ACT] | [🟢🟡🔴] | [INSIGHTS] |

### Efficiency Monitoring
**Current Rate**: [TOKENS_PER_TASK] | **Target**: [BASELINE]  
**Alert Status**: [🟢 On Track | 🟡 Monitor | 🔴 Optimize]  
**Pattern Notes**: [OBSERVATIONS]

---
```

### Session Summary Format  
```markdown
## Session Summary

### Achievements
- **Primary Goals**: [X/Y completed] - [DESCRIPTION]
- **Secondary Goals**: [X/Y completed] - [DESCRIPTION]  
- **Unexpected Issues**: [BLOCKERS_ENCOUNTERED]
- **Key Insights**: [LEARNINGS_GAINED]

### Token Analysis
- **Estimated Total**: [PLANNED_TOKENS]
- **Actual Total**: [USED_TOKENS]  
- **Efficiency**: [PERCENTAGE] ([🟢🟡🔴])
- **Variance Analysis**: [WHY_OVER_UNDER]

### Quality Metrics
- **Rework Required**: [NONE | MINOR | MAJOR]
- **Documentation Sync**: [✅ | ⚠️ | ❌]
- **Cross-References**: [✅ Updated | ⚠️ Partial | ❌ Broken]

### Next Session Setup
- **Phase State**: [📋🔄⏸️✅🔄]
- **Priority Tasks**: [TOP_3_ITEMS]  
- **Context Notes**: [HANDOFF_INFORMATION]
- **Estimated Budget**: [TOKEN_PROJECTION]

---
```

## Phase Transition Standards

### Phase Completion Checklist
```markdown
## Phase [X] Completion Checklist

### Technical Completion
- [ ] All code changes implemented and tested
- [ ] Performance benchmarks met
- [ ] Error handling validated
- [ ] Memory usage optimized

### Documentation Completion  
- [ ] Session archived to 03-SESSIONS/phase-[x]-[name]/
- [ ] Progress-Timeline.md updated with completion
- [ ] Token-Usage-Tracker.md finalized for phase
- [ ] Code-Changes-Log.md includes all technical details
- [ ] Cross-references validated across all files

### Quality Validation
- [ ] No critical bugs or issues remaining
- [ ] User acceptance criteria met
- [ ] Performance requirements satisfied
- [ ] Monitoring and logging functional

### Handoff Preparation
- [ ] Next phase objectives clearly defined
- [ ] Dependencies and blockers identified
- [ ] Resource requirements estimated
- [ ] Risk assessment completed
```

### Phase Planning Format
```markdown
## Phase [X] Planning

### Strategic Objectives
| Objective | Success Criteria | Est. Tokens | Priority | Dependencies |
|-----------|------------------|-------------|----------|--------------|
| [GOAL_1] | [MEASURABLE] | [ESTIMATE] | High | [REQUIREMENTS] |
| [GOAL_2] | [MEASURABLE] | [ESTIMATE] | Med | [REQUIREMENTS] |

### Implementation Strategy
1. **Part 1**: [MILESTONE_1] - [TOKEN_BUDGET] - [TIMELINE]
2. **Part 2**: [MILESTONE_2] - [TOKEN_BUDGET] - [TIMELINE]  
3. **Part 3**: [MILESTONE_3] - [TOKEN_BUDGET] - [TIMELINE]

### Risk Assessment
- **Technical Risks**: [CHALLENGES] - [MITIGATION]
- **Resource Risks**: [CONSTRAINTS] - [MITIGATION]
- **Timeline Risks**: [DELAYS] - [MITIGATION]

### Success Metrics
- **Completion Criteria**: [DEFINITION_OF_DONE]
- **Performance Targets**: [BENCHMARKS]
- **Quality Standards**: [ACCEPTANCE_CRITERIA]
```

## Naming Conventions

### Session File Names
```
# Current session (in 00-ACTIVE/)
Session-Phase[X]-Part[Y]-InProgress.md

# Completed session (in 03-SESSIONS/phase-[x]-[name]/)  
Session-Phase[X]-Part[Y]-Complete.md

# Transition session
Session-Phase[X]-to-Phase[Y]-Transition.md
```

### Folder Organization for Sessions
```
03-SESSIONS/
├── phase-1-initial/
├── phase-2-codebase-cleanup/
├── phase-3-reliability/  
├── phase-4-testing/
│   ├── Session-Phase4-Part1-Complete.md
│   ├── Session-Phase4-Part2-InProgress.md
│   └── testing-logs/
├── phase-5-enhancements/
└── phase-6-monitoring/
```

## Status Icons Reference

### Phase States
- 📋 **Planned** - Objectives defined, not started
- 🔄 **In Progress** - Active development  
- ⏸️ **Paused** - Temporarily stopped
- ✅ **Complete** - Finished and archived
- 🔄 **Transitioning** - Between phases

### Efficiency States  
- 🟢 **Green** - Within 120% of estimates
- 🟡 **Yellow** - 120-150% of estimates  
- 🔴 **Red** - Over 150% of estimates

### Work States
- 📋 **Pending** - Not started
- 🔄 **In Progress** - Currently working
- ⚠️ **Attention** - Needs review or over budget
- ✅ **Complete** - Finished successfully  
- ❌ **Cancelled** - No longer needed

---

*Consistent formatting enables efficient context switching and progress tracking! 🎯*
# Session Time Tracking & Naming Convention

**Added**: 2025-06-16  
**Applies to**: Session-level commands (GO, end sesh, end code)  
**Purpose**: Track session duration and improved naming for productivity analysis

## Convention Details

### Commands with Time Tracking:
- **"GO"**: Records session start time (current timestamp, not guessed)
- **"end sesh"**: Progress session logs (references GO start time)
- **"end code"**: Technical session logs (references GO start time)

### Time Format:
```
Session Start: 2025-06-16T10:30:00-08:00 PST
Session End: 2025-06-16T13:45:00-08:00 PST  
Duration: 3h 15m
```

### Implementation in Command Files:

#### Eight-Command System Updates:
- **end_sesh**: Added `"time_tracking": "Include session start and end times with duration in hours:minutes"`
- **end_code**: Added `"time_tracking": "Include session start and end times with duration in hours:minutes"`

#### Session Commands Updates:
- **end_sesh**: Added "Include session start and end times with duration (hours:minutes)" to auto_actions
- **end_code**: Added "Include session start and end times with duration (hours:minutes)" to auto_actions

## Naming Convention Changes

### New Session Log Naming:
- **OLD**: `[timestamp]-p-session.md`, `[timestamp]-t-session.md`
- **NEW**: `[timestamp]-[session-topic]-p-session.md`, `[timestamp]-[session-topic]-t-session.md`

### Examples:
- `2025-06-16-14-50-backup-cleanup-p-session.md`
- `2025-06-16-14-50-layer2-ui-integration-p-session.md`
- `2025-06-16-14-50-repository-cleanup-t-session.md`

## Template Format

### Session Log Time Header:
```markdown
**Session Date**: 2025-06-16
**Start Time**: 2025-06-16T10:30:00-08:00 PST
**End Time**: 2025-06-16T13:45:00-08:00 PST
**Duration**: 3h 15m
```

### Time Implementation:
- **GO command**: Records ACTUAL current timestamp using `date` command
- **End commands**: Reference GO start time for accurate duration
- **Format**: Standard time format with timezone (PST/PDT)
- **Duration**: Calculate in hours:minutes (e.g., 3h 15m)
- **Accuracy**: Use actual timestamps, not approximations

## Benefits:
- **Productivity Analysis**: Track session efficiency
- **Planning**: Better time estimation for future work
- **Context**: Understand session scope and intensity
- **Documentation**: Complete session records

## Commands NOT Affected:
- **consol** (mini-level, no session tracking)
- **end day** (daily level, different time scope)
- **code** (mini-level, no session tracking)
- **end tech** (daily level, different time scope)
- **GO** (context loading, not time-tracked)

This convention enhances session documentation with useful productivity metrics while maintaining the simplicity of mini and daily level commands.
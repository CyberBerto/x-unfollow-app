# Eight-Command System - Consistent Naming Convention

**Updated**: 2025-06-16  
**Purpose**: Standardized naming across all command levels for easy search and organization

## The Seven Commands:

1. **GO** - Context loading (startup)
2. **consol** - Progress mini-consolidations  
3. **end sesh** - Progress session summaries
4. **end day** - Progress daily recounts
5. **code** - Technical mini changes
6. **end code** - Technical session summaries  
7. **end tech** - Technical daily recounts

## Consistent Naming Pattern:

### Progress Commands:
| Command | Level | Naming Format | Example |
|---------|-------|---------------|---------|
| consol | mini | `[timestamp]-p-mini.md` | `2025-06-16-14-50-p-mini.md` |
| end sesh | session | `[timestamp]-[topic]-p-session.md` | `2025-06-16-14-50-backup-cleanup-p-session.md` |
| end day | daily | `[date]-p-daily.md` | `2025-06-16-p-daily.md` |

### Technical Commands:
| Command | Level | Naming Format | Example |
|---------|-------|---------------|---------|
| code | mini | `[timestamp]-t-mini.md` | `2025-06-16-14-50-t-mini.md` |
| end code | session | `[timestamp]-[topic]-t-session.md` | `2025-06-16-14-50-layer2-ui-t-session.md` |
| end tech | daily | `[date]-t-daily.md` | `2025-06-16-t-daily.md` |

## Folder Structure:

```
docs/
├── progress/
│   ├── p-mini-consolidations/     # consol
│   ├── p-session-logs/           # end sesh  
│   └── p-daily-logs/             # end day
└── technical/
    ├── t-mini-changes/           # code
    ├── t-session-changes/        # end code
    └── t-daily-logs/             # end tech
```

## Search Benefits:

### By Level:
- **Mini**: `*-p-mini.md` or `*-t-mini.md`
- **Session**: `*-p-session.md` or `*-t-session.md`  
- **Daily**: `*-p-daily.md` or `*-t-daily.md`

### By Date:
- **Specific day**: `2025-06-16-*`
- **Any timestamp**: Search by `2025-06-16-14-50-*`

### By Type:
- **Progress files**: `*-p-*.md`
- **Technical files**: `*-t-*.md`

### By Topic (Sessions):
- **Backup work**: `*-backup-*-session.md`
- **Layer work**: `*-layer2-*-session.md`

## Consistency Rules:

1. **Prefixes**: Always use `p-` (progress) or `t-` (technical)
2. **Levels**: mini, session, daily (consistent across both tracks)  
3. **Timestamps**: `YYYY-MM-DD-HH-MM` for mini/session, `YYYY-MM-DD` for daily
4. **Topics**: Only for session-level files (descriptive, kebab-case)
5. **Extensions**: Always `.md`

## Migration Notes:

**Changed Files:**
- `[date]-p-daily-progress.md` → `[date]-p-daily.md`
- `[date]-t-daily-code-changes.md` → `[date]-t-daily.md`

**Benefits of Consistent Naming:**
- Easier file searches and filtering
- Clear hierarchy (mini → session → daily)
- Consistent patterns across progress and technical tracks
- Simple glob patterns for automation
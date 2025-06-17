# Six-Command System Model v1.0

*Complete specification of the parallel logging system*  
*Created: 2025-06-16*  
*Status: Production Ready*

## System Overview

The Six-Command System provides complete parallel logging with three tiers of detail for both progress tracking and technical documentation.

### Command Hierarchy

**PROGRESS Commands (Project-Focused, Descriptive):**
- **"consol"** - Quick progress updates throughout the day
- **"end sesh"** - Session-level progress consolidation  
- **"end day"** - Comprehensive daily progress recount

**TECHNICAL Commands (Code-Focused, Implementation Details):**
- **"code"** - Quick code change logs
- **"end code"** - Session-level technical summaries
- **"end tech"** - Comprehensive daily technical recount

## Folder Structure

### Progress Folders (P-Prefix)
```
docs/progress/
├── p-mini-consolidations/    # "consol" command outputs
├── p-session-logs/          # "end sesh" command outputs  
└── p-daily-logs/            # "end day" command outputs
```

### Technical Folders (T-Prefix)
```
docs/technical/
├── t-mini-changes/          # "code" command outputs
├── t-session-changes/       # "end code" command outputs
└── t-daily-logs/            # "end tech" command outputs
```

## File Naming Conventions

### Timestamped Files (Mini & Session Level)
- **Format**: `YYYY-MM-DD-HH-MM-[p/t]-[mini/session].md`
- **Examples**: 
  - `2025-06-16-14-05-p-mini.md`
  - `2025-06-16-14-30-t-session.md`

### Daily Files
- **Format**: `YYYY-MM-DD-[p/t]-daily-[progress/code-changes].md`
- **Examples**:
  - `2025-06-16-p-daily-progress.md`
  - `2025-06-16-t-daily-code-changes.md`

## Dynamic Date Scanning Logic

### Current Time Detection
```bash
# For timestamped files
TIMESTAMP=$(date "+%Y-%m-%d-%H-%M")

# For daily files and scanning
CURRENT_DATE=$(date "+%Y-%m-%d")
```

### File Pattern Matching
Each command scans for same-day files using pattern: `[CURRENT-DATE]-*`

### Cross-Referencing Rules
- **Mini-level commands** reference previous same-day mini files
- **Session-level commands** reference ALL same-day mini files  
- **Daily-level commands** reference ALL same-day files from ALL folders

## Command Specifications

### "consol" Command
```json
{
  "trigger": "consol",
  "file_location": "docs/progress/p-mini-consolidations/",
  "naming_format": "[timestamp]-p-mini.md",
  "references": "Current day p-mini files matching [CURRENT-DATE]-*",
  "content_focus": "Current accomplishments, next priorities, blocking issues"
}
```

### "end sesh" Command  
```json
{
  "trigger": "end sesh",
  "file_location": "docs/progress/p-session-logs/",
  "naming_format": "[timestamp]-p-session.md", 
  "references": "ALL current day files from p-mini-consolidations and t-mini-changes",
  "content_focus": "Session summary, key accomplishments, context updates"
}
```

### "end day" Command
```json
{
  "trigger": "end day",
  "file_location": "docs/progress/p-daily-logs/",
  "naming_format": "[date]-p-daily-progress.md",
  "references": "ALL current day files from ALL folders",
  "content_focus": "Complete daily summary, major achievements, project impact"
}
```

### "code" Command
```json
{
  "trigger": "code", 
  "file_location": "docs/technical/t-mini-changes/",
  "naming_format": "[timestamp]-t-mini.md",
  "references": "Current day t-mini files matching [CURRENT-DATE]-*",
  "content_focus": "File changes, function modifications, bug fixes"
}
```

### "end code" Command
```json
{
  "trigger": "end code",
  "file_location": "docs/technical/t-session-changes/", 
  "naming_format": "[timestamp]-t-session.md",
  "references": "ALL current day files from t-mini-changes and p-mini-consolidations",
  "content_focus": "Technical implementation details, architecture changes"
}
```

### "end tech" Command
```json
{
  "trigger": "end tech",
  "file_location": "docs/technical/t-daily-logs/",
  "naming_format": "[date]-t-daily-code-changes.md",
  "references": "ALL current day files from ALL folders", 
  "content_focus": "Complete technical summary, code architecture, implementation details"
}
```

## Implementation Benefits

### Organization
- **Clear Separation**: Progress vs. Technical focus
- **Consistent Structure**: Three-tier system for both tracks
- **Easy Navigation**: T/P prefixes eliminate confusion

### Productivity
- **Quick Updates**: Mini-level commands for frequent logging
- **Comprehensive Summaries**: Daily commands compile complete picture
- **Cross-Referencing**: Automatic same-day file scanning

### Scalability  
- **Parallel Systems**: Independent but complementary logging
- **Dynamic Dating**: Works regardless of when commands are used
- **Backup Ready**: Complete system easily preserved and restored

## Usage Examples

### Typical Daily Workflow
1. **Throughout Day**: Use "consol" and "code" for quick updates
2. **End of Session**: Use "end sesh" and "end code" for summaries
3. **End of Day**: Use "end day" and "end tech" for comprehensive recounts

### File Output Example
```
# After a day of work:
docs/progress/p-mini-consolidations/
├── 2025-06-16-09-30-p-mini.md
├── 2025-06-16-12-15-p-mini.md
└── 2025-06-16-15-45-p-mini.md

docs/progress/p-session-logs/
└── 2025-06-16-16-00-p-session.md

docs/progress/p-daily-logs/  
└── 2025-06-16-p-daily-progress.md

# With corresponding technical files in t-* folders
```

## System Restoration

To restore this system from backup:
1. Copy `claude-system-backup-2025-06-16/` contents to `.claude/`
2. Ensure folder structure exists with T/P prefixes
3. Test "consol" command to verify functionality
4. Implement remaining commands as needed

## Version History

- **v1.0** (2025-06-16): Initial six-command system implementation
- **Future**: Additional commands and automation features

This system provides the foundation for comprehensive project documentation with minimal overhead and maximum organization.
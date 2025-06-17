# System Restoration Guide v1.0

*Complete instructions for rebuilding the Six-Command System*  
*Created: 2025-06-16*  
*Backup Location: docs/reference/claude-system-backup-2025-06-16/*

## Quick Restoration

### From Backup (Recommended)
```bash
# 1. Restore .claude system from backup
cp -r docs/reference/claude-system-backup-2025-06-16/* .claude/

# 2. Verify folder structure exists
mkdir -p docs/progress/p-mini-consolidations
mkdir -p docs/progress/p-session-logs  
mkdir -p docs/progress/p-daily-logs
mkdir -p docs/technical/t-mini-changes
mkdir -p docs/technical/t-session-changes
mkdir -p docs/technical/t-daily-logs

# 3. Test system
# Type "GO" to verify context loading
# Type "consol" to verify command functionality
```

### Verification Steps
1. **Check .claude context files exist**:
   - `.claude/context/current-session.json`
   - `.claude/context/layer-status.json`
   - `.claude/context/session-commands.json`
   - `.claude/context/six-command-system.json`
   - `.claude/context/go-command.json`

2. **Verify folder structure**:
   - All T-P prefixed folders exist
   - Existing files properly located in renamed folders

3. **Test commands**:
   - "GO" loads context successfully
   - "consol" creates file in p-mini-consolidations

## Manual Reconstruction

If backup is unavailable, rebuild system from scratch:

### Step 1: Create Folder Structure
```bash
# Create progress folders
mkdir -p docs/progress/p-mini-consolidations
mkdir -p docs/progress/p-session-logs
mkdir -p docs/progress/p-daily-logs

# Create technical folders  
mkdir -p docs/technical/t-mini-changes
mkdir -p docs/technical/t-session-changes
mkdir -p docs/technical/t-daily-logs

# Rename existing folders if they exist
mv docs/progress/mini-consolidations docs/progress/p-mini-consolidations 2>/dev/null || true
mv docs/progress/session-logs docs/progress/p-session-logs 2>/dev/null || true
mv docs/technical/daily-logs docs/technical/t-daily-logs 2>/dev/null || true
```

### Step 2: Create .claude Context Files
```bash
mkdir -p .claude/context .claude/config .claude/prompts
```

Create these essential files:

**`.claude/context/six-command-system.json`**:
```json
{
  "six_command_system": {
    "version": "1.0",
    "description": "Complete parallel logging system with progress and technical commands",
    "timestamp_format": "date \"+%Y-%m-%d-%H-%M\"",
    "date_format": "date \"+%Y-%m-%d\""
  },
  "progress_commands": {
    "consol": {
      "trigger": "consol",
      "file_location": "docs/progress/p-mini-consolidations/",
      "naming_format": "[timestamp]-p-mini.md"
    },
    "end_sesh": {
      "trigger": "end sesh",
      "file_location": "docs/progress/p-session-logs/", 
      "naming_format": "[timestamp]-p-session.md"
    },
    "end_day": {
      "trigger": "end day",
      "file_location": "docs/progress/p-daily-logs/",
      "naming_format": "[date]-p-daily-progress.md"
    }
  },
  "technical_commands": {
    "code": {
      "trigger": "code",
      "file_location": "docs/technical/t-mini-changes/",
      "naming_format": "[timestamp]-t-mini.md"
    },
    "end_code": {
      "trigger": "end code", 
      "file_location": "docs/technical/t-session-changes/",
      "naming_format": "[timestamp]-t-session.md"
    },
    "end_tech": {
      "trigger": "end tech",
      "file_location": "docs/technical/t-daily-logs/",
      "naming_format": "[date]-t-daily-code-changes.md"
    }
  }
}
```

**`.claude/context/go-command.json`**:
```json
{
  "go_command": {
    "trigger": "GO",
    "description": "Load complete context and display current state",
    "implementation": "active",
    "timestamp_format": "date \"+%Y-%m-%d-%H-%M\"",
    "context_sources": {
      "claude_context": ".claude/context/",
      "obsidian_reference": "docs/reference/"
    }
  }
}
```

**`.claude/config/claude-config.json`**:
```json
{
  "project": {
    "name": "X Unfollow App",
    "type": "web_application"
  },
  "session_automation": {
    "commands": {
      "session_start": "GO",
      "progress_mini": "consol", 
      "progress_session": "end sesh",
      "progress_daily": "end day",
      "technical_mini": "code",
      "technical_session": "end code", 
      "technical_daily": "end tech"
    },
    "command_reference": ".claude/context/six-command-system.json"
  }
}
```

### Step 3: Test System
```bash
# Verify structure
ls -la docs/progress/
ls -la docs/technical/
ls -la .claude/context/

# Test timestamp generation
date "+%Y-%m-%d-%H-%M"

# Test file creation (simulate "consol" command)
TIMESTAMP=$(date "+%Y-%m-%d-%H-%M")
echo "# Test File - $TIMESTAMP" > "docs/progress/p-mini-consolidations/${TIMESTAMP}-test-mini.md"
```

## Rollback Instructions

### If Issues Occur
1. **Backup current state before rollback**:
   ```bash
   cp -r .claude .claude-backup-$(date +%Y%m%d)
   ```

2. **Restore from previous backup**:
   ```bash
   rm -rf .claude
   cp -r docs/reference/claude-system-backup-2025-06-16 .claude
   ```

3. **Revert folder structure if needed**:
   ```bash
   mv docs/progress/p-mini-consolidations docs/progress/mini-consolidations
   mv docs/progress/p-session-logs docs/progress/session-logs  
   mv docs/technical/t-daily-logs docs/technical/daily-logs
   ```

## Upgrade Path

### From Previous System
If upgrading from an older organization system:

1. **Backup existing work**:
   ```bash
   cp -r docs docs-backup-$(date +%Y%m%d)
   ```

2. **Migrate files to new structure**:
   ```bash
   # Move existing consolidations
   mv docs/progress/mini-consolidations/* docs/progress/p-mini-consolidations/
   
   # Move existing session logs
   mv docs/progress/session-logs/* docs/progress/p-session-logs/
   
   # Move existing technical logs
   mv docs/technical/daily-logs/* docs/technical/t-daily-logs/
   ```

3. **Update file references** in existing documentation to use new folder paths

4. **Test compatibility** with new command system

## Troubleshooting

### Common Issues

**Commands not recognized**:
- Verify .claude/context files exist and contain command specifications
- Check that GO command loads context properly

**Files created in wrong location**:
- Verify folder structure matches T-P naming convention
- Check command specifications reference correct paths

**Date scanning not working**:
- Test `date` command format: `date "+%Y-%m-%d-%H-%M"`
- Verify files follow proper naming convention

**Context not loading on session start**:
- Ensure .claude/context/ folder exists with required files
- Check docs/reference/ folder contains Session-Command-Behavior.md

### Support Files

Reference these files for detailed specifications:
- `docs/reference/Six-Command-System-Model.md` - Complete command specifications
- `docs/reference/T-P-Folder-Structure.md` - Folder organization details  
- `docs/reference/Dynamic-Date-Scanning-Logic.md` - File scanning implementation

## System Validation

### Health Check Commands
```bash
# Verify all required folders exist
test -d docs/progress/p-mini-consolidations && echo "✅ p-mini-consolidations exists"
test -d docs/progress/p-session-logs && echo "✅ p-session-logs exists"  
test -d docs/progress/p-daily-logs && echo "✅ p-daily-logs exists"
test -d docs/technical/t-mini-changes && echo "✅ t-mini-changes exists"
test -d docs/technical/t-session-changes && echo "✅ t-session-changes exists"
test -d docs/technical/t-daily-logs && echo "✅ t-daily-logs exists"

# Verify context files exist
test -f .claude/context/six-command-system.json && echo "✅ six-command-system.json exists"
test -f .claude/context/go-command.json && echo "✅ go-command.json exists"
test -f .claude/config/claude-config.json && echo "✅ claude-config.json exists"

# Test timestamp generation
date "+%Y-%m-%d-%H-%M" && echo "✅ Timestamp generation working"
```

## Maintenance

### Regular Backups
```bash
# Create weekly backup
cp -r .claude docs/reference/claude-system-backup-$(date +%Y-%m-%d)

# Archive old backups (keep last 4 weeks)
find docs/reference/ -name "claude-system-backup-*" -type d -mtime +28 -exec rm -rf {} \;
```

### System Updates
When making improvements to the command system:
1. Create backup before changes
2. Test changes with "consol" command first
3. Update reference documentation
4. Create new backup with version tag

This restoration guide ensures the Six-Command System can be rebuilt or recovered at any time while maintaining full functionality.
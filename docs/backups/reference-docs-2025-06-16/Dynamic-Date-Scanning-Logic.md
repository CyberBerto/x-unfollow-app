# Dynamic Date Scanning Logic

*Technical specification for automatic same-day file referencing*  
*Created: 2025-06-16*  
*Version: 1.0*

## Overview

Dynamic Date Scanning enables all six commands to automatically reference same-day files when creating consolidations and summaries. This eliminates manual file hunting and ensures comprehensive context compilation.

## Core Logic

### Timestamp Generation
```bash
# For timestamped files (mini and session level)
TIMESTAMP=$(date "+%Y-%m-%d-%H-%M")

# For daily files and date scanning  
CURRENT_DATE=$(date "+%Y-%m-%d")
```

### File Pattern Matching
Each command uses pattern matching to find same-day files:
```bash
# Find all files from current date
find docs/ -name "${CURRENT_DATE}-*" -type f

# Find specific folder files from current date
find docs/progress/p-mini-consolidations/ -name "${CURRENT_DATE}-*" -type f
```

## Command-Specific Scanning Rules

### Mini-Level Commands ("consol", "code")
**Scope**: Reference previous same-day mini files from same category

```bash
# For "consol" command
REFERENCE_FILES=$(find docs/progress/p-mini-consolidations/ -name "${CURRENT_DATE}-*-p-mini.md")

# For "code" command  
REFERENCE_FILES=$(find docs/technical/t-mini-changes/ -name "${CURRENT_DATE}-*-t-mini.md")
```

**Logic**: Build on previous mini updates from the same day

### Session-Level Commands ("end sesh", "end code")  
**Scope**: Reference ALL same-day mini files from both progress and technical

```bash
# For "end sesh" command
P_MINI_FILES=$(find docs/progress/p-mini-consolidations/ -name "${CURRENT_DATE}-*")
T_MINI_FILES=$(find docs/technical/t-mini-changes/ -name "${CURRENT_DATE}-*")

# For "end code" command
T_MINI_FILES=$(find docs/technical/t-mini-changes/ -name "${CURRENT_DATE}-*")  
P_MINI_FILES=$(find docs/progress/p-mini-consolidations/ -name "${CURRENT_DATE}-*")
```

**Logic**: Compile complete session picture from both progress and technical mini updates

### Daily-Level Commands ("end day", "end tech")
**Scope**: Reference ALL same-day files from ALL folders

```bash
# For both "end day" and "end tech" commands
ALL_P_MINI=$(find docs/progress/p-mini-consolidations/ -name "${CURRENT_DATE}-*")
ALL_P_SESSION=$(find docs/progress/p-session-logs/ -name "${CURRENT_DATE}-*") 
ALL_T_MINI=$(find docs/technical/t-mini-changes/ -name "${CURRENT_DATE}-*")
ALL_T_SESSION=$(find docs/technical/t-session-changes/ -name "${CURRENT_DATE}-*")
ALL_T_DAILY=$(find docs/technical/t-daily-logs/ -name "${CURRENT_DATE}-*")
```

**Logic**: Create comprehensive daily summary from complete day's work

## Implementation Examples

### File Reference Generation
```bash
# Function to generate file references for consolidation
generate_same_day_references() {
    local search_paths="$1"
    local current_date=$(date "+%Y-%m-%d")
    
    echo "## Same-Day File References"
    
    for path in $search_paths; do
        files=$(find "$path" -name "${current_date}-*" -type f | sort)
        if [ -n "$files" ]; then
            echo "### ${path##*/} Files:"
            for file in $files; do
                filename=$(basename "$file")
                echo "- [$filename]($file)"
            done
        fi
    done
}
```

### Content Compilation  
```bash
# Function to extract key content from referenced files
compile_day_content() {
    local files="$1"
    
    echo "## Daily Summary Compilation"
    
    for file in $files; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            echo "### From $filename:"
            
            # Extract accomplishments sections
            grep -A 5 "## Current Accomplishments" "$file" | tail -n +2
            
            # Extract next priorities  
            grep -A 3 "## Next Priorities" "$file" | tail -n +2
        fi
    done
}
```

## Scanning Efficiency

### Optimized Search Patterns
- **Date-First Filtering**: Use date prefix to limit search scope
- **Folder-Specific Searches**: Only scan relevant folders for each command
- **File Type Filtering**: Only include .md files in scans

### Performance Considerations
```bash
# Efficient pattern: Start with date, then filter by folder
find docs/progress/p-mini-consolidations/ -name "2025-06-16-*" -name "*.md"

# Avoid: Broad search then filter  
find docs/ -name "*.md" | grep "2025-06-16" | grep "p-mini"
```

## Error Handling

### Missing Files
```bash
# Check if any files found before processing
if [ -z "$REFERENCE_FILES" ]; then
    echo "No same-day files found - creating initial entry for $(date '+%Y-%m-%d')"
else
    echo "Found $(echo $REFERENCE_FILES | wc -w) same-day files to reference"
fi
```

### Date Boundary Issues
```bash
# Handle sessions that span midnight
YESTERDAY=$(date -d "yesterday" "+%Y-%m-%d")
TODAY=$(date "+%Y-%m-%d")

# Check both dates for session-spanning work
YESTERDAY_FILES=$(find docs/ -name "${YESTERDAY}-*" -type f)
TODAY_FILES=$(find docs/ -name "${TODAY}-*" -type f)
```

## Content Integration Strategies

### Automatic Summarization
```markdown
# Template for referenced content integration
## Compilation from Same-Day Files

### Accomplishments Summary
[Automatically extracted from all same-day accomplishment sections]

### Technical Changes Summary  
[Automatically extracted from all same-day technical sections]

### Next Priorities Consolidated
[Automatically merged from all same-day priority lists]
```

### Cross-Reference Links
```markdown
# Template for file reference sections  
## Referenced Files
- [2025-06-16-09-30-p-mini.md](docs/progress/p-mini-consolidations/2025-06-16-09-30-p-mini.md)
- [2025-06-16-12-15-t-mini.md](docs/technical/t-mini-changes/2025-06-16-12-15-t-mini.md)
- [2025-06-16-15-00-p-session.md](docs/progress/p-session-logs/2025-06-16-15-00-p-session.md)
```

## Benefits of Dynamic Scanning

### Automation
- **No Manual File Hunting**: Commands automatically find relevant files
- **Complete Context**: Never miss same-day work when creating summaries
- **Consistent References**: Standardized file inclusion across all commands

### Accuracy
- **Time-Based Relevance**: Only includes files from same work day
- **Comprehensive Coverage**: Daily commands capture all work from the day
- **Chronological Organization**: Files naturally ordered by timestamp

### Scalability  
- **Works Regardless of Volume**: Handles 1 file or 20 files per day equally well
- **Adapts to Usage Patterns**: Commands adjust to actual daily work frequency
- **Future-Proof**: Logic works for any date, any number of files

## Implementation Timeline

1. **Phase 1**: Basic date scanning for "consol" command ✅ Complete
2. **Phase 2**: Session-level scanning for "end sesh" and "end code" 
3. **Phase 3**: Daily-level comprehensive scanning for "end day" and "end tech"
4. **Phase 4**: Optimization and error handling improvements

This dynamic scanning logic provides the intelligence needed for truly automated consolidation and summary generation across the six-command system.
# T-P Folder Structure Documentation

*Complete specification of the parallel folder organization*  
*Created: 2025-06-16*  
*Version: 1.0*

## Overview

The T-P (Technical-Progress) folder structure provides clear separation between code-focused technical documentation and project-focused progress tracking, while maintaining parallel organization for easy cross-referencing.

## Folder Structure

### Progress Folders (P-Prefix)
**Purpose**: Project updates, accomplishments, planning, and descriptive summaries

```
docs/progress/
├── p-mini-consolidations/    # Quick progress updates ("consol" command)
├── p-session-logs/          # Session-level progress summaries ("end sesh" command)  
├── p-daily-logs/            # Comprehensive daily progress ("end day" command)
├── weekly-summaries/        # Existing weekly progress summaries
├── completed-cycles/        # Historical project phases
└── README.md               # Progress folder documentation
```

### Technical Folders (T-Prefix)  
**Purpose**: Code changes, implementation details, and technical documentation

```
docs/technical/
├── t-mini-changes/          # Quick code change logs ("code" command)
├── t-session-changes/       # Session-level technical summaries ("end code" command)
├── t-daily-logs/            # Comprehensive daily technical recounts ("end tech" command)
├── App-Architecture-Analysis.md    # Existing technical analysis
├── Code-Changes-Log.md      # Existing code change tracking
├── Current-Functions-Inventory.md  # Function documentation  
└── Layer-2-Testing-Plan.md  # Technical planning documents
```

## Naming Conventions

### Folder Prefixes
- **T-Prefix**: `t-[folder-name]` for technical folders
- **P-Prefix**: `p-[folder-name]` for progress folders

### File Prefixes
- **T-Files**: `YYYY-MM-DD-HH-MM-t-[type].md` for technical files
- **P-Files**: `YYYY-MM-DD-HH-MM-p-[type].md` for progress files

## Content Guidelines

### Progress Folders (P-Prefix)
**Focus**: What was accomplished, why it matters, what's next

**Content Types**:
- Project milestones and achievements  
- Planning and priority setting
- Blocking issues and resolutions
- User impact and business value
- Layer completion and progress tracking
- Strategic decisions and direction

**Language Style**: Descriptive, goal-oriented, accessible to non-technical readers

### Technical Folders (T-Prefix)
**Focus**: How things were implemented, what code changed, technical details

**Content Types**:
- File modifications and line changes
- Function additions and improvements  
- Architecture decisions and implementations
- Bug fixes and technical resolutions
- Performance optimizations
- Code quality improvements
- Testing and validation details

**Language Style**: Technical, implementation-focused, code-specific

## Cross-Referencing System

### Parallel Structure Benefits
- **Same Timestamps**: Easy to find corresponding progress and technical files
- **Complementary Information**: Progress explains WHY, technical explains HOW  
- **Complete Picture**: Both perspectives provide full understanding
- **Validation**: Technical details validate progress claims

### Reference Examples
```markdown
# In progress file (p-session):
"Enhanced error handling implementation completed (see t-session-changes for technical details)"

# In technical file (t-session):  
"Implemented _parse_unfollow_response() method (supports Layer 2 goals documented in p-session-logs)"
```

## Migration from Previous Structure

### Renamed Folders
- `mini-consolidations/` → `p-mini-consolidations/`
- `session-logs/` → `p-session-logs/`  
- `daily-logs/` (technical) → `t-daily-logs/`

### New Folders Created
- `p-daily-logs/` (new progress daily summaries)
- `t-session-changes/` (new technical session summaries)
- `t-mini-changes/` (new technical mini updates)

### Backwards Compatibility
- All existing files preserved in renamed folders
- File content unchanged, only location updated
- Links and references updated to new folder names

## Advantages of T-P Structure

### Clarity
- **No Ambiguity**: Clear distinction between technical and progress content
- **Easy Navigation**: Folder prefixes immediately indicate content type
- **Consistent Organization**: Same three-tier structure for both tracks

### Efficiency  
- **Focused Writing**: Know exactly what type of content to include
- **Quick Reference**: Find progress OR technical details quickly
- **Parallel Development**: Can update both tracks simultaneously

### Scalability
- **Future Growth**: Easy to add new folder types with T/P prefixes
- **Team Collaboration**: Clear separation allows different team members to focus on different tracks
- **Archive Management**: Easy to archive or backup specific content types

## Usage Guidelines

### When to Use Progress Folders (P-Prefix)
- Documenting accomplishments and milestones
- Planning next steps and priorities  
- Recording strategic decisions
- Summarizing user impact and business value
- Creating accessible project updates

### When to Use Technical Folders (T-Prefix)
- Logging specific code changes
- Documenting implementation details
- Recording architecture decisions
- Tracking performance improvements
- Creating technical references for future development

### Cross-Referencing Best Practices
- Always reference corresponding file from opposite track
- Use same timestamps for easy correlation
- Maintain parallel detail levels (mini-session-daily)
- Link technical achievements to progress goals

## System Maintenance

### Regular Tasks
- Ensure parallel files exist for major work sessions
- Archive old files according to retention policy
- Update cross-references when restructuring
- Validate that T/P folders maintain parallel organization

### Quality Checks
- Progress files focus on WHAT and WHY
- Technical files focus on HOW and implementation details
- File naming follows T-P convention consistently
- Cross-references remain valid and helpful

This T-P structure provides the foundation for organized, scalable documentation that serves both project management and technical development needs.
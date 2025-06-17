yea # Estimation Data Naming & Sorting Standards

*Consistent file naming and organization for long-term analysis*

## File Naming Conventions

### Session Exports
**Format**: `Session-YYYYMMDD_HHMM-[phase]-[type].md`

**Examples**:
- `Session-20250613_1307-Phase39-Debugging.md`
- `Session-20250614_0900-Phase4-Testing.md`
- `Session-20250615_1430-Maintenance-Documentation.md`

**Components**:
- **Date/Time**: ISO format for chronological sorting
- **Phase**: Current development phase (Phase39, Phase4, etc.)
- **Type**: Work category (Debugging, Testing, Feature, Maintenance, Analysis)

### Batch Summaries
**Format**: `Batch-YYYYMMDD-[sequence]-[focus].md`

**Examples**:
- `Batch-20250613-01-CoreDebugging.md`
- `Batch-20250613-02-ErrorHandling.md`
- `Batch-20250614-01-APITesting.md`

**Components**:
- **Date**: Session date
- **Sequence**: 01, 02, 03... (batches within same day)
- **Focus**: Primary work area (max 15 chars)

### Workflow Analysis
**Format**: `Analysis-YYYY-[period]-[metric].md`

**Examples**:
- `Analysis-2025-Week24-TokenEfficiency.md`
- `Analysis-2025-Month06-ComplexityTrends.md`
- `Analysis-2025-Quarter2-ToolUsagePatterns.md`

**Components**:
- **Year**: For long-term tracking
- **Period**: Week##, Month##, Quarter#, or Annual
- **Metric**: Analysis focus area

## Folder Organization Standards

### By Time Period
```
session-exports/
├── 2025/
│   ├── 06-June/
│   │   ├── Week-24/
│   │   └── Week-25/
│   └── 07-July/
├── archive/
│   └── 2024/
```

### By Development Phase
```
session-exports/
├── Phase-3.9-Validation/
├── Phase-4-Testing/
├── Phase-5-Production/
└── Maintenance/
```

### By Work Type
```
session-exports/
├── debugging/
├── feature-development/
├── testing/
├── documentation/
└── analysis/
```

## Sorting and Indexing Standards

### Chronological Index
**File**: `INDEX-Chronological.md`
- All sessions listed by date
- Quick timeline view
- Phase transitions marked

### Efficiency Index  
**File**: `INDEX-Efficiency.md`
- Sessions sorted by token efficiency
- Best/worst performers highlighted
- Pattern identification

### Complexity Index
**File**: `INDEX-Complexity.md`
- Sessions grouped by complexity level
- Tool usage patterns
- Difficulty progression

## Long-Term Analysis Framework

### Monthly Reports
**Generate**: First week of each month
**Content**:
- Token usage trends
- Efficiency improvements
- Tool usage evolution
- Complexity patterns
- Cost analysis

### Quarterly Analysis
**Generate**: End of quarter
**Content**:
- Phase completion analysis
- ROI on infrastructure investment
- Development velocity trends
- Prediction accuracy assessment

### Annual Summary
**Generate**: End of year
**Content**:
- Complete project cost analysis
- Efficiency evolution over time
- Tool effectiveness ranking
- Methodology improvements

## Data Retention Standards

### Active Data (Current Year)
- **Location**: Main folders
- **Detail Level**: Complete session data
- **Access**: Immediate

### Archive Data (Previous Years)
- **Location**: `archive/YYYY/` subfolders
- **Detail Level**: Summary reports only
- **Access**: Reference lookup

### Purge Policy
- **Raw session data**: Keep 2 years
- **Summary reports**: Keep indefinitely
- **Analysis reports**: Keep indefinitely

## Automated Processing Standards

### File Generation Rules
1. **Auto-prefix** with timestamp on creation
2. **Auto-categorize** by detected work type
3. **Auto-index** in chronological listing
4. **Auto-archive** sessions older than 1 year

### Quality Checks
- Filename validation on creation
- Duplicate detection
- Missing data alerts
- Consistency verification

## Integration Points

### With Token Usage Tracker
- Weekly rollup entries
- Monthly summary integration
- Cross-reference validation

### With Session Dashboard
- Current session type detection
- Efficiency alerts
- Progress tracking

### With Development Rules
- Standard compliance checking
- Pattern validation
- Best practice enforcement

---

*Established: 2025-06-13*
*Version: 1.0*
*Next Review: 2025-07-13*
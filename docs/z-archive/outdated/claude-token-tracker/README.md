# Claude Estimation Tracker

Automatic token usage estimation for Claude Code development sessions.

## Overview

This system provides **automatic estimation tracking** without API calls:
- **No manual input required** - tracks workflow automatically
- **Estimation-based** - content analysis instead of API calls  
- **Batch summaries** - every 3-5 exchanges
- **Session summaries** - complete workflow breakdown
- **Transparent about limitations** - estimates 2-5x under actual usage

## Quick Start

1. **Start session:**
   ```bash
   python auto_tracker.py
   ```

2. **Work normally** - estimation tracking happens automatically

3. **End session:**
   ```bash
   python auto_tracker.py --end
   ```

## Features

- **Automatic workflow estimation** - tracks file operations, analysis, code generation
- **Complexity awareness** - simple/medium/complex/very_complex multipliers
- **Batch summaries** - regular progress updates
- **Session summaries** - complete breakdown with disclaimers
- **No API calls** - pure estimation based on content analysis
- **Obsidian integration** - export data for tracking

## Files

- `estimation_tracker.py` - Core estimation system
- `auto_tracker.py` - Session management
- `estimation_log.json` - Detailed estimation logs
- `current_session.json` - Active session metadata

## Integration with Development Workflow

Perfect for:
1. **Session planning** - estimate complexity and token requirements
2. **Workflow analysis** - understand what operations are expensive
3. **Progress tracking** - batch summaries show development velocity
4. **Budget planning** - apply 2-5x multiplier for realistic estimates

## Limitations

⚠️ **Important:** Estimates are 2-5x UNDER actual usage
- Useful for relative comparison and trends
- Not accurate for billing/budget purposes  
- Cannot capture internal AI reasoning costs
- Best used with known multipliers for realistic planning
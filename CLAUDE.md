# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ODCV (Occupancy-Driven Control Valve) analytics dashboard for building management systems. The system analyzes occupancy sensor data and zone control logic to validate BMS (Building Management System) timing compliance and energy efficiency.

**Current Status**: Major refactor in progress from MVP (3 sensors, 22 hours) to production scale (100+ sensors, months of data). See `refactor.md` for detailed phased approach.

## Development Commands

**Core Analysis Scripts:**
```bash
# Main timeline visualizer (primary tool)
python3 timeline_visualizer.py <csv_file> [start_time] [duration_hours]

# Examples:
python3 timeline_visualizer.py SCH-1_data_20250916.csv
python3 timeline_visualizer.py sensor_dump_filtered.csv '2025-09-11 08:00' 12

# Supporting analysis tools
python3 occupancy_analysis.py <csv_file>
python3 detailed_control_analysis.py <csv_file>
python3 filter_sensor_data.py  # Filter large sensor dumps to specific time ranges
```

**Use Python 3** - The environment has `python3` not `python` installed.

## CRITICAL DEPLOYMENT FLOW

**🚨 NEVER merge development to main without explicit user instruction! 🚨**

**Correct Deployment Flow:**
1. **Local Development** → `development` branch
2. **Sync to GitHub** → `git push origin development` (triggers Railway staging)
3. **Railway Staging** → Test on staging environment
4. **Only after approval** → Merge to `main` for production

**Commands for GitHub Sync (staging deployment):**
```bash
git add [files]
git commit -m "description"
git push origin development  # This triggers Railway staging deployment
```

**NEVER run these without explicit instruction:**
- `gh pr create` to main branch
- `gh pr merge` to main branch
- `git push origin main`

**The user controls when development is ready for production deployment to main.**

## Architecture Overview

### Current Monolithic Structure (Being Refactored)
- **timeline_visualizer.py** (1,403 lines) - Monolithic file containing all functionality
- Multiple analysis scripts with duplicated patterns (occupancy_analysis.py, detailed_control_analysis.py)
- Hardcoded `SENSOR_ZONE_MAP` configuration repeated across files
- CSV input → Analysis → HTML output pipeline

### Planned Modular Architecture (Phase 3)
```
src/
├── data/              # CSV loading, timestamp parsing, configuration
├── analysis/          # Statistics, violation detection, timeline processing
└── presentation/      # HTML generation, data formatting
```

**Key Refactor Context**: Currently in Phase 3 (Separation of Concerns). See `refactor.md` for complete phased plan and current status.

## Data Flow & Patterns

### Sensor-to-Zone Mapping
Core configuration pattern used throughout codebase:
```python
SENSOR_ZONE_MAP = {
    '115-4-01 presence': 'BV200',
    '115-4-06 presence': 'BV201',
    '115-4-09 presence': 'BV202'
}
```

### CSV Data Processing
- **Input**: Building sensor CSV files with timestamp, sensor name, value columns
- **Processing**: Occupancy correlation analysis, timing violation detection
- **Output**: Interactive HTML dashboards with timeline visualizations

### Control Logic Validation
- **Timing Rules**: 15min unoccupied → standby, 5min occupied → active
- **Violation Detection**: Early transitions, missed responses
- **Statistics**: Occupancy ratios, control error rates, energy efficiency metrics

## File Structure Context

### Data Files
- `SCH-1_data_20250916.csv` - Recent comprehensive dataset (primary)
- `sensor_dump_*.csv` - Large historical dumps requiring filtering
- `sensor_dump_filtered.csv` - Processed subset for analysis

### Generated Outputs
- `timeline_viewer.html` - Main interactive dashboard (2.3MB+ with embedded data)
- `timeline_with_executive_dashboard.html` - Executive summary version
- Multiple timeline variants for different time ranges and visualizations

### Analysis Documentation
- `ANALYSIS_REPORT.md` - Detailed findings and control performance
- `COMPARATIVE_ANALYSIS.md` - Cross-sensor comparison insights
- `TIMELINE_VIEWER_GUIDE.md` - Dashboard usage instructions

## Scalability Challenges

**Current Limitations (Being Addressed)**:
- Single HTML file approach doesn't scale to 100+ sensors
- Monolithic code structure makes validation rule changes difficult
- Memory constraints with large embedded JavaScript data arrays
- Hardcoded sensor mappings require code changes for new installations

**Planned Solutions**:
- Table-based interface for 100+ sensor overview
- Plugin-based validation architecture
- Database abstraction layer for large datasets
- Configuration-driven sensor management

## Development Context

### Active Refactor Phases
1. **Phase 3** (Current): Separate data/analysis/presentation layers
2. **Phase 2** (Next): Modular validation plugin system
3. **Phase 1** (Final): 100+ sensor table interface with statistics

### Testing Requirements
- Output comparison between old/new implementations
- Unit tests for separated modules
- Performance benchmarking for large datasets
- Manual validation of control logic accuracy

### Critical Patterns
- **Timestamp Parsing**: Multiple datetime formats in sensor data
- **State Transitions**: Occupancy sensor and zone mode correlation
- **Violation Categorization**: Premature standby/occupied transitions
- **Duration Calculations**: Time-based statistics and ratios

Always reference `refactor.md` for current phase status and implementation priorities. The codebase is in active architectural transition to support production deployment.
# ODCV Analytics Dashboard Refactor Plan

## Overview
Refactoring the ODCV (Occupancy-Driven Control Valve) analytics dashboard from MVP (3 sensors, 22 hours) to production scale (100+ sensors, months of data). The refactor is structured in phases to ensure testability and incremental progress.

## Phase Implementation Order
**Revised Priority Order** (per user request):
1. **Phase 3**: Separation of Concerns (CURRENT)
2. **Phase 2**: Modular Validation Architecture
3. **Phase 1**: 100+ Sensor Table Interface
4. **Phase 4**: Data Quality & Performance (Backlog)

*Rationale: Phase 1 cannot be tested without more data, so we build the foundation first.*

---

## Phase 3: Separation of Concerns (CURRENT PHASE)
**Goal**: Extract monolithic `timeline_visualizer.py` (1,403 lines) into modular architecture

### Current Analysis
- **Data Layer**: `load_data()`, `parse_timestamp()` (lines 20-44)
- **Analysis Layer**: `calculate_occupancy_statistics()`, `calculate_error_rates()`, `create_timeline_data()` (lines 56-306)
- **Presentation Layer**: `create_html_viewer()` (lines 307-1334)
- **Orchestration**: `main()` (lines 1336-1404)
- **Configuration**: `SENSOR_ZONE_MAP` hardcoded (lines 14-18)

### Phase 3 Implementation Plan

#### Directory Structure
```
src/
├── data/
│   ├── __init__.py
│   ├── data_loader.py      # CSV loading, timestamp parsing
│   └── config.py           # Sensor mappings, constants
├── analysis/
│   ├── __init__.py
│   ├── occupancy_calculator.py  # Statistics calculation
│   ├── violation_detector.py   # Timing violation logic
│   └── timeline_processor.py   # Event processing, timeline data creation
├── presentation/
│   ├── __init__.py
│   ├── html_generator.py   # HTML template generation
│   └── formatters.py       # Duration formatting, data serialization
└── __init__.py
```

#### File Extraction Tasks
- [ ] **src/data/data_loader.py**: Extract `parse_timestamp()`, `load_data()`
- [ ] **src/data/config.py**: Extract `SENSOR_ZONE_MAP`, defaults
- [ ] **src/analysis/occupancy_calculator.py**: Extract `calculate_occupancy_statistics()`
- [ ] **src/analysis/violation_detector.py**: Extract `calculate_error_rates()`, violation logic
- [ ] **src/analysis/timeline_processor.py**: Extract `create_timeline_data()`
- [ ] **src/presentation/formatters.py**: Extract `format_duration()`, serialization
- [ ] **src/presentation/html_generator.py**: Extract `create_html_viewer()`
- [ ] **timeline_visualizer.py**: Simplify to orchestrator with imports

#### Interface Contracts
- **Data Layer**: CSV → Structured data objects
- **Analysis Layer**: Data objects → Analysis results
- **Presentation Layer**: Analysis results → HTML files

#### Testing Strategy
- [ ] Unit tests for each separated module
- [ ] Integration test: old vs new output comparison
- [ ] Validation: identical HTML generation
- [ ] Performance benchmarks

### Phase 3 Success Criteria
- [x] All functionality preserved (identical output)
- [x] Clean module separation achieved
- [x] Unit tests passing for all modules
- [x] Foundation ready for Phase 2 plugins

---

## Phase 2: Modular Validation Architecture (NEXT)
**Goal**: Convert hardcoded validation logic into plugin-based system

### Planned Architecture
```
src/analysis/validations/
├── __init__.py
├── base_validator.py       # Abstract base class
├── timing_validator.py     # BMS timing rules
├── occupancy_validator.py  # Sensor correlation rules
└── data_quality_validator.py # Missing data, anomalies
```

### Requirements
- Each validation type as separate module/file
- Easy to add new validation rules
- Configuration-driven validation parameters
- Consistent violation reporting format

---

## Phase 1: 100+ Sensor Table Interface (FINAL)
**Goal**: Replace individual timelines with scalable table view

### Requirements
- Table showing 100+ sensor/VAV pairs
- Key statistics per row:
  - % time in standby mode
  - % sensor occupied that zone is occupied
  - % sensor unoccupied that zone is on standby
  - % control violations
- Color coding for performance indicators
- Expandable detail views
- Virtual scrolling for performance

---

## Phase 4: Data Quality & Performance (BACKLOG)
**Goal**: Production-ready data handling

### Planned Features
- Chunked CSV processing for large files
- Data filtering and time range selection
- Database abstraction layer (future TimescaleDB)
- Configuration system for deployment scaling
- Memory optimization and caching

---

## Implementation Notes

### Testing Requirements (After Each Phase)
- Automated validation testing plan
- Manual validation testing plan
- Performance benchmarking
- Output comparison verification

### Git Workflow
- Feature branch per phase
- PR creation with comprehensive testing
- No direct main branch commits
- Pre-merge checklist adherence

### Documentation Updates
This `refactor.md` file will be updated throughout the process to track:
- Progress within each phase
- Decisions made and rationale
- Issues encountered and resolutions
- Architecture evolution and lessons learned

---

## Current Status
**Phase 3: Separation of Concerns** ✅ **COMPLETED**
- [x] Analysis of current monolithic structure completed
- [x] Modular architecture designed
- [x] Directory structure creation
- [x] File extraction implementation
- [x] Testing and validation

**Phase 3 Results:**
- Reduced `timeline_visualizer.py` from 1,403 lines to 89 lines (orchestrator only)
- Created 8 modular files with clean separation of concerns:
  - `src/data/` - data loading and configuration
  - `src/analysis/` - occupancy calculation, violation detection, timeline processing
  - `src/presentation/` - formatting and HTML generation
- Verified identical output with existing test data
- Foundation ready for Phase 2 (modular validation architecture)

**Phase 2: Modular Validation Architecture** ✅ **COMPLETED**

**Phase 2 Results:**
- Created plugin-based validation system with abstract base class
- Extracted hardcoded validation logic into 3 specialized plugins:
  - `TimingValidator` - BMS timing compliance validation
  - `OccupancyValidator` - Sensor-zone correlation validation
  - `DataQualityValidator` - Data gap and anomaly detection
- Added `ValidationManager` to coordinate multiple validators
- Implemented configuration-driven validation parameters with site profiles
- Created validation config system supporting: default, strict, lenient, energy_optimized profiles
- Verified identical violation detection results
- Maintained backward compatibility with existing timeline processor

**Plugin Architecture Benefits:**
- Easy addition of new validation rules without code changes
- Configurable validation parameters per deployment site
- Isolated validation logic for independent testing
- Extensible system ready for custom validation requirements

**Ready for Phase 1: 100+ Sensor Table Interface**

*Last Updated: 2025-09-17*
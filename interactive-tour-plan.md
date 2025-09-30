# Interactive ODCV Analytics Tour - Feature-Focused Implementation Plan

## Phase 1: Tour Infrastructure Overhaul
1. **Remove Modal Overlay**
   - Disable `useModalOverlay: true` to allow user interaction
   - Replace with highlight animations and directional arrows
   - Add progress indicator showing tour step (e.g., "Step 3 of 12")

2. **Interactive Tour Flow**
   - Non-blocking tour that allows clicks and navigation
   - Highlight elements with pulsing borders/arrows
   - "Try It" prompts that guide user actions
   - Progress tracking without complex state management

## Phase 2: Feature-Demonstration Mock Datasets

### Data Structure (All Datasets):
- **12 Sensors Total**: 4 sensors per floor × 3 floors
- **Sensor Layout**: Floor 1 (F1-01, F1-02, F1-03, F1-04), Floor 2 (F2-01, F2-02, F2-03, F2-04), Floor 3 (F3-01, F3-02, F3-03, F3-04)
- **Time Period**: 15 consecutive days
- **Data Density**: Sensor data every 30 seconds (2×/minute), BMS zone data every 60 seconds (1×/minute)
- **Zone Mapping**: Each sensor controls one BMS zone (F1-01 → VAV-101, F2-03 → VAV-203, etc.)

### Dataset A: "Perfect Compliance Showcase"
**Purpose**: Demonstrate ideal BMS performance and analytics baseline
**Narrative**: Recently commissioned building with optimal sensor placement and BMS programming

**Feature Demonstrations**:
- **Timing Compliance**: 98%+ adherence to 15-min unoccupied → standby rule and 5 minute standby → unoccupied
- **Data Quality**: Zero missing data, consistent 30s/60s intervals
- **Occupancy Patterns**: Realistic M-F business hours (8AM-6PM), minimal weekend activity
- **Analytics Results**: All green performance indicators, minimal violations, excellent correlation

**Specific Scenarios**:
- **Floor 1**: Conference rooms with predictable meeting patterns, perfect standby transitions
- **Floor 2**: Open office with consistent occupancy, demonstrates good sensor coverage
- **Floor 3**: Executive offices with sporadic use, shows proper extended standby periods

### Dataset B: "Timing Out of Spec Analysis"
**Purpose**: Showcase out of spec detection and timing rule analysis
**Narrative**: Older building with BMS programming issues causing energy waste

**Feature Demonstrations**:
- **Early Standby Transitions**: 25% of transitions happen <15 minutes after unoccupied
- **Delayed Response Transitions**: 15% of zones take >5 minutes to respond to occupancy
- **Pattern Analysis**: Out of spec clustered on specific floors/sensors showing systematic issues
- **Timeline Visualization**: Purple violation markers clearly visible on timeline
- **Statistics Impact**: Poor performance ratings, high error percentages

**Specific Scenarios**:
- **Floor 1**: F1-02 consistently goes standby after only 8-10 minutes (programming error)
- **Floor 2**: F2-01 and F2-03 slow to respond (5-12 minutes) due to sensor calibration issues
- **Floor 3**: F3-04 has random early standby transitions (shows intermittent BMS communication)

### Dataset C: "Missing Data & Outages"
**Purpose**: Demonstrate data quality analysis and missing data visualization
**Narrative**: Building with networking issues causing intermittent data loss

**Feature Demonstrations**:
- **Sensor Outages**: Specific sensors offline for hours/days showing red bars in missing data charts
- **Partial Data Loss**: Some sensors missing 20-40% of expected data points
- **BMS Communication Issues**: Zone data gaps causing control uncertainty

**Specific Scenarios**:
- **Floor 1**: F1-01 offline for 8 hours on the most recent day (sensor hardware failure)
- **Floor 2**: F2-02 intermittent data loss (20% missing) throughout all data periods (network issues)
- **Floor 3**: F3-03 BMS zone data missing for Days 13-14 (controller maintenance)

### Dataset D: "Mixed Performance Reality"
**Purpose**: Show realistic building performance with varied sensor/zone behavior
**Narrative**: Typical building with some areas performing well, others needing attention

**Feature Demonstrations**:
- **Grouping Benefits**: Floor-level view shows performance patterns
- **Drill-Down Analysis**: Individual sensor investigation reveals specific issues
- **Correlation Analysis**: Some sensors show good occupancy detection but poor BMS response
- **Commissioning Insights**: Identifies which sensors need recalibration vs BMS reprogramming

**Specific Scenarios**:
- **Floor 1**: 85% performance (good sensors, minor BMS tuning needed)
- **Floor 2**: 95% performance (recently maintained, exemplary operation)
- **Floor 3**: 80% performance (mixture of sensor and BMS issues needing attention)

## Phase 3: Mock Data Generation (Execute First)

### Data Structure (All Datasets):
- **12 Sensors Total**: 4 sensors per floor × 3 floors
- **Sensor Layout**: Floor 1 (F1-01, F1-02, F1-03, F1-04), Floor 2 (F2-01, F2-02, F2-03, F2-04), Floor 3 (F3-01, F3-02, F3-03, F3-04)
- **Time Period**: 15 consecutive days
- **Data Density**: Sensor data every 30 seconds (2×/minute), BMS zone data every 60 seconds (1×/minute)
- **Zone Mapping**: Each sensor controls one BMS zone (F1-01 → VAV-101, F2-03 → VAV-203, etc.)

### Create 4 Feature-Demonstration Datasets:
- **Dataset A**: "Perfect Compliance Showcase" (98%+ compliance, zero missing data)
- **Dataset B**: "Timing Out of Spec Analysis" (25% early standby, 15% delayed response)
- **Dataset C**: "Missing Data & Outages" (sensor outages, partial data loss, BMS gaps)
- **Dataset D**: "Mixed Performance Reality" (60-95% compliance variance across floors)

## Phase 4: Comprehensive Interactive Tour Design (Execute After Mock Data)

### Multi-Dataset Feature Tour (15 Steps):

1. **Welcome & Analytics Overview** - Introduce ODCV purpose and interface
2. **Perfect Baseline Demo** - Load Dataset A, show ideal performance metrics
3. **Executive Dashboard** - Explain green indicators, compliance percentages
4. **Building-Level Grouping** - Show floor performance summary view
5. **Time Period Controls** - Switch between 24h/5d/15d views with perfect data
6. **Out-of-Spec Detection** - Load Dataset B, demonstrate violation visualization
7. **Timeline Violations** - Show purple markers, explain timing rule failures
8. **Floor Pattern Analysis** - Drill down to see violation clustering by floor
9. **Data Quality Issues** - Load Dataset C, demonstrate missing data charts
10. **Outage Visualization** - Show red bars, "last outage" indicators
11. **Sensor Reliability** - Compare data completeness across sensors
12. **Mixed Reality Demo** - Load Dataset D, show varied performance
13. **Drill-Down Navigation** - Floor → Room → Timeline progression
14. **Analytics Summary** - Compare all 4 datasets side-by-side
15. **Tour Completion** - Next steps for real data usage

### Dataset Integration Strategy:
- **Progressive Complexity**: Start with perfect data, add complications
- **Feature Highlighting**: Each dataset emphasizes specific analytics capabilities
- **Comparative Analysis**: Show how same interface reveals different insights
- **Real-World Context**: End with realistic mixed performance scenario

### Interactive Elements:
- Dataset selection buttons embedded throughout tour
- Pulsing highlights on clickable elements
- Arrow pointers directing user attention
- "Try clicking..." prompts with action validation
- Automatic progress when user completes required action
- Side-by-side comparisons between datasets

## Phase 5: Mock Data Generation Specifications

### Data File Structure:
```
timestamp,sensor_name,value,type
2024-09-01 07:00:00,F1-01 presence,1,sensor
2024-09-01 07:00:00,VAV-101 mode,occupied,zone
2024-09-01 07:00:30,F1-01 presence,1,sensor
2024-09-01 07:01:00,VAV-101 mode,occupied,zone
```

### Violation Pattern Generation:
- **Early Standby**: Zone transitions to standby 5-14 minutes after sensor shows unoccupied
- **Delayed Response**: Zone stays standby 6-15 minutes after sensor shows occupied
- **Missing Data**: Gaps in timestamp sequences for specified sensors/periods
- **Realistic Timing**: Business hours occupancy with natural variation

### Analytics Validation Requirements:
- Calculated occupancy percentages match expected patterns
- Violation counts align with designed scenarios
- Missing data percentages reflect specified outages
- Timeline visualization clearly shows intended patterns

## Expected Outcome:
Users experience hands-on learning of ODCV Analytics by loading 4 different datasets that progressively demonstrate: perfect performance baseline → timing violation detection → data quality analysis → realistic mixed performance. Each dataset tells a clear story while showcasing specific analytics features through interactive exploration.
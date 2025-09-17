# Comparative Occupancy Control System Analysis

## Executive Summary

Analysis of two separate datasets reveals **significant performance degradation** over time. The control system showed poor but measurable performance in September 10-12, 2025 but **completely failed** by September 15-16, 2025.

## Dataset Comparison

### Dataset 1: Recent Data (SCH-1_data_20250916.csv)
- **Period**: September 15-16, 2025 (23.5 hours)
- **Data Quality**: Good coverage, minimal gaps
- **Control Performance**: **Complete failure** (0-0.5% correct transitions)

### Dataset 2: Historical Data (sensor_dump_filtered.csv)
- **Period**: September 10-12, 2025 (2.5 days, filtered to match zone data)
- **Data Quality**: Significant zone data gaps (178 gaps >5 minutes)
- **Control Performance**: **Poor but functional** (9.1-20.3% correct transitions)

## Detailed Performance Comparison

| Zone | Metric | Recent Data (Sept 15-16) | Historical Data (Sept 10-12) | Change |
|------|--------|---------------------------|-------------------------------|---------|
| **BV200** | Performance Score | **0.0%** | **20.3%** | **-20.3%** ⬇️ |
| | Correct Transitions | 0 | 14 | -14 |
| | Premature Transitions | 73 | 35 | +38 |
| | Total State Changes | 106 | 69 | +37 |
| **BV201** | Performance Score | **0.5%** | **12.2%** | **-11.7%** ⬇️ |
| | Correct Transitions | 1 | 15 | -14 |
| | Premature Transitions | 131 | 72 | +59 |
| | Total State Changes | 187 | 123 | +64 |
| **BV202** | Performance Score | **0.0%** | **9.1%** | **-9.1%** ⬇️ |
| | Correct Transitions | 0 | 11 | -11 |
| | Premature Transitions | 175 | 76 | +99 |
| | Total State Changes | 201 | 121 | +80 |

## Key Findings

### 🚨 Critical Performance Degradation
1. **Complete System Failure**: Recent data shows virtually 0% correct performance across all zones
2. **Increased Instability**: 50-66% more state changes in recent data
3. **More Premature Transitions**: 60-130% increase in premature transitions

### 📊 Data Quality Issues
**Recent Data (Sept 15-16):**
- ✅ Excellent sensor coverage (2,937-3,120 readings per sensor)
- ✅ Good zone coverage (1,358-1,359 readings per zone)
- ✅ Minimal data gaps (one 5-minute gap)

**Historical Data (Sept 10-12):**
- ✅ Good sensor coverage (6,635-7,026 readings per sensor)
- ⚠️ Poor zone coverage (510 readings per zone)
- ❌ Significant zone data gaps (178 gaps >5 minutes)

### 🔍 Timing Analysis
**Recent Data Typical Violations:**
- Zones switching to standby after **30 seconds to 2 minutes** unoccupied (should be 15 minutes)
- Zones activating after **1-3 minutes** occupied (should be 5 minutes)

**Historical Data Typical Violations:**
- Zones switching to standby after **2-5 minutes** unoccupied (closer to spec but still early)
- Zones activating after **1-3 minutes** occupied (consistent problem)

## Analysis Conclusions

### System Health Trend
The control system has **deteriorated significantly** between September 10-12 and September 15-16:

1. **Performance Collapsed**: From poor (9-20%) to complete failure (0%)
2. **Instability Increased**: Much more frequent, erratic state changes
3. **Timing Worse**: Even faster premature transitions in recent data

### Data Quality vs Performance
- **Historical period**: Poor zone data quality BUT some correct control logic
- **Recent period**: Good data quality BUT complete control logic failure

This suggests the **control logic itself degraded**, not just data collection issues.

### Root Cause Indicators

**Most Likely Causes:**
1. **BMS Configuration Change**: Control timing parameters modified incorrectly
2. **Software Update**: Control algorithm updated with bugs
3. **Hardware Malfunction**: Zone controller hardware failing

**Less Likely:**
- Sensor calibration issues (sensors show consistent patterns)
- Data collection problems (recent data quality is good)

## Recommendations

### Immediate Actions (Within 24 Hours)
1. **Check BMS Configuration**: Verify 15-min/5-min timer settings
2. **Review Recent Changes**: Identify any system changes between Sept 12-15
3. **Reset Zone Controllers**: Attempt to restore previous working configuration

### Investigation Priority
1. **BV201**: Worst performance degradation (-11.7% score, +64 state changes)
2. **BV202**: Most instability (+80 state changes, 201 total)
3. **BV200**: Best relative performance but still failed completely

### Monitoring Strategy
1. **Hourly Checks**: Monitor for any performance recovery
2. **Change Logging**: Document all system modifications
3. **Baseline Restoration**: Target return to Sept 10-12 performance levels as interim goal

## Technical Notes

**Filtered Dataset Details:**
- Original sensor dump: 93,817 records (Sept 2-12)
- Filtered to zone data period: 22,189 records (Sept 10-12)
- Zone data availability: Sept 10 11:10 to Sept 12 16:40

The filtering approach ensured fair comparison by only analyzing periods where both sensor and zone data were available, eliminating bias from missing zone data in the earlier historical period.
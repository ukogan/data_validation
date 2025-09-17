# Occupancy Control System Analysis Report

## Executive Summary

Analysis of occupancy sensor data and zone control logic reveals **significant control system performance issues**. The Building Management System (BMS) is not following the specified control logic timing requirements, resulting in:

- **Very poor performance scores** (0-20% across all zones)
- **Premature state transitions** dominating system behavior
- **Incorrect timing** for both occupied-to-standby and standby-to-occupied transitions

## Data Overview

### Dataset 1: SCH-1_data_20250916.csv
- **Time Range**: Sept 15-16, 2025 (23.5 hours)
- **Total Records**: 13,188
- **Sensor Data**: 9,113 readings (3 sensors)
- **Zone Data**: 4,075 readings (3 zones)

### Dataset 2: sensor_dump_202509121643.csv
- **Time Range**: Sept 2-12, 2025 (10 days)
- **Total Records**: 93,817
- **Sensor Data**: 92,284 readings (3 sensors)
- **Zone Data**: 1,533 readings (3 zones)

## Data Completeness Assessment

### ✅ Complete Data Elements
- All 3 occupancy sensors present: 115-4-01, 115-4-06, 115-4-09
- All 3 zone controls present: BV200, BV201, BV202
- Correct sensor-zone mapping confirmed
- Data values in expected range (0/1 for both sensors and zones)

### ⚠️ Data Quality Issues

#### Minor Issues (Dataset 1)
- Small 5-minute gap in zone data on Sept 15 (15:55-16:00)
- Slightly uneven sensor reading counts (2,937-3,120)

#### Major Issues (Dataset 2)
- **Zone data severely limited**: Only 511 readings per zone over 10 days
- **Large data gaps**: 178 gaps >5 minutes in zone data
- **Mismatched coverage**: Sensors have 10 days of data, zones only 2.5 days

## Control Logic Performance Analysis

### Expected Control Logic
- **Unoccupied → Standby**: 15 minutes unoccupied → zone mode = 1 (standby)
- **Occupied → Active**: 5 minutes occupied → zone mode = 0 (occupied)

### Actual Performance Results

| Zone | Dataset | Performance Score | Correct | Delayed | Premature | Total Changes |
|------|---------|------------------|---------|---------|-----------|---------------|
| BV200 | Recent (1 day) | **0.0%** | 0 | 0 | 73 | 106 |
| BV201 | Recent (1 day) | **0.5%** | 1 | 0 | 131 | 187 |
| BV202 | Recent (1 day) | **0.0%** | 0 | 0 | 175 | 201 |
| BV200 | Historical (10 days) | **20.3%** | 14 | 1 | 35 | 69 |
| BV201 | Historical (10 days) | **12.2%** | 15 | 4 | 73 | 123 |
| BV202 | Historical (10 days) | **9.1%** | 11 | 1 | 77 | 121 |

### Key Findings

#### 🚨 Critical Issues
1. **Premature Transitions Dominate**: 60-87% of all state changes happen too early
2. **Incorrect Timing**: Zones switching after 30 seconds - 2 minutes instead of 5-15 minutes
3. **Performance Degradation**: Recent data shows 0% correct transitions vs 9-20% historically

#### Common Timing Violations
- Zones going to standby after only **30 seconds to 2 minutes** unoccupied (should be 15 minutes)
- Zones activating after only **1-3 minutes** occupied (should be 5 minutes)

## Proposed Assessment Method

### 1. Automated Performance Monitoring

**Key Performance Indicators (KPIs):**
- Control Logic Compliance Rate (target: >95%)
- Average Response Time to Occupancy Changes
- Premature Transition Rate (target: <5%)
- Data Availability Rate (target: >98%)

**Monitoring Tools:**
- `occupancy_analysis.py` - Basic data completeness and violations
- `detailed_control_analysis.py` - Performance scoring and detailed timing analysis

### 2. Regular Assessment Schedule

**Daily Monitoring:**
- Check for data gaps >5 minutes
- Verify all sensors/zones reporting
- Alert on performance score <80%

**Weekly Analysis:**
- Calculate weekly performance trends
- Identify recurring problem periods
- Generate performance reports

**Monthly Review:**
- Deep dive into control logic violations
- Assess need for BMS configuration changes
- Validate sensor calibration

### 3. Alerting Thresholds

**Immediate Action Required:**
- Performance score <50%
- Data gaps >1 hour
- Sensor/zone not reporting >30 minutes

**Investigation Needed:**
- Performance score 50-80%
- >10% premature transitions
- Timing violations >2x expected

## Recommendations

### Immediate Actions (High Priority)
1. **Investigate BMS Configuration**: The 15-minute and 5-minute timers appear to be set incorrectly
2. **Check Zone Data Collection**: Zone controllers may have connectivity or logging issues
3. **Validate Sensor Calibration**: Ensure sensors are accurately detecting occupancy

### System Improvements (Medium Priority)
1. **Implement Performance Dashboard**: Real-time monitoring of control logic compliance
2. **Add Data Quality Checks**: Automated alerts for missing data or unusual patterns
3. **Create Baseline Performance**: Establish acceptable performance ranges after fixes

### Long-term Monitoring (Ongoing)
1. **Monthly Performance Reviews**: Track improvement trends
2. **Seasonal Adjustments**: Account for usage pattern changes
3. **Preventive Maintenance**: Regular sensor and controller health checks

## Conclusion

The occupancy control system is **not functioning according to specifications**. The BMS is making state transitions too quickly, suggesting either:

1. **Configuration Error**: Timing parameters set incorrectly in BMS
2. **Logic Error**: Control algorithm not implementing the 15-min/5-min rules
3. **Sensor Issues**: False occupancy readings causing erratic behavior

**Priority**: This requires immediate investigation as the system is essentially non-functional according to the specified control logic.
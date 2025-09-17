# Timeline Viewer Guide

## Overview

I've created an interactive timeline visualizer that lets you visually inspect sensor occupancy and zone mode transitions. This will help you see exactly when and how the control logic is failing.

## Generated Files

1. **`timeline_recent.html`** - Full 24-hour view of recent data (Sept 15-16, 2025)
2. **`timeline_historical.html`** - 12-hour view of historical data (Sept 11, 2025, 8AM-8PM)
3. **`timeline_focused.html`** - Focused 4-hour view of recent data (Sept 16, 1PM-5PM) - **Best for detailed inspection**

## How to Use

### Opening the Timeline
1. Open any of the HTML files in your web browser
2. Each file shows timelines for all 3 sensor-zone pairs

### Reading the Timeline

**Visual Elements:**
- **Red bars**: Sensor shows occupied
- **Blue bars**: Sensor shows unoccupied
- **Green bars**: Zone in occupied mode
- **Orange bars**: Zone in standby mode
- **Purple bars**: Control violations (timing errors)

**Layout:**
- Top track: Sensor occupancy state
- Bottom track: Zone mode state
- Violations are shown as thick purple bars

### Interactive Features
- **Hover over any bar** to see detailed information:
  - Exact timestamp
  - Device name
  - State description
  - For violations: what went wrong and expected timing

### Key Things to Look For

1. **Rapid State Changes**: Look for many closely-spaced events (indicates unstable control)

2. **Purple Violation Bars**: These show where the control logic failed:
   - **Premature Standby**: Zone went to standby too quickly after becoming unoccupied
   - **Premature Occupied**: Zone activated too quickly after becoming occupied

3. **Timing Patterns**: Compare sensor changes to zone responses:
   - **Correct**: Zone should change 5-15 minutes after sensor
   - **Actual**: Zone often changes within 30 seconds to 2 minutes

## Command Line Usage

To create custom timeline views:

```bash
# Full dataset timeline
python3 timeline_visualizer.py SCH-1_data_20250916.csv

# Specific time period (start time and duration in hours)
python3 timeline_visualizer.py SCH-1_data_20250916.csv '2025-09-16 10:00' 6

# Historical data
python3 timeline_visualizer.py sensor_dump_filtered.csv '2025-09-11 12:00' 8
```

## What You'll See

### Recent Data (timeline_focused.html) - **RECOMMENDED START**
- **Extremely rapid transitions**: Zones changing every few minutes
- **Many purple violation bars**: Almost every transition is premature
- **Erratic patterns**: No stable periods

### Historical Data (timeline_historical.html)
- **Fewer but still frequent violations**: Some correct timing mixed with errors
- **Less erratic**: Longer stable periods between changes
- **Better but still poor performance**: 9-20% correct vs 0% recent

## Key Insights from Visual Inspection

1. **System Completely Broken**: Recent data shows constant premature transitions
2. **Performance Degraded**: Historical data was poor but functional, recent is non-functional
3. **All Zones Affected**: No single zone is working correctly
4. **Consistent Pattern**: All zones show same type of failures (too-fast transitions)

## Recommended Investigation Steps

1. **Start with `timeline_focused.html`** for clearest view of current problems
2. **Compare to `timeline_historical.html`** to see the degradation
3. **Look for specific violation patterns** to guide BMS configuration fixes
4. **Use hover tooltips** to get exact timing information for troubleshooting

The timeline viewer makes it immediately clear that the control system timing is completely wrong and needs urgent attention.
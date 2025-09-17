#!/usr/bin/env python3
"""
Occupancy Control System Analysis
Analyzes occupancy sensor data and zone control logic
"""

import csv
from datetime import datetime, timedelta
from collections import defaultdict
import sys

# Sensor to Zone mapping
SENSOR_ZONE_MAP = {
    '115-4-01 presence': 'BV200',
    '115-4-06 presence': 'BV201',
    '115-4-09 presence': 'BV202'
}

# Control logic constants
UNOCCUPIED_TO_STANDBY_MINUTES = 15  # Zone goes to standby after 15 min unoccupied
OCCUPIED_TO_ACTIVE_MINUTES = 5      # Zone goes to active after 5 min occupied

def parse_timestamp(ts_str):
    """Parse timestamp string to datetime object"""
    try:
        # Handle both formats in the data
        if 'T' in ts_str:
            return datetime.fromisoformat(ts_str.replace(' -07:00', '-07:00'))
        else:
            # Remove microseconds and timezone for simpler parsing
            ts_clean = ts_str.split('.')[0].split(' -')[0]
            return datetime.strptime(ts_clean, '%Y-%m-%d %H:%M:%S')
    except:
        return None

def load_data(filename):
    """Load data from CSV file"""
    data = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp = parse_timestamp(row['time'])
            if timestamp:
                data.append({
                    'name': row['name'].strip('"'),
                    'time': timestamp,
                    'value': float(row['value'])
                })
    return sorted(data, key=lambda x: x['time'])

def analyze_data_completeness(data):
    """Analyze data completeness and gaps"""
    print("=== DATA COMPLETENESS ANALYSIS ===\n")

    # Group by sensor/zone
    by_device = defaultdict(list)
    for record in data:
        by_device[record['name']].append(record)

    print("Device data counts:")
    for device, records in by_device.items():
        print(f"  {device}: {len(records)} readings")
        if records:
            start = records[0]['time']
            end = records[-1]['time']
            duration = end - start
            print(f"    Time range: {start} to {end}")
            print(f"    Duration: {duration}")

            # Check for gaps > 5 minutes
            gaps = []
            for i in range(1, len(records)):
                gap = records[i]['time'] - records[i-1]['time']
                if gap > timedelta(minutes=5):
                    gaps.append((records[i-1]['time'], records[i]['time'], gap))

            if gaps:
                print(f"    Found {len(gaps)} gaps > 5 minutes:")
                for start_gap, end_gap, duration in gaps[:5]:  # Show first 5
                    print(f"      {start_gap} to {end_gap} ({duration})")
                if len(gaps) > 5:
                    print(f"      ... and {len(gaps)-5} more gaps")
            print()

def analyze_control_logic(data):
    """Analyze whether control logic is working properly"""
    print("=== CONTROL LOGIC ANALYSIS ===\n")

    # Group data by device
    by_device = defaultdict(list)
    for record in data:
        by_device[record['name']].append(record)

    # Analyze each sensor-zone pair
    for sensor, zone in SENSOR_ZONE_MAP.items():
        print(f"Analyzing {sensor} -> {zone}")

        if sensor not in by_device or zone not in by_device:
            print(f"  ERROR: Missing data for {sensor} or {zone}\n")
            continue

        sensor_data = by_device[sensor]
        zone_data = by_device[zone]

        # Merge and sort by time
        combined = []
        for record in sensor_data:
            combined.append({
                'time': record['time'],
                'type': 'sensor',
                'value': record['value'],
                'name': sensor
            })
        for record in zone_data:
            combined.append({
                'time': record['time'],
                'type': 'zone',
                'value': record['value'],
                'name': zone
            })

        combined.sort(key=lambda x: x['time'])

        # Analyze control behavior
        violations = []
        current_sensor_state = None
        current_zone_state = None
        last_occupancy_change = None

        for record in combined:
            if record['type'] == 'sensor':
                if current_sensor_state != record['value']:
                    current_sensor_state = record['value']
                    last_occupancy_change = record['time']

            elif record['type'] == 'zone':
                current_zone_state = record['value']

                # Check control logic violations
                if last_occupancy_change and current_sensor_state is not None:
                    time_since_change = record['time'] - last_occupancy_change

                    # Rule 1: If unoccupied for 15+ minutes, zone should be in standby (1)
                    if (current_sensor_state == 0 and
                        time_since_change >= timedelta(minutes=UNOCCUPIED_TO_STANDBY_MINUTES) and
                        current_zone_state == 0):
                        violations.append({
                            'time': record['time'],
                            'type': 'standby_delay',
                            'message': f"Zone should be in standby but is occupied mode after {time_since_change} unoccupied"
                        })

                    # Rule 2: If occupied for 5+ minutes, zone should be occupied (0)
                    if (current_sensor_state == 1 and
                        time_since_change >= timedelta(minutes=OCCUPIED_TO_ACTIVE_MINUTES) and
                        current_zone_state == 1):
                        violations.append({
                            'time': record['time'],
                            'type': 'occupied_delay',
                            'message': f"Zone should be in occupied mode but is standby after {time_since_change} occupied"
                        })

        # Report findings
        print(f"  Total sensor readings: {len(sensor_data)}")
        print(f"  Total zone readings: {len(zone_data)}")
        print(f"  Control violations found: {len(violations)}")

        if violations:
            print("  Recent violations:")
            for violation in violations[-5:]:  # Show last 5
                print(f"    {violation['time']}: {violation['message']}")
        print()

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 occupancy_analysis.py <csv_file>")
        sys.exit(1)

    filename = sys.argv[1]
    print(f"Analyzing file: {filename}\n")

    try:
        data = load_data(filename)
        print(f"Loaded {len(data)} records\n")

        analyze_data_completeness(data)
        analyze_control_logic(data)

    except Exception as e:
        print(f"Error analyzing data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
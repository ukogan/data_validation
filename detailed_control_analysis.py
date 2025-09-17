#!/usr/bin/env python3
"""
Detailed Control System Performance Analysis
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

UNOCCUPIED_TO_STANDBY_MINUTES = 15
OCCUPIED_TO_ACTIVE_MINUTES = 5

def parse_timestamp(ts_str):
    """Parse timestamp string to datetime object"""
    try:
        if 'T' in ts_str:
            return datetime.fromisoformat(ts_str.replace(' -07:00', '-07:00'))
        else:
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

def analyze_control_performance(data):
    """Detailed analysis of control system performance"""
    print("=== DETAILED CONTROL PERFORMANCE ANALYSIS ===\n")

    by_device = defaultdict(list)
    for record in data:
        by_device[record['name']].append(record)

    for sensor, zone in SENSOR_ZONE_MAP.items():
        print(f"Analyzing {sensor} -> {zone}")

        if sensor not in by_device or zone not in by_device:
            print(f"  ERROR: Missing data for {sensor} or {zone}\n")
            continue

        sensor_data = by_device[sensor]
        zone_data = by_device[zone]

        # Create timeline of events
        events = []
        for record in sensor_data:
            events.append({
                'time': record['time'],
                'type': 'sensor',
                'value': int(record['value']),
                'source': sensor
            })
        for record in zone_data:
            events.append({
                'time': record['time'],
                'type': 'zone',
                'value': int(record['value']),
                'source': zone
            })

        events.sort(key=lambda x: x['time'])

        # Analyze control performance
        total_state_changes = 0
        correct_transitions = 0
        delayed_transitions = 0
        premature_transitions = 0

        current_sensor_occupied = None
        current_zone_mode = None
        last_sensor_change_time = None

        performance_issues = []

        for event in events:
            if event['type'] == 'sensor':
                new_state = event['value']
                if current_sensor_occupied != new_state:
                    current_sensor_occupied = new_state
                    last_sensor_change_time = event['time']

            elif event['type'] == 'zone':
                new_mode = event['value']
                if current_zone_mode != new_mode:
                    total_state_changes += 1

                    if last_sensor_change_time and current_sensor_occupied is not None:
                        time_since_sensor_change = event['time'] - last_sensor_change_time

                        # Analyze transition timing
                        if current_sensor_occupied == 0:  # Sensor shows unoccupied
                            if new_mode == 1:  # Zone went to standby
                                if time_since_sensor_change < timedelta(minutes=UNOCCUPIED_TO_STANDBY_MINUTES - 2):
                                    premature_transitions += 1
                                    performance_issues.append({
                                        'time': event['time'],
                                        'issue': 'premature_standby',
                                        'details': f"Zone went to standby after only {time_since_sensor_change} unoccupied"
                                    })
                                elif time_since_sensor_change <= timedelta(minutes=UNOCCUPIED_TO_STANDBY_MINUTES + 5):
                                    correct_transitions += 1
                                else:
                                    delayed_transitions += 1
                                    performance_issues.append({
                                        'time': event['time'],
                                        'issue': 'delayed_standby',
                                        'details': f"Zone went to standby after {time_since_sensor_change} unoccupied (expected ~15min)"
                                    })

                        elif current_sensor_occupied == 1:  # Sensor shows occupied
                            if new_mode == 0:  # Zone went to occupied
                                if time_since_sensor_change < timedelta(minutes=OCCUPIED_TO_ACTIVE_MINUTES - 1):
                                    premature_transitions += 1
                                    performance_issues.append({
                                        'time': event['time'],
                                        'issue': 'premature_occupied',
                                        'details': f"Zone went to occupied after only {time_since_sensor_change} occupied"
                                    })
                                elif time_since_sensor_change <= timedelta(minutes=OCCUPIED_TO_ACTIVE_MINUTES + 2):
                                    correct_transitions += 1
                                else:
                                    delayed_transitions += 1
                                    performance_issues.append({
                                        'time': event['time'],
                                        'issue': 'delayed_occupied',
                                        'details': f"Zone went to occupied after {time_since_sensor_change} occupied (expected ~5min)"
                                    })

                    current_zone_mode = new_mode

        # Calculate performance metrics
        if total_state_changes > 0:
            performance_score = (correct_transitions / total_state_changes) * 100
        else:
            performance_score = 0

        print(f"  Performance Summary:")
        print(f"    Total zone state changes: {total_state_changes}")
        print(f"    Correct transitions: {correct_transitions}")
        print(f"    Delayed transitions: {delayed_transitions}")
        print(f"    Premature transitions: {premature_transitions}")
        print(f"    Performance score: {performance_score:.1f}%")
        print()

        if performance_issues:
            print(f"  Performance Issues (showing last 5):")
            for issue in performance_issues[-5:]:
                print(f"    {issue['time']}: {issue['issue']} - {issue['details']}")
            print()

        # Check for current state alignment
        if sensor_data and zone_data:
            latest_sensor = sensor_data[-1]
            latest_zone = zone_data[-1]

            print(f"  Current State Check:")
            print(f"    Latest sensor reading: {int(latest_sensor['value'])} ({'occupied' if latest_sensor['value'] else 'unoccupied'}) at {latest_sensor['time']}")
            print(f"    Latest zone mode: {int(latest_zone['value'])} ({'standby' if latest_zone['value'] else 'occupied'}) at {latest_zone['time']}")

            # Check if current states make sense
            time_diff = abs((latest_sensor['time'] - latest_zone['time']).total_seconds()) / 60
            if time_diff > 30:  # More than 30 minutes apart
                print(f"    WARNING: Sensor and zone readings are {time_diff:.1f} minutes apart")

        print("-" * 60)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 detailed_control_analysis.py <csv_file>")
        sys.exit(1)

    filename = sys.argv[1]
    print(f"Detailed analysis of: {filename}\n")

    try:
        data = load_data(filename)
        analyze_control_performance(data)

    except Exception as e:
        print(f"Error analyzing data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
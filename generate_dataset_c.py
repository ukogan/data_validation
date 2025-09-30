#!/usr/bin/env python3
"""
Generate Dataset C: Missing Data & Outages
- 12 sensors (4 per floor × 3 floors)
- 15 consecutive days
- Specific sensor outages for hours/days
- Partial data loss (20-40% missing data points)
- BMS communication issues
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_missing_data_dataset():
    # Configuration
    start_date = datetime(2024, 9, 1, 0, 0, 0)
    end_date = start_date + timedelta(days=15)

    # Sensor configuration
    sensors = []
    zones = []
    for floor in range(1, 4):  # Floors 1, 2, 3
        for sensor_num in range(1, 5):  # 4 sensors per floor
            sensor_id = f"F{floor}-{sensor_num:02d}"
            zone_id = f"VAV-{floor}{sensor_num:02d}"
            sensors.append(f"{sensor_id} presence")
            zones.append(f"{zone_id} mode")

    print(f"Generating missing data for {len(sensors)} sensors and {len(zones)} zones")
    print(f"Date range: {start_date} to {end_date}")

    # Generate timeline - sensor data every 30 seconds, BMS every 60 seconds
    sensor_timestamps = []
    current_time = start_date
    while current_time < end_date:
        sensor_timestamps.append(current_time)
        current_time += timedelta(seconds=30)

    bms_timestamps = []
    current_time = start_date
    while current_time < end_date:
        bms_timestamps.append(current_time)
        current_time += timedelta(seconds=60)

    print(f"Generated {len(sensor_timestamps)} sensor timestamps and {len(bms_timestamps)} BMS timestamps")

    # Define outage scenarios as specified in plan
    outage_scenarios = {
        'F1-01 presence': {
            'type': 'complete_outage',
            'start': start_date + timedelta(days=14),  # Most recent day (day 15)
            'duration_hours': 8,
            'description': 'sensor hardware failure'
        },
        'F2-02 presence': {
            'type': 'intermittent',
            'missing_percentage': 20,  # 20% of data points missing throughout
            'description': 'network issues'
        },
        'VAV-303 mode': {
            'type': 'complete_outage',
            'start': start_date + timedelta(days=12),  # Days 13-14
            'duration_hours': 48,
            'description': 'controller maintenance'
        }
    }

    # Storage for all data
    all_data = []

    # Generate data for each sensor/zone pair
    for i, (sensor_name, zone_name) in enumerate(zip(sensors, zones)):
        print(f"Generating data for {sensor_name} -> {zone_name}")

        # Generate occupancy patterns for this sensor
        sensor_data = generate_occupancy_with_outages(sensor_timestamps, sensor_name, outage_scenarios)
        all_data.extend(sensor_data)

        # Generate corresponding BMS zone data
        zone_data = generate_bms_with_outages(bms_timestamps, zone_name, sensor_data, sensor_timestamps, outage_scenarios)
        all_data.extend(zone_data)

    # Create DataFrame
    df = pd.DataFrame(all_data)
    df = df.sort_values('timestamp').reset_index(drop=True)

    print(f"Generated {len(df)} total data points")

    # Print outage summary
    print("\nOutage Summary:")
    for sensor_name, scenario in outage_scenarios.items():
        if scenario['type'] == 'complete_outage':
            print(f"  {sensor_name}: {scenario['duration_hours']}h outage starting {scenario['start']}")
        elif scenario['type'] == 'intermittent':
            print(f"  {sensor_name}: {scenario['missing_percentage']}% data loss throughout period")

    # Save to CSV
    filename = "dataset_c_missing_data.csv"
    df.to_csv(filename, index=False)
    print(f"Saved to {filename}")

    return df

def generate_occupancy_with_outages(timestamps, sensor_name, outage_scenarios):
    """Generate occupancy patterns with planned outages"""
    data = []

    # Check if this sensor has an outage scenario
    outage_scenario = outage_scenarios.get(sensor_name)

    # Different patterns for different floor/sensor types
    floor_num = int(sensor_name.split('-')[0][1])  # Extract floor number
    sensor_num = int(sensor_name.split('-')[1].split()[0])  # Extract sensor number

    # Pattern characteristics based on location
    if floor_num == 1:  # Conference rooms - meeting patterns
        base_occupancy_prob = 0.3
        meeting_duration_avg = 90  # minutes
    elif floor_num == 2:  # Open office - consistent occupancy
        base_occupancy_prob = 0.7
        meeting_duration_avg = 240  # minutes (longer work periods)
    else:  # Floor 3 - Executive offices - sporadic use
        base_occupancy_prob = 0.4
        meeting_duration_avg = 120  # minutes

    current_occupied = False
    occupancy_start_time = None

    for timestamp in timestamps:
        # Check if this timestamp should be missing due to outage
        should_skip = False

        if outage_scenario:
            if outage_scenario['type'] == 'complete_outage':
                # Complete outage for specified duration
                outage_start = outage_scenario['start']
                outage_end = outage_start + timedelta(hours=outage_scenario['duration_hours'])
                if outage_start <= timestamp < outage_end:
                    should_skip = True
            elif outage_scenario['type'] == 'intermittent':
                # Random missing data points
                if random.random() < (outage_scenario['missing_percentage'] / 100):
                    should_skip = True

        if should_skip:
            continue  # Skip this data point (simulate missing data)

        hour = timestamp.hour
        weekday = timestamp.weekday()  # 0=Monday, 6=Sunday

        # Business hours: 8AM-6PM, Monday-Friday
        is_business_hours = (weekday < 5) and (8 <= hour < 18)

        if is_business_hours:
            # During business hours - use occupancy patterns
            if not current_occupied:
                # Chance to become occupied
                if random.random() < (base_occupancy_prob / 120):  # Per 30-second interval
                    current_occupied = True
                    occupancy_start_time = timestamp
            else:
                # Currently occupied - check if should become unoccupied
                if occupancy_start_time:
                    duration_minutes = (timestamp - occupancy_start_time).total_seconds() / 60
                    # Probability of ending based on duration
                    end_prob = duration_minutes / meeting_duration_avg / 120  # Per 30-second interval
                    if random.random() < end_prob:
                        current_occupied = False
                        occupancy_start_time = None
        else:
            # Outside business hours - very low occupancy (2% chance)
            if current_occupied:
                if random.random() < 0.05:  # 5% chance to become unoccupied per interval
                    current_occupied = False
                    occupancy_start_time = None
            else:
                if random.random() < 0.0003:  # 0.03% chance to become occupied per interval
                    current_occupied = True
                    occupancy_start_time = timestamp

        # Add data point
        data.append({
            'timestamp': timestamp,
            'sensor_name': sensor_name,
            'value': 1 if current_occupied else 0,
            'type': 'sensor'
        })

    return data

def generate_bms_with_outages(bms_timestamps, zone_name, sensor_data, sensor_timestamps, outage_scenarios):
    """Generate BMS zone responses with potential communication outages"""
    data = []

    # Check if this zone has an outage scenario
    outage_scenario = outage_scenarios.get(zone_name)

    # Create sensor state lookup for quick access
    sensor_states = {}
    for entry in sensor_data:
        # Round to nearest minute for BMS correlation
        minute_timestamp = entry['timestamp'].replace(second=0, microsecond=0)
        sensor_states[minute_timestamp] = entry['value']

    current_zone_mode = 'standby'
    last_sensor_change = None
    last_sensor_state = 0

    for timestamp in bms_timestamps:
        # Check if this timestamp should be missing due to outage
        should_skip = False

        if outage_scenario:
            if outage_scenario['type'] == 'complete_outage':
                # Complete outage for specified duration
                outage_start = outage_scenario['start']
                outage_end = outage_start + timedelta(hours=outage_scenario['duration_hours'])
                if outage_start <= timestamp < outage_end:
                    should_skip = True
            elif outage_scenario['type'] == 'intermittent':
                # Random missing data points
                if random.random() < (outage_scenario['missing_percentage'] / 100):
                    should_skip = True

        if should_skip:
            continue  # Skip this data point (simulate missing data)

        minute_timestamp = timestamp.replace(second=0, microsecond=0)

        # Get current sensor state (use most recent if exact timestamp not found)
        current_sensor_state = last_sensor_state
        for check_time in [minute_timestamp - timedelta(seconds=s) for s in range(0, 60, 30)]:
            if check_time in sensor_states:
                current_sensor_state = sensor_states[check_time]
                break

        # Check for sensor state change
        if current_sensor_state != last_sensor_state:
            last_sensor_change = timestamp
            last_sensor_state = current_sensor_state

        # Normal BMS response logic (similar to Dataset A)
        if last_sensor_change:
            time_since_change = (timestamp - last_sensor_change).total_seconds() / 60  # minutes

            if current_sensor_state == 1:  # Sensor shows occupied
                # Rule: Zone should respond within 5 minutes (normal = 2-3 minutes)
                if time_since_change >= random.uniform(2, 3.5) and current_zone_mode == 'standby':
                    current_zone_mode = 'occupied'
            else:  # Sensor shows unoccupied
                # Rule: Zone should wait 15 minutes before going to standby
                if time_since_change >= random.uniform(15, 16.5) and current_zone_mode == 'occupied':
                    current_zone_mode = 'standby'

        # Add data point
        data.append({
            'timestamp': timestamp,
            'sensor_name': zone_name,
            'value': current_zone_mode,
            'type': 'zone'
        })

    return data

if __name__ == "__main__":
    df = generate_missing_data_dataset()
    print(f"Dataset C generation complete. Shape: {df.shape}")
    print("\nSample data:")
    print(df.head(10))
    print(f"\nSensor data points: {len(df[df['type'] == 'sensor'])}")
    print(f"Zone data points: {len(df[df['type'] == 'zone'])}")

    # Calculate missing data statistics
    expected_sensor_points = 43200 * 12  # 43200 timestamps × 12 sensors
    expected_zone_points = 21600 * 12    # 21600 timestamps × 12 zones
    actual_sensor_points = len(df[df['type'] == 'sensor'])
    actual_zone_points = len(df[df['type'] == 'zone'])

    print(f"\nMissing Data Analysis:")
    print(f"Expected sensor points: {expected_sensor_points}, Actual: {actual_sensor_points} ({(1-actual_sensor_points/expected_sensor_points)*100:.1f}% missing)")
    print(f"Expected zone points: {expected_zone_points}, Actual: {actual_zone_points} ({(1-actual_zone_points/expected_zone_points)*100:.1f}% missing)")
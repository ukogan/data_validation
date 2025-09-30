#!/usr/bin/env python3
"""
Generate Dataset B: Timing Out of Spec Analysis
- 12 sensors (4 per floor × 3 floors)
- 15 consecutive days
- 25% early standby violations (<15 min after unoccupied)
- 15% delayed response violations (>5 min to respond to occupancy)
- Clustered violations showing systematic issues
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_timing_violations_dataset():
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

    print(f"Generating violation data for {len(sensors)} sensors and {len(zones)} zones")
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

    # Storage for all data
    all_data = []

    # Generate data for each sensor/zone pair with specific violation patterns
    for i, (sensor_name, zone_name) in enumerate(zip(sensors, zones)):
        print(f"Generating violation data for {sensor_name} -> {zone_name}")

        # Generate occupancy patterns for this sensor
        sensor_data = generate_occupancy_pattern(sensor_timestamps, sensor_name, i)
        all_data.extend(sensor_data)

        # Generate BMS zone data with specific violation patterns
        zone_data = generate_violation_bms_response(bms_timestamps, zone_name, sensor_data, sensor_timestamps, i)
        all_data.extend(zone_data)

    # Create DataFrame
    df = pd.DataFrame(all_data)
    df = df.sort_values('timestamp').reset_index(drop=True)

    print(f"Generated {len(df)} total data points")

    # Save to CSV
    filename = "dataset_b_timing_violations.csv"
    df.to_csv(filename, index=False)
    print(f"Saved to {filename}")

    return df

def generate_occupancy_pattern(timestamps, sensor_name, sensor_index):
    """Generate realistic occupancy patterns similar to Dataset A"""
    data = []

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

def generate_violation_bms_response(bms_timestamps, zone_name, sensor_data, sensor_timestamps, sensor_index):
    """Generate BMS zone responses with intentional timing violations"""
    data = []

    # Define violation patterns by sensor
    # zone_name format: "VAV-101 mode" -> extract 101 -> floor=1, sensor=01
    zone_number = zone_name.split('-')[1].split()[0]  # Extract "101" from "VAV-101 mode"
    floor_num = int(zone_number[0])  # First digit is floor
    sensor_num = int(zone_number[1:])  # Remaining digits are sensor number

    # Violation characteristics by location (as specified in plan)
    if floor_num == 1 and sensor_num == 2:  # F1-02 -> VAV-102
        # Consistently goes standby after only 8-10 minutes (programming error)
        early_standby_prob = 0.8  # 80% of transitions are early
        delayed_response_prob = 0.1
        early_standby_time = random.uniform(8, 10)  # minutes
    elif floor_num == 2 and sensor_num in [1, 3]:  # F2-01, F2-03 -> VAV-201, VAV-203
        # Slow to respond (5-12 minutes) due to sensor calibration issues
        early_standby_prob = 0.1
        delayed_response_prob = 0.7  # 70% of responses are delayed
        delayed_response_time = random.uniform(6, 12)  # minutes
    elif floor_num == 3 and sensor_num == 4:  # F3-04 -> VAV-304
        # Random early standby transitions (intermittent BMS communication)
        early_standby_prob = 0.4  # 40% early transitions
        delayed_response_prob = 0.2
        early_standby_time = random.uniform(5, 14)  # minutes
    else:
        # Other sensors have normal violation rates
        early_standby_prob = 0.15  # 15% early transitions
        delayed_response_prob = 0.10  # 10% delayed responses

    # Create sensor state lookup for quick access
    sensor_states = {}
    for entry in sensor_data:
        # Round to nearest minute for BMS correlation
        minute_timestamp = entry['timestamp'].replace(second=0, microsecond=0)
        sensor_states[minute_timestamp] = entry['value']

    current_zone_mode = 'standby'
    last_sensor_change = None
    last_sensor_state = 0
    violation_triggered = False

    for timestamp in bms_timestamps:
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
            violation_triggered = False  # Reset for new transition

        # Violation logic
        if last_sensor_change and not violation_triggered:
            time_since_change = (timestamp - last_sensor_change).total_seconds() / 60  # minutes

            if current_sensor_state == 1:  # Sensor shows occupied
                # Normal response: 2-3 minutes, Violation: >5 minutes
                if random.random() < delayed_response_prob:
                    # Delayed response violation
                    response_time = delayed_response_time if 'delayed_response_time' in locals() else random.uniform(6, 12)
                    if time_since_change >= response_time and current_zone_mode == 'standby':
                        current_zone_mode = 'occupied'
                        violation_triggered = True
                else:
                    # Normal response (2-3 minutes)
                    if time_since_change >= random.uniform(2, 3.5) and current_zone_mode == 'standby':
                        current_zone_mode = 'occupied'
                        violation_triggered = True

            else:  # Sensor shows unoccupied
                # Normal: 15+ minutes, Violation: <15 minutes
                if random.random() < early_standby_prob:
                    # Early standby violation
                    standby_time = early_standby_time if 'early_standby_time' in locals() else random.uniform(5, 14)
                    if time_since_change >= standby_time and current_zone_mode == 'occupied':
                        current_zone_mode = 'standby'
                        violation_triggered = True
                else:
                    # Normal timing (15-16 minutes)
                    if time_since_change >= random.uniform(15, 16.5) and current_zone_mode == 'occupied':
                        current_zone_mode = 'standby'
                        violation_triggered = True

        # Add data point
        data.append({
            'timestamp': timestamp,
            'sensor_name': zone_name,
            'value': current_zone_mode,
            'type': 'zone'
        })

    return data

if __name__ == "__main__":
    df = generate_timing_violations_dataset()
    print(f"Dataset B generation complete. Shape: {df.shape}")
    print("\nSample data:")
    print(df.head(10))
    print(f"\nSensor data points: {len(df[df['type'] == 'sensor'])}")
    print(f"Zone data points: {len(df[df['type'] == 'zone'])}")
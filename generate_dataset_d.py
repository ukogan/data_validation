#!/usr/bin/env python3
"""
Generate Dataset D: Mixed Performance Reality
- 12 sensors (4 per floor × 3 floors)
- 15 consecutive days
- Floor 1: 85% performance (good sensors, minor BMS tuning needed)
- Floor 2: 95% performance (recently maintained, exemplary operation)
- Floor 3: 80% performance (mixture of sensor and BMS issues)
- Realistic building performance with varied sensor/zone behavior
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_mixed_performance_dataset():
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

    print(f"Generating mixed performance data for {len(sensors)} sensors and {len(zones)} zones")
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

    # Generate data for each sensor/zone pair with floor-specific performance
    for i, (sensor_name, zone_name) in enumerate(zip(sensors, zones)):
        print(f"Generating data for {sensor_name} -> {zone_name}")

        # Generate occupancy patterns for this sensor
        sensor_data = generate_occupancy_pattern(sensor_timestamps, sensor_name, i)
        all_data.extend(sensor_data)

        # Generate BMS zone data with floor-specific performance levels
        zone_data = generate_mixed_bms_response(bms_timestamps, zone_name, sensor_data, sensor_timestamps, i)
        all_data.extend(zone_data)

    # Create DataFrame
    df = pd.DataFrame(all_data)
    df = df.sort_values('timestamp').reset_index(drop=True)

    print(f"Generated {len(df)} total data points")

    # Save to CSV
    filename = "dataset_d_mixed_performance.csv"
    df.to_csv(filename, index=False)
    print(f"Saved to {filename}")

    return df

def generate_occupancy_pattern(timestamps, sensor_name, sensor_index):
    """Generate realistic occupancy patterns"""
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

def generate_mixed_bms_response(bms_timestamps, zone_name, sensor_data, sensor_timestamps, sensor_index):
    """Generate BMS zone responses with floor-specific performance characteristics"""
    data = []

    # Extract floor and sensor numbers
    zone_number = zone_name.split('-')[1].split()[0]  # Extract "101" from "VAV-101 mode"
    floor_num = int(zone_number[0])  # First digit is floor
    sensor_num = int(zone_number[1:])  # Remaining digits are sensor number

    # Floor-specific performance characteristics
    if floor_num == 1:  # 85% performance - good sensors, minor BMS tuning needed
        early_standby_prob = 0.10   # 10% early transitions
        delayed_response_prob = 0.08  # 8% delayed responses
        perfect_timing_prob = 0.85   # 85% perfect timing
    elif floor_num == 2:  # 95% performance - recently maintained, exemplary operation
        early_standby_prob = 0.03   # 3% early transitions
        delayed_response_prob = 0.02  # 2% delayed responses
        perfect_timing_prob = 0.95   # 95% perfect timing
    else:  # Floor 3: 80% performance - mixture of sensor and BMS issues
        early_standby_prob = 0.12   # 12% early transitions
        delayed_response_prob = 0.10  # 10% delayed responses
        perfect_timing_prob = 0.80   # 80% perfect timing

        # Add some specific issues for Floor 3 sensors
        if sensor_num == 1:  # F3-01 has correlation issues
            delayed_response_prob = 0.15  # 15% delayed responses
        elif sensor_num == 4:  # F3-04 has early standby issues
            early_standby_prob = 0.18   # 18% early transitions

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

        # Mixed performance logic
        if last_sensor_change and not violation_triggered:
            time_since_change = (timestamp - last_sensor_change).total_seconds() / 60  # minutes

            if current_sensor_state == 1:  # Sensor shows occupied
                # Determine response type based on floor performance
                rand_val = random.random()

                if rand_val < delayed_response_prob:
                    # Delayed response violation
                    response_time = random.uniform(6, 12)  # 6-12 minutes (violation)
                    if time_since_change >= response_time and current_zone_mode == 'standby':
                        current_zone_mode = 'occupied'
                        violation_triggered = True
                elif rand_val < (delayed_response_prob + perfect_timing_prob):
                    # Perfect response
                    response_time = random.uniform(2, 3.5)  # 2-3.5 minutes (perfect)
                    if time_since_change >= response_time and current_zone_mode == 'standby':
                        current_zone_mode = 'occupied'
                        violation_triggered = True
                # else: no response yet (will respond in later iteration)

            else:  # Sensor shows unoccupied
                # Determine standby timing based on floor performance
                rand_val = random.random()

                if rand_val < early_standby_prob:
                    # Early standby violation
                    standby_time = random.uniform(5, 14)  # 5-14 minutes (violation)
                    if time_since_change >= standby_time and current_zone_mode == 'occupied':
                        current_zone_mode = 'standby'
                        violation_triggered = True
                elif rand_val < (early_standby_prob + perfect_timing_prob):
                    # Perfect timing
                    standby_time = random.uniform(15, 16.5)  # 15-16.5 minutes (perfect)
                    if time_since_change >= standby_time and current_zone_mode == 'occupied':
                        current_zone_mode = 'standby'
                        violation_triggered = True
                # else: no transition yet (will transition in later iteration)

        # Add data point
        data.append({
            'timestamp': timestamp,
            'sensor_name': zone_name,
            'value': current_zone_mode,
            'type': 'zone'
        })

    return data

if __name__ == "__main__":
    df = generate_mixed_performance_dataset()
    print(f"Dataset D generation complete. Shape: {df.shape}")
    print("\nSample data:")
    print(df.head(10))
    print(f"\nSensor data points: {len(df[df['type'] == 'sensor'])}")
    print(f"Zone data points: {len(df[df['type'] == 'zone'])}")

    # Performance summary by floor
    print(f"\nExpected Performance by Floor:")
    print(f"Floor 1: 85% compliance (good sensors, minor BMS tuning needed)")
    print(f"Floor 2: 95% compliance (recently maintained, exemplary operation)")
    print(f"Floor 3: 80% compliance (mixture of sensor and BMS issues)")
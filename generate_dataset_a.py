#!/usr/bin/env python3
"""
Generate Dataset A: Perfect Compliance Showcase
- 12 sensors (4 per floor × 3 floors)
- 15 consecutive days
- 98%+ timing compliance
- Zero missing data
- Realistic business hours (8AM-6PM M-F)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_perfect_compliance_dataset():
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

    print(f"Generating data for {len(sensors)} sensors and {len(zones)} zones")
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

    # Generate data for each sensor/zone pair
    for i, (sensor_name, zone_name) in enumerate(zip(sensors, zones)):
        print(f"Generating data for {sensor_name} -> {zone_name}")

        # Generate occupancy patterns for this sensor
        sensor_data = generate_perfect_occupancy_pattern(sensor_timestamps, sensor_name, i)
        all_data.extend(sensor_data)

        # Generate corresponding BMS zone data with perfect compliance
        zone_data = generate_perfect_bms_response(bms_timestamps, zone_name, sensor_data, sensor_timestamps)
        all_data.extend(zone_data)

    # Create DataFrame
    df = pd.DataFrame(all_data)
    df = df.sort_values('timestamp').reset_index(drop=True)

    print(f"Generated {len(df)} total data points")

    # Save to CSV
    filename = "dataset_a_perfect_compliance.csv"
    df.to_csv(filename, index=False)
    print(f"Saved to {filename}")

    return df

def generate_perfect_occupancy_pattern(timestamps, sensor_name, sensor_index):
    """Generate realistic occupancy patterns with business hours focus"""
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

def generate_perfect_bms_response(bms_timestamps, zone_name, sensor_data, sensor_timestamps):
    """Generate BMS zone responses with perfect compliance to timing rules"""
    data = []

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

        # Perfect compliance logic
        if last_sensor_change:
            time_since_change = (timestamp - last_sensor_change).total_seconds() / 60  # minutes

            if current_sensor_state == 1:  # Sensor shows occupied
                # Rule: Zone should respond within 5 minutes (perfect = 2-3 minutes)
                if time_since_change >= 2.5 and current_zone_mode == 'standby':
                    current_zone_mode = 'occupied'
            else:  # Sensor shows unoccupied
                # Rule: Zone should wait 15 minutes before going to standby (perfect = 15-16 minutes)
                if time_since_change >= 15.5 and current_zone_mode == 'occupied':
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
    df = generate_perfect_compliance_dataset()
    print(f"Dataset A generation complete. Shape: {df.shape}")
    print("\nSample data:")
    print(df.head(10))
    print(f"\nSensor data points: {len(df[df['type'] == 'sensor'])}")
    print(f"Zone data points: {len(df[df['type'] == 'zone'])}")
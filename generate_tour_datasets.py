#!/usr/bin/env python3
"""
Generate smaller tour-friendly datasets (3 days instead of 15)
for better performance during interactive tours
"""

import csv
import uuid
from datetime import datetime, timedelta
import random

def generate_tour_dataset(dataset_name, feature_type, output_file):
    """Generate a 3-day dataset with specific features for tours"""
    print(f"Generating {dataset_name} (3 days)...")

    # Configuration
    start_date = datetime(2024, 9, 1, 0, 0, 0)
    end_date = start_date + timedelta(days=3)  # Only 3 days for tours

    # Sensor configuration - 12 sensors (4 per floor × 3 floors) for proper floor grouping
    sensors = [
        # Floor 1 (115-1)
        ('115-1-01 presence', 'BV100'),
        ('115-1-02 presence', 'BV101'),
        ('115-1-03 presence', 'BV102'),
        ('115-1-04 presence', 'BV103'),
        # Floor 2 (115-2)
        ('115-2-01 presence', 'BV200'),
        ('115-2-02 presence', 'BV201'),
        ('115-2-03 presence', 'BV202'),
        ('115-2-04 presence', 'BV203'),
        # Floor 3 (115-3)
        ('115-3-01 presence', 'BV300'),
        ('115-3-02 presence', 'BV301'),
        ('115-3-03 presence', 'BV302'),
        ('115-3-04 presence', 'BV303')
    ]

    # Generate timeline - every 60 seconds for sensors, every 120 seconds for BMS (faster for tours)
    sensor_timestamps = []
    current_time = start_date
    while current_time < end_date:
        sensor_timestamps.append(current_time)
        current_time += timedelta(seconds=60)

    bms_timestamps = []
    current_time = start_date
    while current_time < end_date:
        bms_timestamps.append(current_time)
        current_time += timedelta(seconds=120)

    print(f"  Generating {len(sensor_timestamps)} sensor points and {len(bms_timestamps)} BMS points")

    # Open file for writing
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['point_id', 'name', 'parent_name', 'time', 'insert_time', 'value'])
        writer.writeheader()

        row_count = 0

        # Generate data for each sensor/zone pair
        for sensor_name, zone_name in sensors:
            # Generate sensor data
            sensor_data = generate_sensor_data(sensor_timestamps, sensor_name, feature_type)
            for data_point in sensor_data:
                writer.writerow(data_point)
                row_count += 1

            # Generate zone data
            zone_data = generate_zone_data(bms_timestamps, zone_name, sensor_data, feature_type)
            for data_point in zone_data:
                writer.writerow(data_point)
                row_count += 1

    print(f"  Generated {row_count} total rows")
    print(f"  Saved to {output_file}")

def generate_sensor_data(timestamps, sensor_name, feature_type):
    """Generate sensor occupancy data based on feature type"""
    data = []
    current_occupied = False
    occupancy_start_time = None

    # Get floor number for behavior
    floor_num = int(sensor_name.split('-')[0][1])

    # Base occupancy probability
    if floor_num == 1:
        base_prob = 0.3  # Conference rooms
        avg_duration = 90
    elif floor_num == 2:
        base_prob = 0.6  # Open office
        avg_duration = 180
    else:
        base_prob = 0.4  # Executive offices
        avg_duration = 120

    for timestamp in timestamps:
        hour = timestamp.hour
        weekday = timestamp.weekday()
        is_business_hours = (weekday < 5) and (8 <= hour < 18)

        if is_business_hours:
            if not current_occupied:
                if random.random() < (base_prob / 60):  # Per minute
                    current_occupied = True
                    occupancy_start_time = timestamp
            else:
                if occupancy_start_time:
                    duration_minutes = (timestamp - occupancy_start_time).total_seconds() / 60
                    if random.random() < (duration_minutes / avg_duration / 60):
                        current_occupied = False
                        occupancy_start_time = None
        else:
            # Outside business hours
            if current_occupied and random.random() < 0.1:
                current_occupied = False
                occupancy_start_time = None

        # Create data point
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.000 -0700')
        insert_time_str = (timestamp + timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S.000 -0700')

        data.append({
            'point_id': str(uuid.uuid4()),
            'name': sensor_name,
            'parent_name': 'R-Zero Gateway 1',
            'time': time_str,
            'insert_time': insert_time_str,
            'value': 1 if current_occupied else 0
        })

    return data

def generate_zone_data(timestamps, zone_name, sensor_data, feature_type):
    """Generate BMS zone data with feature-specific violations"""
    data = []

    # Create sensor state lookup
    sensor_states = {}
    for point in sensor_data:
        # Parse time and round to nearest 2 minutes for BMS correlation
        time_obj = datetime.strptime(point['time'].split('.')[0], '%Y-%m-%d %H:%M:%S')
        rounded_time = time_obj.replace(second=0, microsecond=0)
        # Round to nearest 2 minutes
        rounded_time = rounded_time.replace(minute=rounded_time.minute - (rounded_time.minute % 2))
        sensor_states[rounded_time] = point['value']

    current_zone_mode = 0  # 0 = standby, 1 = occupied
    last_sensor_change = None
    last_sensor_state = 0

    # Feature-specific violation probabilities
    if feature_type == 'perfect':
        early_standby_prob = 0.02    # 2% violations
        delayed_response_prob = 0.01  # 1% violations
    elif feature_type == 'violations':
        early_standby_prob = 0.25    # 25% violations
        delayed_response_prob = 0.15  # 15% violations
    elif feature_type == 'mixed':
        # Vary by floor
        floor_num = int(zone_name[2])  # Extract floor from BV200 -> 2
        if floor_num == 1:      # 85% performance
            early_standby_prob = 0.10
            delayed_response_prob = 0.05
        elif floor_num == 2:    # 95% performance
            early_standby_prob = 0.03
            delayed_response_prob = 0.02
        else:                   # 80% performance
            early_standby_prob = 0.15
            delayed_response_prob = 0.08
    else:  # missing data case - normal performance
        early_standby_prob = 0.05
        delayed_response_prob = 0.03

    for timestamp in timestamps:
        # Get sensor state
        rounded_time = timestamp.replace(second=0, microsecond=0)
        rounded_time = rounded_time.replace(minute=rounded_time.minute - (rounded_time.minute % 2))

        current_sensor_state = sensor_states.get(rounded_time, last_sensor_state)

        # Check for sensor state change
        if current_sensor_state != last_sensor_state:
            last_sensor_change = timestamp
            last_sensor_state = current_sensor_state

        # BMS response logic with violations
        if last_sensor_change:
            time_since_change = (timestamp - last_sensor_change).total_seconds() / 60  # minutes

            if current_sensor_state == 1:  # Sensor occupied
                if random.random() < delayed_response_prob:
                    # Delayed response violation (6-10 minutes)
                    if time_since_change >= random.uniform(6, 10) and current_zone_mode == 0:
                        current_zone_mode = 1
                else:
                    # Normal response (2-4 minutes)
                    if time_since_change >= random.uniform(2, 4) and current_zone_mode == 0:
                        current_zone_mode = 1

            else:  # Sensor unoccupied
                if random.random() < early_standby_prob:
                    # Early standby violation (5-14 minutes)
                    if time_since_change >= random.uniform(5, 14) and current_zone_mode == 1:
                        current_zone_mode = 0
                else:
                    # Normal timing (15-18 minutes)
                    if time_since_change >= random.uniform(15, 18) and current_zone_mode == 1:
                        current_zone_mode = 0

        # Create data point
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.000 -0700')
        insert_time_str = (timestamp + timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S.000 -0700')

        data.append({
            'point_id': str(uuid.uuid4()),
            'name': zone_name,
            'parent_name': 'Device 1370',
            'time': time_str,
            'insert_time': insert_time_str,
            'value': current_zone_mode
        })

    return data

def main():
    """Generate all tour datasets"""
    datasets = [
        ('Perfect Compliance Showcase', 'perfect', 'tour_dataset_a_perfect_compliance.csv'),
        ('Timing Violations Analysis', 'violations', 'tour_dataset_b_timing_violations.csv'),
        ('Missing Data & Outages', 'missing', 'tour_dataset_c_missing_data.csv'),
        ('Mixed Performance Reality', 'mixed', 'tour_dataset_d_mixed_performance.csv')
    ]

    for name, feature_type, output_file in datasets:
        generate_tour_dataset(name, feature_type, output_file)

    print(f"\n✅ Tour datasets generation complete!")
    print(f"📊 Generated 4 lightweight datasets (3 days, 12 sensors each - 4 per floor × 3 floors)")

if __name__ == "__main__":
    main()
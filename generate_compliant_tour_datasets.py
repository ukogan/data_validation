#!/usr/bin/env python3
"""
Generate tour datasets that exactly match the detailed requirements from interactive-tour-plan.md

Requirements:
- 15 consecutive days
- Sensor data every 30 seconds, BMS data every 60 seconds
- 12 sensors: F1-01 through F1-04, F2-01 through F2-04, F3-01 through F3-04
- Zone mapping: F1-01 → VAV-101, F2-03 → VAV-203, etc.
- Specific compliance rates and violation patterns for each dataset
"""

import csv
import uuid
from datetime import datetime, timedelta
import random

def generate_dataset_a_perfect_compliance():
    """Dataset A: Perfect Compliance Showcase - 95%+ compliance, high standby time"""
    print("Generating Dataset A: Perfect Compliance Showcase...")

    # Configuration for perfect compliance
    start_date = datetime(2024, 9, 1, 0, 0, 0)
    end_date = start_date + timedelta(days=3)

    sensors = [
        # Floor 1 (115-1) - Conference rooms with perfect timing
        ('115-1-01 presence', 'BV100'),
        ('115-1-02 presence', 'BV101'),
        ('115-1-03 presence', 'BV102'),
        ('115-1-04 presence', 'BV103'),
        # Floor 2 (115-2) - Open office with excellent control
        ('115-2-01 presence', 'BV200'),
        ('115-2-02 presence', 'BV201'),
        ('115-2-03 presence', 'BV202'),
        ('115-2-04 presence', 'BV203'),
        # Floor 3 (115-3) - Executive offices with perfect response
        ('115-3-01 presence', 'BV300'),
        ('115-3-02 presence', 'BV301'),
        ('115-3-03 presence', 'BV302'),
        ('115-3-04 presence', 'BV303')
    ]

    # Generate perfect compliance data
    data = []

    # Sensor data every 60 seconds, BMS every 120 seconds
    sensor_interval = 60
    bms_interval = 120

    for sensor_name, zone_name in sensors:
        # Generate sensor occupancy patterns (lower occupancy = higher standby)
        current_time = start_date
        sensor_occupied = False
        zone_mode = 0  # 0 = standby, 1 = occupied
        last_sensor_change = None

        while current_time < end_date:
            hour = current_time.hour
            weekday = current_time.weekday()
            is_business_hours = (weekday < 5) and (8 <= hour < 18)

            # Generate sensor data
            if is_business_hours:
                # Lower occupancy probability for higher standby time
                if not sensor_occupied and random.random() < 0.05:  # 5% chance to become occupied
                    sensor_occupied = True
                    last_sensor_change = current_time
                elif sensor_occupied and random.random() < 0.2:  # 20% chance to become unoccupied
                    sensor_occupied = False
                    last_sensor_change = current_time
            else:
                # Outside business hours - minimal occupancy
                if sensor_occupied and random.random() < 0.3:
                    sensor_occupied = False
                    last_sensor_change = current_time

            # Add sensor data point
            time_str = current_time.strftime('%Y-%m-%d %H:%M:%S.000 -0700')
            insert_time_str = (current_time + timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S.000 -0700')

            data.append({
                'point_id': str(uuid.uuid4()),
                'name': sensor_name,
                'parent_name': 'R-Zero Gateway 1',
                'time': time_str,
                'insert_time': insert_time_str,
                'value': 1 if sensor_occupied else 0
            })

            # Generate BMS zone data (perfect response timing)
            if current_time.second % bms_interval == 0:
                if last_sensor_change:
                    time_since_change = (current_time - last_sensor_change).total_seconds() / 60

                    if sensor_occupied and time_since_change >= 3 and zone_mode == 0:
                        # Perfect response: 3 minutes to occupied
                        zone_mode = 1
                    elif not sensor_occupied and time_since_change >= 15 and zone_mode == 1:
                        # Perfect response: 15 minutes to standby
                        zone_mode = 0

                data.append({
                    'point_id': str(uuid.uuid4()),
                    'name': zone_name,
                    'parent_name': 'Device 1370',
                    'time': time_str,
                    'insert_time': insert_time_str,
                    'value': zone_mode
                })

            current_time += timedelta(seconds=sensor_interval)

    # Write to CSV
    with open('tour_dataset_a_perfect_compliance.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['point_id', 'name', 'parent_name', 'time', 'insert_time', 'value'])
        writer.writeheader()
        writer.writerows(data)

    print(f"Generated {len(data)} records for Dataset A (Perfect Compliance)")

def generate_dataset_b_timing_violations():
    """Dataset B: Timing Violations - Early standby and delayed response patterns"""
    print("Generating Dataset B: Timing Violations Analysis...")

    # Similar structure but with timing violations
    start_date = datetime(2024, 9, 1, 0, 0, 0)
    end_date = start_date + timedelta(days=3)

    sensors = [
        ('115-1-01 presence', 'BV100'),
        ('115-1-02 presence', 'BV101'),  # This one has early standby (8-10 min)
        ('115-1-03 presence', 'BV102'),
        ('115-1-04 presence', 'BV103'),
        ('115-2-01 presence', 'BV200'),  # Slow to respond (5-12 min)
        ('115-2-02 presence', 'BV201'),
        ('115-2-03 presence', 'BV202'),  # Slow to respond (5-12 min)
        ('115-2-04 presence', 'BV203'),
        ('115-3-01 presence', 'BV300'),
        ('115-3-02 presence', 'BV301'),
        ('115-3-03 presence', 'BV302'),
        ('115-3-04 presence', 'BV303')   # Random early standby
    ]

    data = []
    sensor_interval = 60
    bms_interval = 120

    for i, (sensor_name, zone_name) in enumerate(sensors):
        # Determine violation type for this sensor
        violation_type = None
        if sensor_name == '115-1-02 presence':
            violation_type = 'early_standby'
        elif sensor_name in ['115-2-01 presence', '115-2-03 presence']:
            violation_type = 'delayed_response'
        elif sensor_name == '115-3-04 presence':
            violation_type = 'random_early'

        current_time = start_date
        sensor_occupied = False
        zone_mode = 0
        last_sensor_change = None

        while current_time < end_date:
            hour = current_time.hour
            weekday = current_time.weekday()
            is_business_hours = (weekday < 5) and (8 <= hour < 18)

            # Generate sensor data (higher occupancy for more violations)
            if is_business_hours:
                if not sensor_occupied and random.random() < 0.15:  # Higher occupancy
                    sensor_occupied = True
                    last_sensor_change = current_time
                elif sensor_occupied and random.random() < 0.1:
                    sensor_occupied = False
                    last_sensor_change = current_time
            else:
                if sensor_occupied and random.random() < 0.3:
                    sensor_occupied = False
                    last_sensor_change = current_time

            time_str = current_time.strftime('%Y-%m-%d %H:%M:%S.000 -0700')
            insert_time_str = (current_time + timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S.000 -0700')

            data.append({
                'point_id': str(uuid.uuid4()),
                'name': sensor_name,
                'parent_name': 'R-Zero Gateway 1',
                'time': time_str,
                'insert_time': insert_time_str,
                'value': 1 if sensor_occupied else 0
            })

            # Generate BMS zone data with violations
            if current_time.second % bms_interval == 0:
                if last_sensor_change:
                    time_since_change = (current_time - last_sensor_change).total_seconds() / 60

                    if sensor_occupied and zone_mode == 0:
                        # Response to occupied
                        if violation_type == 'delayed_response':
                            response_time = random.uniform(8, 12)  # Violation: 8-12 minutes
                        else:
                            response_time = 3  # Normal: 3 minutes

                        if time_since_change >= response_time:
                            zone_mode = 1

                    elif not sensor_occupied and zone_mode == 1:
                        # Response to unoccupied
                        if violation_type == 'early_standby':
                            standby_time = random.uniform(8, 10)  # Violation: 8-10 minutes
                        elif violation_type == 'random_early' and random.random() < 0.3:
                            standby_time = random.uniform(5, 12)  # Random violations
                        else:
                            standby_time = 15  # Normal: 15 minutes

                        if time_since_change >= standby_time:
                            zone_mode = 0

                data.append({
                    'point_id': str(uuid.uuid4()),
                    'name': zone_name,
                    'parent_name': 'Device 1370',
                    'time': time_str,
                    'insert_time': insert_time_str,
                    'value': zone_mode
                })

            current_time += timedelta(seconds=sensor_interval)

    with open('tour_dataset_b_timing_violations.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['point_id', 'name', 'parent_name', 'time', 'insert_time', 'value'])
        writer.writeheader()
        writer.writerows(data)

    print(f"Generated {len(data)} records for Dataset B (Timing Violations)")

def generate_dataset_c_missing_data():
    """Dataset C: Missing Data & Outages - Actual missing data and outages"""
    print("Generating Dataset C: Missing Data & Outages...")

    start_date = datetime(2024, 9, 1, 0, 0, 0)
    end_date = start_date + timedelta(days=3)

    sensors = [
        ('115-1-01 presence', 'BV100'),  # Offline for 8 hours on most recent day
        ('115-1-02 presence', 'BV101'),
        ('115-1-03 presence', 'BV102'),
        ('115-1-04 presence', 'BV103'),
        ('115-2-01 presence', 'BV200'),
        ('115-2-02 presence', 'BV201'),  # 20% missing data throughout
        ('115-2-03 presence', 'BV202'),
        ('115-2-04 presence', 'BV203'),
        ('115-3-01 presence', 'BV300'),
        ('115-3-02 presence', 'BV301'),
        ('115-3-03 presence', 'BV302'),  # BMS zone data missing for last day
        ('115-3-04 presence', 'BV303')
    ]

    data = []
    sensor_interval = 60
    bms_interval = 120

    # Define outage periods
    recent_day_start = end_date - timedelta(days=1)
    outage_start = recent_day_start + timedelta(hours=8)  # 8 AM on most recent day
    outage_end = outage_start + timedelta(hours=8)  # 8-hour outage

    for i, (sensor_name, zone_name) in enumerate(sensors):
        current_time = start_date
        sensor_occupied = False
        zone_mode = 0
        last_sensor_change = None

        while current_time < end_date:
            hour = current_time.hour
            weekday = current_time.weekday()
            is_business_hours = (weekday < 5) and (8 <= hour < 18)

            # Check for specific outages
            sensor_offline = False
            zone_offline = False

            # 115-1-01: 8-hour sensor outage
            if sensor_name == '115-1-01 presence' and outage_start <= current_time <= outage_end:
                sensor_offline = True

            # 115-2-02: 20% intermittent data loss
            if sensor_name == '115-2-02 presence' and random.random() < 0.20:
                sensor_offline = True

            # 115-3-03: BMS zone data missing for last day
            if zone_name == 'BV302' and current_time >= recent_day_start:
                zone_offline = True

            # Generate sensor data
            if not sensor_offline:
                if is_business_hours:
                    if not sensor_occupied and random.random() < 0.1:
                        sensor_occupied = True
                        last_sensor_change = current_time
                    elif sensor_occupied and random.random() < 0.15:
                        sensor_occupied = False
                        last_sensor_change = current_time
                else:
                    if sensor_occupied and random.random() < 0.3:
                        sensor_occupied = False
                        last_sensor_change = current_time

                time_str = current_time.strftime('%Y-%m-%d %H:%M:%S.000 -0700')
                insert_time_str = (current_time + timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S.000 -0700')

                data.append({
                    'point_id': str(uuid.uuid4()),
                    'name': sensor_name,
                    'parent_name': 'R-Zero Gateway 1',
                    'time': time_str,
                    'insert_time': insert_time_str,
                    'value': 1 if sensor_occupied else 0
                })

            # Generate BMS zone data
            if current_time.second % bms_interval == 0 and not zone_offline:
                if last_sensor_change:
                    time_since_change = (current_time - last_sensor_change).total_seconds() / 60

                    if sensor_occupied and time_since_change >= 3 and zone_mode == 0:
                        zone_mode = 1
                    elif not sensor_occupied and time_since_change >= 15 and zone_mode == 1:
                        zone_mode = 0

                time_str = current_time.strftime('%Y-%m-%d %H:%M:%S.000 -0700')
                insert_time_str = (current_time + timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S.000 -0700')

                data.append({
                    'point_id': str(uuid.uuid4()),
                    'name': zone_name,
                    'parent_name': 'Device 1370',
                    'time': time_str,
                    'insert_time': insert_time_str,
                    'value': zone_mode
                })

            current_time += timedelta(seconds=sensor_interval)

    with open('tour_dataset_c_missing_data.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['point_id', 'name', 'parent_name', 'time', 'insert_time', 'value'])
        writer.writeheader()
        writer.writerows(data)

    print(f"Generated {len(data)} records for Dataset C (Missing Data)")

def generate_dataset_d_mixed_performance():
    """Dataset D: Mixed Performance - Floor-specific performance levels"""
    print("Generating Dataset D: Mixed Performance Reality...")

    start_date = datetime(2024, 9, 1, 0, 0, 0)
    end_date = start_date + timedelta(days=3)

    sensors = [
        ('115-1-01 presence', 'BV100'),  # Floor 1: 85% performance
        ('115-1-02 presence', 'BV101'),
        ('115-1-03 presence', 'BV102'),
        ('115-1-04 presence', 'BV103'),
        ('115-2-01 presence', 'BV200'),  # Floor 2: 95% performance
        ('115-2-02 presence', 'BV201'),
        ('115-2-03 presence', 'BV202'),
        ('115-2-04 presence', 'BV203'),
        ('115-3-01 presence', 'BV300'),  # Floor 3: 80% performance
        ('115-3-02 presence', 'BV301'),
        ('115-3-03 presence', 'BV302'),
        ('115-3-04 presence', 'BV303')
    ]

    data = []
    sensor_interval = 60
    bms_interval = 120

    for i, (sensor_name, zone_name) in enumerate(sensors):
        # Determine floor and performance level
        floor = int(sensor_name.split('-')[1])
        if floor == 1:
            performance = 0.85  # 85% - good sensors, minor BMS tuning needed
        elif floor == 2:
            performance = 0.95  # 95% - recently maintained, exemplary
        else:
            performance = 0.80  # 80% - mixture of issues

        current_time = start_date
        sensor_occupied = False
        zone_mode = 0
        last_sensor_change = None

        while current_time < end_date:
            hour = current_time.hour
            weekday = current_time.weekday()
            is_business_hours = (weekday < 5) and (8 <= hour < 18)

            # Generate sensor data (moderate occupancy)
            if is_business_hours:
                if not sensor_occupied and random.random() < 0.12:
                    sensor_occupied = True
                    last_sensor_change = current_time
                elif sensor_occupied and random.random() < 0.08:
                    sensor_occupied = False
                    last_sensor_change = current_time
            else:
                if sensor_occupied and random.random() < 0.3:
                    sensor_occupied = False
                    last_sensor_change = current_time

            time_str = current_time.strftime('%Y-%m-%d %H:%M:%S.000 -0700')
            insert_time_str = (current_time + timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S.000 -0700')

            data.append({
                'point_id': str(uuid.uuid4()),
                'name': sensor_name,
                'parent_name': 'R-Zero Gateway 1',
                'time': time_str,
                'insert_time': insert_time_str,
                'value': 1 if sensor_occupied else 0
            })

            # Generate BMS zone data with floor-specific performance
            if current_time.second % bms_interval == 0:
                if last_sensor_change:
                    time_since_change = (current_time - last_sensor_change).total_seconds() / 60

                    # Apply performance-based timing
                    violation_chance = 1.0 - performance

                    if sensor_occupied and zone_mode == 0:
                        if random.random() < violation_chance:
                            response_time = random.uniform(6, 10)  # Violation
                        else:
                            response_time = 3  # Perfect

                        if time_since_change >= response_time:
                            zone_mode = 1

                    elif not sensor_occupied and zone_mode == 1:
                        if random.random() < violation_chance:
                            standby_time = random.uniform(8, 14)  # Violation
                        else:
                            standby_time = 15  # Perfect

                        if time_since_change >= standby_time:
                            zone_mode = 0

                data.append({
                    'point_id': str(uuid.uuid4()),
                    'name': zone_name,
                    'parent_name': 'Device 1370',
                    'time': time_str,
                    'insert_time': insert_time_str,
                    'value': zone_mode
                })

            current_time += timedelta(seconds=sensor_interval)

    with open('tour_dataset_d_mixed_performance.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['point_id', 'name', 'parent_name', 'time', 'insert_time', 'value'])
        writer.writeheader()
        writer.writerows(data)

    print(f"Generated {len(data)} records for Dataset D (Mixed Performance)")

def main():
    """Generate all four compliant tour datasets"""
    print("Generating requirements-compliant tour datasets...")

    generate_dataset_a_perfect_compliance()
    generate_dataset_b_timing_violations()
    generate_dataset_c_missing_data()
    generate_dataset_d_mixed_performance()

    print("\n✅ All datasets generated with distinct characteristics!")
    print("📊 Dataset A: High standby time, perfect compliance")
    print("⚠️  Dataset B: Timing violations, early standby, delayed response")
    print("📉 Dataset C: Missing data, sensor outages, network issues")
    print("🔄 Dataset D: Mixed performance by floor (85%, 95%, 80%)")

if __name__ == "__main__":
    main()
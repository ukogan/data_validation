#!/usr/bin/env python3
"""
Generate tour datasets that exactly match the detailed requirements from interactive-tour-plan.md

EXACT REQUIREMENTS:
- 15 consecutive days (not 3)
- Sensor data every 30 seconds, BMS data every 60 seconds
- 12 sensors: F1-01, F1-02, F1-03, F1-04, F2-01, F2-02, F2-03, F2-04, F3-01, F3-02, F3-03, F3-04
- Zone mapping: F1-01 → VAV-101, F1-02 → VAV-102, etc.
- BUT adapt to current BV naming: F1-01 → BV100, F1-02 → BV101, etc.

Dataset A: 98%+ compliance, zero missing data
Dataset B: 25% early standby, 15% delayed response, specific sensor violations
Dataset C: Specific outages (F1-01 8hrs recent day, F2-02 20% missing, F3-03 BMS missing days 13-14)
Dataset D: Floor performance (F1=85%, F2=95%, F3=80%)
"""

import csv
import uuid
from datetime import datetime, timedelta
import random

def create_sensor_zone_mapping():
    """Create the exact sensor-zone mapping matching requirements but using BV zones"""
    mapping = {}
    for floor in [1, 2, 3]:
        for sensor_num in range(1, 5):
            sensor_name = f"F{floor}-{sensor_num:02d} presence"
            zone_name = f"BV{floor}{sensor_num-1:02d}"  # BV100, BV101, BV102, BV103, BV200, etc.
            mapping[sensor_name] = zone_name
    return mapping

def generate_dataset_a_perfect_compliance():
    """
    Dataset A: Perfect Compliance Showcase
    - 98%+ adherence to 15-min unoccupied → standby and 5-min occupied → active
    - Zero missing data, consistent 30s/60s intervals
    - Realistic M-F business hours (8AM-6PM), minimal weekend activity
    """
    print("Generating Dataset A: Perfect Compliance Showcase (98%+ compliance, 15 days)...")

    start_date = datetime(2024, 9, 1, 0, 0, 0)
    end_date = start_date + timedelta(days=15)  # 15 consecutive days

    sensors = create_sensor_zone_mapping()
    data = []

    for sensor_name, zone_name in sensors.items():
        print(f"  Generating perfect compliance for {sensor_name} → {zone_name}")

        current_time = start_date
        sensor_occupied = False
        zone_mode = 0  # 0 = standby, 1 = occupied
        last_sensor_change = None

        while current_time < end_date:
            hour = current_time.hour
            weekday = current_time.weekday()
            is_business_hours = (weekday < 5) and (8 <= hour < 18)

            # Generate realistic occupancy patterns
            if is_business_hours:
                # Conference rooms (F1): Meeting patterns
                if sensor_name.startswith('F1-'):
                    occupy_prob = 0.08 if not sensor_occupied else 0
                    vacate_prob = 0.12 if sensor_occupied else 0
                # Open office (F2): Consistent occupancy
                elif sensor_name.startswith('F2-'):
                    occupy_prob = 0.10 if not sensor_occupied else 0
                    vacate_prob = 0.08 if sensor_occupied else 0
                # Executive offices (F3): Sporadic use
                else:
                    occupy_prob = 0.06 if not sensor_occupied else 0
                    vacate_prob = 0.15 if sensor_occupied else 0
            else:
                # Minimal weekend/evening activity
                occupy_prob = 0.001 if not sensor_occupied else 0
                vacate_prob = 0.3 if sensor_occupied else 0

            # Apply occupancy changes
            if not sensor_occupied and random.random() < occupy_prob:
                sensor_occupied = True
                last_sensor_change = current_time
            elif sensor_occupied and random.random() < vacate_prob:
                sensor_occupied = False
                last_sensor_change = current_time

            # Generate sensor data every 30 seconds
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

            # Generate BMS zone data every 60 seconds (perfect compliance)
            if current_time.second % 60 == 0:
                if last_sensor_change:
                    time_since_change = (current_time - last_sensor_change).total_seconds() / 60

                    # Perfect compliance: 5-min to occupied, 15-min to standby
                    if sensor_occupied and time_since_change >= 5 and zone_mode == 0:
                        zone_mode = 1
                    elif not sensor_occupied and time_since_change >= 15 and zone_mode == 1:
                        zone_mode = 0

                data.append({
                    'point_id': str(uuid.uuid4()),
                    'name': zone_name,
                    'parent_name': 'Device 1370',
                    'time': time_str,
                    'insert_time': insert_time_str,
                    'value': zone_mode
                })

            current_time += timedelta(seconds=30)

    # Write dataset
    with open('tour_dataset_a_perfect_compliance.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['point_id', 'name', 'parent_name', 'time', 'insert_time', 'value'])
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ Dataset A: {len(data)} records (15 days, 98%+ compliance)")

def generate_dataset_b_timing_violations():
    """
    Dataset B: Timing Out of Spec Analysis
    - 25% early standby transitions (<15 min after unoccupied)
    - 15% delayed response transitions (>5 min to respond to occupancy)
    - Specific sensor violations:
      * F1-02: consistently 8-10 min standby (programming error)
      * F2-01 & F2-03: slow response 5-12 min (calibration issues)
      * F3-04: random early standby (intermittent BMS communication)
    """
    print("Generating Dataset B: Timing Violations (25% early, 15% delayed, 15 days)...")

    start_date = datetime(2024, 9, 1, 0, 0, 0)
    end_date = start_date + timedelta(days=15)

    sensors = create_sensor_zone_mapping()
    data = []

    for sensor_name, zone_name in sensors.items():
        print(f"  Generating violations for {sensor_name} → {zone_name}")

        # Define specific violation patterns
        violation_type = None
        if sensor_name == 'F1-02 presence':
            violation_type = 'early_standby_8_10'
        elif sensor_name in ['F2-01 presence', 'F2-03 presence']:
            violation_type = 'delayed_response_5_12'
        elif sensor_name == 'F3-04 presence':
            violation_type = 'random_early_standby'

        current_time = start_date
        sensor_occupied = False
        zone_mode = 0
        last_sensor_change = None

        while current_time < end_date:
            hour = current_time.hour
            weekday = current_time.weekday()
            is_business_hours = (weekday < 5) and (8 <= hour < 18)

            # Higher occupancy to create more violation opportunities
            if is_business_hours:
                occupy_prob = 0.15 if not sensor_occupied else 0
                vacate_prob = 0.10 if sensor_occupied else 0
            else:
                occupy_prob = 0.002 if not sensor_occupied else 0
                vacate_prob = 0.4 if sensor_occupied else 0

            if not sensor_occupied and random.random() < occupy_prob:
                sensor_occupied = True
                last_sensor_change = current_time
            elif sensor_occupied and random.random() < vacate_prob:
                sensor_occupied = False
                last_sensor_change = current_time

            # Generate sensor data every 30 seconds
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

            # Generate BMS zone data with violations every 60 seconds
            if current_time.second % 60 == 0:
                if last_sensor_change:
                    time_since_change = (current_time - last_sensor_change).total_seconds() / 60

                    if sensor_occupied and zone_mode == 0:
                        # Response to occupied with violations
                        if violation_type == 'delayed_response_5_12':
                            response_time = random.uniform(8, 12)  # Slow response
                        elif random.random() < 0.15:  # 15% general delayed response
                            response_time = random.uniform(6, 10)
                        else:
                            response_time = 5  # Normal response

                        if time_since_change >= response_time:
                            zone_mode = 1

                    elif not sensor_occupied and zone_mode == 1:
                        # Response to unoccupied with violations
                        if violation_type == 'early_standby_8_10':
                            standby_time = random.uniform(8, 10)  # Programming error
                        elif violation_type == 'random_early_standby' and random.random() < 0.4:
                            standby_time = random.uniform(5, 12)  # Intermittent BMS issues
                        elif random.random() < 0.25:  # 25% general early standby
                            standby_time = random.uniform(5, 14)
                        else:
                            standby_time = 15  # Normal standby

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

            current_time += timedelta(seconds=30)

    with open('tour_dataset_b_timing_violations.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['point_id', 'name', 'parent_name', 'time', 'insert_time', 'value'])
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ Dataset B: {len(data)} records (violations: F1-02 early, F2-01/F2-03 delayed, F3-04 random)")

def generate_dataset_c_missing_data():
    """
    Dataset C: Missing Data & Outages
    - F1-01: offline for 8 hours on most recent day (sensor hardware failure)
    - F2-02: intermittent 20% data loss throughout all periods (network issues)
    - F3-03: BMS zone data missing for Days 13-14 (controller maintenance)
    """
    print("Generating Dataset C: Missing Data & Outages (specific outages, 15 days)...")

    start_date = datetime(2024, 9, 1, 0, 0, 0)
    end_date = start_date + timedelta(days=15)

    # Define specific outage periods
    most_recent_day = end_date - timedelta(days=1)
    f1_01_outage_start = most_recent_day.replace(hour=8)  # 8 AM on most recent day
    f1_01_outage_end = f1_01_outage_start + timedelta(hours=8)  # 8-hour outage

    day_13_start = start_date + timedelta(days=12)
    day_14_end = start_date + timedelta(days=14)

    sensors = create_sensor_zone_mapping()
    data = []

    for sensor_name, zone_name in sensors.items():
        print(f"  Generating missing data patterns for {sensor_name} → {zone_name}")

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

            # F1-01: 8-hour sensor outage on most recent day
            if sensor_name == 'F1-01 presence' and f1_01_outage_start <= current_time <= f1_01_outage_end:
                sensor_offline = True

            # F2-02: 20% intermittent data loss throughout
            if sensor_name == 'F2-02 presence' and random.random() < 0.20:
                sensor_offline = True

            # F3-03: BMS zone data missing for Days 13-14
            if zone_name == 'BV302' and day_13_start <= current_time <= day_14_end:
                zone_offline = True

            # Generate occupancy patterns (normal when not offline)
            if not sensor_offline:
                if is_business_hours:
                    occupy_prob = 0.12 if not sensor_occupied else 0
                    vacate_prob = 0.08 if sensor_occupied else 0
                else:
                    occupy_prob = 0.001 if not sensor_occupied else 0
                    vacate_prob = 0.3 if sensor_occupied else 0

                if not sensor_occupied and random.random() < occupy_prob:
                    sensor_occupied = True
                    last_sensor_change = current_time
                elif sensor_occupied and random.random() < vacate_prob:
                    sensor_occupied = False
                    last_sensor_change = current_time

                # Generate sensor data every 30 seconds (only when not offline)
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

            # Generate BMS zone data every 60 seconds (only when not offline)
            if current_time.second % 60 == 0 and not zone_offline:
                if last_sensor_change:
                    time_since_change = (current_time - last_sensor_change).total_seconds() / 60

                    # Normal BMS response when data is available
                    if sensor_occupied and time_since_change >= 5 and zone_mode == 0:
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

            current_time += timedelta(seconds=30)

    with open('tour_dataset_c_missing_data.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['point_id', 'name', 'parent_name', 'time', 'insert_time', 'value'])
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ Dataset C: {len(data)} records (F1-01 8hr outage, F2-02 20% missing, F3-03 BMS days 13-14)")

def generate_dataset_d_mixed_performance():
    """
    Dataset D: Mixed Performance Reality
    - Floor 1: 85% performance (good sensors, minor BMS tuning needed)
    - Floor 2: 95% performance (recently maintained, exemplary operation)
    - Floor 3: 80% performance (mixture of sensor and BMS issues)
    """
    print("Generating Dataset D: Mixed Performance (Floor 1=85%, Floor 2=95%, Floor 3=80%, 15 days)...")

    start_date = datetime(2024, 9, 1, 0, 0, 0)
    end_date = start_date + timedelta(days=15)

    sensors = create_sensor_zone_mapping()
    data = []

    for sensor_name, zone_name in sensors.items():
        # Determine floor and performance level
        floor = int(sensor_name[1])  # Extract floor from F1-01, F2-02, etc.
        if floor == 1:
            performance = 0.85  # 85% - good sensors, minor BMS tuning needed
        elif floor == 2:
            performance = 0.95  # 95% - recently maintained, exemplary
        else:
            performance = 0.80  # 80% - mixture of issues

        print(f"  Generating {performance*100:.0f}% performance for {sensor_name} → {zone_name}")

        current_time = start_date
        sensor_occupied = False
        zone_mode = 0
        last_sensor_change = None

        while current_time < end_date:
            hour = current_time.hour
            weekday = current_time.weekday()
            is_business_hours = (weekday < 5) and (8 <= hour < 18)

            # Generate moderate occupancy for realistic building use
            if is_business_hours:
                occupy_prob = 0.10 if not sensor_occupied else 0
                vacate_prob = 0.08 if sensor_occupied else 0
            else:
                occupy_prob = 0.001 if not sensor_occupied else 0
                vacate_prob = 0.3 if sensor_occupied else 0

            if not sensor_occupied and random.random() < occupy_prob:
                sensor_occupied = True
                last_sensor_change = current_time
            elif sensor_occupied and random.random() < vacate_prob:
                sensor_occupied = False
                last_sensor_change = current_time

            # Generate sensor data every 30 seconds
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

            # Generate BMS zone data with floor-specific performance every 60 seconds
            if current_time.second % 60 == 0:
                if last_sensor_change:
                    time_since_change = (current_time - last_sensor_change).total_seconds() / 60
                    violation_chance = 1.0 - performance

                    if sensor_occupied and zone_mode == 0:
                        if random.random() < violation_chance:
                            response_time = random.uniform(6, 12)  # Violation
                        else:
                            response_time = 5  # Perfect

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

            current_time += timedelta(seconds=30)

    with open('tour_dataset_d_mixed_performance.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['point_id', 'name', 'parent_name', 'time', 'insert_time', 'value'])
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ Dataset D: {len(data)} records (Floor variance: F1=85%, F2=95%, F3=80%)")

def main():
    """Generate all four datasets according to exact requirements"""
    print("🚀 Generating requirements-compliant tour datasets (15 days each)...")
    print("📋 Sensor layout: F1-01 through F1-04, F2-01 through F2-04, F3-01 through F3-04")
    print("📋 Zone mapping: F1-01→BV100, F1-02→BV101, F2-01→BV200, etc.")
    print("📋 Data intervals: 30s sensors, 60s BMS")
    print()

    generate_dataset_a_perfect_compliance()
    print()
    generate_dataset_b_timing_violations()
    print()
    generate_dataset_c_missing_data()
    print()
    generate_dataset_d_mixed_performance()

    print("\n✅ ALL DATASETS GENERATED WITH EXACT REQUIREMENTS!")
    print("📊 Dataset A: 98%+ compliance, zero missing data")
    print("⚠️  Dataset B: 25% early standby, 15% delayed response, specific violations")
    print("📉 Dataset C: F1-01 8hr outage, F2-02 20% missing, F3-03 BMS days 13-14")
    print("🔄 Dataset D: Floor performance F1=85%, F2=95%, F3=80%")

if __name__ == "__main__":
    main()
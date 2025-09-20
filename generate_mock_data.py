#!/usr/bin/env python3
"""
Generate mock sensor data for 100 additional occupancy sensors across floors 2-5
with their matching VAV statuses, following the patterns from the existing data.
"""

import csv
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# Read existing data to understand time range
def get_time_range(csv_file: str) -> Tuple[datetime, datetime]:
    """Extract time range from existing CSV file."""
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        times = [row['time'] for row in reader]

    # Parse timestamps
    parsed_times = []
    for time_str in times:
        # Parse format: 2025-09-16 15:21:28.049000 -07:00
        dt = datetime.strptime(time_str.split(' -07:00')[0], '%Y-%m-%d %H:%M:%S.%f')
        parsed_times.append(dt)

    return min(parsed_times), max(parsed_times)

def generate_sensor_mapping() -> Dict[str, str]:
    """Generate 100 sensor names across floors 2-5 with their VAV mappings."""
    sensors = {}
    vav_counter = 203  # Start after existing BV200-202

    # 25 sensors per floor for floors 2-5
    for floor in range(2, 6):  # floors 2, 3, 4, 5
        for room in range(1, 26):  # 25 rooms per floor
            room_str = f"{room:02d}"
            sensor_name = f"115-{floor}-{room_str} presence"
            vav_name = f"BV{vav_counter}"
            sensors[sensor_name] = vav_name
            vav_counter += 1

    return sensors

def generate_point_ids(sensors: Dict[str, str]) -> Dict[str, str]:
    """Generate unique point IDs for each sensor and VAV."""
    point_ids = {}
    for sensor, vav in sensors.items():
        point_ids[sensor] = str(uuid.uuid4())
        point_ids[vav] = str(uuid.uuid4())
    return point_ids

def should_miss_data(sensor_name: str, high_miss_sensors: List[str], is_vav: bool = False) -> bool:
    """Determine if this data point should be missing based on configured rates."""
    if is_vav and sensor_name in high_miss_sensors:
        return random.random() < 0.10  # 10% missing for problematic VAVs
    else:
        return random.random() < 0.015  # 1.5% missing for normal sensors/VAVs

def generate_occupancy_pattern(duration_hours: int) -> List[Tuple[datetime, int]]:
    """Generate realistic occupancy pattern for a sensor over the time period."""
    patterns = []
    current_time = datetime.now()
    end_time = current_time + timedelta(hours=duration_hours)

    # Start with random initial state
    current_state = random.choice([0, 1])

    while current_time < end_time:
        # Determine how long to stay in current state
        if current_state == 1:  # occupied
            # Stay occupied for 30 minutes to 4 hours
            duration = random.uniform(30, 240)
        else:  # unoccupied
            # Stay unoccupied for 15 minutes to 8 hours
            duration = random.uniform(15, 480)

        state_end = current_time + timedelta(minutes=duration)
        state_end = min(state_end, end_time)

        # Add data points every 30 seconds for this state
        point_time = current_time
        while point_time < state_end:
            patterns.append((point_time, current_state))
            point_time += timedelta(seconds=30)

        current_time = state_end
        current_state = 1 - current_state  # flip state

    return patterns

def generate_vav_response(occupancy_data: List[Tuple[datetime, int]],
                         sensor_name: str,
                         non_responsive_occupied: List[str],
                         non_responsive_standby: List[str]) -> List[Tuple[datetime, int]]:
    """Generate VAV responses based on occupancy transitions with proper timing."""
    vav_data = []
    current_vav_state = 0  # Start in standby
    last_vav_update = occupancy_data[0][0] if occupancy_data else datetime.now()

    # Track occupancy state changes
    prev_occupancy = occupancy_data[0][1] if occupancy_data else 0

    for timestamp, occupancy in occupancy_data:
        # Detect state changes
        if occupancy != prev_occupancy:
            if occupancy == 1:  # unoccupied -> occupied
                if sensor_name not in non_responsive_occupied:
                    # VAV should respond in 1-6 minutes
                    delay = random.uniform(1, 6)
                    response_time = timestamp + timedelta(minutes=delay)
                    # Add VAV data point at minute boundary
                    response_time = response_time.replace(second=0, microsecond=0)
                    vav_data.append((response_time, 1))
                    current_vav_state = 1
                    last_vav_update = response_time
            else:  # occupied -> unoccupied
                if sensor_name not in non_responsive_standby:
                    # VAV should respond in 1-20 minutes
                    delay = random.uniform(1, 20)
                    response_time = timestamp + timedelta(minutes=delay)
                    # Add VAV data point at minute boundary
                    response_time = response_time.replace(second=0, microsecond=0)
                    vav_data.append((response_time, 0))
                    current_vav_state = 0
                    last_vav_update = response_time

        prev_occupancy = occupancy

        # Add regular VAV status updates every minute (approximately)
        if timestamp >= last_vav_update + timedelta(minutes=1):
            # Add data point at minute boundary
            update_time = timestamp.replace(second=0, microsecond=0)
            vav_data.append((update_time, current_vav_state))
            last_vav_update = update_time

    return vav_data

def main():
    # Generate 30 days of data starting from the existing data's start time
    existing_file = "/Users/urikogan/code/data_validation/SCH-1_data_20250916.csv"
    original_start, _ = get_time_range(existing_file)

    # Start from original start time and generate 30 days
    start_time = original_start
    end_time = start_time + timedelta(days=30)
    duration_hours = 30 * 24  # 30 days * 24 hours

    print(f"Generating mock data from {start_time} to {end_time} ({duration_hours:.1f} hours / 30 days)")

    # Generate sensor mappings and point IDs
    sensors = generate_sensor_mapping()
    point_ids = generate_point_ids(sensors)

    print(f"Generated {len(sensors)} sensor-VAV pairs")

    # Select problematic VAVs (10 random ones with high miss rate)
    all_vavs = list(sensors.values())
    high_miss_vavs = random.sample(all_vavs, 10)

    # Select non-responsive VAVs
    all_sensor_names = list(sensors.keys())
    non_responsive_occupied = random.sample(all_sensor_names, int(len(all_sensor_names) * 0.02))  # 2%
    non_responsive_standby = random.sample(all_sensor_names, int(len(all_sensor_names) * 0.01))   # 1%

    print(f"High miss rate VAVs: {len(high_miss_vavs)}")
    print(f"Non-responsive to occupied: {len(non_responsive_occupied)}")
    print(f"Non-responsive to standby: {len(non_responsive_standby)}")

    # Generate all data
    all_records = []

    for i, (sensor_name, vav_name) in enumerate(sensors.items()):
        if i % 10 == 0:
            print(f"Processing sensor {i+1}/{len(sensors)}: {sensor_name}")

        # Generate occupancy pattern
        occupancy_data = generate_occupancy_pattern(duration_hours)

        # Adjust timestamps to match actual time range
        adjusted_occupancy = []
        for j, (timestamp, value) in enumerate(occupancy_data):
            actual_time = start_time + timedelta(seconds=j * 30)
            if actual_time <= end_time:
                adjusted_occupancy.append((actual_time, value))

        # Generate VAV response data
        vav_data = generate_vav_response(adjusted_occupancy, sensor_name,
                                       non_responsive_occupied, non_responsive_standby)

        # Add occupancy sensor records
        for timestamp, value in adjusted_occupancy:
            if not should_miss_data(sensor_name, high_miss_vavs, is_vav=False):
                record = {
                    'point_id': point_ids[sensor_name],
                    'name': sensor_name,
                    'parent_name': 'R-Zero Gateway 1',
                    'time': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + ' -07:00',
                    'insert_time': (timestamp + timedelta(seconds=2)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + ' -07:00',
                    'value': value
                }
                all_records.append(record)

        # Add VAV records
        for timestamp, value in vav_data:
            if not should_miss_data(vav_name, high_miss_vavs, is_vav=True):
                record = {
                    'point_id': point_ids[vav_name],
                    'name': vav_name,
                    'parent_name': 'Device 1370',
                    'time': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + ' -07:00',
                    'insert_time': (timestamp + timedelta(seconds=2)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + ' -07:00',
                    'value': value
                }
                all_records.append(record)

    # Sort records by timestamp
    all_records.sort(key=lambda x: x['time'])

    print(f"Generated {len(all_records)} total records")

    # Read existing data
    existing_records = []
    with open(existing_file, 'r') as f:
        reader = csv.DictReader(f)
        existing_records = list(reader)

    print(f"Existing records: {len(existing_records)}")

    # Combine and save
    combined_records = existing_records + all_records
    combined_records.sort(key=lambda x: x['time'])

    output_file = "/Users/urikogan/code/data_validation/SCH-1_data_20250916_with_mock.csv"
    with open(output_file, 'w', newline='') as f:
        fieldnames = ['point_id', 'name', 'parent_name', 'time', 'insert_time', 'value']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_records)

    print(f"Saved combined data to {output_file}")
    print(f"Total records: {len(combined_records)}")

    # Print summary of generated sensors
    print("\nGenerated sensor summary:")
    print(f"Floors 2-5: {len(sensors)} sensors")
    print(f"VAV range: BV203-BV{202 + len(sensors)}")
    print(f"Problematic VAVs (10% miss rate): {high_miss_vavs[:5]}...")
    print(f"Non-responsive to occupied (2%): {len(non_responsive_occupied)} sensors")
    print(f"Non-responsive to standby (1%): {len(non_responsive_standby)} sensors")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3

import csv
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_stanford_data():
    filepath = "/Users/urikogan/Library/CloudStorage/GoogleDrive-ukogan@rzero.com/Shared drives/R-Zero Systems/EPD/Product/Projects/2025/Energy/ODCV Pilots/Stanford Children's Health Energy Pilot/Main Campus (Floor 2-5)/stanford_3_room_pilot through_9_24_944am.csv"

    print("=== STANFORD CSV DATA ANALYSIS ===\n")

    sensor_data = defaultdict(list)
    vav_data = defaultdict(list)

    # Read and parse the CSV
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            name = row['name']
            timestamp_str = row['time']
            value = row['value']

            # Parse timestamp
            try:
                timestamp = datetime.strptime(timestamp_str.split('.')[0] + ' ' + timestamp_str.split(' ')[-1],
                                           '%Y-%m-%d %H:%M:%S %z')
            except:
                # Fallback parsing
                timestamp = datetime.strptime(timestamp_str[:19], '%Y-%m-%d %H:%M:%S')

            if 'presence' in name:
                sensor_data[name].append((timestamp, value))
            elif name in ['BV200', 'BV201', 'BV202']:
                vav_data[name].append((timestamp, value))

    # Sort data by timestamp
    for sensor in sensor_data:
        sensor_data[sensor].sort()
    for vav in vav_data:
        vav_data[vav].sort()

    print("SENSOR COUNTS:")
    for sensor, data in sensor_data.items():
        print(f"  {sensor}: {len(data)} records")
        if data:
            print(f"    First: {data[0][0]}")
            print(f"    Last:  {data[-1][0]}")

    print("\nVAV COUNTS:")
    for vav, data in vav_data.items():
        print(f"  {vav}: {len(data)} records")
        if data:
            print(f"    First: {data[0][0]}")
            print(f"    Last:  {data[-1][0]}")

    # Check for gaps in 115-4-01 data
    print("\n=== 115-4-01 DATA ANALYSIS ===")
    if '115-4-01 presence' in sensor_data:
        data = sensor_data['115-4-01 presence']
        print(f"Total records: {len(data)}")

        # Check for large gaps (> 10 minutes)
        gaps = []
        for i in range(1, len(data)):
            time_diff = (data[i][0] - data[i-1][0]).total_seconds() / 60  # minutes
            if time_diff > 10:
                gaps.append((data[i-1][0], data[i][0], time_diff))

        if gaps:
            print(f"\nLarge gaps (>10 min) found: {len(gaps)}")
            for start, end, duration in gaps[:10]:  # Show first 10
                print(f"  Gap: {start} to {end} ({duration:.1f} minutes)")

        # Check data by day
        daily_counts = defaultdict(int)
        for timestamp, _ in data:
            date = timestamp.date()
            daily_counts[date] += 1

        print("\nDaily record counts:")
        for date in sorted(daily_counts.keys()):
            print(f"  {date}: {daily_counts[date]} records")

    # Check data sorting
    print("\n=== DATA SORTING CHECK ===")
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        timestamps = []
        for i, row in enumerate(reader):
            if i > 100:  # Check first 100 records
                break
            try:
                timestamp = datetime.strptime(row['time'].split('.')[0] + ' ' + row['time'].split(' ')[-1],
                                           '%Y-%m-%d %H:%M:%S %z')
                timestamps.append(timestamp)
            except:
                timestamp = datetime.strptime(row['time'][:19], '%Y-%m-%d %H:%M:%S')
                timestamps.append(timestamp)

    sorted_timestamps = sorted(timestamps)
    if timestamps == sorted_timestamps:
        print("✓ Data appears to be sorted chronologically (ascending)")
    elif timestamps == sorted(timestamps, reverse=True):
        print("⚠ Data is sorted in REVERSE chronological order (descending)")
    else:
        print("✗ Data is NOT sorted chronologically")

if __name__ == "__main__":
    analyze_stanford_data()
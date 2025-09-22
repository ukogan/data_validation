#!/usr/bin/env python3
"""
Data Summary Analysis Script
Analyzes CSV files in the data directory to provide:
1. Time period coverage
2. Data points per day per sensor/BV
3. Sensor-BMS response pairing validation
"""

import pandas as pd
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict
import sys

def parse_timestamp(timestamp_str):
    """Parse various timestamp formats found in the data"""
    try:
        # Handle timezone aware timestamps
        if '+' in timestamp_str or '-' in timestamp_str[-6:]:
            # Remove timezone for simpler parsing
            timestamp_str = timestamp_str.rsplit(' ', 1)[0]

        # Try common formats
        for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M']:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        return None
    except:
        return None

def extract_sensor_number(sensor_name):
    """Extract the number part from sensor names like '115-4-01 presence' -> 1"""
    match = re.search(r'115-\d+-(\d+)', sensor_name)
    if match:
        return int(match.group(1))
    return None

def extract_bv_number(bv_name):
    """Extract the number part from BV names like 'BV200' -> 200"""
    match = re.search(r'BV(\d+)', bv_name)
    if match:
        return int(match.group(1))
    return None

def analyze_csv_file(file_path):
    """Analyze a single CSV file"""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {os.path.basename(file_path)}")
    print(f"{'='*60}")

    try:
        # Read CSV file
        df = pd.read_csv(file_path)

        # Basic file info
        print(f"Total rows: {len(df):,}")
        print(f"Columns: {list(df.columns)}")

        if 'time' not in df.columns or 'name' not in df.columns:
            print("ERROR: Required columns 'time' and 'name' not found")
            return None

        # Parse timestamps
        df['parsed_time'] = df['time'].apply(parse_timestamp)
        valid_timestamps = df['parsed_time'].notna()

        if not valid_timestamps.any():
            print("ERROR: No valid timestamps found")
            return None

        df_valid = df[valid_timestamps].copy()
        print(f"Valid timestamp rows: {len(df_valid):,}")

        # Time period analysis
        start_time = df_valid['parsed_time'].min()
        end_time = df_valid['parsed_time'].max()
        duration = end_time - start_time

        print(f"\nTIME PERIOD COVERAGE:")
        print(f"Start: {start_time}")
        print(f"End: {end_time}")
        print(f"Duration: {duration}")
        print(f"Total days: {duration.days + duration.seconds/86400:.2f}")

        # Device type analysis
        sensors = []
        bv_devices = []
        other_devices = []

        unique_names = df_valid['name'].unique()

        for name in unique_names:
            if 'presence' in name and '115-' in name:
                sensors.append(name)
            elif name.startswith('BV'):
                bv_devices.append(name)
            else:
                other_devices.append(name)

        print(f"\nDEVICE BREAKDOWN:")
        print(f"Sensors (115-x-x presence): {len(sensors)}")
        print(f"BV devices: {len(bv_devices)}")
        print(f"Other devices: {len(other_devices)}")

        # Detailed device listings
        if sensors:
            print(f"\nSENSORS FOUND:")
            for sensor in sorted(sensors):
                sensor_num = extract_sensor_number(sensor)
                count = len(df_valid[df_valid['name'] == sensor])
                print(f"  {sensor} (#{sensor_num}) - {count:,} data points")

        if bv_devices:
            print(f"\nBV DEVICES FOUND:")
            for bv in sorted(bv_devices):
                bv_num = extract_bv_number(bv)
                count = len(df_valid[df_valid['name'] == bv])
                print(f"  {bv} (#{bv_num}) - {count:,} data points")

        if other_devices:
            print(f"\nOTHER DEVICES:")
            for device in sorted(other_devices):
                count = len(df_valid[df_valid['name'] == device])
                print(f"  {device} - {count:,} data points")

        # Daily data point analysis
        if duration.days > 0:
            df_valid['date'] = df_valid['parsed_time'].dt.date
            daily_stats = {}

            print(f"\nDAILY DATA POINTS PER DEVICE:")

            for device_name in unique_names:
                device_data = df_valid[df_valid['name'] == device_name]
                daily_counts = device_data.groupby('date').size()

                if len(daily_counts) > 0:
                    avg_per_day = daily_counts.mean()
                    min_per_day = daily_counts.min()
                    max_per_day = daily_counts.max()
                    days_with_data = len(daily_counts)

                    daily_stats[device_name] = {
                        'avg_per_day': avg_per_day,
                        'min_per_day': min_per_day,
                        'max_per_day': max_per_day,
                        'days_with_data': days_with_data,
                        'total_points': len(device_data)
                    }

                    print(f"  {device_name}:")
                    print(f"    Avg/day: {avg_per_day:.1f}, Min: {min_per_day}, Max: {max_per_day}")
                    print(f"    Days with data: {days_with_data}/{duration.days + 1}")

        # Sensor-BV pairing analysis
        print(f"\nSENSOR-BV PAIRING ANALYSIS:")

        sensor_numbers = []
        bv_numbers = []

        for sensor in sensors:
            num = extract_sensor_number(sensor)
            if num is not None:
                sensor_numbers.append(num)

        for bv in bv_devices:
            num = extract_bv_number(bv)
            if num is not None:
                bv_numbers.append(num)

        sensor_numbers = sorted(sensor_numbers)
        bv_numbers = sorted(bv_numbers)

        print(f"Sensor numbers found: {sensor_numbers}")
        print(f"BV numbers found: {bv_numbers}")

        # Expected pairing logic (based on project documentation)
        # Sensor 01 -> BV200, Sensor 06 -> BV201, Sensor 09 -> BV202
        expected_pairs = {
            1: 200,   # 115-4-01 -> BV200
            6: 201,   # 115-4-06 -> BV201
            9: 202    # 115-4-09 -> BV202
        }

        print(f"\nEXPECTED PAIRING VALIDATION:")
        for sensor_num in sensor_numbers:
            if sensor_num in expected_pairs:
                expected_bv = expected_pairs[sensor_num]
                bv_exists = expected_bv in bv_numbers
                status = "✓ PAIRED" if bv_exists else "✗ MISSING BV"
                print(f"  Sensor {sensor_num:02d} -> BV{expected_bv}: {status}")
            else:
                print(f"  Sensor {sensor_num:02d} -> UNKNOWN PAIRING")

        # Check for unpaired BVs
        expected_bv_nums = set(expected_pairs.values())
        unpaired_bvs = [bv for bv in bv_numbers if bv not in expected_bv_nums]
        if unpaired_bvs:
            print(f"\nUNPAIRED BVs: {unpaired_bvs}")

        return {
            'file_path': file_path,
            'total_rows': len(df),
            'valid_rows': len(df_valid),
            'start_time': start_time,
            'end_time': end_time,
            'duration_days': duration.days + duration.seconds/86400,
            'sensors': sensors,
            'bv_devices': bv_devices,
            'sensor_numbers': sensor_numbers,
            'bv_numbers': bv_numbers,
            'daily_stats': daily_stats if duration.days > 0 else {}
        }

    except Exception as e:
        print(f"ERROR analyzing {file_path}: {str(e)}")
        return None

def main():
    """Main analysis function"""
    # Get the target file or analyze all CSV files
    target_file = None
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        if not os.path.exists(target_file):
            # Try in current directory
            target_file = os.path.join('.', target_file)
        if not os.path.exists(target_file):
            print(f"ERROR: File not found: {sys.argv[1]}")
            sys.exit(1)

    print("DATA SUMMARY ANALYSIS")
    print(f"Current directory: {os.getcwd()}")
    print(f"Timestamp: {datetime.now()}")

    if target_file:
        # Analyze single file
        result = analyze_csv_file(target_file)
    else:
        # Analyze all CSV files in current directory
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]

        if not csv_files:
            print("No CSV files found in current directory")
            return

        print(f"\nFound {len(csv_files)} CSV files:")
        for f in csv_files:
            print(f"  {f}")

        results = []
        for csv_file in sorted(csv_files):
            result = analyze_csv_file(csv_file)
            if result:
                results.append(result)

        # Summary comparison
        if len(results) > 1:
            print(f"\n{'='*60}")
            print("CROSS-FILE SUMMARY")
            print(f"{'='*60}")

            for result in results:
                filename = os.path.basename(result['file_path'])
                print(f"\n{filename}:")
                print(f"  Duration: {result['duration_days']:.2f} days")
                print(f"  Sensors: {len(result['sensors'])}")
                print(f"  BV devices: {len(result['bv_devices'])}")
                print(f"  Valid data points: {result['valid_rows']:,}")

if __name__ == "__main__":
    main()
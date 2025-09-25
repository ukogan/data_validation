#!/usr/bin/env python3
"""
Comprehensive Dataset Validation
Validates ALL CSV files in data/ directory against the complete SENSOR_ZONE_MAP
from src/data/config.py to ensure proper sensor-BV pairings exist.
"""

import pandas as pd
import os
import sys
import time
from datetime import datetime

# Add src to path for imports
sys.path.append('src')
from data.config import SENSOR_ZONE_MAP

def parse_timestamp(timestamp_str):
    """Parse various timestamp formats found in the data"""
    try:
        # Handle timezone aware timestamps
        if '+' in timestamp_str or '-' in timestamp_str[-6:]:
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

def analyze_file_pairings(file_path, max_rows=None):
    """Analyze sensor-BV pairings in a single CSV file"""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {os.path.basename(file_path)}")
    print(f"{'='*80}")

    start_time = time.time()

    try:
        # Read CSV with optional row limit for large files
        if max_rows:
            df = pd.read_csv(file_path, nrows=max_rows)
            print(f"Reading first {max_rows:,} rows for large file analysis...")
        else:
            df = pd.read_csv(file_path)

        print(f"Total rows loaded: {len(df):,}")

        if 'name' not in df.columns:
            print("ERROR: 'name' column not found")
            return None

        # Get unique device names
        unique_names = set(df['name'].unique())
        print(f"Unique devices found: {len(unique_names)}")

        # Categorize devices
        sensors_in_file = []
        bvs_in_file = []
        other_devices = []

        for name in unique_names:
            if 'presence' in name and '115-' in name:
                sensors_in_file.append(name)
            elif name.startswith('BV'):
                bvs_in_file.append(name)
            else:
                other_devices.append(name)

        print(f"\nDEVICE BREAKDOWN:")
        print(f"Sensors: {len(sensors_in_file)}")
        print(f"BV devices: {len(bvs_in_file)}")
        print(f"Other devices: {len(other_devices)}")

        # Check against complete SENSOR_ZONE_MAP
        print(f"\nSENSOR-BV PAIRING VALIDATION:")
        print(f"Expected total pairs from config: {len(SENSOR_ZONE_MAP)}")

        found_pairs = []
        missing_sensors = []
        missing_bvs = []
        unpaired_sensors = []
        unpaired_bvs = []

        # Check each expected pairing
        for sensor, expected_bv in SENSOR_ZONE_MAP.items():
            sensor_exists = sensor in sensors_in_file
            bv_exists = expected_bv in bvs_in_file

            if sensor_exists and bv_exists:
                found_pairs.append((sensor, expected_bv))
            elif sensor_exists and not bv_exists:
                missing_bvs.append((sensor, expected_bv))
            elif not sensor_exists and bv_exists:
                missing_sensors.append((sensor, expected_bv))
            else:
                # Both missing - don't report as issue for partial datasets
                pass

        # Check for extra devices not in config
        for sensor in sensors_in_file:
            if sensor not in SENSOR_ZONE_MAP:
                unpaired_sensors.append(sensor)

        for bv in bvs_in_file:
            if bv not in SENSOR_ZONE_MAP.values():
                unpaired_bvs.append(bv)

        # Report results
        print(f"\n✅ COMPLETE PAIRS FOUND: {len(found_pairs)}")
        if found_pairs:
            # Group by floor for better display
            floors = {}
            for sensor, bv in found_pairs:
                floor = sensor.split('-')[1]  # Extract floor number
                if floor not in floors:
                    floors[floor] = []
                floors[floor].append((sensor, bv))

            for floor in sorted(floors.keys()):
                print(f"  Floor {floor}: {len(floors[floor])} pairs")
                if len(floors[floor]) <= 10:  # Show details for small floors
                    for sensor, bv in sorted(floors[floor]):
                        print(f"    {sensor} → {bv}")

        if missing_bvs:
            print(f"\n❌ SENSORS WITHOUT MATCHING BVs: {len(missing_bvs)}")
            for sensor, expected_bv in missing_bvs[:10]:  # Show first 10
                print(f"  {sensor} → missing {expected_bv}")
            if len(missing_bvs) > 10:
                print(f"  ... and {len(missing_bvs) - 10} more")

        if missing_sensors:
            print(f"\n⚠️  BVs WITHOUT MATCHING SENSORS: {len(missing_sensors)}")
            for sensor, bv in missing_sensors[:10]:  # Show first 10
                print(f"  {bv} → missing {sensor}")
            if len(missing_sensors) > 10:
                print(f"  ... and {len(missing_sensors) - 10} more")

        if unpaired_sensors:
            print(f"\n🔍 EXTRA SENSORS (not in config): {len(unpaired_sensors)}")
            for sensor in unpaired_sensors[:10]:
                print(f"  {sensor}")
            if len(unpaired_sensors) > 10:
                print(f"  ... and {len(unpaired_sensors) - 10} more")

        if unpaired_bvs:
            print(f"\n🔍 EXTRA BVs (not in config): {len(unpaired_bvs)}")
            for bv in unpaired_bvs[:10]:
                print(f"  {bv}")
            if len(unpaired_bvs) > 10:
                print(f"  ... and {len(unpaired_bvs) - 10} more")

        # Time analysis if timestamps available
        if 'time' in df.columns:
            df['parsed_time'] = df['time'].apply(parse_timestamp)
            valid_timestamps = df['parsed_time'].notna()

            if valid_timestamps.any():
                df_valid = df[valid_timestamps]
                start_time_data = df_valid['parsed_time'].min()
                end_time_data = df_valid['parsed_time'].max()
                duration = end_time_data - start_time_data

                print(f"\nTIME COVERAGE:")
                print(f"Start: {start_time_data}")
                print(f"End: {end_time_data}")
                print(f"Duration: {duration.days} days, {duration.seconds//3600} hours")

        elapsed = time.time() - start_time
        print(f"\nAnalysis completed in {elapsed:.1f} seconds")

        return {
            'file': os.path.basename(file_path),
            'total_devices': len(unique_names),
            'sensors': len(sensors_in_file),
            'bvs': len(bvs_in_file),
            'complete_pairs': len(found_pairs),
            'missing_bvs': len(missing_bvs),
            'missing_sensors': len(missing_sensors),
            'unpaired_sensors': len(unpaired_sensors),
            'unpaired_bvs': len(unpaired_bvs),
            'analysis_time': elapsed
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None

def main():
    """Validate all CSV files in data directory"""
    print("COMPREHENSIVE DATASET VALIDATION")
    print(f"Configuration: {len(SENSOR_ZONE_MAP)} expected sensor-BV pairs")
    print(f"Expected sensors: 115-2-01 through 115-5-25 presence")
    print(f"Expected BVs: BV200 through BV299")
    print(f"Timestamp: {datetime.now()}")

    data_dir = 'data'
    if not os.path.exists(data_dir):
        print(f"ERROR: {data_dir} directory not found")
        return

    # Find all CSV files
    csv_files = []
    for file in os.listdir(data_dir):
        if file.endswith('.csv'):
            file_path = os.path.join(data_dir, file)
            file_size = os.path.getsize(file_path)
            csv_files.append((file_path, file_size))

    if not csv_files:
        print("No CSV files found in data directory")
        return

    # Sort by file size
    csv_files.sort(key=lambda x: x[1])

    print(f"\nFound {len(csv_files)} CSV files:")
    for file_path, size in csv_files:
        size_mb = size / (1024 * 1024)
        print(f"  {os.path.basename(file_path)} ({size_mb:.1f} MB)")

    # Analyze each file
    results = []
    for file_path, size in csv_files:
        size_mb = size / (1024 * 1024)

        # Use sampling for very large files (>500MB)
        max_rows = None
        if size_mb > 500:
            max_rows = 100000  # Sample first 100k rows
            print(f"\nLarge file detected ({size_mb:.1f} MB) - sampling first {max_rows:,} rows")

        result = analyze_file_pairings(file_path, max_rows)
        if result:
            results.append(result)

    # Summary report
    if len(results) > 1:
        print(f"\n{'='*80}")
        print("SUMMARY REPORT")
        print(f"{'='*80}")

        print(f"{'File':<40} {'Sensors':<8} {'BVs':<6} {'Pairs':<6} {'Missing':<8} {'Time':<6}")
        print("-" * 80)

        total_pairs = 0
        for result in results:
            missing_total = result['missing_bvs'] + result['missing_sensors']
            print(f"{result['file']:<40} {result['sensors']:<8} {result['bvs']:<6} "
                  f"{result['complete_pairs']:<6} {missing_total:<8} {result['analysis_time']:<6.1f}s")
            total_pairs = max(total_pairs, result['complete_pairs'])

        print(f"\nBest dataset: {total_pairs} complete sensor-BV pairs out of {len(SENSOR_ZONE_MAP)} possible")

        if total_pairs == len(SENSOR_ZONE_MAP):
            print("🎉 PERFECT! At least one dataset has all expected sensor-BV pairs!")
        elif total_pairs > 0:
            coverage = (total_pairs / len(SENSOR_ZONE_MAP)) * 100
            print(f"📊 Coverage: {coverage:.1f}% of expected pairs found")
        else:
            print("⚠️  No complete pairs found in any dataset")

if __name__ == "__main__":
    main()
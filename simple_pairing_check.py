#!/usr/bin/env python3
"""
Simple CSV Pairing Validation (No Dependencies)
Checks all CSV files for sensor-BV pairings using only standard library.
"""

import csv
import os
import sys

# Add src to path for imports
sys.path.append('src')
from data.config import SENSOR_ZONE_MAP

def analyze_csv_simple(file_path, max_rows=50000):
    """Analyze CSV file for device names using standard library"""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {os.path.basename(file_path)}")
    print(f"File size: {os.path.getsize(file_path) / (1024*1024):.1f} MB")
    print(f"{'='*60}")

    devices_found = set()
    rows_processed = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            if 'name' not in reader.fieldnames:
                print("ERROR: 'name' column not found")
                return None

            for row in reader:
                if rows_processed >= max_rows:
                    print(f"Reached {max_rows:,} row limit for large file")
                    break

                device_name = row.get('name', '').strip()
                if device_name:
                    devices_found.add(device_name)

                rows_processed += 1

        print(f"Rows processed: {rows_processed:,}")
        print(f"Unique devices: {len(devices_found)}")

        # Categorize devices
        sensors = [d for d in devices_found if 'presence' in d and '115-' in d]
        bvs = [d for d in devices_found if d.startswith('BV')]
        others = [d for d in devices_found if d not in sensors and d not in bvs]

        print(f"\nDEVICE BREAKDOWN:")
        print(f"Sensors: {len(sensors)}")
        print(f"BVs: {len(bvs)}")
        print(f"Others: {len(others)}")

        # Check pairings against config
        complete_pairs = []
        missing_bvs = []
        missing_sensors = []

        for sensor, expected_bv in SENSOR_ZONE_MAP.items():
            sensor_found = sensor in sensors
            bv_found = expected_bv in bvs

            if sensor_found and bv_found:
                complete_pairs.append((sensor, expected_bv))
            elif sensor_found and not bv_found:
                missing_bvs.append((sensor, expected_bv))
            elif not sensor_found and bv_found:
                missing_sensors.append((sensor, expected_bv))

        print(f"\nPAIRING ANALYSIS:")
        print(f"✅ Complete pairs: {len(complete_pairs)}/{len(SENSOR_ZONE_MAP)}")

        if complete_pairs:
            # Group by floor
            floors = {}
            for sensor, bv in complete_pairs:
                floor = sensor.split('-')[1]
                if floor not in floors:
                    floors[floor] = 0
                floors[floor] += 1

            for floor in sorted(floors.keys()):
                print(f"  Floor {floor}: {floors[floor]} pairs")

        if missing_bvs:
            print(f"❌ Sensors without BVs: {len(missing_bvs)}")

        if missing_sensors:
            print(f"⚠️  BVs without sensors: {len(missing_sensors)}")

        # Show some examples of found devices
        if sensors:
            print(f"\nSample sensors found:")
            for sensor in sorted(sensors)[:5]:
                print(f"  {sensor}")
            if len(sensors) > 5:
                print(f"  ... and {len(sensors) - 5} more")

        if bvs:
            print(f"\nSample BVs found:")
            for bv in sorted(bvs)[:5]:
                print(f"  {bv}")
            if len(bvs) > 5:
                print(f"  ... and {len(bvs) - 5} more")

        return {
            'file': os.path.basename(file_path),
            'devices': len(devices_found),
            'sensors': len(sensors),
            'bvs': len(bvs),
            'complete_pairs': len(complete_pairs),
            'rows_processed': rows_processed
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None

def main():
    """Check all CSV files"""
    print("SIMPLE CSV PAIRING VALIDATION")
    print(f"Expected configuration: {len(SENSOR_ZONE_MAP)} sensor-BV pairs")
    print(f"Sensors: 115-2-01 through 115-5-25 presence")
    print(f"BVs: BV200 through BV299")

    # Find CSV files
    data_dir = 'data'
    csv_files = []

    for file in os.listdir(data_dir):
        if file.endswith('.csv'):
            file_path = os.path.join(data_dir, file)
            size = os.path.getsize(file_path)
            csv_files.append((file_path, size))

    csv_files.sort(key=lambda x: x[1])  # Sort by size

    print(f"\nFound {len(csv_files)} CSV files:")
    for file_path, size in csv_files:
        size_mb = size / (1024 * 1024)
        print(f"  {os.path.basename(file_path)} ({size_mb:.1f} MB)")

    # Analyze each file
    results = []
    for file_path, size in csv_files:
        result = analyze_csv_simple(file_path)
        if result:
            results.append(result)

    # Summary
    if results:
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")

        print(f"{'File':<35} {'Devices':<8} {'Sensors':<8} {'BVs':<6} {'Pairs':<6}")
        print("-" * 70)

        best_pairs = 0
        for r in results:
            print(f"{r['file']:<35} {r['devices']:<8} {r['sensors']:<8} {r['bvs']:<6} {r['complete_pairs']:<6}")
            best_pairs = max(best_pairs, r['complete_pairs'])

        coverage = (best_pairs / len(SENSOR_ZONE_MAP)) * 100
        print(f"\nBest coverage: {best_pairs}/{len(SENSOR_ZONE_MAP)} pairs ({coverage:.1f}%)")

        if best_pairs == len(SENSOR_ZONE_MAP):
            print("🎉 PERFECT! Found dataset with ALL expected sensor-BV pairs!")
        elif best_pairs > 50:
            print("👍 Good coverage - sufficient for testing CSV download feature")
        elif best_pairs > 0:
            print("⚠️ Partial coverage - some CSV downloads will work")
        else:
            print("❌ No paired data found")

if __name__ == "__main__":
    main()
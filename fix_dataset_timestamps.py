#!/usr/bin/env python3
"""
Fix the timestamps in our tour datasets to be recent (last 3 days)
so they work with the app's time period filtering
"""

import csv
import uuid
from datetime import datetime, timedelta

def fix_dataset_timestamps(input_file, output_file):
    """Update timestamps to be in the last 3 days"""
    print(f"Fixing timestamps in {input_file}...")

    # Calculate new start date - 3 days ago from now
    now = datetime.now()
    new_start_date = now - timedelta(days=3)

    # Read original dataset to get the time span
    original_start = None
    original_end = None

    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse timestamp (remove timezone)
            time_str = row['time'].split('.')[0].replace(' -0700', '')
            timestamp = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')

            if original_start is None or timestamp < original_start:
                original_start = timestamp
            if original_end is None or timestamp > original_end:
                original_end = timestamp

    # Calculate time offset
    time_offset = new_start_date - original_start
    print(f"  Original timespan: {original_start} to {original_end}")
    print(f"  New timespan: {new_start_date} to {original_end + time_offset}")
    print(f"  Time offset: {time_offset}")

    # Update all timestamps
    row_count = 0
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()

        for row in reader:
            row_count += 1
            if row_count % 10000 == 0:
                print(f"  Processed {row_count} rows...")

            # Parse and update timestamp
            time_str = row['time'].split('.')[0].replace(' -0700', '')
            original_timestamp = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            new_timestamp = original_timestamp + time_offset

            # Update insert_time too
            insert_time_str = row['insert_time'].split('.')[0].replace(' -0700', '')
            original_insert_time = datetime.strptime(insert_time_str, '%Y-%m-%d %H:%M:%S')
            new_insert_time = original_insert_time + time_offset

            # Format new timestamps
            row['time'] = new_timestamp.strftime('%Y-%m-%d %H:%M:%S.000 -0700')
            row['insert_time'] = new_insert_time.strftime('%Y-%m-%d %H:%M:%S.000 -0700')

            writer.writerow(row)

    print(f"  Updated {row_count} rows")
    print(f"  Saved to {output_file}")

def main():
    """Fix timestamps in all tour datasets"""
    datasets = [
        ('tour_dataset_a_perfect_compliance.csv', 'tour_dataset_a_perfect_compliance_fixed.csv'),
        ('tour_dataset_b_timing_violations.csv', 'tour_dataset_b_timing_violations_fixed.csv'),
        ('tour_dataset_c_missing_data.csv', 'tour_dataset_c_missing_data_fixed.csv'),
        ('tour_dataset_d_mixed_performance.csv', 'tour_dataset_d_mixed_performance_fixed.csv')
    ]

    for input_file, output_file in datasets:
        try:
            fix_dataset_timestamps(input_file, output_file)
        except FileNotFoundError:
            print(f"  ❌ File {input_file} not found, skipping...")
        except Exception as e:
            print(f"  ❌ Error fixing {input_file}: {e}")

    print(f"\n✅ Timestamp fixing complete!")

if __name__ == "__main__":
    main()
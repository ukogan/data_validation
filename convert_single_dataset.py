#!/usr/bin/env python3
"""
Convert a single dataset efficiently to the real CSV format
"""

import csv
import uuid
from datetime import datetime, timedelta

def convert_single_dataset_efficiently(input_file, output_file):
    """Convert dataset efficiently using CSV reader/writer"""
    print(f"Converting {input_file} to {output_file}...")

    row_count = 0
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=['point_id', 'name', 'parent_name', 'time', 'insert_time', 'value'])
        writer.writeheader()

        for row in reader:
            row_count += 1
            if row_count % 10000 == 0:
                print(f"  Processed {row_count} rows...")

            # Parse timestamp
            timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')

            # Create formatted timestamp strings
            time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.000 -0700')
            insert_time_str = (timestamp + timedelta(seconds=3)).strftime('%Y-%m-%d %H:%M:%S.000 -0700')

            # Determine parent_name based on sensor type
            if row['type'] == 'sensor':
                parent_name = 'R-Zero Gateway 1'
            else:  # zone
                parent_name = 'Device 1370'

            # Convert zone values to match BMS format
            if row['type'] == 'zone':
                if row['value'] == 'occupied':
                    value = 1
                elif row['value'] == 'standby':
                    value = 0
                else:
                    value = int(float(row['value']))
            else:
                value = int(float(row['value']))

            writer.writerow({
                'point_id': str(uuid.uuid4()),
                'name': row['sensor_name'],
                'parent_name': parent_name,
                'time': time_str,
                'insert_time': insert_time_str,
                'value': value
            })

    print(f"  Converted {row_count} rows")
    print(f"  Saved to {output_file}")

if __name__ == "__main__":
    # Convert just Dataset A first to test
    convert_single_dataset_efficiently('dataset_a_perfect_compliance.csv', 'dataset_a_perfect_compliance_real_format.csv')
#!/usr/bin/env python3
"""
Convert our generated mock datasets to match the real CSV format expected by the app.
Required columns: point_id,name,parent_name,time,insert_time,value
Actually used columns: name,time,value
"""

import pandas as pd
import uuid
from datetime import datetime, timedelta

def convert_dataset_to_real_format(input_file, output_file):
    """Convert our dataset format to the real format"""
    print(f"Converting {input_file} to {output_file}...")

    # Read our generated dataset
    df = pd.read_csv(input_file)
    print(f"  Input shape: {df.shape}")

    # Create new dataframe with required columns
    converted_data = []

    for _, row in df.iterrows():
        # Parse timestamp to datetime
        timestamp = pd.to_datetime(row['timestamp'])

        # Create formatted timestamp strings (matching real data format)
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + ' -0700'  # Pacific timezone
        insert_time_str = (timestamp + timedelta(seconds=3)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + ' -0700'

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
                value = int(row['value'])
        else:
            value = int(row['value'])

        converted_data.append({
            'point_id': str(uuid.uuid4()),
            'name': row['sensor_name'],
            'parent_name': parent_name,
            'time': time_str,
            'insert_time': insert_time_str,
            'value': value
        })

    # Create new dataframe and save
    converted_df = pd.DataFrame(converted_data)
    print(f"  Output shape: {converted_df.shape}")

    # Sort by time as the real data does
    converted_df = converted_df.sort_values('time')

    # Save to CSV
    converted_df.to_csv(output_file, index=False)
    print(f"  Saved to {output_file}")

    # Show sample
    print("  Sample data:")
    print(converted_df.head(3).to_string(index=False))
    print()

def main():
    datasets = [
        ('dataset_a_perfect_compliance.csv', 'dataset_a_perfect_compliance_real_format.csv'),
        ('dataset_b_timing_violations.csv', 'dataset_b_timing_violations_real_format.csv'),
        ('dataset_c_missing_data.csv', 'dataset_c_missing_data_real_format.csv'),
        ('dataset_d_mixed_performance.csv', 'dataset_d_mixed_performance_real_format.csv')
    ]

    for input_file, output_file in datasets:
        try:
            convert_dataset_to_real_format(input_file, output_file)
        except FileNotFoundError:
            print(f"  ❌ File {input_file} not found, skipping...")
        except Exception as e:
            print(f"  ❌ Error converting {input_file}: {e}")

    print("✅ Dataset conversion complete!")

if __name__ == "__main__":
    main()
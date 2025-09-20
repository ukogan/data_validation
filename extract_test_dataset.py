#!/usr/bin/env python3
"""
Extract test dataset from full 30-day dataset
Creates a smaller dataset with first 4 sensors and corresponding BV zones
"""

import pandas as pd
from datetime import datetime

def extract_test_dataset():
    """Extract test dataset with first 4 sensors and BV zones"""

    # Read the full dataset
    print("Reading full 30-day dataset...")
    df = pd.read_csv('SCH-1_data_30_days_mock.csv')

    print(f"Total rows in full dataset: {len(df)}")
    print(f"Unique sensors/zones: {df['name'].nunique()}")

    # Define sensors and corresponding BV zones we want
    target_sensors = [
        '115-2-01 presence',
        '115-2-02 presence',
        '115-2-03 presence',
        '115-2-04 presence'
    ]

    target_bv_zones = [
        'BV200',
        'BV201',
        'BV202',
        'BV203'
    ]

    # Combine all target names
    target_names = target_sensors + target_bv_zones

    print(f"Extracting data for: {target_names}")

    # Filter data for target sensors and BV zones
    filtered_df = df[df['name'].isin(target_names)].copy()

    print(f"Filtered rows: {len(filtered_df)}")
    print(f"Filtered unique names: {filtered_df['name'].nunique()}")
    print(f"Names found: {sorted(filtered_df['name'].unique())}")

    # Sort by time to maintain chronological order
    filtered_df = filtered_df.sort_values('time')

    # Save the extracted dataset
    output_file = 'SCH-1_data_30_days_test_subset.csv'
    filtered_df.to_csv(output_file, index=False)

    print(f"Saved test dataset to: {output_file}")

    # Print summary statistics
    print("\nDataset Summary:")
    print(f"Date range: {filtered_df['time'].min()} to {filtered_df['time'].max()}")
    print(f"Total data points: {len(filtered_df)}")

    print("\nData points per sensor/zone:")
    name_counts = filtered_df['name'].value_counts()
    for name in target_names:
        count = name_counts.get(name, 0)
        print(f"  {name}: {count} points")

    # Verify we have both sensor and BV data
    sensors_found = [name for name in target_sensors if name in filtered_df['name'].unique()]
    bv_zones_found = [name for name in target_bv_zones if name in filtered_df['name'].unique()]

    print(f"\nSensors found: {len(sensors_found)}/4")
    print(f"BV zones found: {len(bv_zones_found)}/4")

    if len(sensors_found) == 4 and len(bv_zones_found) == 4:
        print("✅ Successfully extracted complete test dataset with sensors and BV zones!")
    else:
        print("⚠️ Warning: Missing some sensors or BV zones")
        print(f"Missing sensors: {set(target_sensors) - set(sensors_found)}")
        print(f"Missing BV zones: {set(target_bv_zones) - set(bv_zones_found)}")

if __name__ == "__main__":
    extract_test_dataset()
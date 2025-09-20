#!/usr/bin/env python3
"""
Validate the sensor-zone mapping for the test dataset
"""

import pandas as pd

def validate_test_mapping():
    """Check that the test dataset has proper sensor-zone mappings"""

    # Expected mapping based on automatic alphabetical pairing
    expected_mapping = {
        '115-2-01 presence': 'BV200',
        '115-2-02 presence': 'BV201',
        '115-2-03 presence': 'BV202',
        '115-2-04 presence': 'BV203'
    }

    print("Expected sensor-zone mapping:")
    for sensor, zone in expected_mapping.items():
        print(f"  {sensor} → {zone}")

    # Read the test dataset
    df = pd.read_csv('SCH-1_data_30_days_test_subset.csv')

    # Get unique names
    unique_names = set(df['name'].unique())

    # Check sensors
    sensors_found = []
    for sensor in expected_mapping.keys():
        if sensor in unique_names:
            sensors_found.append(sensor)
        else:
            print(f"❌ Missing sensor: {sensor}")

    # Check BV zones
    bv_zones_found = []
    for bv_zone in expected_mapping.values():
        if bv_zone in unique_names:
            bv_zones_found.append(bv_zone)
        else:
            print(f"❌ Missing BV zone: {bv_zone}")

    print(f"\n✅ Sensors found: {len(sensors_found)}/4")
    print(f"✅ BV zones found: {len(bv_zones_found)}/4")

    if len(sensors_found) == 4 and len(bv_zones_found) == 4:
        print("\n🎯 Test dataset is valid with complete sensor-zone pairs!")
        print("This dataset can be used to validate automatic mapping functionality.")

        # Show data point distribution
        print("\nData point distribution:")
        name_counts = df['name'].value_counts()
        for name in sorted(expected_mapping.keys()) + sorted(expected_mapping.values()):
            count = name_counts.get(name, 0)
            print(f"  {name}: {count:,} points")
    else:
        print("\n⚠️ Test dataset is incomplete - missing sensors or BV zones")

if __name__ == "__main__":
    validate_test_mapping()
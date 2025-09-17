#!/usr/bin/env python3
"""
Filter sensor dump data to match zone data availability period
"""

import csv
from datetime import datetime

def parse_timestamp(ts_str):
    """Parse timestamp string to datetime object"""
    try:
        if 'T' in ts_str:
            return datetime.fromisoformat(ts_str.replace(' -07:00', '-07:00'))
        else:
            ts_clean = ts_str.split('.')[0].split(' -')[0]
            return datetime.strptime(ts_clean, '%Y-%m-%d %H:%M:%S')
    except:
        return None

def main():
    # Zone data is available from 2025-09-10 11:10:00 to 2025-09-12 16:40:00
    start_time = datetime(2025, 9, 10, 11, 10, 0)
    end_time = datetime(2025, 9, 12, 16, 40, 0)

    print(f"Filtering data from {start_time} to {end_time}")

    filtered_count = 0
    total_count = 0

    with open('sensor_dump_202509121643.csv', 'r') as infile, \
         open('sensor_dump_filtered.csv', 'w', newline='') as outfile:

        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()

        for row in reader:
            total_count += 1
            timestamp = parse_timestamp(row['time'])

            if timestamp and start_time <= timestamp <= end_time:
                writer.writerow(row)
                filtered_count += 1

    print(f"Filtered {filtered_count} records out of {total_count} total records")
    print(f"Filtered data saved to: sensor_dump_filtered.csv")

if __name__ == "__main__":
    main()
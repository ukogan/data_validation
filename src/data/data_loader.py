"""
Data loading utilities for ODCV analytics dashboard.
Handles CSV file parsing and timestamp processing.
"""

import csv
from datetime import datetime


def parse_timestamp(ts_str):
    """Parse timestamp string to datetime object"""
    try:
        # Handle timezone format like "2025-09-15 15:49:58.021 -07:00"
        if ' -07:00' in ts_str or ' -08:00' in ts_str:
            # Remove timezone and microseconds for simple parsing
            ts_clean = ts_str.split(' -')[0]
            if '.' in ts_clean:
                ts_clean = ts_clean.split('.')[0]
            return datetime.strptime(ts_clean, '%Y-%m-%d %H:%M:%S')
        elif 'T' in ts_str:
            return datetime.fromisoformat(ts_str.replace(' -07:00', '-07:00'))
        else:
            ts_clean = ts_str.split('.')[0].split(' -')[0]
            return datetime.strptime(ts_clean, '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Failed to parse timestamp: {ts_str}, error: {e}")
        return None


def load_data(filename):
    """Load data from CSV file"""
    data = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp = parse_timestamp(row['time'])
            if timestamp:
                data.append({
                    'name': row['name'].strip('"'),
                    'time': timestamp,
                    'value': float(row['value'])
                })
    return sorted(data, key=lambda x: x['time'])
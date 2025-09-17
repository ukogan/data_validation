#!/usr/bin/env python3
"""
Timeline Visualizer for Occupancy Control System
Creates visual timelines showing sensor occupancy and zone mode transitions

Refactored to use modular architecture for improved maintainability.
"""

import sys
import os
from datetime import datetime

# Import from modular components
from src.data.data_loader import load_data
from src.data.config import SENSOR_ZONE_MAP
from src.analysis.timeline_processor import create_timeline_data
from src.presentation.html_generator import create_html_viewer


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 timeline_visualizer.py <csv_file> [start_time] [duration_hours]")
        print("Examples:")
        print("  python3 timeline_visualizer.py SCH-1_data_20250916.csv")
        print("    (Default: starts at 5pm on 9/15, ~22 hour duration)")
        print("  python3 timeline_visualizer.py SCH-1_data_20250916.csv '2025-09-16 08:00' 8")
        print("  python3 timeline_visualizer.py sensor_dump_filtered.csv '2025-09-11 08:00' 12")
        sys.exit(1)

    filename = sys.argv[1]
    start_time = None
    duration_hours = None

    # Set smart defaults based on filename
    if 'SCH-1' in filename:
        # For recent data, default to 5pm on 9/15 for comprehensive analysis
        start_time = datetime(2025, 9, 15, 17, 0)  # 5pm on 9/15
        duration_hours = 22  # Until ~3pm on 9/16
    else:
        # For other files, use 24 hour default
        duration_hours = 24

    if len(sys.argv) > 2:
        try:
            start_time = datetime.strptime(sys.argv[2], '%Y-%m-%d %H:%M')
        except:
            print("Invalid start time format. Use: YYYY-MM-DD HH:MM")
            sys.exit(1)

    if len(sys.argv) > 3:
        try:
            duration_hours = float(sys.argv[3])
        except:
            print("Invalid duration. Use number of hours.")
            sys.exit(1)

    print(f"Creating enhanced timeline visualization for: {filename}")
    if start_time:
        print(f"Start time: {start_time}")
    print(f"Duration: {duration_hours} hours")

    try:
        data = load_data(filename)
        print(f"Loaded {len(data)} records")

        timeline_data_list = []

        for sensor, zone in SENSOR_ZONE_MAP.items():
            print(f"Creating timeline for {sensor} -> {zone}")
            timeline_data = create_timeline_data(data, sensor, zone, start_time, duration_hours)
            if timeline_data:
                timeline_data_list.append(timeline_data)
            else:
                print(f"  No data found for {sensor} -> {zone}")

        if timeline_data_list:
            output_file = create_html_viewer(timeline_data_list)
            print(f"\\nTimeline viewer created: {output_file}")
            print("Open this file in a web browser to view the interactive timeline.")
        else:
            print("No timeline data created.")

    except Exception as e:
        print(f"Error creating timeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
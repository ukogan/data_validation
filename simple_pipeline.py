#!/usr/bin/env python3
"""
Simple ODCV Pipeline - Always runs the same query
Hardcoded for r0_bacnet_dw.r0_vw_sch1_pilot_since_20250915 view
"""

import os
import sys
from datetime import datetime, timedelta

# Import ODCV modules
from src.data.db_connector import create_connection_from_env
from src.data.data_loader import load_data
from src.analysis.timeline_processor import create_timeline_data
from src.presentation.html_generator import create_html_viewer


def run_sch1_pipeline(start_time=None, duration_hours=24):
    """
    Execute pipeline with hardcoded SCH-1 query

    Args:
        start_time: Analysis start time (optional)
        duration_hours: Duration for analysis window
    """
    print("🏢 Running SCH-1 ODCV Pipeline...")

    # Step 1: Connect to database
    print("🔗 Connecting to database...")
    db = create_connection_from_env()
    if not db or not db.test_connection():
        print("❌ Database connection failed")
        return None
    print("✅ Database connected")

    # Step 2: Execute your specific query
    print("📊 Executing SCH-1 query...")

    query = """
    SELECT point_id, name, parent_name, "time", insert_time, value
    FROM r0_bacnet_dw.r0_vw_sch1_pilot_since_20250915
    ORDER BY "time", name
    """

    # Create temporary CSV file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"sch1_data_{timestamp}.csv"

    try:
        db.query_to_csv(query, csv_path)
        print(f"✅ Data exported to: {csv_path}")
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return None

    # Step 3: Load and process data
    print("⚡ Processing sensor data...")
    data = load_data(csv_path)
    print(f"✅ Loaded {len(data)} sensor readings")

    # Step 4: Create timeline analysis
    timeline_data = create_timeline_data(data, start_time, duration_hours)
    print("✅ Timeline analysis complete")

    # Step 5: Generate dashboard
    print("🎨 Generating dashboard...")
    dashboard_path = f"sch1_dashboard_{timestamp}.html"
    create_html_viewer(timeline_data, dashboard_path)
    print(f"✅ Dashboard created: {dashboard_path}")

    return dashboard_path


def main():
    """Command line interface"""
    start_time = None
    duration_hours = 24

    if len(sys.argv) > 1:
        try:
            start_time = datetime.strptime(sys.argv[1], '%Y-%m-%d %H:%M')
        except:
            print("Invalid start time format. Use: YYYY-MM-DD HH:MM")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            duration_hours = int(sys.argv[2])
        except:
            print("Invalid duration. Must be integer hours.")
            sys.exit(1)

    # Run pipeline
    dashboard_path = run_sch1_pipeline(start_time, duration_hours)

    if dashboard_path:
        print(f"🎉 Pipeline complete! Dashboard: {dashboard_path}")

        # Open dashboard in browser (macOS)
        if sys.platform == "darwin":
            os.system(f"open {dashboard_path}")
    else:
        print("❌ Pipeline failed")
        sys.exit(1)


if __name__ == "__main__":
    print("Usage: python3 simple_pipeline.py [start_time] [duration_hours]")
    print("Examples:")
    print("  python3 simple_pipeline.py")
    print("  python3 simple_pipeline.py '2025-09-16 08:00' 12")
    print("")
    main()
#!/usr/bin/env python3
"""
Automated ODCV Data Pipeline
One-click solution to query database → export CSV → generate dashboard
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Import ODCV modules
from src.data.db_connector import create_connection_from_env, ODCVQueryBuilder
from src.data.data_loader import load_data
from src.analysis.timeline_processor import create_timeline_data
from src.presentation.html_generator import create_html_viewer


class ODCVPipeline:
    """Automated pipeline for ODCV data analysis"""

    def __init__(self):
        self.db_connector = None
        self.temp_csv_path = None

    def setup_database(self) -> bool:
        """Initialize database connection"""
        self.db_connector = create_connection_from_env()
        if not self.db_connector:
            print("❌ Database connection not configured")
            print("Set environment variables: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
            return False

        if not self.db_connector.test_connection():
            print("❌ Database connection failed")
            return False

        print("✅ Database connection established")
        return True

    def query_data(
        self,
        view_name: str,
        start_time: datetime = None,
        end_time: datetime = None,
        duration_hours: int = 24
    ) -> str:
        """
        Query database and export to temporary CSV

        Args:
            view_name: Database view/table name
            start_time: Query start time (defaults to 24h ago)
            end_time: Query end time (defaults to now)
            duration_hours: Duration in hours if start_time not provided

        Returns:
            Path to generated CSV file
        """
        # Set default time range
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=duration_hours)

        print(f"📅 Querying data from {start_time} to {end_time}")

        # Build query
        query = ODCVQueryBuilder.build_sensor_query(
            view_name=view_name,
            start_time=start_time,
            end_time=end_time
        )

        print("🔍 Executing database query...")

        # Create temporary CSV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.temp_csv_path = f"temp_sensor_data_{timestamp}.csv"

        # Execute query and save to CSV
        try:
            params = {
                'start_time': start_time,
                'end_time': end_time
            }
            self.db_connector.query_to_csv(query, self.temp_csv_path, params)
            print(f"✅ Data exported to: {self.temp_csv_path}")
            return self.temp_csv_path

        except Exception as e:
            print(f"❌ Query failed: {e}")
            raise

    def generate_dashboard(self, csv_path: str, start_time: datetime = None, duration_hours: int = None) -> str:
        """
        Generate interactive dashboard from CSV data

        Args:
            csv_path: Path to CSV file
            start_time: Analysis start time
            duration_hours: Analysis duration

        Returns:
            Path to generated HTML dashboard
        """
        print("🔄 Loading and processing data...")

        # Load data using existing ODCV loader
        data = load_data(csv_path)
        print(f"✅ Loaded {len(data)} sensor readings")

        # Create timeline data
        timeline_data = create_timeline_data(data, start_time, duration_hours)
        print("✅ Timeline analysis complete")

        # Generate HTML dashboard
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"automated_dashboard_{timestamp}.html"

        create_html_viewer(timeline_data, output_path)
        print(f"✅ Dashboard created: {output_path}")

        return output_path

    def run_full_pipeline(
        self,
        view_name: str,
        start_time: datetime = None,
        end_time: datetime = None,
        duration_hours: int = 24
    ) -> str:
        """
        Execute complete pipeline: DB query → CSV → Dashboard

        Args:
            view_name: Database view/table name
            start_time: Query start time
            end_time: Query end time
            duration_hours: Duration if start_time not provided

        Returns:
            Path to generated dashboard HTML file
        """
        print("🚀 Starting automated ODCV pipeline...")

        # Step 1: Setup database
        if not self.setup_database():
            sys.exit(1)

        # Step 2: Query and export data
        csv_path = self.query_data(view_name, start_time, end_time, duration_hours)

        # Step 3: Generate dashboard
        dashboard_path = self.generate_dashboard(csv_path, start_time, duration_hours)

        # Step 4: Cleanup (optional - keep CSV for debugging)
        # os.remove(csv_path)

        print(f"🎉 Pipeline complete! Dashboard: {dashboard_path}")
        return dashboard_path

    def cleanup(self):
        """Remove temporary files"""
        if self.temp_csv_path and os.path.exists(self.temp_csv_path):
            os.remove(self.temp_csv_path)
            print(f"🧹 Cleaned up: {self.temp_csv_path}")


def main():
    """Command line interface"""
    if len(sys.argv) < 2:
        print("Usage: python3 automated_pipeline.py <view_name> [start_time] [duration_hours]")
        print("Examples:")
        print("  python3 automated_pipeline.py sensor_data_view")
        print("  python3 automated_pipeline.py sensor_data_view '2025-09-16 08:00' 12")
        print("  python3 automated_pipeline.py bms_readings '2025-09-15 17:00' 22")
        print("")
        print("Environment variables required:")
        print("  DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
        print("  Optional: DB_PORT (default: 5432), DB_TYPE (default: postgresql)")
        sys.exit(1)

    view_name = sys.argv[1]
    start_time = None
    duration_hours = 24

    if len(sys.argv) > 2:
        try:
            start_time = datetime.strptime(sys.argv[2], '%Y-%m-%d %H:%M')
        except:
            print("Invalid start time format. Use: YYYY-MM-DD HH:MM")
            sys.exit(1)

    if len(sys.argv) > 3:
        try:
            duration_hours = int(sys.argv[3])
        except:
            print("Invalid duration. Must be integer hours.")
            sys.exit(1)

    # Run pipeline
    pipeline = ODCVPipeline()
    try:
        dashboard_path = pipeline.run_full_pipeline(view_name, start_time, None, duration_hours)

        # Open dashboard in browser (macOS)
        if sys.platform == "darwin":
            os.system(f"open {dashboard_path}")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)
    finally:
        # Optional cleanup
        # pipeline.cleanup()
        pass


if __name__ == "__main__":
    main()
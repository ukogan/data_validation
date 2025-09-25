#!/usr/bin/env python3
"""
Web server for ODCV Data Pipeline
Provides button-triggered database query and dashboard generation
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Import ODCV pipeline
from automated_pipeline import ODCVPipeline


app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

# Global pipeline instance
pipeline = ODCVPipeline()


@app.route('/')
def index():
    """Serve the main dashboard"""
    return send_file('dashboard.html')

@app.route('/dashboard.html')
def dashboard():
    """Serve the dashboard"""
    return send_file('dashboard.html')


@app.route('/api/test-db')
def test_database_connection():
    """Test database connection endpoint"""
    try:
        success = pipeline.setup_database()
        if success:
            return jsonify({
                'success': True,
                'message': 'Database connection successful'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Database connection failed - check environment variables'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/load-database', methods=['POST'])
def load_database():
    """Load data from database compatible with dashboard API"""
    try:
        data = request.json
        start_time_str = data.get('startTime')
        duration = data.get('duration', 24)

        # Parse start time
        start_time = None
        end_time = None
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('T', ' '))
                from datetime import timedelta
                end_time = start_time + timedelta(hours=duration)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid start time format'
                })

        # Connect to database and execute query
        if not pipeline.setup_database():
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            })

        # Execute the SCH-1 query
        query = """
        SELECT point_id, name, parent_name, "time", insert_time, value
        FROM r0_bacnet_dw.r0_vw_sch1_pilot_since_20250915
        """

        # Add time filtering if specified
        params = {}
        if start_time and end_time:
            query += ' WHERE "time" >= %(start_time)s AND "time" <= %(end_time)s'
            params['start_time'] = start_time
            params['end_time'] = end_time

        query += ' ORDER BY "time", name'

        # Execute query and get raw data
        df = pipeline.db_connector.execute_query(query, params)

        # Create CSV file for the existing pipeline
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"db_export_{timestamp}.csv"

        # Save in format expected by data loader: time, name, value
        output_df = df[['time', 'name', 'value']].copy()
        output_df.to_csv(csv_path, index=False)

        return jsonify({
            'success': True,
            'records_count': len(df),
            'csv_file': csv_path,
            'message': f'Loaded {len(df)} records from database'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/load-dataset', methods=['POST'])
def load_dataset():
    """Compatible endpoint with dashboard's existing API - loads database data"""
    print("🚀 [DEBUG] load_dataset endpoint called!")
    try:
        print("🔍 [DEBUG] Parsing request JSON...")
        data = request.json
        print(f"📝 [DEBUG] Request data: {data}")
        dataset_name = data.get('dataset', 'database')
        print(f"🎯 [DEBUG] Dataset name: {dataset_name}")

        # If requesting database dataset, load from database
        if dataset_name == 'database':
            print("📊 [DEBUG] Loading ALL data from database view since Sept 15, 2025 3PM")

            # Connect to database
            if not pipeline.setup_database():
                return jsonify({
                    'success': False,
                    'error': 'Database connection failed'
                })

            # Execute the SCH-1 query - get ALL data from the view (no time filtering)
            # The view already filters to data since 2025-09-15, so we don't need WHERE clause
            query = """
            SELECT point_id, name, parent_name, "time", insert_time, value
            FROM r0_bacnet_dw.r0_vw_sch1_pilot_since_20250915
            ORDER BY "time", name
            """

            params = {}  # No parameters needed - get all data from view

            # Execute query
            print(f"🔍 Executing database query...")
            df = pipeline.db_connector.execute_query(query, params)
            print(f"✅ Query executed successfully, got {len(df)} records")

            # Create CSV file that the existing system can process
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = f"database_export_{timestamp}.csv"

            # Save in format expected by data loader: time, name, value
            output_df = df[['time', 'name', 'value']].copy()
            output_df.to_csv(csv_path, index=False)
            print(f"📄 CSV file created: {csv_path}")

            # Now run the complete ODCV pipeline
            try:
                # Import the required modules for the full pipeline
                print("📦 Importing ODCV pipeline modules...")
                from src.data.data_loader import load_data
                from src.analysis.timeline_processor import create_timeline_data
                from src.presentation.html_generator import create_html_viewer

                # Process the data through the full pipeline
                print(f"⚡ Processing {len(df)} records through ODCV pipeline...")

                # Load and process data
                print("📊 Loading sensor data...")
                sensor_data = load_data(csv_path)

                # Create timeline analysis - let it auto-detect date range from data
                print("⏱️ Creating timeline analysis...")
                timeline_data = create_timeline_data(sensor_data, None, None)  # Auto-detect from data

                # Generate dashboard
                print("🎨 Generating dashboard...")
                dashboard_path = f"database_dashboard_{timestamp}.html"
                create_html_viewer(timeline_data, dashboard_path)

                print(f"✅ Dashboard generated: {dashboard_path}")

                # Also notify the main server by making a request to upload the data
                import requests
                try:
                    print("📤 Notifying main server...")
                    # Send the CSV data to the main server
                    with open(csv_path, 'rb') as f:
                        files = {'file': (csv_path, f, 'text/csv')}
                        response = requests.post('http://localhost:8000/api/upload', files=files)
                        print(f"📤 Main server notified: {response.status_code}")
                except Exception as notify_error:
                    print(f"⚠️ Could not notify main server: {notify_error}")

                return jsonify({
                    'success': True,
                    'records_count': len(df),
                    'source': 'database',
                    'dashboard_path': dashboard_path,
                    'csv_path': csv_path,
                    'time_range': f'{start_time.strftime("%Y-%m-%d %H:%M")} to {end_time.strftime("%Y-%m-%d %H:%M")}',
                    'message': f'Processed {len(df)} records through full ODCV pipeline'
                })

            except Exception as pipeline_error:
                # If pipeline fails, at least return the CSV data
                print(f"❌ Pipeline processing failed: {pipeline_error}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': True,
                    'records_count': len(df),
                    'source': 'database',
                    'csv_path': csv_path,
                    'warning': f'Data exported but pipeline failed: {str(pipeline_error)}',
                    'time_range': f'{start_time.strftime("%Y-%m-%d %H:%M")} to {end_time.strftime("%Y-%m-%d %H:%M")}',
                    'message': f'Loaded {len(df)} records from database (CSV only)'
                })

        else:
            # For other datasets, return error since we're focusing on database integration
            return jsonify({
                'success': False,
                'error': f'Dataset {dataset_name} not available. Use "database" for live data.'
            })

    except Exception as e:
        print(f"❌ [CRITICAL ERROR] Load dataset failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/dashboard/<filename>')
def serve_dashboard(filename):
    """Serve generated dashboard files"""
    try:
        return send_file(filename)
    except FileNotFoundError:
        return jsonify({
            'error': 'Dashboard file not found'
        }), 404


@app.route('/api/list-dashboards')
def list_dashboards():
    """List available dashboard files"""
    try:
        dashboard_files = []
        for file in os.listdir('.'):
            if file.startswith('automated_dashboard_') and file.endswith('.html'):
                stat = os.stat(file)
                dashboard_files.append({
                    'filename': file,
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'size': stat.st_size
                })

        dashboard_files.sort(key=lambda x: x['created'], reverse=True)

        return jsonify({
            'success': True,
            'dashboards': dashboard_files
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/config')
def get_config():
    """Get current configuration status"""
    env_vars = {
        'DB_HOST': bool(os.getenv('DB_HOST')),
        'DB_NAME': bool(os.getenv('DB_NAME')),
        'DB_USER': bool(os.getenv('DB_USER')),
        'DB_PASSWORD': bool(os.getenv('DB_PASSWORD')),
        'DB_PORT': os.getenv('DB_PORT', '5432'),
        'DB_TYPE': os.getenv('DB_TYPE', 'postgresql')
    }

    all_configured = all([
        env_vars['DB_HOST'],
        env_vars['DB_NAME'],
        env_vars['DB_USER'],
        env_vars['DB_PASSWORD']
    ])

    return jsonify({
        'configured': all_configured,
        'env_vars': env_vars
    })


def check_requirements():
    """Check if all requirements are met"""
    missing_modules = []

    try:
        import pandas
    except ImportError:
        missing_modules.append('pandas')

    try:
        import sqlalchemy
    except ImportError:
        missing_modules.append('sqlalchemy')

    # Check for database drivers
    db_type = os.getenv('DB_TYPE', 'postgresql')
    if db_type == 'postgresql':
        try:
            import psycopg2
        except ImportError:
            missing_modules.append('psycopg2-binary')
    elif db_type == 'mysql':
        try:
            import pymysql
        except ImportError:
            missing_modules.append('pymysql')

    if missing_modules:
        print("⚠️  Missing required Python packages:")
        for module in missing_modules:
            print(f"   pip install {module}")
        print("")

    # Check environment variables
    missing_env = []
    required_env = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    for var in required_env:
        if not os.getenv(var):
            missing_env.append(var)

    if missing_env:
        print("⚠️  Missing required environment variables:")
        for var in missing_env:
            print(f"   export {var}='your_value'")
        print("")

    return len(missing_modules) == 0 and len(missing_env) == 0


if __name__ == '__main__':
    print("🏢 ODCV Data Pipeline Web Server")
    print("=" * 40)

    # Check requirements
    if not check_requirements():
        print("❌ Requirements not met. Please install missing dependencies.")
        exit(1)

    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'

    print(f"🌐 Starting server on http://localhost:{port}")
    print(f"📊 Dashboard interface: http://localhost:{port}")
    print("")

    app.run(host='0.0.0.0', port=port, debug=debug)
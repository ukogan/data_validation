#!/usr/bin/env python3
"""
FastAPI application for ODCV analytics dashboard.
Converts existing modular Python architecture to web API.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import tempfile
import os
from datetime import datetime, timedelta, timezone

# Load environment variables from .env file manually
def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load environment variables
load_env_file()

# Import our existing modules
from src.data.data_loader import load_data, parse_timestamp
from src.data.config import SENSOR_ZONE_MAP, DEFAULT_OCCUPIED_DURATION, DEFAULT_UNOCCUPIED_DURATION
from src.analysis.occupancy_calculator import calculate_occupancy_statistics, calculate_hourly_zone_standby
from src.analysis.violation_detector import calculate_error_rates, detect_timing_deviations
from src.analysis.validations.validation_manager import ValidationManager
from src.presentation.html_generator import create_html_viewer

# Import the regular data loading functions first
from src.data.data_loader import load_data
from src.analysis.timeline_processor import create_timeline_data

# Database integration - deferred imports to avoid startup crashes
# Test if database dependencies are available without importing them
HAS_DATABASE_INTEGRATION = False
DATABASE_IMPORT_ERROR = None
try:
    import pandas  # Test the key dependency
    import sqlalchemy
    import psycopg2
    HAS_DATABASE_INTEGRATION = True
except ImportError as e:
    HAS_DATABASE_INTEGRATION = False
    DATABASE_IMPORT_ERROR = str(e)

# Global placeholders for database-specific imports
ODCVPipeline = None

def _import_database_modules():
    """Import database modules on-demand to avoid startup crashes"""
    global ODCVPipeline, DATABASE_IMPORT_ERROR

    if ODCVPipeline is None:
        try:
            from automated_pipeline import ODCVPipeline as _ODCVPipeline
            ODCVPipeline = _ODCVPipeline
            return True
        except ImportError as e:
            error_msg = f"❌ Failed to import database modules: {e}"
            print(error_msg)
            DATABASE_IMPORT_ERROR = error_msg
            return False
    return True

app = FastAPI(
    title="ODCV Analytics Dashboard API",
    description="Building Management System validation and continuous commissioning",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for Shepherd.js
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models for API
class SensorData(BaseModel):
    name: str
    time: str
    value: float

class AnalysisRequest(BaseModel):
    start_time: Optional[str] = None
    duration_hours: Optional[int] = 24

class DatasetRequest(BaseModel):
    dataset: str

class DashboardMetrics(BaseModel):
    standby_mode_percent: float
    airflow_reduction_percent: float
    correlation_health: Dict[str, int]
    data_quality_percent: float
    sensor_quality_percent: float = 0.0
    bms_quality_percent: float = 0.0

class SensorMetrics(BaseModel):
    sensor_id: str
    zone_id: str
    occupancy_correlation: float
    standby_correlation: float
    total_deviations_count: int
    es_count: int = 0  # Early Standby deviations
    ls_count: int = 0  # Late Standby deviations
    eo_count: int = 0  # Early Occupied deviations
    lo_count: int = 0  # Late Occupied deviations
    performance_level: str
    trend_data: List[float]
    sensor_occupied_percent: float = 0.0
    zone_occupied_percent: float = 0.0
    sensor_unoccupied_percent: float = 0.0
    zone_standby_percent: float = 0.0
    sensor_missing_percent: float = 0.0  # Missing sensor data percentage
    zone_missing_percent: float = 0.0    # Missing zone data percentage
    last_outage_duration: str = "--:--"   # Duration of last outage >5min in HH:MM format
    last_outage_when: str = "None"        # When the last outage occurred (relative time)
    total_mode_changes: int = 0

# Global data storage (in production, use a database)
uploaded_data = []
processed_results = {}

def filter_data_by_period(data, period: str):
    """Filter data to specified time period from current time"""
    if not data:
        return []

    # Use current time as the end point for filtering
    # Check if data contains timezone-aware timestamps
    sample_time = data[0]['time'] if data else datetime.now()
    if sample_time.tzinfo is not None:
        current_time = datetime.now(timezone.utc)
    else:
        current_time = datetime.now()

    # Calculate the start time based on period from current time
    if period == "24h":
        start_time = current_time - timedelta(hours=24)
    elif period == "5d":
        start_time = current_time - timedelta(days=5)
    elif period == "30d":
        start_time = current_time - timedelta(days=30)
    else:
        # Default to 24h if invalid period
        start_time = current_time - timedelta(hours=24)

    print(f"🔍 [FILTER] Period: {period}, filtering from {start_time} to {current_time}")

    # Filter data to the specified time window
    filtered_data = [record for record in data if record['time'] >= start_time]
    print(f"🔍 [FILTER] Filtered {len(data)} records down to {len(filtered_data)} records")

    return filtered_data

def calculate_data_quality(filtered_data, period: str):
    """Calculate data quality based on missing intervals (not duplicate points)"""
    if not filtered_data:
        return {
            'overall_quality': 0.0,
            'sensor_quality': 0.0,
            'bms_quality': 0.0
        }

    # Get actual time range from the data, but don't include future time periods
    timestamps = [record['time'] for record in filtered_data]
    raw_start_time = min(timestamps)
    raw_end_time = max(timestamps)

    # Don't analyze beyond current time to avoid future periods
    current_time = datetime.now()

    # Make sure all timestamps are timezone-naive for comparison
    if raw_start_time.tzinfo is not None:
        start_time = raw_start_time.replace(tzinfo=None)
    else:
        start_time = raw_start_time

    if raw_end_time.tzinfo is not None:
        raw_end_time = raw_end_time.replace(tzinfo=None)

    # Ensure current_time is also timezone-naive for comparison
    if current_time.tzinfo is not None:
        current_time_naive = current_time.replace(tzinfo=None)
    else:
        current_time_naive = current_time

    end_time = min(raw_end_time, current_time_naive)

    # Filter out any future data points - handle timezone-aware timestamps
    filtered_timestamps = []
    for t in timestamps:
        if t.tzinfo is not None:
            t_naive = t.replace(tzinfo=None)
        else:
            t_naive = t
        if t_naive <= current_time:
            filtered_timestamps.append(t_naive)
    if not filtered_timestamps:
        return {
            'overall_quality': 0.0,
            'sensor_quality': 0.0,
            'bms_quality': 0.0
        }

    actual_duration = end_time - start_time

    # Separate sensor and BMS data by device
    sensor_intervals = {}  # sensor_name -> set of 30s interval slots
    bms_intervals = {}     # bms_name -> set of 60s interval slots

    # Process each data point to find which intervals have data
    for record in filtered_data:
        if record['value'] not in [0, 1]:  # Skip invalid values
            continue

        timestamp = record['time']

        # Skip future data points - make sure both are timezone-naive
        if timestamp.tzinfo is not None:
            timestamp_naive = timestamp.replace(tzinfo=None)
        else:
            timestamp_naive = timestamp

        if timestamp_naive > current_time:
            continue

        if 'presence' in record['name']:  # Sensor data (30s intervals)
            # Calculate which 30-second slot this timestamp falls into
            seconds_from_start = (timestamp_naive - start_time).total_seconds()
            interval_slot = int(seconds_from_start // 30)

            if record['name'] not in sensor_intervals:
                sensor_intervals[record['name']] = set()
            sensor_intervals[record['name']].add(interval_slot)

        elif record['name'].startswith('BV'):  # BMS data (60s intervals)
            # Calculate which 60-second slot this timestamp falls into
            seconds_from_start = (timestamp_naive - start_time).total_seconds()
            interval_slot = int(seconds_from_start // 60)

            if record['name'] not in bms_intervals:
                bms_intervals[record['name']] = set()
            bms_intervals[record['name']].add(interval_slot)

    # Calculate total expected intervals
    total_30s_intervals = int(actual_duration.total_seconds() // 30)
    total_60s_intervals = int(actual_duration.total_seconds() // 60)

    # Calculate sensor coverage (% of 30s intervals with data)
    sensor_coverage_rates = []
    for sensor_name in SENSOR_ZONE_MAP.keys():
        if sensor_name in sensor_intervals:
            covered_intervals = len(sensor_intervals[sensor_name])
            coverage_rate = (covered_intervals / total_30s_intervals) * 100 if total_30s_intervals > 0 else 0
            sensor_coverage_rates.append(coverage_rate)
        else:
            sensor_coverage_rates.append(0.0)  # No data for this sensor

    # Calculate BMS coverage (% of 60s intervals with data)
    bms_coverage_rates = []
    for bms_name in set(SENSOR_ZONE_MAP.values()):
        if bms_name in bms_intervals:
            covered_intervals = len(bms_intervals[bms_name])
            coverage_rate = (covered_intervals / total_60s_intervals) * 100 if total_60s_intervals > 0 else 0
            bms_coverage_rates.append(coverage_rate)
        else:
            bms_coverage_rates.append(0.0)  # No data for this BMS

    # Average coverage across all devices
    sensor_quality = sum(sensor_coverage_rates) / len(sensor_coverage_rates) if sensor_coverage_rates else 0
    bms_quality = sum(bms_coverage_rates) / len(bms_coverage_rates) if bms_coverage_rates else 0
    overall_quality = (sensor_quality + bms_quality) / 2

    # Debug logging
    print(f"📊 [DATA QUALITY DEBUG] Period: {period}")
    print(f"   Time span: {actual_duration} ({start_time} to {end_time})")
    print(f"   Total 30s intervals: {total_30s_intervals}, Total 60s intervals: {total_60s_intervals}")
    print(f"   Sensor coverage rates: {[f'{rate:.1f}%' for rate in sensor_coverage_rates]}")
    print(f"   BMS coverage rates: {[f'{rate:.1f}%' for rate in bms_coverage_rates]}")
    print(f"   Average sensor quality: {sensor_quality:.1f}% (% of 30s intervals with data)")
    print(f"   Average BMS quality: {bms_quality:.1f}% (% of 60s intervals with data)")
    print(f"   Overall quality: {overall_quality:.1f}%")

    return {
        'overall_quality': overall_quality,
        'sensor_quality': sensor_quality,
        'bms_quality': bms_quality,
        'total_30s_intervals': total_30s_intervals,
        'total_60s_intervals': total_60s_intervals,
        'sensor_coverage_rates': sensor_coverage_rates,
        'bms_coverage_rates': bms_coverage_rates
    }

def calculate_last_outage(data, sensor_name, zone_name, start_time, end_time, current_time):
    """Calculate the most recent data outage lasting more than 5 minutes"""
    try:
        from datetime import timedelta

        # Dataset validation and logging
        if data:
            earliest_data = min(record['time'] for record in data)
            latest_data = max(record['time'] for record in data)
            dataset_span = latest_data - earliest_data
            dataset_span_hours = dataset_span.total_seconds() / 3600
        else:
            earliest_data = None
            latest_data = None
            dataset_span_hours = 0

        print(f"🔍 [OUTAGE] === DATASET INFO ===")
        print(f"🔍 [OUTAGE] Using dataset: {len(data)} records")
        print(f"🔍 [OUTAGE] Dataset timespan: {earliest_data} to {latest_data} ({dataset_span_hours:.1f}h)")
        print(f"🔍 [OUTAGE] Calculating outage for sensor: {sensor_name}, zone: {zone_name}")
        print(f"🔍 [OUTAGE] Analysis window: {start_time} to {end_time}, current: {current_time}")
        print(f"🔍 [OUTAGE] === END DATASET INFO ===")

        # Normalize timezone-aware datetimes to timezone-naive for consistent comparison
        if start_time.tzinfo is not None:
            start_time_naive = start_time.replace(tzinfo=None)
        else:
            start_time_naive = start_time

        if end_time.tzinfo is not None:
            end_time_naive = end_time.replace(tzinfo=None)
        else:
            end_time_naive = end_time

        if current_time.tzinfo is not None:
            current_time_naive = current_time.replace(tzinfo=None)
        else:
            current_time_naive = current_time

        # Optimize data filtering for Railway performance
        sensor_data = []
        zone_data = []

        # Single pass through data to avoid multiple iterations
        for r in data:
            # Normalize record time to timezone-naive for comparison
            record_time = r['time']
            if record_time.tzinfo is not None:
                record_time_naive = record_time.replace(tzinfo=None)
            else:
                record_time_naive = record_time

            if record_time_naive <= current_time_naive and r['value'] in [0, 1]:
                if r['name'] == sensor_name:
                    # Store the normalized time back in the record for consistency
                    sensor_record = r.copy()
                    sensor_record['time'] = record_time_naive
                    sensor_data.append(sensor_record)
                elif r['name'] == zone_name:
                    zone_record = r.copy()
                    zone_record['time'] = record_time_naive
                    zone_data.append(zone_record)

        print(f"🔍 [OUTAGE] Filtered sensor data: {len(sensor_data)} records")
        print(f"🔍 [OUTAGE] Filtered zone data: {len(zone_data)} records")

        if not sensor_data and not zone_data:
            print(f"❌ [OUTAGE] No data found for sensor/zone combination")
            return "--:--", "None"

        # Combine and sort data points - analyze ALL data in time window for accuracy
        all_data = []
        for record in sensor_data:  # Use ALL sensor data within time window
            all_data.append({'time': record['time'], 'source': 'sensor'})
        for record in zone_data:    # Use ALL zone data within time window
            all_data.append({'time': record['time'], 'source': 'zone'})

        all_data.sort(key=lambda x: x['time'])

        # Find gaps longer than 5 minutes - limit search for performance
        outages = []
        min_outage_duration = timedelta(minutes=5)
        max_outages_to_check = 10  # Only keep track of the 10 most recent outages

        # Check for gaps between consecutive data points
        gaps_found = 0
        large_gaps_found = 0
        print(f"🔍 [OUTAGE] Analyzing ALL {len(all_data)} data points for gaps > 5 minutes...")

        for i in range(1, len(all_data)):  # Analyze ALL data points in time window
            prev_time = all_data[i-1]['time']
            curr_time = all_data[i]['time']
            gap_duration = curr_time - prev_time

            if gap_duration > timedelta(seconds=30):  # Log all gaps > 30 seconds
                gaps_found += 1
                if gaps_found <= 5:  # Only log first 5 gaps to avoid spam
                    print(f"🔍 [OUTAGE] Gap {gaps_found}: {gap_duration} between {prev_time} and {curr_time}")

            if gap_duration > min_outage_duration:
                large_gaps_found += 1
                print(f"🔍 [OUTAGE] OUTAGE FOUND #{large_gaps_found}: {gap_duration} from {prev_time} to {curr_time}")
                outages.append({
                    'start': prev_time,
                    'end': curr_time,
                    'duration': gap_duration
                })

                # Keep only the most recent outages for memory efficiency
                if len(outages) > max_outages_to_check:
                    outages = sorted(outages, key=lambda x: x['start'])[-max_outages_to_check:]

        print(f"🔍 [OUTAGE] Gap analysis complete: {gaps_found} gaps > 30s, {large_gaps_found} outages > 5min")

        # Check for gap at the end (if last data point is far from end_time)
        if all_data:
            try:
                analysis_end_time = min(end_time_naive, current_time_naive)
                last_data_time = all_data[-1]['time']
                final_gap = analysis_end_time - last_data_time

                if final_gap > min_outage_duration:
                    outages.append({
                        'start': last_data_time,
                        'end': analysis_end_time,
                        'duration': final_gap
                    })
            except Exception as e:
                print(f"❌ [OUTAGE] Error calculating final gap: {e}")

        if not outages:
            return "--:--", "None"

        # Find the most recent outage
        most_recent_outage = max(outages, key=lambda x: x['start'])

        # Format duration as HH:MM
        total_minutes = int(most_recent_outage['duration'].total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        duration_str = f"{hours:02d}:{minutes:02d}"

        # Calculate relative time (how long ago the outage started)
        time_since_outage = current_time_naive - most_recent_outage['start']
        if time_since_outage.days > 0:
            when_str = f"{time_since_outage.days}d ago"
        elif time_since_outage.seconds > 3600:
            hours_ago = time_since_outage.seconds // 3600
            when_str = f"{hours_ago}h ago"
        else:
            minutes_ago = time_since_outage.seconds // 60
            when_str = f"{minutes_ago}m ago" if minutes_ago > 0 else "Just now"

        return duration_str, when_str

    except Exception as e:
        print(f"❌ [OUTAGE] Error in calculate_last_outage: {e}")
        return "--:--", "Error"

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard HTML page"""
    try:
        # Serve our custom dashboard.html file
        with open('dashboard.html', 'r') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Dashboard not found</h1><p>Please ensure dashboard.html exists</p>",
            status_code=404
        )

@app.get("/dashboard.html", response_class=HTMLResponse)
async def dashboard_html():
    """Serve the dashboard HTML file"""
    try:
        with open('dashboard.html', 'r') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Dashboard not found</h1><p>Please ensure dashboard.html exists</p>",
            status_code=404
        )

@app.get("/api/health")
async def health_check():
    """Comprehensive health check endpoint with data state validation"""
    timestamp = datetime.now().isoformat()

    # Basic system health
    health_status = {
        "status": "healthy",
        "timestamp": timestamp,
        "system": {
            "api_server": "running",
            "data_loader": "available"
        },
        "data": {
            "loaded": False,
            "records_count": 0,
            "sensors_count": 0,
            "zones_count": 0,
            "mappings_count": 0,
            "time_range": None,
            "issues": []
        },
        "configuration": {
            "sensor_zone_map": len(SENSOR_ZONE_MAP),
            "data_source": "none"
        }
    }

    # Check data state
    if uploaded_data:
        health_status["data"]["loaded"] = True
        health_status["data"]["records_count"] = len(uploaded_data)

        # Count sensors and zones
        sensors = [r['name'] for r in uploaded_data if 'presence' in r['name']]
        zones = [r['name'] for r in uploaded_data if r['name'].startswith('BV')]
        unique_sensors = list(set(sensors))
        unique_zones = list(set(zones))

        health_status["data"]["sensors_count"] = len(unique_sensors)
        health_status["data"]["zones_count"] = len(unique_zones)
        health_status["data"]["mappings_count"] = len(SENSOR_ZONE_MAP)

        # Time range
        if uploaded_data:
            health_status["data"]["time_range"] = {
                "start": uploaded_data[0]['time'].isoformat(),
                "end": uploaded_data[-1]['time'].isoformat()
            }

        # Data validation issues
        issues = []

        # Check for sensor-zone mapping coverage
        unmapped_sensors = [s for s in unique_sensors if s not in SENSOR_ZONE_MAP]
        if unmapped_sensors:
            issues.append(f"{len(unmapped_sensors)} sensors not mapped to zones")

        # Check for orphaned zones
        mapped_zones = list(SENSOR_ZONE_MAP.values())
        orphaned_zones = [z for z in unique_zones if z not in mapped_zones]
        if orphaned_zones:
            issues.append(f"{len(orphaned_zones)} zones not mapped to sensors")

        # Check data quality basics
        if len(unique_sensors) == 0:
            issues.append("No presence sensors found in data")
        if len(unique_zones) == 0:
            issues.append("No BV zones found in data")

        # Check for recent data (within last 7 days)
        if uploaded_data:
            latest_time = uploaded_data[-1]['time']
            days_old = (datetime.now().replace(tzinfo=latest_time.tzinfo) - latest_time).days
            if days_old > 7:
                issues.append(f"Data is {days_old} days old")

        health_status["data"]["issues"] = issues

        # Overall health status
        if issues:
            health_status["status"] = "degraded"
            if len(issues) > 2:
                health_status["status"] = "unhealthy"
    else:
        health_status["status"] = "no_data"
        health_status["data"]["issues"] = ["No data loaded - use dataset selection or upload CSV"]

    return health_status

@app.get("/api/debug/environment")
async def debug_environment():
    """Debug endpoint to check Railway environment and database config"""
    print("🐛 [DEBUG] /api/debug/environment called")

    return {
        "timestamp": datetime.now().isoformat(),
        "environment_variables": {
            "DB_HOST": os.getenv("DB_HOST", "NOT_SET"),
            "DB_PORT": os.getenv("DB_PORT", "NOT_SET"),
            "DB_NAME": os.getenv("DB_NAME", "NOT_SET"),
            "DB_USER": os.getenv("DB_USER", "NOT_SET"),
            "DB_PASSWORD": "SET" if os.getenv("DB_PASSWORD") else "NOT_SET",
            "DB_TYPE": os.getenv("DB_TYPE", "NOT_SET"),
            "PORT": os.getenv("PORT", "NOT_SET"),
        },
        "system_info": {
            "has_database_integration": HAS_DATABASE_INTEGRATION,
            "database_import_error": DATABASE_IMPORT_ERROR,
            "working_directory": os.getcwd(),
            "python_path": os.environ.get("PYTHONPATH", "NOT_SET"),
        },
        "request_info": {
            "message": "If you see this on Railway, the server is running and reachable"
        }
    }

@app.post("/api/debug/test-database")
async def debug_test_database():
    """Test database connection endpoint for Railway debugging"""
    print("🐛 [DEBUG] /api/debug/test-database called")

    if not HAS_DATABASE_INTEGRATION:
        return {
            "status": "error",
            "message": "Database integration not available - missing imports"
        }

    env_vars = {
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("DB_PORT"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": "***" if os.getenv("DB_PASSWORD") else None,
        "DB_TYPE": os.getenv("DB_TYPE"),
    }

    try:
        print("🐛 [DEBUG] Attempting to import database modules...")
        if not _import_database_modules():
            return {
                "status": "error",
                "message": "Failed to import database modules",
                "environment_vars": env_vars,
                "error_type": "ImportError"
            }

        print("🐛 [DEBUG] Attempting to create ODCVPipeline...")
        pipeline = ODCVPipeline()
        print("🐛 [DEBUG] ODCVPipeline created, attempting setup...")
        result = pipeline.setup_database()
        print(f"🐛 [DEBUG] Database setup result: {result}")

        return {
            "status": "success" if result else "failed",
            "message": "Database connection test completed",
            "environment_vars": env_vars,
            "setup_result": result
        }
    except Exception as e:
        print(f"🐛 [DEBUG] Database test failed with error: {e}")
        return {
            "status": "error",
            "message": f"Database test failed: {str(e)}",
            "environment_vars": env_vars,
            "error_type": type(e).__name__
        }

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload and process CSV data file"""
    global uploaded_data, SENSOR_ZONE_MAP

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        # Load data using our existing data loader
        uploaded_data = load_data(tmp_file_path)

        # Auto-generate sensor-zone mapping from the uploaded data
        sensors = [record['name'] for record in uploaded_data if 'presence' in record['name']]
        zones = [record['name'] for record in uploaded_data if record['name'].startswith('BV')]

        # Create mapping: assume sensors and zones are paired by number
        new_sensor_zone_map = {}
        unique_sensors = sorted(list(set(sensors)))
        unique_zones = sorted(list(set(zones)))

        # Map sensors to zones (1:1 mapping by order)
        for i, sensor in enumerate(unique_sensors):
            if i < len(unique_zones):
                new_sensor_zone_map[sensor] = unique_zones[i]

        # Update global mapping
        SENSOR_ZONE_MAP.clear()
        SENSOR_ZONE_MAP.update(new_sensor_zone_map)

        return {
            "message": "File uploaded successfully",
            "records_count": len(uploaded_data),
            "sensors_found": len(unique_sensors),
            "zones_found": len(unique_zones),
            "mappings_created": len(new_sensor_zone_map),
            "time_range": {
                "start": uploaded_data[0]['time'].isoformat() if uploaded_data else None,
                "end": uploaded_data[-1]['time'].isoformat() if uploaded_data else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")
    finally:
        # Clean up temporary file
        os.unlink(tmp_file_path)

@app.post("/api/load-dataset")
async def load_dataset(request: DatasetRequest):
    """Load a preset dataset by name or database data"""
    global uploaded_data, SENSOR_ZONE_MAP

    print(f"🚀 [ENDPOINT] /api/load-dataset called with request: {request}")
    print(f"🚀 [ENDPOINT] Raw request dict: {request.dict() if hasattr(request, 'dict') else 'no dict method'}")

    dataset_key = request.dataset
    print(f"🚀 [ENDPOINT] Extracted dataset_key: '{dataset_key}'")
    print(f"🚀 [ENDPOINT] Dataset key type: {type(dataset_key)}")
    print(f"🚀 [ENDPOINT] HAS_DATABASE_INTEGRATION global: {HAS_DATABASE_INTEGRATION}")

    # Log current environment variables (without password)
    import os
    print(f"🚀 [ENDPOINT] DB_HOST env: {os.environ.get('DB_HOST', 'NOT_SET')}")
    print(f"🚀 [ENDPOINT] DB_PORT env: {os.environ.get('DB_PORT', 'NOT_SET')}")
    print(f"🚀 [ENDPOINT] DB_NAME env: {os.environ.get('DB_NAME', 'NOT_SET')}")
    print(f"🚀 [ENDPOINT] DB_USER env: {os.environ.get('DB_USER', 'NOT_SET')}")
    print(f"🚀 [ENDPOINT] DB_PASSWORD env: {'SET' if os.environ.get('DB_PASSWORD') else 'NOT_SET'}")
    print(f"🚀 [ENDPOINT] DB_TYPE env: {os.environ.get('DB_TYPE', 'NOT_SET')}")
    print(f"🚀 [ENDPOINT] Starting processing for dataset: '{dataset_key}'")

    # Handle database integration
    if dataset_key == "database":
        print(f"🔍 [DATABASE] Processing database dataset request")
        print(f"🔍 [DATABASE] HAS_DATABASE_INTEGRATION: {HAS_DATABASE_INTEGRATION}")

        if not HAS_DATABASE_INTEGRATION:
            print(f"❌ [DATABASE] Database integration not available")
            raise HTTPException(status_code=400, detail="Database integration not available")

        try:
            print(f"🔍 [DATABASE] Starting database integration process...")

            # Check environment variables
            import os
            db_host = os.environ.get('DB_HOST')
            db_port = os.environ.get('DB_PORT')
            db_name = os.environ.get('DB_NAME')
            db_user = os.environ.get('DB_USER')
            print(f"🔍 [DATABASE] Environment variables - Host: {db_host}, Port: {db_port}, DB: {db_name}, User: {db_user}")

            # Import database modules on demand
            print(f"🔍 [DATABASE] Importing database modules...")
            if not _import_database_modules():
                raise HTTPException(status_code=500, detail="Failed to import database modules")

            # Initialize pipeline if not already done
            if not hasattr(load_dataset, 'pipeline'):
                print(f"🔍 [DATABASE] Initializing ODCVPipeline...")
                load_dataset.pipeline = ODCVPipeline()
            else:
                print(f"🔍 [DATABASE] Using existing pipeline")

            # Connect to database
            print(f"🔍 [DATABASE] Setting up database connection...")
            db_setup_result = load_dataset.pipeline.setup_database()
            print(f"🔍 [DATABASE] Database setup result: {db_setup_result}")

            if not db_setup_result:
                print(f"❌ [DATABASE] Database connection failed")
                raise HTTPException(status_code=500, detail="Database connection failed")

            # Execute the SCH-1 query - get ALL data from the view
            query = """
            SELECT point_id, name, parent_name, "time", insert_time, value
            FROM r0_bacnet_dw.r0_vw_sch1_pilot_since_20250915
            ORDER BY "time", name
            """
            print(f"🔍 [DATABASE] Executing query: {query[:100]}...")

            # Execute query
            print(f"🔍 [DATABASE] Calling execute_query...")
            df = load_dataset.pipeline.db_connector.execute_query(query, {})
            print(f"🔍 [DATABASE] Query executed successfully, got {len(df) if df is not None else 'None'} rows")

            if df is None or len(df) == 0:
                print(f"⚠️ [DATABASE] No data returned from query")
                raise HTTPException(status_code=500, detail="No data returned from database query")

            print(f"🔍 [DATABASE] Processing {len(df)} rows into expected format...")
            # Process the data to match expected format
            processed_data = []
            for idx, row in df.iterrows():
                processed_data.append({
                    'time': row['time'],
                    'name': row['name'],
                    'value': row['value']
                })
                if idx < 3:  # Log first few rows
                    print(f"🔍 [DATABASE] Row {idx}: time={row['time']}, name={row['name']}, value={row['value']}")

            print(f"🔍 [DATABASE] Sorting {len(processed_data)} records by time...")
            # Sort by time
            uploaded_data = sorted(processed_data, key=lambda x: x['time'])

            print(f"🔍 [DATABASE] Generating sensor-zone mapping...")
            # Auto-generate sensor-zone mapping from the loaded data
            sensors = [record['name'] for record in uploaded_data if 'presence' in record['name']]
            zones = [record['name'] for record in uploaded_data if record['name'].startswith('BV')]
            print(f"🔍 [DATABASE] Found {len(sensors)} sensors and {len(zones)} zones")

            # Create mapping: assume sensors and zones are paired by number
            new_sensor_zone_map = {}
            unique_sensors = sorted(list(set(sensors)))
            unique_zones = sorted(list(set(zones)))
            print(f"🔍 [DATABASE] Unique sensors: {unique_sensors}")
            print(f"🔍 [DATABASE] Unique zones: {unique_zones}")

            # Map sensors to zones (1:1 mapping by order)
            for i, sensor in enumerate(unique_sensors):
                if i < len(unique_zones):
                    new_sensor_zone_map[sensor] = unique_zones[i]

            print(f"🔍 [DATABASE] Created mapping: {new_sensor_zone_map}")

            # Update global mapping
            SENSOR_ZONE_MAP.clear()
            SENSOR_ZONE_MAP.update(new_sensor_zone_map)
            print(f"🔍 [DATABASE] Updated global SENSOR_ZONE_MAP: {SENSOR_ZONE_MAP}")

            result = {
                "message": f"Database dataset loaded successfully",
                "records_count": len(uploaded_data),
                "sensors_found": len(unique_sensors),
                "zones_found": len(unique_zones),
                "mappings_created": len(new_sensor_zone_map),
                "time_range": {
                    "start": uploaded_data[0]['time'].isoformat() if uploaded_data else None,
                    "end": uploaded_data[-1]['time'].isoformat() if uploaded_data else None
                }
            }
            print(f"✅ [DATABASE] Success! Returning result: {result}")
            return result

        except Exception as e:
            print(f"❌ [DATABASE] Exception occurred: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"❌ [DATABASE] Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Database loading failed: {str(e)}")

    # Handle preset dataset files
    # Define dataset file mappings
    dataset_files = {
        "30_days_mock": "data/SCH-1_data_30_days_mock.csv",
        "5_days_mock": "data/SCH-1_data_5_days_mock.csv",
        "1_day_mock": "data/SCH-1_data_1_day_mock.csv",
        "30_days_sensors_01_04": "data/SCH-1_data_30_days_sensors_01-04.csv",
        "30_days_test_subset": "data/SCH-1_data_30_days_test_subset.csv"
    }

    if dataset_key not in dataset_files:
        raise HTTPException(status_code=400, detail=f"Unknown dataset: {dataset_key}")

    file_path = dataset_files[dataset_key]

    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Dataset file not found: {file_path}")

    try:
        # Load data using our existing data loader
        uploaded_data = load_data(file_path)

        # Auto-generate sensor-zone mapping from the loaded data
        sensors = [record['name'] for record in uploaded_data if 'presence' in record['name']]
        zones = [record['name'] for record in uploaded_data if record['name'].startswith('BV')]

        # Create mapping: assume sensors and zones are paired by number
        new_sensor_zone_map = {}
        unique_sensors = sorted(list(set(sensors)))
        unique_zones = sorted(list(set(zones)))

        # Map sensors to zones (1:1 mapping by order)
        for i, sensor in enumerate(unique_sensors):
            if i < len(unique_zones):
                new_sensor_zone_map[sensor] = unique_zones[i]

        # Update global mapping
        SENSOR_ZONE_MAP.clear()
        SENSOR_ZONE_MAP.update(new_sensor_zone_map)

        return {
            "message": f"Dataset {dataset_key} loaded successfully",
            "records_count": len(uploaded_data),
            "sensors_found": len(unique_sensors),
            "zones_found": len(unique_zones),
            "mappings_created": len(new_sensor_zone_map),
            "time_range": {
                "start": uploaded_data[0]['time'].isoformat() if uploaded_data else None,
                "end": uploaded_data[-1]['time'].isoformat() if uploaded_data else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset: {str(e)}")

@app.get("/api/sensors")
async def get_sensors() -> List[str]:
    """Get list of available sensors"""
    if not uploaded_data:
        return []

    sensors = list(set(record['name'] for record in uploaded_data))
    return sorted(sensors)

@app.get("/api/sensor-zone-map")
async def get_sensor_zone_map() -> Dict[str, str]:
    """Get sensor to zone mapping configuration"""
    return SENSOR_ZONE_MAP

@app.get("/api/dataset-info")
async def get_dataset_info():
    """Get information about the currently loaded dataset"""
    global uploaded_data

    if not uploaded_data:
        return {
            "record_count": 0,
            "earliest_timestamp": None,
            "latest_timestamp": None,
            "data_source": "none",
            "timespan_hours": 0,
            "load_timestamp": None
        }

    print(f"🔍 [DATASET INFO] Analyzing dataset with {len(uploaded_data)} records")

    # Get earliest and latest timestamps
    earliest = min(record['time'] for record in uploaded_data)
    latest = max(record['time'] for record in uploaded_data)

    # Calculate timespan
    timespan = latest - earliest
    timespan_hours = timespan.total_seconds() / 3600

    # Determine data source (check if we're using database or CSV)
    data_source = "database" if os.getenv('DB_HOST') else "csv"

    result = {
        "record_count": len(uploaded_data),
        "earliest_timestamp": earliest.isoformat() if earliest else None,
        "latest_timestamp": latest.isoformat() if latest else None,
        "data_source": data_source,
        "timespan_hours": round(timespan_hours, 1),
        "load_timestamp": datetime.now().isoformat()
    }

    print(f"📊 [DATASET INFO] Dataset spans {timespan_hours:.1f} hours from {earliest} to {latest}")
    return result

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics(period: str = Query("24h", description="Time period: 24h, 5d, or 30d")) -> DashboardMetrics:
    """Get system-wide dashboard metrics"""
    print(f"\n🚀 [BACKEND] Dashboard metrics calculation started for period: {period}")
    print(f"📊 [BACKEND] Total uploaded data records: {len(uploaded_data) if uploaded_data else 0}")

    if not uploaded_data:
        print("❌ [BACKEND] No uploaded data available")
        raise HTTPException(
            status_code=400,
            detail="No data loaded. Please use the dataset selection interface or upload a CSV file before requesting metrics."
        )

    # Filter data by time period
    print(f"🔍 [BACKEND] Filtering data for period: {period}")
    filtered_data = filter_data_by_period(uploaded_data, period)
    print(f"📋 [BACKEND] Filtered data: {len(filtered_data)} records (from {len(uploaded_data)} total)")

    # Calculate metrics using existing analysis modules
    sensors = list(SENSOR_ZONE_MAP.keys())
    print(f"🎯 [BACKEND] Processing {len(sensors)} sensors: {sensors}")
    print(f"🗺️ [BACKEND] Sensor-Zone mappings: {SENSOR_ZONE_MAP}")

    good_correlation = 0
    poor_correlation = 0
    total_standby_time = 0
    total_time = 0

    sensors_processed = 0
    sensors_with_data = 0

    for sensor_name in sensors:
        print(f"\n🔧 [BACKEND] Processing sensor: {sensor_name}")

        sensor_has_data = sensor_name in [r['name'] for r in filtered_data]
        print(f"📡 [BACKEND] Sensor {sensor_name} has data in filtered dataset: {sensor_has_data}")

        if sensor_has_data:
            zone_name = SENSOR_ZONE_MAP[sensor_name]
            print(f"🏢 [BACKEND] Mapped to zone: {zone_name}")

            # Get data for this sensor-zone pair from filtered data
            sensor_data = [r for r in filtered_data if r['name'] == sensor_name]
            zone_data = [r for r in filtered_data if r['name'] == zone_name]

            print(f"📊 [BACKEND] Sensor data records: {len(sensor_data)}")
            print(f"🏢 [BACKEND] Zone data records: {len(zone_data)}")

            if sensor_data and zone_data:
                sensors_with_data += 1
                start_time = min(r['time'] for r in sensor_data + zone_data)
                end_time = max(r['time'] for r in sensor_data + zone_data)
                print(f"⏰ [BACKEND] Time range: {start_time} to {end_time}")

                # Calculate occupancy statistics
                print(f"🧮 [BACKEND] Calculating occupancy statistics for {sensor_name}...")
                stats = calculate_occupancy_statistics(sensor_data, zone_data, start_time, end_time)

                print(f"📈 [BACKEND] Stats for {sensor_name}:")
                print(f"   Zone standby ratio: {stats.get('zone_standby_ratio', 'N/A')}%")
                print(f"   Zone standby time: {stats.get('zone_standby_time', 'N/A')}")
                print(f"   Total duration: {stats.get('total_duration', 'N/A')}")

                # Check correlation
                ratio = stats['zone_standby_ratio']
                if 80 <= ratio <= 120:
                    good_correlation += 1
                    print(f"✅ [BACKEND] Good correlation for {sensor_name} (ratio: {ratio}%)")
                else:
                    poor_correlation += 1
                    print(f"❌ [BACKEND] Poor correlation for {sensor_name} (ratio: {ratio}%)")

                # Accumulate standby time
                standby_seconds = stats['zone_standby_time'].total_seconds()
                duration_seconds = stats['total_duration'].total_seconds()
                total_standby_time += standby_seconds
                total_time += duration_seconds

                print(f"⏱️ [BACKEND] Added {standby_seconds:.2f}s standby / {duration_seconds:.2f}s total")
                print(f"📊 [BACKEND] Running totals: {total_standby_time:.2f}s standby / {total_time:.2f}s total")
            else:
                print(f"❌ [BACKEND] Missing data - sensor_data: {len(sensor_data)}, zone_data: {len(zone_data)}")

        sensors_processed += 1
        print(f"🔄 [BACKEND] Processed {sensors_processed}/{len(sensors)} sensors")

    print(f"\n📊 [BACKEND] CALCULATION SUMMARY:")
    print(f"   Sensors processed: {sensors_processed}")
    print(f"   Sensors with data: {sensors_with_data}")
    print(f"   Good correlations: {good_correlation}")
    print(f"   Poor correlations: {poor_correlation}")
    print(f"   Total standby time: {total_standby_time:.2f} seconds")
    print(f"   Total time: {total_time:.2f} seconds")

    standby_percent = (total_standby_time / total_time * 100) if total_time > 0 else 0
    airflow_percent = standby_percent * 0.75

    print(f"\n🎯 [BACKEND] FINAL CALCULATIONS:")
    print(f"   Standby percentage: {standby_percent:.4f}% ({total_standby_time:.2f}s / {total_time:.2f}s)")
    print(f"   Airflow reduction: {airflow_percent:.4f}% (standby × 0.75)")

    # Calculate real data quality
    print(f"\n🔍 [BACKEND] Calculating data quality...")
    data_quality = calculate_data_quality(filtered_data, period)
    print(f"✅ [BACKEND] Data quality calculated: {data_quality}")

    final_result = DashboardMetrics(
        standby_mode_percent=standby_percent,
        airflow_reduction_percent=airflow_percent,
        correlation_health={"good": good_correlation, "poor": poor_correlation},
        data_quality_percent=data_quality['overall_quality'],
        sensor_quality_percent=data_quality['sensor_quality'],
        bms_quality_percent=data_quality['bms_quality']
    )

    print(f"\n📋 [BACKEND] RETURNING RESULT:")
    print(f"   standby_mode_percent: {final_result.standby_mode_percent}")
    print(f"   airflow_reduction_percent: {final_result.airflow_reduction_percent}")
    print(f"   correlation_health: good={final_result.correlation_health['good']}, poor={final_result.correlation_health['poor']}")
    print(f"   data_quality_percent: {final_result.data_quality_percent}")
    print(f"🏁 [BACKEND] Dashboard metrics calculation completed\n")

    return final_result

@app.get("/api/sensors/metrics")
async def get_sensor_metrics(period: str = Query("24h", description="Time period: 24h, 5d, or 30d")) -> List[SensorMetrics]:
    """Get detailed metrics for all sensors"""

    # Dataset logging for transparency and multiple dataset detection
    if uploaded_data:
        earliest = min(record['time'] for record in uploaded_data)
        latest = max(record['time'] for record in uploaded_data)
        timespan_hours = (latest - earliest).total_seconds() / 3600
        data_source = "database" if os.getenv('DB_HOST') else "csv"
        print(f"📊 [SENSOR_METRICS] Dataset analysis starting - Period: {period}")
        print(f"📊 [SENSOR_METRICS] Dataset info: {len(uploaded_data)} records, {timespan_hours:.1f}h span, source: {data_source}")
        print(f"📊 [SENSOR_METRICS] Timespan: {earliest.isoformat()} to {latest.isoformat()}")
    else:
        print(f"❌ [SENSOR_METRICS] No dataset loaded for analysis")

    if not uploaded_data:
        raise HTTPException(
            status_code=400,
            detail="No data loaded. Please use the dataset selection interface or upload a CSV file before requesting sensor metrics."
        )

    # Filter data by time period
    filtered_data = filter_data_by_period(uploaded_data, period)

    metrics = []
    sensors = list(SENSOR_ZONE_MAP.keys())

    for sensor_name in sensors:
        if sensor_name not in [r['name'] for r in filtered_data]:
            continue

        zone_name = SENSOR_ZONE_MAP[sensor_name]

        # Get data for this sensor-zone pair from filtered data
        sensor_data = [r for r in filtered_data if r['name'] == sensor_name]
        zone_data = [r for r in filtered_data if r['name'] == zone_name]

        if not (sensor_data and zone_data):
            continue

        # Use the filtered time range to ensure missing data percentages are calculated
        # for the selected period only (not the entire dataset timespan)
        filtered_timestamps = [r['time'] for r in filtered_data if r['name'] in [sensor_name, zone_name]]
        if filtered_timestamps:
            filtered_start_time = min(filtered_timestamps)
            filtered_end_time = max(filtered_timestamps)
        else:
            # Fallback if no data in filtered period
            filtered_start_time = datetime.now(timezone.utc) - timedelta(hours=24)
            filtered_end_time = datetime.now(timezone.utc)

        start_time = filtered_start_time
        end_time = filtered_end_time

        # Calculate statistics
        stats = calculate_occupancy_statistics(sensor_data, zone_data, start_time, end_time)

        # Detect deviations
        deviations = detect_spec_deviations_for_sensor(sensor_data, zone_data, start_time, end_time)
        deviation_counts = categorize_deviations(deviations)

        # Calculate error rates to get mode changes data
        error_rates = calculate_error_rates(deviations, zone_data)

        # Determine performance level based on deviations count
        if deviation_counts['total_deviations_count'] == 0:
            performance = 'good'
        elif deviation_counts['total_deviations_count'] <= 2:
            performance = 'fair'
        else:
            performance = 'poor'

        # Generate real hourly zone standby trend data
        zone_data = [r for r in uploaded_data if r['name'] == zone_name]
        if uploaded_data:
            end_time = uploaded_data[-1]['time']  # Use latest timestamp from data
            trend_data = calculate_hourly_zone_standby(zone_data, end_time)
        else:
            trend_data = [0.0] * 24

        # Calculate missing data percentages using same logic as global data quality
        actual_duration = end_time - start_time

        # Don't analyze beyond current time to avoid future periods
        # Use timezone-aware current time if data is timezone-aware (from database)
        if start_time.tzinfo is not None:
            from datetime import timezone
            current_time = datetime.now(timezone.utc)
        else:
            current_time = datetime.now()

        # Make sure both start_time and end_time are timezone-naive for comparison
        if start_time.tzinfo is not None:
            start_time_naive = start_time.replace(tzinfo=None)
        else:
            start_time_naive = start_time

        if end_time.tzinfo is not None:
            end_time_naive = end_time.replace(tzinfo=None)
        else:
            end_time_naive = end_time

        # Make current_time timezone-naive for comparison with end_time_naive
        if current_time.tzinfo is not None:
            current_time_naive = current_time.replace(tzinfo=None)
        else:
            current_time_naive = current_time

        analysis_end_time = min(end_time_naive, current_time_naive)
        actual_analysis_duration = analysis_end_time - start_time_naive

        # Calculate missing percentages using time-based approach (consistent with occupied/standby percentages)
        sensor_missing_percent = 0
        zone_missing_percent = 0

        if actual_analysis_duration.total_seconds() > 0:
            sensor_missing_percent = (stats['sensor_missing_time'].total_seconds() / actual_analysis_duration.total_seconds()) * 100
            zone_missing_percent = (stats['zone_missing_time'].total_seconds() / actual_analysis_duration.total_seconds()) * 100

        # Ensure missing percentages are not negative
        sensor_missing_percent = max(0, sensor_missing_percent)
        zone_missing_percent = max(0, zone_missing_percent)

        # Debug logging for missing data calculation
        print(f"🔍 [MISSING DATA DEBUG] Sensor: {sensor_name}")
        print(f"   Total Duration: {actual_analysis_duration} ({actual_analysis_duration.total_seconds():.0f}s)")
        print(f"   Sensor Data Time: {stats['sensor_occupied_time'] + stats['sensor_unoccupied_time']} ({(stats['sensor_occupied_time'] + stats['sensor_unoccupied_time']).total_seconds():.0f}s)")
        print(f"   Sensor Missing Time: {stats['sensor_missing_time']} ({stats['sensor_missing_time'].total_seconds():.0f}s)")
        print(f"   Sensor missing: {sensor_missing_percent:.1f}%")
        print(f"   Zone Data Time: {stats['zone_occupied_time'] + stats['zone_standby_time']} ({(stats['zone_occupied_time'] + stats['zone_standby_time']).total_seconds():.0f}s)")
        print(f"   Zone Missing Time: {stats['zone_missing_time']} ({stats['zone_missing_time'].total_seconds():.0f}s)")
        print(f"   Zone missing: {zone_missing_percent:.1f}%")
        print(f"   Verification - Sensor Total: {stats['sensor_occupied_percent']:.1f}% + {stats['sensor_unoccupied_percent']:.1f}% + {sensor_missing_percent:.1f}% = {stats['sensor_occupied_percent'] + stats['sensor_unoccupied_percent'] + sensor_missing_percent:.1f}%")
        print(f"   Verification - Zone Total: {stats['zone_occupied_percent']:.1f}% + {stats['zone_standby_percent']:.1f}% + {zone_missing_percent:.1f}% = {stats['zone_occupied_percent'] + stats['zone_standby_percent'] + zone_missing_percent:.1f}%")

        # Calculate last outage information with fallback for Railway performance
        try:
            outage_duration, outage_when = calculate_last_outage(
                uploaded_data, sensor_name, zone_name, start_time, end_time, current_time
            )
            print(f"🔍 [OUTAGE DEBUG] Sensor: {sensor_name}")
            print(f"   Last outage: {outage_duration} ({outage_when})")
        except Exception as e:
            print(f"❌ [OUTAGE] Failed to calculate outage for {sensor_name}: {e}")
            outage_duration, outage_when = "--:--", "Error"

        metrics.append(SensorMetrics(
            sensor_id=sensor_name.replace(' presence', ''),
            zone_id=zone_name,
            occupancy_correlation=stats['zone_occupied_ratio'],
            standby_correlation=stats['zone_standby_ratio'],
            total_deviations_count=deviation_counts['total_deviations_count'],
            es_count=deviation_counts['es_count'],
            ls_count=deviation_counts['ls_count'],
            eo_count=deviation_counts['eo_count'],
            lo_count=deviation_counts['lo_count'],
            performance_level=performance,
            trend_data=trend_data,
            sensor_occupied_percent=stats['sensor_occupied_percent'],
            zone_occupied_percent=stats['zone_occupied_percent'],
            sensor_unoccupied_percent=stats['sensor_unoccupied_percent'],
            zone_standby_percent=stats['zone_standby_percent'],
            sensor_missing_percent=sensor_missing_percent,
            zone_missing_percent=zone_missing_percent,
            last_outage_duration=outage_duration,
            last_outage_when=outage_when,
            total_mode_changes=error_rates['total_mode_changes']
        ))

    return metrics

@app.get("/api/sensors/{sensor_id}/timeline")
async def get_sensor_timeline(
    sensor_id: str,
    start_time: Optional[str] = None,
    duration_hours: Optional[int] = 24
):
    """Get timeline data for a specific sensor"""
    if not uploaded_data:
        raise HTTPException(status_code=404, detail="No data uploaded")

    # Find sensor name
    sensor_name = None
    for name in SENSOR_ZONE_MAP.keys():
        if sensor_id in name:
            sensor_name = name
            break

    if not sensor_name:
        raise HTTPException(status_code=404, detail="Sensor not found")

    zone_name = SENSOR_ZONE_MAP[sensor_name]

    # Get data
    sensor_data = [r for r in uploaded_data if r['name'] == sensor_name]
    zone_data = [r for r in uploaded_data if r['name'] == zone_name]

    if not (sensor_data and zone_data):
        raise HTTPException(status_code=404, detail="No data found for sensor")

    # Filter data by time period if duration_hours is specified
    if duration_hours:
        # Get the latest timestamp from the data
        all_data = sensor_data + zone_data
        if all_data:
            latest_time = max(r['time'] for r in all_data)
            filter_start_time = latest_time - timedelta(hours=duration_hours)

            # Filter data to the specified time window
            sensor_data = [r for r in sensor_data if r['time'] >= filter_start_time]
            zone_data = [r for r in zone_data if r['time'] >= filter_start_time]

    # Process timeline data
    timeline_data = process_timeline_data(sensor_data, zone_data, sensor_name, zone_name)

    return timeline_data

def detect_spec_deviations_for_sensor(sensor_data, zone_data, start_time, end_time):
    """Detect timing deviations for a sensor-zone pair"""
    deviations = []

    # Simple deviation detection
    combined_data = sorted(sensor_data + zone_data, key=lambda x: x['time'])

    current_sensor_state = None
    current_zone_state = None
    last_sensor_change = None

    for record in combined_data:
        if record['name'] in SENSOR_ZONE_MAP:  # Sensor data
            new_sensor_state = int(record['value'])
            # Only update last_sensor_change when sensor state actually changes
            if current_sensor_state != new_sensor_state:
                last_sensor_change = record['time']
            current_sensor_state = new_sensor_state
        else:  # Zone data
            new_zone_state = int(record['value'])

            # Detect deviations using updated deviation logic
            if current_zone_state is not None and current_zone_state != new_zone_state:
                deviations.extend(detect_timing_deviations(
                    combined_data, current_sensor_state, current_zone_state,
                    last_sensor_change, new_zone_state, record['time']
                ))

            current_zone_state = new_zone_state

    return deviations


def categorize_deviations(deviations):
    """Categorize deviations by type"""
    es_count = len([d for d in deviations if d.get('type') == 'early_standby'])
    ls_count = len([d for d in deviations if d.get('type') == 'late_standby'])
    eo_count = len([d for d in deviations if d.get('type') == 'early_occupied'])
    lo_count = len([d for d in deviations if d.get('type') == 'late_occupied'])

    return {
        'es_count': es_count,
        'ls_count': ls_count,
        'eo_count': eo_count,
        'lo_count': lo_count,
        'total_deviations_count': len(deviations)
    }

def process_timeline_data(sensor_data, zone_data, sensor_name, zone_name):
    """Process timeline data for a sensor-zone pair"""
    start_time = min(r['time'] for r in sensor_data + zone_data)
    end_time = max(r['time'] for r in sensor_data + zone_data)

    # Calculate statistics
    stats = calculate_occupancy_statistics(sensor_data, zone_data, start_time, end_time)

    # Process events
    events = []
    for record in sensor_data:
        events.append({
            'timestamp': record['time'].isoformat(),
            'type': 'sensor',
            'value': record['value'],
            'device': sensor_name,
            'description': f"Sensor {'occupied' if record['value'] == 1 else 'unoccupied'}"
        })

    for record in zone_data:
        events.append({
            'timestamp': record['time'].isoformat(),
            'type': 'zone',
            'value': record['value'],
            'device': zone_name,
            'description': f"Zone {'standby' if record['value'] == 1 else 'occupied'} mode"
        })

    # Sort events by timestamp
    events.sort(key=lambda x: x['timestamp'])

    # Detect violations
    violations = detect_spec_deviations_for_sensor(sensor_data, zone_data, start_time, end_time)

    # Calculate error rates
    error_rates = calculate_error_rates(violations, zone_data)

    return {
        'sensor': sensor_name,
        'zone': zone_name,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'events': events,
        'violations': violations,
        'statistics': {
            'sensor_occupied_time': format_duration(stats['sensor_occupied_time']),
            'sensor_unoccupied_time': format_duration(stats['sensor_unoccupied_time']),
            'zone_occupied_time': format_duration(stats['zone_occupied_time']),
            'zone_standby_time': format_duration(stats['zone_standby_time']),
            'zone_occupied_ratio': stats['zone_occupied_ratio'],
            'zone_standby_ratio': stats['zone_standby_ratio'],
            'total_duration': format_duration(stats['total_duration'])
        },
        'error_rates': error_rates,
        'summary': {
            'sensor_events': len(sensor_data),
            'zone_events': len(zone_data),
            'total_events': len(sensor_data) + len(zone_data),
            'violations': len(violations)
        }
    }

def format_duration(timedelta_obj):
    """Format timedelta as human-readable string"""
    total_seconds = int(timedelta_obj.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

@app.get("/api/generate-test-data")
async def generate_test_data(
    sensors: int = Query(100, description="Number of sensors to generate"),
    days: int = Query(30, description="Number of days of data")
):
    """Generate test data for scalability testing"""
    global uploaded_data

    # Generate mock sensor data using SENSOR_ZONE_MAP pattern
    mock_data = []
    base_time = datetime.now() - timedelta(days=days)

    # Update the global SENSOR_ZONE_MAP for test data
    global SENSOR_ZONE_MAP
    test_sensor_zone_map = {}

    buildings = ['115', '116', '117', '118']
    floors = [1, 2, 3, 4]

    for i in range(1, min(sensors, 100) + 1):  # Limit to 100 for reasonable test
        building = buildings[i % len(buildings)]
        floor = floors[i % len(floors)]

        sensor_name = f"{building}-{floor}-{i:02d} presence"
        zone_name = f"BV{200 + i}"

        test_sensor_zone_map[sensor_name] = zone_name

        # Generate time series data
        current_time = base_time
        sensor_state = 0
        zone_state = 1

        while current_time < datetime.now():
            # Add sensor event
            mock_data.append({
                'name': sensor_name,
                'time': current_time,
                'value': float(sensor_state)
            })

            # Add zone event
            mock_data.append({
                'name': zone_name,
                'time': current_time + timedelta(minutes=1),
                'value': float(zone_state)
            })

            # More realistic state changes with some violations
            if current_time.minute % 45 == 0:  # Change every 45 minutes
                sensor_state = 1 - sensor_state
                # Zone should follow with some delay and occasional violations
                if current_time.minute % 90 == 0:  # Occasionally violate timing
                    zone_state = 1 - zone_state  # Immediate change (violation)
                else:
                    # Add proper delay for zone change
                    delay_time = current_time + timedelta(minutes=7 if sensor_state == 1 else 17)
                    mock_data.append({
                        'name': zone_name,
                        'time': delay_time,
                        'value': float(1 - zone_state)
                    })
                    zone_state = 1 - zone_state

            current_time += timedelta(minutes=5)

    # Update the global sensor zone map for this session
    SENSOR_ZONE_MAP.update(test_sensor_zone_map)

    uploaded_data = sorted(mock_data, key=lambda x: x['time'])

    return {
        "message": f"Generated test data for {min(sensors, 100)} sensors over {days} days",
        "records_count": len(uploaded_data),
        "sensors_generated": min(sensors, 100),
        "sensor_zone_pairs": len(test_sensor_zone_map),
        "time_range": {
            "start": uploaded_data[0]['time'].isoformat(),
            "end": uploaded_data[-1]['time'].isoformat()
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
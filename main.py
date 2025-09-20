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
from datetime import datetime, timedelta

# Import our existing modules
from src.data.data_loader import load_data, parse_timestamp
from src.data.config import SENSOR_ZONE_MAP, DEFAULT_OCCUPIED_DURATION, DEFAULT_UNOCCUPIED_DURATION
from src.analysis.occupancy_calculator import calculate_occupancy_statistics, calculate_hourly_zone_standby
from src.analysis.violation_detector import calculate_error_rates, detect_timing_deviations
from src.analysis.validations.validation_manager import ValidationManager
from src.presentation.html_generator import create_html_viewer

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

# Pydantic models for API
class SensorData(BaseModel):
    name: str
    time: str
    value: float

class AnalysisRequest(BaseModel):
    start_time: Optional[str] = None
    duration_hours: Optional[int] = 24

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
    total_mode_changes: int = 0

# Global data storage (in production, use a database)
uploaded_data = []
processed_results = {}

def filter_data_by_period(data, period: str):
    """Filter data to specified time period from the most recent timestamp"""
    if not data:
        return []

    # Find the most recent timestamp in the dataset
    latest_time = max(record['time'] for record in data)

    # Calculate the start time based on period
    if period == "24h":
        start_time = latest_time - timedelta(hours=24)
    elif period == "5d":
        start_time = latest_time - timedelta(days=5)
    elif period == "30d":
        start_time = latest_time - timedelta(days=30)
    else:
        # Default to 24h if invalid period
        start_time = latest_time - timedelta(hours=24)

    # Filter data to the specified time window
    return [record for record in data if record['time'] >= start_time]

def calculate_data_quality(filtered_data, period: str):
    """Calculate data quality based on expected data rates and validity"""
    if not filtered_data:
        return {
            'overall_quality': 0.0,
            'sensor_quality': 0.0,
            'bms_quality': 0.0
        }

    # Calculate expected data points based on time period duration
    if period == "24h":
        hours = 24
    elif period == "5d":
        hours = 5 * 24
    elif period == "30d":
        hours = 30 * 24
    else:
        hours = 24  # Default to 24h

    # Expected totals (2 points/min for sensors, 1 point/min for BMS)
    expected_sensor_points = hours * 120  # 2 per minute
    expected_bms_points = hours * 60      # 1 per minute

    # Count actual valid data points
    valid_sensor_points = 0
    valid_bms_points = 0

    for record in filtered_data:
        # Check if value is valid (0 or 1)
        if record['value'] in [0, 1]:
            if 'presence' in record['name']:  # Sensor data
                valid_sensor_points += 1
            elif record['name'].startswith('BV'):  # BMS/Zone data
                valid_bms_points += 1

    # Calculate quality percentages
    sensor_quality = (valid_sensor_points / expected_sensor_points) * 100 if expected_sensor_points > 0 else 0
    bms_quality = (valid_bms_points / expected_bms_points) * 100 if expected_bms_points > 0 else 0

    # Overall quality (weighted average)
    total_expected = expected_sensor_points + expected_bms_points
    total_valid = valid_sensor_points + valid_bms_points
    overall_quality = (total_valid / total_expected) * 100 if total_expected > 0 else 0

    return {
        'overall_quality': min(100.0, overall_quality),  # Cap at 100%
        'sensor_quality': min(100.0, sensor_quality),
        'bms_quality': min(100.0, bms_quality),
        'valid_sensor_points': valid_sensor_points,
        'expected_sensor_points': expected_sensor_points,
        'valid_bms_points': valid_bms_points,
        'expected_bms_points': expected_bms_points
    }

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
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics(period: str = Query("24h", description="Time period: 24h, 5d, or 30d")) -> DashboardMetrics:
    """Get system-wide dashboard metrics"""
    if not uploaded_data:
        return DashboardMetrics(
            standby_mode_percent=0.0,
            airflow_reduction_percent=0.0,
            correlation_health={"good": 0, "poor": 0},
            data_quality_percent=0.0,
            sensor_quality_percent=0.0,
            bms_quality_percent=0.0
        )

    # Filter data by time period
    filtered_data = filter_data_by_period(uploaded_data, period)

    # Calculate metrics using existing analysis modules
    sensors = list(SENSOR_ZONE_MAP.keys())
    good_correlation = 0
    poor_correlation = 0
    total_standby_time = 0
    total_time = 0

    for sensor_name in sensors:
        if sensor_name in [r['name'] for r in filtered_data]:
            zone_name = SENSOR_ZONE_MAP[sensor_name]

            # Get data for this sensor-zone pair from filtered data
            sensor_data = [r for r in filtered_data if r['name'] == sensor_name]
            zone_data = [r for r in filtered_data if r['name'] == zone_name]

            if sensor_data and zone_data:
                start_time = min(r['time'] for r in sensor_data + zone_data)
                end_time = max(r['time'] for r in sensor_data + zone_data)

                # Calculate occupancy statistics
                stats = calculate_occupancy_statistics(sensor_data, zone_data, start_time, end_time)

                # Check correlation
                if 80 <= stats['zone_standby_ratio'] <= 120:
                    good_correlation += 1
                else:
                    poor_correlation += 1

                # Accumulate standby time
                total_standby_time += stats['zone_standby_time'].total_seconds()
                total_time += stats['total_duration'].total_seconds()

    standby_percent = (total_standby_time / total_time * 100) if total_time > 0 else 0

    # Calculate real data quality
    data_quality = calculate_data_quality(filtered_data, period)

    return DashboardMetrics(
        standby_mode_percent=standby_percent,
        airflow_reduction_percent=standby_percent * 0.75,
        correlation_health={"good": good_correlation, "poor": poor_correlation},
        data_quality_percent=data_quality['overall_quality'],
        sensor_quality_percent=data_quality['sensor_quality'],
        bms_quality_percent=data_quality['bms_quality']
    )

@app.get("/api/sensors/metrics")
async def get_sensor_metrics(period: str = Query("24h", description="Time period: 24h, 5d, or 30d")) -> List[SensorMetrics]:
    """Get detailed metrics for all sensors"""
    if not uploaded_data:
        return []

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

        start_time = min(r['time'] for r in sensor_data + zone_data)
        end_time = max(r['time'] for r in sensor_data + zone_data)

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
            current_sensor_state = int(record['value'])
            last_sensor_change = record['time']
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
    violations = detect_violations_for_sensor(sensor_data, zone_data, start_time, end_time)

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
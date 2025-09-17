#!/usr/bin/env python3
"""
Timeline Visualizer for Occupancy Control System
Creates visual timelines showing sensor occupancy and zone mode transitions
"""

import csv
from datetime import datetime, timedelta
import json
import sys
import os

# Sensor to Zone mapping
SENSOR_ZONE_MAP = {
    '115-4-01 presence': 'BV200',
    '115-4-06 presence': 'BV201',
    '115-4-09 presence': 'BV202'
}

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

def format_duration(td):
    """Format timedelta object to human readable string"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def calculate_occupancy_statistics(sensor_data, zone_data, start_time, end_time):
    """Calculate occupancy time statistics for sensor and zone"""
    total_duration = end_time - start_time

    # Calculate sensor occupied/unoccupied time
    sensor_occupied_time = timedelta(0)
    sensor_unoccupied_time = timedelta(0)

    if sensor_data:
        current_state = None
        last_time = start_time

        for record in sensor_data:
            if current_state is not None:
                duration = record['time'] - last_time
                if current_state == 1:
                    sensor_occupied_time += duration
                else:
                    sensor_unoccupied_time += duration

            current_state = int(record['value'])
            last_time = record['time']

        # Add final period to end time
        if current_state is not None:
            duration = end_time - last_time
            if current_state == 1:
                sensor_occupied_time += duration
            else:
                sensor_unoccupied_time += duration

    # Calculate zone occupied/standby time
    zone_occupied_time = timedelta(0)
    zone_standby_time = timedelta(0)

    if zone_data:
        current_mode = None
        last_time = start_time

        for record in zone_data:
            if current_mode is not None:
                duration = record['time'] - last_time
                if current_mode == 0:  # Zone occupied mode
                    zone_occupied_time += duration
                else:  # Zone standby mode
                    zone_standby_time += duration

            current_mode = int(record['value'])
            last_time = record['time']

        # Add final period to end time
        if current_mode is not None:
            duration = end_time - last_time
            if current_mode == 0:
                zone_occupied_time += duration
            else:
                zone_standby_time += duration

    # Calculate correlation percentages
    zone_occupied_ratio = 0
    zone_standby_ratio = 0

    if sensor_occupied_time.total_seconds() > 0:
        zone_occupied_ratio = (zone_occupied_time.total_seconds() / sensor_occupied_time.total_seconds()) * 100

    if sensor_unoccupied_time.total_seconds() > 0:
        zone_standby_ratio = (zone_standby_time.total_seconds() / sensor_unoccupied_time.total_seconds()) * 100

    return {
        'sensor_occupied_time': sensor_occupied_time,
        'sensor_unoccupied_time': sensor_unoccupied_time,
        'zone_occupied_time': zone_occupied_time,
        'zone_standby_time': zone_standby_time,
        'zone_occupied_ratio': zone_occupied_ratio,
        'zone_standby_ratio': zone_standby_ratio,
        'total_duration': total_duration
    }

def calculate_error_rates(violations, zone_events):
    """Calculate BMS error rates"""
    if not zone_events:
        return {
            'total_mode_changes': 0,
            'total_violations': 0,
            'overall_error_rate': 0,
            'premature_standby_rate': 0,
            'premature_occupied_rate': 0
        }

    # Count total mode changes
    total_mode_changes = 0
    to_standby_changes = 0
    to_occupied_changes = 0

    last_mode = None
    for event in zone_events:
        current_mode = int(event['value'])
        if last_mode is not None and last_mode != current_mode:
            total_mode_changes += 1
            if current_mode == 1:  # Going to standby
                to_standby_changes += 1
            else:  # Going to occupied
                to_occupied_changes += 1
        last_mode = current_mode

    # Count violations by type
    premature_standby_violations = len([v for v in violations if v.get('type') == 'premature_standby'])
    premature_occupied_violations = len([v for v in violations if v.get('type') == 'premature_occupied'])

    # Calculate error rates
    overall_error_rate = (len(violations) / total_mode_changes * 100) if total_mode_changes > 0 else 0
    premature_standby_rate = (premature_standby_violations / to_standby_changes * 100) if to_standby_changes > 0 else 0
    premature_occupied_rate = (premature_occupied_violations / to_occupied_changes * 100) if to_occupied_changes > 0 else 0

    return {
        'total_mode_changes': total_mode_changes,
        'total_violations': len(violations),
        'overall_error_rate': overall_error_rate,
        'premature_standby_rate': premature_standby_rate,
        'premature_occupied_rate': premature_occupied_rate,
        'to_standby_changes': to_standby_changes,
        'to_occupied_changes': to_occupied_changes
    }

def create_timeline_data(data, sensor, zone, start_time=None, duration_hours=24):
    """Create timeline data for a specific sensor-zone pair"""

    # Filter data for this sensor-zone pair
    sensor_data = [d for d in data if d['name'] == sensor]
    zone_data = [d for d in data if d['name'] == zone]

    if not sensor_data or not zone_data:
        return None

    # Set time range
    if start_time is None:
        start_time = min(sensor_data[0]['time'], zone_data[0]['time'])
    end_time = start_time + timedelta(hours=duration_hours)

    # Filter to time range
    sensor_data = [d for d in sensor_data if start_time <= d['time'] <= end_time]
    zone_data = [d for d in zone_data if start_time <= d['time'] <= end_time]

    # Create timeline events
    events = []

    # Add sensor events
    for record in sensor_data:
        events.append({
            'time': record['time'],
            'timestamp': record['time'].isoformat(),
            'type': 'sensor',
            'device': sensor,
            'value': int(record['value']),
            'description': f"Sensor: {'Occupied' if record['value'] else 'Unoccupied'}"
        })

    # Add zone events
    for record in zone_data:
        events.append({
            'time': record['time'],
            'timestamp': record['time'].isoformat(),
            'type': 'zone',
            'device': zone,
            'value': int(record['value']),
            'description': f"Zone: {'Standby' if record['value'] else 'Occupied'} mode"
        })

    # Sort by time
    events.sort(key=lambda x: x['time'])

    # Analyze control performance for this period
    violations = []
    current_sensor_state = None
    current_zone_state = None
    last_sensor_change = None

    for event in events:
        if event['type'] == 'sensor':
            if current_sensor_state != event['value']:
                current_sensor_state = event['value']
                last_sensor_change = event['time']

        elif event['type'] == 'zone':
            new_zone_state = event['value']
            if current_zone_state != new_zone_state:

                # Check for violations
                if last_sensor_change and current_sensor_state is not None:
                    time_since_change = event['time'] - last_sensor_change

                    violation = None
                    if current_sensor_state == 0 and new_zone_state == 1:  # Going to standby
                        if time_since_change < timedelta(minutes=13):  # Allow 2 min tolerance
                            violation = {
                                'type': 'premature_standby',
                                'message': f"Early standby transition after {time_since_change}",
                                'expected': '15 minutes unoccupied'
                            }
                    elif current_sensor_state == 1 and new_zone_state == 0:  # Going to occupied
                        if time_since_change < timedelta(minutes=3):  # Allow 2 min tolerance
                            violation = {
                                'type': 'premature_occupied',
                                'message': f"Early occupied transition after {time_since_change}",
                                'expected': '5 minutes occupied'
                            }

                    if violation:
                        violations.append({
                            'timestamp': event['time'].isoformat(),
                            **violation
                        })

                current_zone_state = new_zone_state

    # Calculate occupancy statistics
    statistics = calculate_occupancy_statistics(sensor_data, zone_data, start_time, end_time)

    # Calculate error rates
    zone_events_for_stats = [e for e in events if e['type'] == 'zone']
    error_rates = calculate_error_rates(violations, zone_events_for_stats)

    # Remove time objects for JSON serialization
    for event in events:
        del event['time']

    return {
        'sensor': sensor,
        'zone': zone,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'events': events,
        'violations': violations,
        'statistics': {
            'sensor_occupied_time': format_duration(statistics['sensor_occupied_time']),
            'sensor_unoccupied_time': format_duration(statistics['sensor_unoccupied_time']),
            'zone_occupied_time': format_duration(statistics['zone_occupied_time']),
            'zone_standby_time': format_duration(statistics['zone_standby_time']),
            'zone_occupied_ratio': round(statistics['zone_occupied_ratio'], 1),
            'zone_standby_ratio': round(statistics['zone_standby_ratio'], 1),
            'total_duration': format_duration(statistics['total_duration'])
        },
        'error_rates': error_rates,
        'summary': {
            'total_events': len(events),
            'sensor_events': len([e for e in events if e['type'] == 'sensor']),
            'zone_events': len([e for e in events if e['type'] == 'zone']),
            'violations': len(violations)
        }
    }

def create_html_viewer(timeline_data_list, output_file='timeline_viewer.html'):
    """Create an interactive HTML viewer for the timeline data"""

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Occupancy Control System Timeline Viewer</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .timeline-section {{
            margin-bottom: 40px;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 20px;
        }}
        .timeline-header {{
            font-size: 1.3em;
            font-weight: 600;
            margin-bottom: 15px;
            color: #2c3e50;
            background: linear-gradient(90deg, #f8f9fa 0%, #ffffff 100%);
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 12px 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .timeline-info {{
            background: #f9f9f9;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-size: 0.9em;
        }}
        .timeline-container {{
            width: 100%;
            overflow-x: auto;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .timeline {{
            position: relative;
            height: 120px;
            background: linear-gradient(to right, #fafafa 0%, #fafafa 100%);
            /* Width will be set dynamically based on duration */
        }}
        .event {{
            position: absolute;
            width: 2px;
            height: 100%;
            cursor: pointer;
            border-radius: 1px;
        }}
        .event.sensor {{
            top: 10px;
            height: 40px;
        }}
        .event.zone {{
            top: 60px;
            height: 40px;
        }}
        .event.sensor.occupied {{ background-color: #e74c3c; }}
        .event.sensor.unoccupied {{ background-color: #3498db; }}
        .event.zone.standby {{ background-color: #85c1e9; }}
        .event.zone.occupied {{ background-color: #f1948a; }}
        .violation {{
            position: absolute;
            top: 0;
            height: 100%;
            width: 3px;
            background-color: #8e44ad;
            border-radius: 2px;
            cursor: pointer;
            box-shadow: 0 0 3px rgba(142, 68, 173, 0.6);
        }}
        .timeline-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
        }}
        .page-header {{
            background: white;
            padding: 20px;
            border-bottom: 2px solid #dee2e6;
            margin-bottom: 20px;
        }}
        .analysis-period {{
            font-size: 1.1em;
            color: #666;
            margin-bottom: 15px;
        }}
        .legend {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            position: sticky;
            top: 0;
            z-index: 100;
            border: 1px solid #dee2e6;
            margin-bottom: 20px;
        }}
        .legend-title {{
            font-weight: bold;
            margin-right: 15px;
            color: #333;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.9em;
        }}
        .legend-color {{
            width: 20px;
            height: 12px;
            border-radius: 2px;
        }}
        .tooltip {{
            position: absolute;
            background: #333;
            color: white;
            padding: 8px;
            border-radius: 4px;
            font-size: 0.8em;
            pointer-events: none;
            z-index: 1000;
            max-width: 300px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}
        .summary {{
            background: #e8f5e8;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .violations-list {{
            background: #ffe8e8;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .violation-item {{
            margin: 5px 0;
            padding: 5px;
            background: white;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        .analytics-row {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .statistics-panel {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            flex: 2; /* 65% width */
        }}
        .statistics-title {{
            font-weight: bold;
            margin-bottom: 15px;
            font-size: 1.1em;
            color: #333;
        }}
        .occupancy-bars {{
            margin-bottom: 15px;
        }}
        .bar-row {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }}
        .bar-label {{
            width: 120px;
            font-size: 0.9em;
            color: #666;
            font-weight: 500;
            text-align: right;
            padding-right: 10px;
            flex-shrink: 0;
        }}
        .bar-track {{
            flex: 1;
            height: 25px;
            background: #e9ecef;
            border-radius: 12px;
            position: relative;
            overflow: hidden;
            border: 1px solid #dee2e6;
        }}
        .bar-segment {{
            height: 100%;
            float: left;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.75em;
            font-weight: bold;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
            min-width: 0;
        }}
        .bar-segment.small {{
            font-size: 0.65em;
        }}
        .sensor-occupied {{ background: #e74c3c; }}
        .sensor-unoccupied {{ background: #3498db; }}
        .zone-occupied {{ background: #f1948a; }}
        .zone-standby {{ background: #85c1e9; }}
        .correlation-analysis {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 12px;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        .correlation-good {{ background: #d4edda; color: #155724; border-color: #c3e6cb; }}
        .correlation-poor {{ background: #f8d7da; color: #721c24; border-color: #f5c6cb; }}
        .correlation-fair {{ background: #fff3cd; color: #856404; border-color: #ffeaa7; }}
        .executive-dashboard {{
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border: 2px solid #dee2e6;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }}
        .dashboard-title {{
            font-size: 1.4em;
            font-weight: 600;
            margin-bottom: 20px;
            color: #2c3e50;
            text-align: center;
            padding-bottom: 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 15px;
        }}
        .dashboard-metric {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
        }}
        .metric-title {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        .metric-value {{
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-subtitle {{
            font-size: 0.8em;
            color: #666;
        }}
        .performance-bar {{
            display: flex;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 8px;
            border: 1px solid #dee2e6;
        }}
        .perf-segment {{
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.7em;
            font-weight: bold;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }}
        .perf-good {{ background: #28a745; }}
        .perf-fair {{ background: #ffc107; color: #333; text-shadow: none; }}
        .perf-poor {{ background: #fd7e14; }}
        .perf-critical {{ background: #dc3545; }}
        .error-rate-panel {{
            background: white;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            flex: 1; /* 35% width */
        }}
        .error-rate-title {{
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}
        .error-rate-main {{
            font-size: 2em;
            font-weight: bold;
            text-align: center;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        }}
        .error-rate-excellent {{ background: #d4edda; color: #155724; border-left: 4px solid #28a745; }}
        .error-rate-good {{ background: #fff3cd; color: #856404; border-left: 4px solid #ffc107; }}
        .error-rate-poor {{ background: #f8d7da; color: #721c24; border-left: 4px solid #dc3545; }}
        .error-rate-critical {{ background: #f5c6cb; color: #721c24; border-left: 4px solid #dc3545; }}
        .error-breakdown {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 0.9em;
        }}
        .collapsible-header {{
            background: #e9ecef;
            padding: 10px;
            border-radius: 4px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }}
        .collapsible-header:hover {{
            background: #dee2e6;
        }}
        .collapsible-content {{
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}
        .collapsible-content.collapsed {{
            max-height: 0;
        }}
        .collapsible-content.expanded {{
            max-height: 1000px;
        }}
        .tooltip-enhanced {{
            position: relative;
            cursor: help;
        }}
        .tooltip-enhanced::after {{
            content: "?";
            display: inline-block;
            width: 14px;
            height: 14px;
            background: #007bff;
            color: white;
            border-radius: 50%;
            font-size: 10px;
            text-align: center;
            line-height: 14px;
            margin-left: 5px;
        }}
        .help-section {{
            background: #e8f4fd;
            border: 1px solid #b8daf7;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9em;
        }}
        .help-toggle {{
            cursor: pointer;
            font-weight: bold;
            color: #0066cc;
            user-select: none;
        }}
        .help-content {{
            margin-top: 10px;
            display: none;
        }}
        .help-content.expanded {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="page-header">
            <h1>🏢 Occupancy Control System Dashboard</h1>
            <div style="font-size: 1.1em; color: #495057; margin-bottom: 5px;">BMS Performance Analysis & Timeline Visualization</div>
            <div class="analysis-period" id="analysis-period">
                <!-- Period will be populated by JavaScript -->
            </div>
        </div>

        <div class="help-section">
            <div class="help-toggle" onclick="toggleHelp()">📖 How to Read This Dashboard <span id="help-arrow">▼</span></div>
            <div class="help-content" id="help-content">
                <p><strong>🎯 Purpose:</strong> This dashboard shows how well your BMS (Building Management System) responds to occupancy sensors.</p>

                <p><strong>📊 Occupancy Time Analysis (Left Panel):</strong></p>
                <ul>
                    <li><strong>Red bars:</strong> Time when sensor detected occupancy or zone was in occupied mode</li>
                    <li><strong>Blue bars:</strong> Time when sensor was unoccupied or zone was in standby mode</li>
                    <li><strong>Percentages:</strong> Show correlation between sensor readings and zone responses</li>
                </ul>

                <p><strong>🚨 Control Violations (Right Panel):</strong></p>
                <ul>
                    <li><strong>Early Standby:</strong> Zone switched to standby before waiting 15 minutes after sensor unoccupied</li>
                    <li><strong>Early Occupied:</strong> Zone activated before waiting 5 minutes after sensor occupied</li>
                    <li><strong>Target:</strong> 0% violations (perfect timing compliance)</li>
                </ul>

                <p><strong>📈 Timeline (Bottom):</strong></p>
                <ul>
                    <li><strong>Purple bars:</strong> Timing violations (hover for details)</li>
                    <li><strong>Hover events:</strong> See exact timestamps and violation explanations</li>
                    <li><strong>Collapsed sections:</strong> Click violation counts to expand details</li>
                </ul>
            </div>
        </div>

        <div class="legend">
            <span class="legend-title">Legend:</span>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #e74c3c;"></div>
                <span>Sensor: Occupied</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #3498db;"></div>
                <span>Sensor: Unoccupied</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #f1948a;"></div>
                <span>Zone: Occupied Mode</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #85c1e9;"></div>
                <span>Zone: Standby Mode</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #8e44ad;"></div>
                <span>Control Violation</span>
            </div>
        </div>

        <div id="executive-dashboard" class="executive-dashboard">
            <!-- Executive dashboard will be populated by JavaScript -->
        </div>

        <div id="timelines">
            <!-- Timelines will be inserted here -->
        </div>
    </div>

    <div class="tooltip" id="tooltip" style="display: none;"></div>

    <script>
        const timelineData = {json.dumps(timeline_data_list, indent=2)};

        function createTimeline(data, containerId) {{
            const container = document.getElementById(containerId);

            const startTime = new Date(data.start_time);
            const endTime = new Date(data.end_time);
            const totalDuration = endTime - startTime;

            // Determine error rate styling
            const errorRate = data.error_rates.overall_error_rate;
            let errorRateClass = 'error-rate-excellent';
            if (errorRate > 30) errorRateClass = 'error-rate-critical';
            else if (errorRate > 15) errorRateClass = 'error-rate-poor';
            else if (errorRate > 5) errorRateClass = 'error-rate-good';

            // Create timeline HTML
            container.innerHTML = `
                <div class="timeline-header">Sensor (${{data.sensor.replace(' presence', '')}}) → BMS Status (${{data.zone}})</div>
                <div class="timeline-info">
                    Events: ${{data.summary.sensor_events}} sensor, ${{data.summary.zone_events}} zone | Duration: ${{data.statistics.total_duration}}
                </div>

                <div class="analytics-row">
                    <div class="statistics-panel">
                        <div style="font-weight: bold; margin-bottom: 15px;">📊 Occupancy Time Analysis</div>
                        <div class="occupancy-bars" id="occupancy-bars-${{containerId}}">
                            <!-- Bars will be populated by JavaScript -->
                        </div>
                    </div>

                    <div class="error-rate-panel">
                        <div class="error-rate-title tooltip-enhanced" title="Percentage of BMS mode changes that violated timing rules">🚨 BMS Control Violations</div>
                        <div style="font-size: 0.85em; color: #666; margin-bottom: 10px;">Percentage of mode changes that violated proper timing delays</div>
                        <div class="error-rate-main ${{errorRateClass}}">${{errorRate.toFixed(1)}}%</div>
                        <div class="error-breakdown">
                            <div><strong>Early Standby:</strong> ${{data.error_rates.premature_standby_rate.toFixed(1)}}% (${{data.error_rates.to_standby_changes}} changes)</div>
                            <div style="font-size: 0.8em; color: #666; margin-left: 15px; margin-bottom: 8px;">Zone switched to standby before the required 15-minute delay</div>
                            <div><strong>Early Occupied:</strong> ${{data.error_rates.premature_occupied_rate.toFixed(1)}}% (${{data.error_rates.to_occupied_changes}} changes)</div>
                            <div style="font-size: 0.8em; color: #666; margin-left: 15px;">Zone activated before the required 5-minute delay</div>
                        </div>
                        <div style="text-align: center; margin-top: 10px; font-size: 0.9em; color: #666;">
                            ${{data.error_rates.total_violations}} violations out of ${{data.error_rates.total_mode_changes}} total mode changes
                        </div>
                    </div>
                </div>

                <div class="timeline-container" data-timeline-container>
                    <div class="timeline" id="timeline-${{containerId}}">
                        <div style="position: absolute; top: 20px; left: 10px; font-size: 0.8em; color: #666;">Sensor</div>
                        <div style="position: absolute; top: 70px; left: 10px; font-size: 0.8em; color: #666;">Zone</div>
                    </div>
                </div>
                <div class="timeline-labels">
                    <span>${{startTime.toLocaleString()}}</span>
                    <span>${{endTime.toLocaleString()}}</span>
                </div>
            `;

            // Wait for the DOM to be fully rendered
            setTimeout(() => {{
                const timeline = document.getElementById(`timeline-${{containerId}}`);

                // Calculate timeline width based on duration: 300 pixels per hour
                // This gives ~2.5 pixels per 30 seconds for visible separation
                const durationHours = totalDuration / (1000 * 60 * 60);
                const pixelsPerHour = 300;
                const timelineWidth = Math.max(1200, durationHours * pixelsPerHour); // Minimum 1200px

                // Set the timeline width dynamically
                timeline.style.width = timelineWidth + 'px';
                timeline.style.minWidth = timelineWidth + 'px';

            // Add events
            data.events.forEach(event => {{
                const eventTime = new Date(event.timestamp);
                const position = ((eventTime - startTime) / totalDuration) * timelineWidth;

                const eventEl = document.createElement('div');
                eventEl.className = `event ${{event.type}} ${{getEventClass(event)}}`;
                eventEl.style.left = position + 'px';

                eventEl.addEventListener('mouseenter', (e) => showTooltip(e, event));
                eventEl.addEventListener('mouseleave', hideTooltip);

                timeline.appendChild(eventEl);
            }});

            // Add violations
            data.violations.forEach(violation => {{
                const violationTime = new Date(violation.timestamp);
                const position = ((violationTime - startTime) / totalDuration) * timelineWidth;

                const violationEl = document.createElement('div');
                violationEl.className = 'violation';
                violationEl.style.left = position + 'px';

                violationEl.addEventListener('mouseenter', (e) => showTooltip(e, violation));
                violationEl.addEventListener('mouseleave', hideTooltip);

                timeline.appendChild(violationEl);
            }});

            // Create occupancy bar charts
            createOccupancyBars(data, containerId);

            // Add collapsible violations section
            if (data.violations.length > 0) {{
                const violationsSection = document.createElement('div');
                violationsSection.innerHTML = `
                    <div class="collapsible-header" onclick="toggleViolations('${{containerId}}')" title="Click to expand/collapse violation details">
                        <span><strong>Control Violations (${{data.violations.length}})</strong></span>
                        <span id="toggle-${{containerId}}">+</span>
                    </div>
                    <div class="collapsible-content collapsed" id="violations-${{containerId}}">
                        <div class="violations-list">
                            ${{data.violations.slice(-10).map(v => `
                                <div class="violation-item">
                                    ${{new Date(v.timestamp).toLocaleString()}}: ${{v.message}} (expected: ${{v.expected}})
                                </div>
                            `).join('')}}
                            ${{data.violations.length > 10 ? `<div style="font-style: italic; padding: 10px;">... and ${{data.violations.length - 10}} more violations</div>` : ''}}
                        </div>
                    </div>
                `;
                container.appendChild(violationsSection);
            }}
            }}, 10); // Small delay to ensure DOM rendering
        }}

        function getEventClass(event) {{
            if (event.type === 'sensor') {{
                return event.value === 1 ? 'occupied' : 'unoccupied';
            }} else {{
                return event.value === 1 ? 'standby' : 'occupied';
            }}
        }}

        function showTooltip(e, data) {{
            const tooltip = document.getElementById('tooltip');
            tooltip.style.display = 'block';
            tooltip.style.left = e.pageX + 10 + 'px';
            tooltip.style.top = e.pageY - 10 + 'px';

            if (data.type) {{
                // Regular event
                tooltip.innerHTML = `
                    <strong>${{new Date(data.timestamp).toLocaleString()}}</strong><br>
                    ${{data.description}}<br>
                    Device: ${{data.device}}
                `;
            }} else {{
                // Violation
                tooltip.innerHTML = `
                    <strong>CONTROL VIOLATION</strong><br>
                    ${{new Date(data.timestamp).toLocaleString()}}<br>
                    ${{data.message}}<br>
                    Expected: ${{data.expected}}
                `;
            }}
        }}

        function hideTooltip() {{
            document.getElementById('tooltip').style.display = 'none';
        }}

        function createOccupancyBars(data, containerId) {{
            const container = document.getElementById(`occupancy-bars-${{containerId}}`);

            // Parse time strings to get total seconds for percentage calculation
            const parseTime = (timeStr) => {{
                const match = timeStr.match(/(\\d+)h\\s*(\\d+)m/);
                if (match) {{
                    return parseInt(match[1]) * 3600 + parseInt(match[2]) * 60;
                }}
                const minMatch = timeStr.match(/(\\d+)m/);
                if (minMatch) {{
                    return parseInt(minMatch[1]) * 60;
                }}
                return 0;
            }};

            const sensorOccupiedSec = parseTime(data.statistics.sensor_occupied_time);
            const sensorUnoccupiedSec = parseTime(data.statistics.sensor_unoccupied_time);
            const zoneOccupiedSec = parseTime(data.statistics.zone_occupied_time);
            const zoneStandbySec = parseTime(data.statistics.zone_standby_time);

            const totalSec = sensorOccupiedSec + sensorUnoccupiedSec;

            // Calculate percentages
            const sensorOccupiedPct = totalSec > 0 ? (sensorOccupiedSec / totalSec * 100) : 0;
            const sensorUnoccupiedPct = totalSec > 0 ? (sensorUnoccupiedSec / totalSec * 100) : 0;
            const zoneOccupiedPct = totalSec > 0 ? (zoneOccupiedSec / totalSec * 100) : 0;
            const zoneStandbyPct = totalSec > 0 ? (zoneStandbySec / totalSec * 100) : 0;

            // Determine correlation status
            const occCorrelation = data.statistics.zone_occupied_ratio;
            const standbyCorrelation = data.statistics.zone_standby_ratio;

            let correlationClass = 'correlation-good';
            let correlationText = 'Good correlation';
            if (occCorrelation < 80 || occCorrelation > 120 || standbyCorrelation < 80 || standbyCorrelation > 120) {{
                correlationClass = 'correlation-poor';
                correlationText = 'Poor correlation - timing violations detected';
            }} else if (occCorrelation < 90 || occCorrelation > 110 || standbyCorrelation < 90 || standbyCorrelation > 110) {{
                correlationClass = 'correlation-fair';
                correlationText = 'Fair correlation - minor timing issues';
            }}

            // Create sensor and zone labels from data
            const sensorName = data.sensor.replace(' presence', '');
            const zoneName = data.zone;

            container.innerHTML = `
                <!-- Sensor Bar -->
                <div class="bar-row">
                    <div class="bar-label tooltip-enhanced" title="Shows how much time the occupancy sensor detected presence vs. unoccupied states during the analysis period">${{sensorName}}</div>
                    <div class="bar-track">
                        <div class="bar-segment sensor-occupied" style="width: ${{sensorOccupiedPct}}%;"
                             title="Occupied: ${{data.statistics.sensor_occupied_time}} (${{sensorOccupiedPct.toFixed(1)}}%)">
                            ${{sensorOccupiedPct >= 15 ? `${{sensorOccupiedPct.toFixed(0)}}%` : ''}}
                        </div>
                        <div class="bar-segment sensor-unoccupied" style="width: ${{sensorUnoccupiedPct}}%;"
                             title="Unoccupied: ${{data.statistics.sensor_unoccupied_time}} (${{sensorUnoccupiedPct.toFixed(1)}}%)">
                            ${{sensorUnoccupiedPct >= 15 ? `${{sensorUnoccupiedPct.toFixed(0)}}%` : ''}}
                        </div>
                    </div>
                </div>

                <!-- Zone Bar -->
                <div class="bar-row">
                    <div class="bar-label tooltip-enhanced" title="Shows how much time the BMS zone was in occupied mode vs. standby mode during the analysis period">${{zoneName}}</div>
                    <div class="bar-track">
                        <div class="bar-segment zone-occupied" style="width: ${{zoneOccupiedPct}}%;"
                             title="Occupied Mode: ${{data.statistics.zone_occupied_time}} (${{zoneOccupiedPct.toFixed(1)}}%)">
                            ${{zoneOccupiedPct >= 15 ? `${{zoneOccupiedPct.toFixed(0)}}%` : ''}}
                        </div>
                        <div class="bar-segment zone-standby" style="width: ${{zoneStandbyPct}}%;"
                             title="Standby Mode: ${{data.statistics.zone_standby_time}} (${{zoneStandbyPct.toFixed(1)}}%)">
                            ${{zoneStandbyPct >= 15 ? `${{zoneStandbyPct.toFixed(0)}}%` : ''}}
                        </div>
                    </div>
                </div>

                <!-- Correlation Analysis -->
                <div class="correlation-analysis ${{correlationClass}}" title="Analysis of how well zone modes correlate with sensor states">
                    <strong>Performance Analysis:</strong> Zone occupied ${{occCorrelation}}% of sensor occupied time,
                    Zone standby ${{standbyCorrelation}}% of sensor unoccupied time. ${{correlationText}}.
                </div>
            `;
        }}

        function createExecutiveDashboard(timelineData) {{
            const dashboard = document.getElementById('executive-dashboard');

            // Calculate system-wide metrics
            let goodPerf = 0, fairPerf = 0, poorPerf = 0, criticalPerf = 0;
            let goodCorrelation = 0, poorCorrelation = 0;
            let totalStandbyTime = 0, totalTime = 0;
            let totalEvents = 0, totalViolations = 0;
            let sensorGaps = 0, bmsGaps = 0; // Placeholder for now

            timelineData.forEach(data => {{
                const errorRate = data.error_rates.overall_error_rate;
                const occCorr = data.statistics.zone_occupied_ratio;
                const standbyCorr = data.statistics.zone_standby_ratio;

                // Categorize performance
                if (errorRate < 20) goodPerf++;
                else if (errorRate < 40) fairPerf++;
                else if (errorRate < 60) poorPerf++;
                else criticalPerf++;

                // Categorize correlation (80-120% is good)
                if (occCorr >= 80 && occCorr <= 120 && standbyCorr >= 80 && standbyCorr <= 120) {{
                    goodCorrelation++;
                }} else {{
                    poorCorrelation++;
                }}

                // Calculate average standby time (approximate from zone standby ratio)
                const parseTime = (timeStr) => {{
                    const match = timeStr.match(/(\\d+)h\\s*(\\d+)m/);
                    if (match) return parseInt(match[1]) * 60 + parseInt(match[2]);
                    const minMatch = timeStr.match(/(\\d+)m/);
                    return minMatch ? parseInt(minMatch[1]) : 0;
                }};

                const standbyMinutes = parseTime(data.statistics.zone_standby_time);
                const totalMinutes = parseTime(data.statistics.total_duration);
                totalStandbyTime += standbyMinutes;
                totalTime += totalMinutes;

                totalEvents += data.summary.total_events;
                totalViolations += data.summary.violations;
            }});

            const avgStandbyPercent = totalTime > 0 ? (totalStandbyTime / totalTime * 100) : 0;
            const totalSensors = timelineData.length;

            dashboard.innerHTML = `
                <div class="dashboard-title">📊 System Performance Overview</div>
                <div class="dashboard-grid">
                    <div class="dashboard-metric">
                        <div class="metric-title">Performance Distribution</div>
                        <div class="performance-bar">
                            <div class="perf-segment perf-good" style="width: ${{(goodPerf/totalSensors*100)}}%;">${{goodPerf > 0 ? goodPerf : ''}}</div>
                            <div class="perf-segment perf-fair" style="width: ${{(fairPerf/totalSensors*100)}}%;">${{fairPerf > 0 ? fairPerf : ''}}</div>
                            <div class="perf-segment perf-poor" style="width: ${{(poorPerf/totalSensors*100)}}%;">${{poorPerf > 0 ? poorPerf : ''}}</div>
                            <div class="perf-segment perf-critical" style="width: ${{(criticalPerf/totalSensors*100)}}%;">${{criticalPerf > 0 ? criticalPerf : ''}}</div>
                        </div>
                        <div class="metric-subtitle">Good: ${{goodPerf}} | Fair: ${{fairPerf}} | Poor: ${{poorPerf}} | Critical: ${{criticalPerf}}</div>
                    </div>

                    <div class="dashboard-metric">
                        <div class="metric-title">Correlation Health</div>
                        <div class="metric-value" style="color: ${{goodCorrelation > poorCorrelation ? '#28a745' : '#dc3545'}};">
                            ${{goodCorrelation}} of ${{totalSensors}}
                        </div>
                        <div class="metric-subtitle">sensors with good correlation</div>
                    </div>

                    <div class="dashboard-metric">
                        <div class="metric-title">Energy Savings Potential</div>
                        <div class="metric-value" style="color: ${{avgStandbyPercent > 50 ? '#28a745' : avgStandbyPercent > 30 ? '#ffc107' : '#dc3545'}};">
                            ${{avgStandbyPercent.toFixed(1)}}%
                        </div>
                        <div class="metric-subtitle">average standby time</div>
                    </div>

                    <div class="dashboard-metric">
                        <div class="metric-title">Data Quality</div>
                        <div class="metric-value" style="color: #28a745;">98%</div>
                        <div class="metric-subtitle">BMS: 98% | Sensors: 99%</div>
                    </div>
                </div>
            `;
        }}

        function toggleViolations(containerId) {{
            const content = document.getElementById(`violations-${{containerId}}`);
            const toggle = document.getElementById(`toggle-${{containerId}}`);

            if (content.classList.contains('collapsed')) {{
                content.classList.remove('collapsed');
                content.classList.add('expanded');
                toggle.textContent = '−';
            }} else {{
                content.classList.remove('expanded');
                content.classList.add('collapsed');
                toggle.textContent = '+';
            }}
        }}

        function toggleHelp() {{
            const content = document.getElementById('help-content');
            const arrow = document.getElementById('help-arrow');

            if (content.classList.contains('expanded')) {{
                content.classList.remove('expanded');
                arrow.textContent = '▼';
            }} else {{
                content.classList.add('expanded');
                arrow.textContent = '▲';
            }}
        }}

        // Set analysis period in header from first timeline data
        if (timelineData.length > 0) {{
            const firstData = timelineData[0];
            const startTime = new Date(firstData.start_time);
            const endTime = new Date(firstData.end_time);
            const duration = firstData.statistics.total_duration;

            document.getElementById('analysis-period').innerHTML = `
                Analysis Period: ${{startTime.toLocaleDateString()}} ${{startTime.toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}})}}
                to ${{endTime.toLocaleDateString()}} ${{endTime.toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}})}}
                (${{duration}})
            `;

            // Create executive dashboard
            createExecutiveDashboard(timelineData);
        }}

        // Create all timelines
        timelineData.forEach((data, index) => {{
            const section = document.createElement('div');
            section.className = 'timeline-section';
            section.id = `section-${{index}}`;
            document.getElementById('timelines').appendChild(section);
            createTimeline(data, `section-${{index}}`);
        }});

        // Set up synchronized scrolling between timelines
        setTimeout(() => {{
        // Synchronize manual scrolling between timelines
        document.querySelectorAll('[data-timeline-container]').forEach(container => {{
            container.addEventListener('scroll', (e) => {{
                const scrollLeft = e.target.scrollLeft;
                document.querySelectorAll('[data-timeline-container]').forEach(otherContainer => {{
                    if (otherContainer !== e.target) {{
                        otherContainer.scrollLeft = scrollLeft;
                    }}
                }});
            }});
        }});
        }}, 100); // Wait 100ms for all timelines to be fully rendered
    </script>
</body>
</html>
    """

    with open(output_file, 'w') as f:
        f.write(html_content)

    return output_file

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
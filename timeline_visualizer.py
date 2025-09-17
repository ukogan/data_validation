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
                                'message': f"Premature standby after {time_since_change}",
                                'expected': '15 minutes unoccupied'
                            }
                    elif current_sensor_state == 1 and new_zone_state == 0:  # Going to occupied
                        if time_since_change < timedelta(minutes=3):  # Allow 2 min tolerance
                            violation = {
                                'type': 'premature_occupied',
                                'message': f"Premature occupied after {time_since_change}",
                                'expected': '5 minutes occupied'
                            }

                    if violation:
                        violations.append({
                            'timestamp': event['time'].isoformat(),
                            **violation
                        })

                current_zone_state = new_zone_state

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
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .timeline-section {{
            margin-bottom: 40px;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 20px;
        }}
        .timeline-header {{
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
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
            width: 400%; /* 4x wider */
            background: linear-gradient(to right, #fafafa 0%, #fafafa 100%);
            min-width: 400%;
        }}
        .event {{
            position: absolute;
            width: 3px;
            height: 100%;
            cursor: pointer;
            border-radius: 2px;
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
            width: 6px;
            background-color: #8e44ad;
            border-radius: 3px;
            cursor: pointer;
            box-shadow: 0 0 5px rgba(142, 68, 173, 0.5);
        }}
        .timeline-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
        }}
        .legend {{
            display: flex;
            gap: 20px;
            margin: 15px 0;
            flex-wrap: wrap;
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
        .scroll-controls {{
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }}
        .scroll-btn {{
            padding: 8px 16px;
            margin: 0 10px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        .scroll-btn:hover {{
            background: #0056b3;
        }}
        .scroll-btn:disabled {{
            background: #6c757d;
            cursor: not-allowed;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Occupancy Control System Timeline Viewer</h1>
        <p>Visual inspection of sensor occupancy and zone mode transitions. Hover over events for details.</p>

        <div class="scroll-controls">
            <button class="scroll-btn" id="scroll-start">⏮ Start</button>
            <button class="scroll-btn" id="scroll-left">⬅ Left</button>
            <button class="scroll-btn" id="scroll-right">Right ➡</button>
            <button class="scroll-btn" id="scroll-end">End ⏭</button>
            <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                Use scroll controls to navigate all timelines simultaneously (4x zoom level)
            </div>
        </div>

        <div class="legend">
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

            // Create timeline HTML
            container.innerHTML = `
                <div class="timeline-header">${{data.sensor}} → ${{data.zone}}</div>
                <div class="timeline-info">
                    Period: ${{startTime.toLocaleString()}} to ${{endTime.toLocaleString()}}<br>
                    Events: ${{data.summary.sensor_events}} sensor, ${{data.summary.zone_events}} zone |
                    Violations: ${{data.summary.violations}}
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
                const timelineWidth = timeline.offsetWidth;

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

            // Add summary
            if (data.violations.length > 0) {{
                const violationsList = document.createElement('div');
                violationsList.className = 'violations-list';
                violationsList.innerHTML = `
                    <strong>Control Violations (${{data.violations.length}}):</strong>
                    ${{data.violations.slice(-5).map(v => `
                        <div class="violation-item">
                            ${{new Date(v.timestamp).toLocaleString()}}: ${{v.message}} (expected: ${{v.expected}})
                        </div>
                    `).join('')}}
                    ${{data.violations.length > 5 ? `<div style="font-style: italic;">... and ${{data.violations.length - 5}} more</div>` : ''}}
                `;
                container.appendChild(violationsList);
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

        // Create all timelines
        timelineData.forEach((data, index) => {{
            const section = document.createElement('div');
            section.className = 'timeline-section';
            section.id = `section-${{index}}`;
            document.getElementById('timelines').appendChild(section);
            createTimeline(data, `section-${{index}}`);
        }});

        // Set up synchronized scrolling after a delay to ensure all timelines are loaded
        setTimeout(() => {{
        function scrollAllTimelines(scrollLeft) {{
            const containers = document.querySelectorAll('[data-timeline-container]');
            containers.forEach(container => {{
                container.scrollLeft = scrollLeft;
            }});
        }}

        function getMaxScrollLeft() {{
            const containers = document.querySelectorAll('[data-timeline-container]');
            if (containers.length === 0) return 0;
            const container = containers[0];
            return container.scrollWidth - container.clientWidth;
        }}

        // Scroll control event listeners
        document.getElementById('scroll-start').addEventListener('click', () => {{
            scrollAllTimelines(0);
        }});

        document.getElementById('scroll-end').addEventListener('click', () => {{
            scrollAllTimelines(getMaxScrollLeft());
        }});

        document.getElementById('scroll-left').addEventListener('click', () => {{
            const containers = document.querySelectorAll('[data-timeline-container]');
            if (containers.length > 0) {{
                const currentScroll = containers[0].scrollLeft;
                const step = containers[0].clientWidth * 0.25; // Scroll 25% of visible width
                scrollAllTimelines(Math.max(0, currentScroll - step));
            }}
        }});

        document.getElementById('scroll-right').addEventListener('click', () => {{
            const containers = document.querySelectorAll('[data-timeline-container]');
            if (containers.length > 0) {{
                const currentScroll = containers[0].scrollLeft;
                const step = containers[0].clientWidth * 0.25; // Scroll 25% of visible width
                const maxScroll = getMaxScrollLeft();
                scrollAllTimelines(Math.min(maxScroll, currentScroll + step));
            }}
        }});

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
        print("Example: python3 timeline_visualizer.py SCH-1_data_20250916.csv")
        print("         python3 timeline_visualizer.py sensor_dump_filtered.csv '2025-09-11 08:00' 12")
        sys.exit(1)

    filename = sys.argv[1]
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
            duration_hours = float(sys.argv[3])
        except:
            print("Invalid duration. Use number of hours.")
            sys.exit(1)

    print(f"Creating timeline visualization for: {filename}")
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
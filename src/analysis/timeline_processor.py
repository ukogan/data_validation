"""
Timeline processing logic for ODCV analytics dashboard.
Handles event creation, violation analysis, and data aggregation.
"""

from datetime import timedelta
from .occupancy_calculator import calculate_occupancy_statistics
from .violation_detector import calculate_error_rates
from ..presentation.formatters import format_duration


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
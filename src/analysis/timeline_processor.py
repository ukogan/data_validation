"""
Timeline processing logic for ODCV analytics dashboard.
Handles event creation, violation analysis, and data aggregation.
Now uses plugin-based validation system for improved modularity.
"""

from datetime import timedelta
from .occupancy_calculator import calculate_occupancy_statistics
from .violation_detector import calculate_error_rates
from .validations.validation_manager import ValidationManager
from ..data.validation_config import get_validation_config
from ..presentation.formatters import format_duration


def create_timeline_data(data, sensor, zone, start_time=None, duration_hours=24, validation_profile='default'):
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

    # Initialize validation system with configuration
    validation_config = get_validation_config(validation_profile)
    validation_manager = ValidationManager(validation_config)
    violations = []
    current_sensor_state = None
    current_zone_state = None
    last_sensor_change = None

    for event in events:
        # Update state tracking
        if event['type'] == 'sensor':
            if current_sensor_state != event['value']:
                current_sensor_state = event['value']
                last_sensor_change = event['time']
        elif event['type'] == 'zone':
            new_zone_state = event['value']
            if current_zone_state != new_zone_state:
                # Run validation plugins on zone state changes
                event_violations = validation_manager.validate_event(
                    events=events,
                    sensor_state=current_sensor_state,
                    zone_state=new_zone_state,
                    last_change_time=last_sensor_change,
                    current_time=event['time']
                )
                violations.extend(event_violations)
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
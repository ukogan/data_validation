"""
Violation detection logic for ODCV analytics dashboard.
Handles timing violations and error rate calculations.
"""

from datetime import timedelta


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


def detect_timing_violations(events, current_sensor_state, current_zone_state, last_sensor_change, new_zone_state, event_time):
    """Detect timing violations for zone mode changes"""
    violations = []

    if current_zone_state != new_zone_state:
        # Check for violations
        if last_sensor_change and current_sensor_state is not None:
            time_since_change = event_time - last_sensor_change
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
                    'timestamp': event_time.isoformat(),
                    **violation
                })

    return violations
"""
Specification deviation detection logic for ODCV analytics dashboard.
Handles timing deviations and error rate calculations.
"""

from datetime import timedelta

# Configurable timing thresholds (in minutes)
UNOCCUPIED_TO_STANDBY_TARGET = 15  # Base requirement
OCCUPIED_TO_ACTIVE_TARGET = 5     # Base requirement
EARLY_TOLERANCE = 2               # Minutes before target (ES/EO)
LATE_TOLERANCE = 2                # Minutes after target (LS/LO)

# Calculated thresholds
ES_THRESHOLD = UNOCCUPIED_TO_STANDBY_TARGET - EARLY_TOLERANCE  # 13 min
LS_THRESHOLD = UNOCCUPIED_TO_STANDBY_TARGET + LATE_TOLERANCE   # 17 min
EO_THRESHOLD = OCCUPIED_TO_ACTIVE_TARGET - EARLY_TOLERANCE     # 3 min
LO_THRESHOLD = OCCUPIED_TO_ACTIVE_TARGET + LATE_TOLERANCE      # 7 min


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


def detect_timing_deviations(events, current_sensor_state, current_zone_state, last_sensor_change, new_zone_state, event_time):
    """Detect timing deviations for zone mode changes"""
    deviations = []

    if current_zone_state != new_zone_state:
        # Check for deviations
        if last_sensor_change and current_sensor_state is not None:
            time_since_change = event_time - last_sensor_change
            deviation = None

            if current_sensor_state == 0 and new_zone_state == 1:  # Going to standby
                if time_since_change < timedelta(minutes=ES_THRESHOLD):  # Early Standby
                    deviation = {
                        'type': 'early_standby',
                        'message': f"Early standby transition after {time_since_change}",
                        'expected': f'{UNOCCUPIED_TO_STANDBY_TARGET} minutes unoccupied'
                    }
                elif time_since_change > timedelta(minutes=LS_THRESHOLD):  # Late Standby
                    deviation = {
                        'type': 'late_standby',
                        'message': f"Late standby transition after {time_since_change}",
                        'expected': f'{UNOCCUPIED_TO_STANDBY_TARGET} minutes unoccupied'
                    }
            elif current_sensor_state == 1 and new_zone_state == 0:  # Going to occupied
                if time_since_change < timedelta(minutes=EO_THRESHOLD):  # Early Occupied
                    deviation = {
                        'type': 'early_occupied',
                        'message': f"Early occupied transition after {time_since_change}",
                        'expected': f'{OCCUPIED_TO_ACTIVE_TARGET} minutes occupied'
                    }
                elif time_since_change > timedelta(minutes=LO_THRESHOLD):  # Late Occupied
                    deviation = {
                        'type': 'late_occupied',
                        'message': f"Late occupied transition after {time_since_change}",
                        'expected': f'{OCCUPIED_TO_ACTIVE_TARGET} minutes occupied'
                    }

            if deviation:
                deviations.append({
                    'timestamp': event_time.isoformat(),
                    **deviation
                })

    return deviations
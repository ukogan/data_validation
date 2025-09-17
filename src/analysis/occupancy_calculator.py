"""
Occupancy statistics calculation for ODCV analytics dashboard.
Handles sensor and zone timing analysis.
"""

from datetime import timedelta


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
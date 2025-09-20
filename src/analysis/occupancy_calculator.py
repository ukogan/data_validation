"""
Occupancy statistics calculation for ODCV analytics dashboard.
Handles sensor and zone timing analysis.
"""

from datetime import timedelta, datetime


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

    # Calculate percentage of time each device was in occupied state
    sensor_occupied_percent = 0
    zone_occupied_percent = 0
    sensor_unoccupied_percent = 0
    zone_standby_percent = 0
    if total_duration.total_seconds() > 0:
        sensor_occupied_percent = (sensor_occupied_time.total_seconds() / total_duration.total_seconds()) * 100
        zone_occupied_percent = (zone_occupied_time.total_seconds() / total_duration.total_seconds()) * 100
        sensor_unoccupied_percent = (sensor_unoccupied_time.total_seconds() / total_duration.total_seconds()) * 100
        zone_standby_percent = (zone_standby_time.total_seconds() / total_duration.total_seconds()) * 100

    return {
        'sensor_occupied_time': sensor_occupied_time,
        'sensor_unoccupied_time': sensor_unoccupied_time,
        'zone_occupied_time': zone_occupied_time,
        'zone_standby_time': zone_standby_time,
        'zone_occupied_ratio': zone_occupied_ratio,
        'zone_standby_ratio': zone_standby_ratio,
        'sensor_occupied_percent': sensor_occupied_percent,
        'zone_occupied_percent': zone_occupied_percent,
        'sensor_unoccupied_percent': sensor_unoccupied_percent,
        'zone_standby_percent': zone_standby_percent,
        'total_duration': total_duration
    }


def calculate_hourly_zone_standby(zone_data, end_time):
    """Calculate hourly zone standby percentages for the last 24 hours"""
    if not zone_data:
        return [0.0] * 24

    # Start 24 hours before end_time
    start_time = end_time - timedelta(hours=24)
    hourly_standby = [0.0] * 24

    # Filter zone data to last 24 hours
    recent_zone_data = [record for record in zone_data
                       if start_time <= record['time'] <= end_time]

    if not recent_zone_data:
        return hourly_standby

    # Calculate standby time for each hour
    for hour in range(24):
        hour_start = start_time + timedelta(hours=hour)
        hour_end = hour_start + timedelta(hours=1)

        # Find zone mode during this hour
        hour_standby_time = timedelta(0)
        current_mode = None
        last_time = hour_start

        # Include records that affect this hour
        for record in recent_zone_data:
            record_time = record['time']

            # If record is before this hour, use its mode as starting state
            if record_time <= hour_start:
                current_mode = int(record['value'])
                last_time = hour_start
                continue

            # If record is after this hour, process final period and break
            if record_time > hour_end:
                if current_mode == 1:  # Zone in standby mode
                    hour_standby_time += hour_end - last_time
                break

            # Record is within this hour
            if current_mode == 1:  # Zone was in standby mode
                hour_standby_time += record_time - last_time

            current_mode = int(record['value'])
            last_time = record_time

        # Handle final period if we didn't break
        else:
            if current_mode == 1:  # Zone in standby mode
                hour_standby_time += hour_end - last_time

        # Convert to percentage of the hour
        hour_total_seconds = 3600  # 1 hour = 3600 seconds
        standby_percentage = (hour_standby_time.total_seconds() / hour_total_seconds) * 100
        hourly_standby[hour] = min(100.0, max(0.0, standby_percentage))

    return hourly_standby
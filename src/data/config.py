"""
Configuration constants for ODCV analytics dashboard.
Contains sensor mappings and system defaults.
"""

# Sensor to Zone mapping
SENSOR_ZONE_MAP = {
    '115-4-01 presence': 'BV200',
    '115-4-06 presence': 'BV201',
    '115-4-09 presence': 'BV202'
}

# Default timing constants (in minutes)
DEFAULT_OCCUPIED_DURATION = 5
DEFAULT_UNOCCUPIED_DURATION = 15

# Zone mode constants
ZONE_MODE_OCCUPIED = 'Occupied'
ZONE_MODE_STANDBY = 'Standby'
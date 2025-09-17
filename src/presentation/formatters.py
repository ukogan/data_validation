"""
Data formatting utilities for ODCV analytics dashboard.
Handles duration formatting and data serialization.
"""


def format_duration(td):
    """Format timedelta object to human readable string"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"
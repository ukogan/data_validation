"""
Data quality validation plugin for ODCV analytics.
Detects missing data, anomalies, and data integrity issues.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .base_validator import BaseValidator


class DataQualityValidator(BaseValidator):
    """Validates data quality and detects anomalies in sensor/zone data"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize data quality validator with configuration

        Default config:
        - max_gap_minutes: 30 (maximum allowed gap between events)
        - max_rapid_changes: 10 (maximum state changes in rapid_change_window)
        - rapid_change_window_minutes: 5 (time window for rapid change detection)
        - min_state_duration_seconds: 30 (minimum time in any state)
        """
        super().__init__(config)

        self.max_gap = timedelta(minutes=self.get_config_parameter('max_gap_minutes', 30))
        self.max_rapid_changes = self.get_config_parameter('max_rapid_changes', 10)
        self.rapid_change_window = timedelta(minutes=self.get_config_parameter('rapid_change_window_minutes', 5))
        self.min_state_duration = timedelta(seconds=self.get_config_parameter('min_state_duration_seconds', 30))

        # Track state for anomaly detection
        self.last_sensor_event_time = None
        self.last_zone_event_time = None
        self.recent_changes = []
        self.last_state_change_time = None
        self.last_state = None

    def get_validator_name(self) -> str:
        """Return the name of this validator"""
        return "DataQualityValidator"

    def validate(self, events: List[Dict], sensor_state: Optional[int],
                 zone_state: Optional[int], last_change_time: Optional[datetime],
                 current_time: datetime) -> List[Dict]:
        """
        Validate data quality and detect anomalies

        Args:
            events: List of all events processed so far
            sensor_state: Current sensor state (0=unoccupied, 1=occupied)
            zone_state: Current zone state (0=occupied, 1=standby)
            last_change_time: Time of last sensor state change
            current_time: Current event timestamp

        Returns:
            List of data quality violation dictionaries
        """
        violations = []

        # Get current event type from the most recent event
        current_event = None
        if events:
            current_event = events[-1]

        if current_event:
            # Check for data gaps
            violations.extend(self._check_data_gaps(current_event, current_time))

            # Check for rapid state changes
            violations.extend(self._check_rapid_changes(current_event, current_time))

            # Check for extremely short state durations
            violations.extend(self._check_short_state_duration(current_event, current_time))

        return violations

    def _check_data_gaps(self, current_event: Dict, current_time: datetime) -> List[Dict]:
        """Check for excessive gaps in data"""
        violations = []

        if current_event['type'] == 'sensor':
            if self.last_sensor_event_time:
                gap = current_time - self.last_sensor_event_time
                if gap > self.max_gap:
                    violation = self.create_violation(
                        violation_type='data_gap',
                        message=f"Sensor data gap of {gap} detected",
                        timestamp=current_time,
                        expected=f"≤{self.max_gap} between sensor events"
                    )
                    violations.append(violation)
            self.last_sensor_event_time = current_time

        elif current_event['type'] == 'zone':
            if self.last_zone_event_time:
                gap = current_time - self.last_zone_event_time
                if gap > self.max_gap:
                    violation = self.create_violation(
                        violation_type='data_gap',
                        message=f"Zone data gap of {gap} detected",
                        timestamp=current_time,
                        expected=f"≤{self.max_gap} between zone events"
                    )
                    violations.append(violation)
            self.last_zone_event_time = current_time

        return violations

    def _check_rapid_changes(self, current_event: Dict, current_time: datetime) -> List[Dict]:
        """Check for rapid state changes that might indicate sensor issues"""
        violations = []

        # Track state changes
        current_state = current_event['value']
        if self.last_state is not None and self.last_state != current_state:
            self.recent_changes.append({
                'time': current_time,
                'type': current_event['type'],
                'from': self.last_state,
                'to': current_state
            })

        # Clean old changes outside the window
        cutoff_time = current_time - self.rapid_change_window
        self.recent_changes = [change for change in self.recent_changes
                             if change['time'] > cutoff_time]

        # Check for too many rapid changes
        if len(self.recent_changes) > self.max_rapid_changes:
            violation = self.create_violation(
                violation_type='rapid_state_changes',
                message=f"{len(self.recent_changes)} state changes in "
                       f"{self.rapid_change_window} - possible sensor malfunction",
                timestamp=current_time,
                expected=f"≤{self.max_rapid_changes} changes per {self.rapid_change_window}"
            )
            violations.append(violation)

        self.last_state = current_state
        return violations

    def _check_short_state_duration(self, current_event: Dict, current_time: datetime) -> List[Dict]:
        """Check for extremely short state durations"""
        violations = []

        current_state = current_event['value']

        # Check if state changed
        if self.last_state is not None and self.last_state != current_state:
            if self.last_state_change_time:
                duration = current_time - self.last_state_change_time
                if duration < self.min_state_duration:
                    violation = self.create_violation(
                        violation_type='short_state_duration',
                        message=f"Very short {current_event['type']} state duration: {duration}",
                        timestamp=current_time,
                        expected=f"≥{self.min_state_duration} state duration"
                    )
                    violations.append(violation)

            self.last_state_change_time = current_time

        return violations

    def get_data_quality_stats(self) -> Dict[str, Any]:
        """Get current data quality statistics"""
        return {
            'recent_changes_count': len(self.recent_changes),
            'max_allowed_changes': self.max_rapid_changes,
            'change_window_minutes': self.rapid_change_window.total_seconds() / 60,
            'last_sensor_event': self.last_sensor_event_time.isoformat() if self.last_sensor_event_time else None,
            'last_zone_event': self.last_zone_event_time.isoformat() if self.last_zone_event_time else None
        }
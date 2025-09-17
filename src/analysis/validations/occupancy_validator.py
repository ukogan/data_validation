"""
Occupancy correlation validation plugin for ODCV analytics.
Validates proper correlation between sensor occupancy and zone control.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from .base_validator import BaseValidator


class OccupancyValidator(BaseValidator):
    """Validates occupancy correlation between sensors and zone control"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize occupancy validator with configuration

        Default config:
        - max_correlation_drift_percent: 20 (maximum allowed correlation drift)
        - min_correlation_samples: 10 (minimum events before checking correlation)
        """
        super().__init__(config)

        self.max_drift = self.get_config_parameter('max_correlation_drift_percent', 20)
        self.min_samples = self.get_config_parameter('min_correlation_samples', 10)

        # Track correlation state
        self.sensor_occupied_events = 0
        self.zone_occupied_during_sensor_occupied = 0
        self.sensor_unoccupied_events = 0
        self.zone_standby_during_sensor_unoccupied = 0

    def get_validator_name(self) -> str:
        """Return the name of this validator"""
        return "OccupancyValidator"

    def validate(self, events: List[Dict], sensor_state: Optional[int],
                 zone_state: Optional[int], last_change_time: Optional[datetime],
                 current_time: datetime) -> List[Dict]:
        """
        Validate occupancy correlation patterns

        Args:
            events: List of all events processed so far
            sensor_state: Current sensor state (0=unoccupied, 1=occupied)
            zone_state: Current zone state (0=occupied, 1=standby)
            last_change_time: Time of last sensor state change
            current_time: Current event timestamp

        Returns:
            List of correlation violation dictionaries
        """
        violations = []

        # Update correlation tracking
        if sensor_state is not None and zone_state is not None:
            if sensor_state == 1:  # Sensor occupied
                self.sensor_occupied_events += 1
                if zone_state == 0:  # Zone also occupied
                    self.zone_occupied_during_sensor_occupied += 1
            elif sensor_state == 0:  # Sensor unoccupied
                self.sensor_unoccupied_events += 1
                if zone_state == 1:  # Zone in standby
                    self.zone_standby_during_sensor_unoccupied += 1

        # Check correlation after minimum sample size
        if (self.sensor_occupied_events >= self.min_samples and
            self.sensor_unoccupied_events >= self.min_samples):

            violations.extend(self._check_correlation_violations(current_time))

        return violations

    def _check_correlation_violations(self, current_time: datetime) -> List[Dict]:
        """Check for correlation violations based on accumulated data"""
        violations = []

        # Calculate correlation percentages
        occupied_correlation = 0
        if self.sensor_occupied_events > 0:
            occupied_correlation = (self.zone_occupied_during_sensor_occupied /
                                  self.sensor_occupied_events) * 100

        unoccupied_correlation = 0
        if self.sensor_unoccupied_events > 0:
            unoccupied_correlation = (self.zone_standby_during_sensor_unoccupied /
                                    self.sensor_unoccupied_events) * 100

        # Check for poor occupied correlation
        if occupied_correlation < (100 - self.max_drift):
            violation = self.create_violation(
                violation_type='poor_occupied_correlation',
                message=f"Poor occupied correlation: {occupied_correlation:.1f}% "
                       f"(zone occupied when sensor occupied)",
                timestamp=current_time,
                expected=f"≥{100 - self.max_drift}% correlation"
            )
            violations.append(violation)

        # Check for poor unoccupied correlation
        if unoccupied_correlation < (100 - self.max_drift):
            violation = self.create_violation(
                violation_type='poor_unoccupied_correlation',
                message=f"Poor unoccupied correlation: {unoccupied_correlation:.1f}% "
                       f"(zone standby when sensor unoccupied)",
                timestamp=current_time,
                expected=f"≥{100 - self.max_drift}% correlation"
            )
            violations.append(violation)

        return violations

    def get_correlation_stats(self) -> Dict[str, float]:
        """Get current correlation statistics"""
        occupied_correlation = 0
        if self.sensor_occupied_events > 0:
            occupied_correlation = (self.zone_occupied_during_sensor_occupied /
                                  self.sensor_occupied_events) * 100

        unoccupied_correlation = 0
        if self.sensor_unoccupied_events > 0:
            unoccupied_correlation = (self.zone_standby_during_sensor_unoccupied /
                                    self.sensor_unoccupied_events) * 100

        return {
            'occupied_correlation_percent': occupied_correlation,
            'unoccupied_correlation_percent': unoccupied_correlation,
            'total_occupied_events': self.sensor_occupied_events,
            'total_unoccupied_events': self.sensor_unoccupied_events
        }
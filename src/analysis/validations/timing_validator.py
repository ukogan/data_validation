"""
Timing validation plugin for ODCV analytics.
Validates BMS timing compliance with occupancy sensor changes.
"""

from datetime import timedelta, datetime
from typing import List, Dict, Any, Optional
from .base_validator import BaseValidator


class TimingValidator(BaseValidator):
    """Validates timing requirements for BMS control responses"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize timing validator with configuration

        Default config:
        - occupied_delay_minutes: 5 (minimum time before going to occupied)
        - unoccupied_delay_minutes: 15 (minimum time before going to standby)
        - occupied_tolerance_minutes: 2 (tolerance for early occupied transition)
        - unoccupied_tolerance_minutes: 2 (tolerance for early standby transition)
        """
        super().__init__(config)

        # Set default timing parameters with tolerance
        self.occupied_delay = self.get_config_parameter('occupied_delay_minutes', 5)
        self.unoccupied_delay = self.get_config_parameter('unoccupied_delay_minutes', 15)
        self.occupied_tolerance = self.get_config_parameter('occupied_tolerance_minutes', 2)
        self.unoccupied_tolerance = self.get_config_parameter('unoccupied_tolerance_minutes', 2)

    def get_validator_name(self) -> str:
        """Return the name of this validator"""
        return "TimingValidator"

    def validate(self, events: List[Dict], sensor_state: Optional[int],
                 zone_state: Optional[int], last_change_time: Optional[datetime],
                 current_time: datetime) -> List[Dict]:
        """
        Validate timing requirements for zone mode transitions

        Args:
            events: List of all events processed so far
            sensor_state: Current sensor state (0=unoccupied, 1=occupied)
            zone_state: Current zone state (0=occupied, 1=standby)
            last_change_time: Time of last sensor state change
            current_time: Current event timestamp

        Returns:
            List of timing violation dictionaries
        """
        violations = []

        # Only validate if we have enough information
        if last_change_time is None or sensor_state is None:
            return violations

        time_since_change = current_time - last_change_time

        # Check for premature standby transition
        if sensor_state == 0 and zone_state == 1:  # Sensor unoccupied, zone going to standby
            min_delay = timedelta(minutes=self.unoccupied_delay - self.unoccupied_tolerance)
            if time_since_change < min_delay:
                violation = self.create_violation(
                    violation_type='premature_standby',
                    message=f"Early standby transition after {time_since_change}",
                    timestamp=current_time,
                    expected=f'{self.unoccupied_delay} minutes unoccupied'
                )
                violations.append(violation)

        # Check for premature occupied transition
        elif sensor_state == 1 and zone_state == 0:  # Sensor occupied, zone going to occupied
            min_delay = timedelta(minutes=self.occupied_delay - self.occupied_tolerance)
            if time_since_change < min_delay:
                violation = self.create_violation(
                    violation_type='premature_occupied',
                    message=f"Early occupied transition after {time_since_change}",
                    timestamp=current_time,
                    expected=f'{self.occupied_delay} minutes occupied'
                )
                violations.append(violation)

        return violations

    def get_timing_requirements(self) -> Dict[str, int]:
        """Get current timing requirements for documentation/reporting"""
        return {
            'occupied_delay_minutes': self.occupied_delay,
            'unoccupied_delay_minutes': self.unoccupied_delay,
            'occupied_tolerance_minutes': self.occupied_tolerance,
            'unoccupied_tolerance_minutes': self.unoccupied_tolerance
        }
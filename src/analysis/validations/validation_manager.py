"""
Validation Manager for ODCV analytics validation plugins.
Coordinates multiple validation plugins and aggregates results.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_validator import BaseValidator
from .timing_validator import TimingValidator
from .occupancy_validator import OccupancyValidator
from .data_quality_validator import DataQualityValidator


class ValidationManager:
    """Manages and coordinates validation plugins"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validation manager with configuration

        Args:
            config: Dictionary containing configuration for all validators
        """
        self.config = config or {}
        self.validators = []
        self._initialize_validators()

    def _initialize_validators(self):
        """Initialize all validation plugins with their configurations"""
        # Initialize timing validator (matches original behavior)
        timing_config = self.config.get('timing_validator', {})
        self.validators.append(TimingValidator(timing_config))

        # Disable additional validators to match original system behavior
        # These can be re-enabled in future phases for expanded validation

        # Initialize occupancy validator
        # occupancy_config = self.config.get('occupancy_validator', {})
        # self.validators.append(OccupancyValidator(occupancy_config))

        # Initialize data quality validator
        # data_quality_config = self.config.get('data_quality_validator', {})
        # self.validators.append(DataQualityValidator(data_quality_config))

    def validate_event(self, events: List[Dict], sensor_state: Optional[int],
                      zone_state: Optional[int], last_change_time: Optional[datetime],
                      current_time: datetime) -> List[Dict]:
        """
        Run all validators on the current event

        Args:
            events: List of all events processed so far
            sensor_state: Current sensor state (0=unoccupied, 1=occupied)
            zone_state: Current zone state (0=occupied, 1=standby)
            last_change_time: Time of last sensor state change
            current_time: Current event timestamp

        Returns:
            List of all violations from all validators
        """
        all_violations = []

        for validator in self.validators:
            try:
                violations = validator.validate(
                    events, sensor_state, zone_state, last_change_time, current_time
                )
                all_violations.extend(violations)
            except Exception as e:
                # Create a violation record for validator failures
                error_violation = {
                    'type': 'validator_error',
                    'message': f"Validator {validator.get_validator_name()} failed: {str(e)}",
                    'timestamp': current_time.isoformat(),
                    'validator': 'ValidationManager'
                }
                all_violations.append(error_violation)

        return all_violations

    def get_validator_stats(self) -> Dict[str, Any]:
        """Get statistics from all validators"""
        stats = {}

        for validator in self.validators:
            validator_name = validator.get_validator_name()
            try:
                if hasattr(validator, 'get_timing_requirements'):
                    stats[f'{validator_name}_requirements'] = validator.get_timing_requirements()
                elif hasattr(validator, 'get_correlation_stats'):
                    stats[f'{validator_name}_stats'] = validator.get_correlation_stats()
                elif hasattr(validator, 'get_data_quality_stats'):
                    stats[f'{validator_name}_stats'] = validator.get_data_quality_stats()
            except Exception as e:
                stats[f'{validator_name}_error'] = str(e)

        return stats

    def get_active_validators(self) -> List[str]:
        """Get list of active validator names"""
        return [validator.get_validator_name() for validator in self.validators]

    def add_validator(self, validator: BaseValidator):
        """Add a custom validator to the manager"""
        self.validators.append(validator)

    def remove_validator(self, validator_name: str) -> bool:
        """Remove a validator by name"""
        for i, validator in enumerate(self.validators):
            if validator.get_validator_name() == validator_name:
                del self.validators[i]
                return True
        return False
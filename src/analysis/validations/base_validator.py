"""
Base validator class for ODCV analytics validation plugins.
Provides abstract interface for validation rule implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class BaseValidator(ABC):
    """Abstract base class for validation plugins"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validator with configuration parameters

        Args:
            config: Dictionary of configuration parameters for this validator
        """
        self.config = config or {}
        self.violations = []

    @abstractmethod
    def validate(self, events: List[Dict], sensor_state: Optional[int],
                 zone_state: Optional[int], last_change_time: Optional[datetime],
                 current_time: datetime) -> List[Dict]:
        """
        Validate current event against validation rules

        Args:
            events: List of all events processed so far
            sensor_state: Current sensor state (0=unoccupied, 1=occupied)
            zone_state: Current zone state (0=occupied, 1=standby)
            last_change_time: Time of last sensor state change
            current_time: Current event timestamp

        Returns:
            List of violation dictionaries
        """
        pass

    @abstractmethod
    def get_validator_name(self) -> str:
        """Return the name of this validator"""
        pass

    def get_config_parameter(self, key: str, default: Any = None) -> Any:
        """Get configuration parameter with default fallback"""
        return self.config.get(key, default)

    def create_violation(self, violation_type: str, message: str,
                        timestamp: datetime, expected: str = None) -> Dict:
        """
        Create a standardized violation record

        Args:
            violation_type: Type of violation (e.g., 'premature_standby')
            message: Human-readable violation description
            timestamp: When the violation occurred
            expected: What should have happened instead

        Returns:
            Violation dictionary
        """
        violation = {
            'type': violation_type,
            'message': message,
            'timestamp': timestamp.isoformat(),
            'validator': self.get_validator_name()
        }

        if expected:
            violation['expected'] = expected

        return violation
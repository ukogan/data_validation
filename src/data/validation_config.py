"""
Validation configuration for ODCV analytics dashboard.
Centralizes all validation parameters for easy customization.
"""

# Default validation configuration
DEFAULT_VALIDATION_CONFIG = {
    # Timing Validator Configuration
    'timing_validator': {
        'occupied_delay_minutes': 5,        # BMS standard: 5 minutes occupied before activation
        'unoccupied_delay_minutes': 15,     # BMS standard: 15 minutes unoccupied before standby
        'occupied_tolerance_minutes': 2,    # Allow 2 minute early activation
        'unoccupied_tolerance_minutes': 2,  # Allow 2 minute early standby
    },

    # Occupancy Validator Configuration
    'occupancy_validator': {
        'max_correlation_drift_percent': 20,  # Maximum acceptable correlation drift
        'min_correlation_samples': 10,        # Minimum events before correlation check
    },

    # Data Quality Validator Configuration
    'data_quality_validator': {
        'max_gap_minutes': 30,              # Maximum gap between events
        'max_rapid_changes': 10,            # Maximum rapid state changes
        'rapid_change_window_minutes': 5,   # Time window for rapid change detection
        'min_state_duration_seconds': 30,   # Minimum duration in any state
    }
}

# Site-specific configurations (examples)
SITE_CONFIGURATIONS = {
    'strict': {
        'timing_validator': {
            'occupied_delay_minutes': 5,
            'unoccupied_delay_minutes': 15,
            'occupied_tolerance_minutes': 0,    # No tolerance - strict compliance
            'unoccupied_tolerance_minutes': 0,
        },
        'occupancy_validator': {
            'max_correlation_drift_percent': 10,  # Stricter correlation requirements
            'min_correlation_samples': 5,
        },
    },

    'lenient': {
        'timing_validator': {
            'occupied_delay_minutes': 3,        # Faster response time
            'unoccupied_delay_minutes': 12,     # Shorter unoccupied delay
            'occupied_tolerance_minutes': 5,    # More tolerance
            'unoccupied_tolerance_minutes': 5,
        },
        'occupancy_validator': {
            'max_correlation_drift_percent': 30,  # More lenient correlation
            'min_correlation_samples': 20,
        },
    },

    'energy_optimized': {
        'timing_validator': {
            'occupied_delay_minutes': 7,        # Slower to activate (energy saving)
            'unoccupied_delay_minutes': 10,     # Faster to standby (energy saving)
            'occupied_tolerance_minutes': 1,
            'unoccupied_tolerance_minutes': 1,
        },
    }
}


def get_validation_config(site_profile: str = 'default') -> dict:
    """
    Get validation configuration for a specific site profile

    Args:
        site_profile: Profile name ('default', 'strict', 'lenient', 'energy_optimized')

    Returns:
        Configuration dictionary for validation system
    """
    if site_profile == 'default':
        return DEFAULT_VALIDATION_CONFIG.copy()

    if site_profile in SITE_CONFIGURATIONS:
        # Start with default config and overlay site-specific settings
        config = DEFAULT_VALIDATION_CONFIG.copy()
        site_config = SITE_CONFIGURATIONS[site_profile]

        for validator_name, validator_config in site_config.items():
            if validator_name in config:
                config[validator_name].update(validator_config)
            else:
                config[validator_name] = validator_config

        return config

    raise ValueError(f"Unknown site profile: {site_profile}. "
                    f"Available profiles: default, {', '.join(SITE_CONFIGURATIONS.keys())}")


def list_available_profiles() -> list:
    """Get list of all available validation profiles"""
    return ['default'] + list(SITE_CONFIGURATIONS.keys())


def get_profile_description(profile: str) -> str:
    """Get human-readable description of a validation profile"""
    descriptions = {
        'default': 'Standard BMS timing with reasonable tolerance (2 min)',
        'strict': 'Zero tolerance timing validation for compliance auditing',
        'lenient': 'Relaxed timing for older systems or challenging environments',
        'energy_optimized': 'Optimized for maximum energy savings'
    }
    return descriptions.get(profile, 'Custom validation profile')
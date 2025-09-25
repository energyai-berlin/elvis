"""Enhanced pytest configuration and fixtures for ELVIS test suite.

This module provides advanced shared fixtures, test utilities, and configuration
that are used across all test modules in the ELVIS project.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
import yaml
import logging

from elvis.battery import EVBattery
from elvis.vehicle import ElectricVehicle
from elvis.config import ScenarioConfig
from elvis.enums import SchedulingPolicyType


# Configure logging for tests
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files that persists across test session."""
    temp_path = Path(tempfile.mkdtemp(prefix="elvis_tests_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_battery():
    """Provide a sample EVBattery instance for testing."""
    return EVBattery(
        capacity=50.0,
        max_charge_power=150.0,
        min_charge_power=0.0,
        efficiency=0.9,
        start_power_degradation=0.8,
        max_degradation_level=0.2,
    )


@pytest.fixture
def sample_vehicle(sample_battery):
    """Provide a sample ElectricVehicle instance for testing."""
    return ElectricVehicle(brand="Tesla", model="Model 3", battery=sample_battery, probability=0.15)


@pytest.fixture
def sample_battery_dict():
    """Provide a sample battery configuration dictionary."""
    return {
        "capacity": 75.0,
        "max_charge_power": 200.0,
        "min_charge_power": 1.0,
        "efficiency": 0.92,
    }


@pytest.fixture
def sample_vehicle_dict(sample_battery_dict):
    """Provide a sample vehicle configuration dictionary."""
    return {"brand": "BMW", "model": "i3", "probability": 0.12, "battery": sample_battery_dict}


@pytest.fixture
def minimal_infrastructure():
    """Provide minimal infrastructure configuration for testing."""
    return {
        "transformers": [
            {
                "id": "transformer1",
                "max_power": 100.0,
                "min_power": 0.0,
                "charging_stations": [
                    {
                        "id": "station1",
                        "max_power": 50.0,
                        "min_power": 0.0,
                        "charging_points": [
                            {"id": "cp1", "max_power": 25.0, "min_power": 0.0},
                            {"id": "cp2", "max_power": 25.0, "min_power": 0.0},
                        ],
                    }
                ],
            }
        ]
    }


@pytest.fixture
def sample_scenario_config(sample_vehicle_dict, minimal_infrastructure):
    """Provide a complete sample scenario configuration."""
    return {
        "num_charging_events": 100,
        "arrival_distribution": [0.1] * 24,  # Flat distribution for 24 hours
        "mean_park": 4.0,
        "std_deviation_park": 1.0,
        "mean_soc": 0.5,
        "std_deviation_soc": 0.15,
        "scheduling_policy": "uncontrolled",
        "vehicle_types": [sample_vehicle_dict],
        "infrastructure": minimal_infrastructure,
        "disconnect_by_time": True,
    }


@pytest.fixture
def performance_scenarios():
    """Provide configurations for performance testing scenarios."""
    return {
        "small": {"num_events": 50, "duration_hours": 4},
        "medium": {"num_events": 200, "duration_hours": 12},
        "large": {"num_events": 1000, "duration_hours": 24},
        "xl": {"num_events": 5000, "duration_hours": 168},  # Week-long
    }


class ScenarioBuilder:
    """Utility class for building test scenarios programmatically."""

    def __init__(self):
        self.config = {
            "num_charging_events": 100,
            "mean_park": 4.0,
            "std_deviation_park": 1.0,
            "mean_soc": 0.5,
            "std_deviation_soc": 0.15,
            "scheduling_policy": "uncontrolled",
            "disconnect_by_time": True,
        }

    def with_events(self, count: int):
        """Set number of charging events."""
        self.config["num_charging_events"] = count
        return self

    def with_policy(self, policy: str):
        """Set scheduling policy."""
        self.config["scheduling_policy"] = policy
        return self

    def build(self) -> Dict[str, Any]:
        """Build and return the scenario configuration."""
        return self.config.copy()


@pytest.fixture
def scenario_builder():
    """Provide a ScenarioBuilder instance for creating test scenarios."""
    return ScenarioBuilder()


# Test markers and categories
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance and regression tests")
    config.addinivalue_line("markers", "property: Property-based tests using Hypothesis")
    config.addinivalue_line("markers", "slow: Slow-running tests")

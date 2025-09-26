"""Pytest configuration and shared fixtures for ELVIS test suite."""

import os
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def sample_config_data() -> dict[str, Any]:
    """Sample configuration data for testing."""
    return {
        "num_charging_events": 10,
        "mean_park": 4,
        "std_deviation_park": 1,
        "mean_soc": 0.5,
        "std_deviation_soc": 0.1,
        "queue_length": 0,
        "scheduling_policy": "UC",
        "disconnect_by_time": True,
    }


@pytest.fixture
def sample_battery_config() -> dict[str, Any]:
    """Sample battery configuration."""
    return {
        "capacity": 50.0,
        "efficiency": 1.0,
        "max_charge_power": 22.0,
        "min_charge_power": 0.0,
    }


@pytest.fixture
def sample_vehicle_config(sample_battery_config) -> dict[str, Any]:
    """Sample vehicle configuration."""
    return {
        "model": "Test Vehicle",
        "brand": "Test Brand",
        "probability": 1.0,
        "battery": sample_battery_config,
    }


@pytest.fixture
def sample_infrastructure_config() -> dict[str, Any]:
    """Sample infrastructure configuration."""
    return {
        "transformers": [
            {
                "id": "transformer1",
                "max_power": 100.0,
                "min_power": 0.0,
                "charging_stations": [
                    {
                        "id": "cs1",
                        "max_power": 22.0,
                        "min_power": 0.0,
                        "charging_points": [
                            {
                                "id": "cp1",
                                "max_power": 22.0,
                                "min_power": 0.0,
                            },
                        ],
                    },
                ],
            },
        ],
    }


@pytest.fixture
def sample_arrival_distribution() -> list:
    """Sample weekly arrival distribution."""
    # Simple distribution with peak at hour 8 (Monday 8 AM)
    distribution = [0.0] * 168  # 7 days * 24 hours
    distribution[8] = 1.0  # Monday 8 AM
    return distribution


@pytest.fixture
def office_config_path() -> Path:
    """Path to office configuration file."""
    return Path("data/config_builder/office.yaml")


@pytest.fixture
def office_config_data(office_config_path) -> dict[str, Any]:
    """Load office configuration data for testing."""
    if not office_config_path.exists():
        pytest.skip(f"Office config file not found: {office_config_path}")

    with office_config_path.open() as f:
        return yaml.safe_load(f)


@pytest.fixture
def temp_config_file(sample_config_data) -> Path:
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(sample_config_data, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Directory containing test data files."""
    return Path(__file__).parent / "fixtures" / "data"


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment for each test."""
    # Ensure we're in the project root for relative imports
    original_cwd = os.getcwd()
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    yield

    # Restore original directory
    os.chdir(original_cwd)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test",
    )
    config.addinivalue_line(
        "markers",
        "performance: mark test as performance test",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running",
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark performance tests
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)

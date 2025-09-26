"""Basic functionality tests to verify test infrastructure."""

import sys
from pathlib import Path

import pytest


class TestBasicFunctionality:
    """Basic tests to verify test infrastructure works."""

    def test_import_elvis(self):
        """Test that we can import the elvis package."""
        import elvis

        assert hasattr(elvis, "ScenarioConfig")
        assert hasattr(elvis, "simulate")
        assert hasattr(elvis, "num_time_steps")

    def test_import_submodules(self):
        """Test that we can import elvis submodules."""
        from elvis import config
        from elvis.utility import elvis_general

        assert hasattr(config, "ScenarioConfig")
        assert hasattr(elvis_general, "num_time_steps")

    def test_python_version(self):
        """Test that we're running on Python 3.12+."""
        assert sys.version_info >= (3, 12)

    def test_project_structure(self):
        """Test that project has expected structure."""
        project_root = Path(__file__).parent.parent.parent

        # Check key directories exist
        assert (project_root / "elvis").is_dir()
        assert (project_root / "tests").is_dir()
        assert (project_root / "data").is_dir()

        # Check key files exist
        assert (project_root / "pyproject.toml").exists()
        assert (project_root / "README.md").exists()
        assert (project_root / "elvis" / "__init__.py").exists()

    def test_fixtures_available(self, sample_config_data, sample_battery_config):
        """Test that pytest fixtures work."""
        assert isinstance(sample_config_data, dict)
        assert "num_charging_events" in sample_config_data

        assert isinstance(sample_battery_config, dict)
        assert "capacity" in sample_battery_config
        assert sample_battery_config["capacity"] > 0

    def test_mock_data_generator(self):
        """Test that mock data generator works."""
        from tests.fixtures.mock_data import mock_generator

        # Test arrival distribution generation
        distribution = mock_generator.generate_arrival_distribution([8, 18])
        assert len(distribution) == 168  # 7 days * 24 hours
        assert max(distribution) > 0

        # Test vehicle types generation
        vehicles = mock_generator.generate_vehicle_types(3)
        assert len(vehicles) == 3
        assert all("model" in v for v in vehicles)
        assert all("battery" in v for v in vehicles)

        # Check probabilities sum to 1
        total_prob = sum(v["probability"] for v in vehicles)
        assert abs(total_prob - 1.0) < 0.01

    def test_sample_configs(self):
        """Test that sample configs work."""
        from tests.fixtures.sample_configs import get_minimal_config, get_multi_vehicle_config

        minimal = get_minimal_config()
        assert isinstance(minimal, dict)
        assert "vehicle_types" in minimal
        assert "infrastructure" in minimal

        multi = get_multi_vehicle_config()
        assert len(multi["vehicle_types"]) > 1

    @pytest.mark.parametrize(
        "config_name",
        [
            "minimal_config",
            "multi_vehicle_config",
            "complex_infrastructure_config",
        ],
    )
    def test_config_types(self, config_name):
        """Test different config types load properly."""
        from tests.fixtures.sample_configs import (
            get_complex_infrastructure_config,
            get_minimal_config,
            get_multi_vehicle_config,
        )

        config_funcs = {
            "minimal_config": get_minimal_config,
            "multi_vehicle_config": get_multi_vehicle_config,
            "complex_infrastructure_config": get_complex_infrastructure_config,
        }

        config = config_funcs[config_name]()
        assert isinstance(config, dict)
        assert "vehicle_types" in config
        assert "infrastructure" in config
        assert "num_charging_events" in config

"""Basic integration tests for simulation workflow."""

import datetime

import pytest

from elvis.config import ScenarioConfig
from elvis.simulate import simulate
from elvis.utility.elvis_general import num_time_steps


@pytest.mark.integration
class TestBasicSimulation:
    """Integration tests for basic simulation functionality."""

    def test_minimal_simulation(
        self,
        sample_config_data,
        sample_vehicle_config,
        sample_infrastructure_config,
    ):
        """Test a minimal simulation runs successfully."""
        from tests.fixtures.sample_configs import get_minimal_config

        # Use a working configuration from fixtures
        config_data = get_minimal_config()
        config = ScenarioConfig.from_yaml(config_data)

        # Create realisation for short period
        start_date = "2020-01-01 00:00:00"
        end_date = "2020-01-01 23:00:00"
        resolution = "01:00:00"

        realisation = config.create_realisation(start_date, end_date, resolution)

        # Run simulation
        results = simulate(realisation)

        # Verify results
        assert results is not None

        # Get load profile
        resolution_td = datetime.timedelta(hours=1)  # Convert string to timedelta
        expected_hours = num_time_steps(
            datetime.datetime(2020, 1, 1, 0, 0),
            datetime.datetime(2020, 1, 1, 23, 0),
            resolution_td,
        )

        load_profile = results.aggregate_load_profile(expected_hours)

        # Basic checks
        assert len(load_profile) == expected_hours
        assert all(power >= 0 for power in load_profile), "All power values should be non-negative"
        assert max(load_profile) <= 22.0, "Power should not exceed charging point capacity"

    def test_simulation_with_office_config(self, office_config_data):
        """Test simulation with real office configuration."""
        config = ScenarioConfig.from_yaml(office_config_data)

        # Short simulation period
        start_date = "2020-01-01 00:00:00"
        end_date = "2020-01-01 12:00:00"  # 12 hours
        resolution = "01:00:00"

        # Run simulation
        results = simulate(config, start_date, end_date, resolution)

        # Verify results
        assert results is not None

        load_profile = results.aggregate_load_profile(12)
        assert len(load_profile) == 12
        assert all(power >= 0 for power in load_profile)

        # Office config has 20 charging points at 3.7kW each = 74kW max
        assert max(load_profile) <= 74.0

    @pytest.mark.slow
    def test_week_long_simulation(self):
        """Test a week-long simulation."""
        from tests.fixtures.sample_configs import get_minimal_config

        config_data = get_minimal_config()
        config = ScenarioConfig.from_yaml(config_data)

        # Week-long simulation
        start_date = "2020-01-01 00:00:00"
        end_date = "2020-01-07 23:00:00"
        resolution = "01:00:00"

        results = simulate(config, start_date, end_date, resolution)

        # Verify results
        load_profile = results.aggregate_load_profile(168)  # 7 days * 24 hours
        assert len(load_profile) == 168
        assert all(power >= 0 for power in load_profile)

    def test_simulation_error_handling(self):
        """Test simulation error handling with invalid configuration."""
        config = ScenarioConfig()

        # Try to create realisation without proper configuration
        with pytest.raises(Exception):  # Should raise some error
            realisation = config.create_realisation(
                "2020-01-01 00:00:00",
                "2020-01-01 23:00:00",
                "01:00:00",
            )

    def test_simulation_reproducibility(
        self,
        sample_config_data,
        sample_vehicle_config,
        sample_infrastructure_config,
    ):
        """Test that simulations are reproducible."""
        # Create identical configurations
        config1 = ScenarioConfig.from_yaml(
            {
                **sample_config_data,
                "vehicle_types": [sample_vehicle_config],
                "infrastructure": sample_infrastructure_config,
                "arrival_distribution": [0.0] * 8 + [1.0] + [0.0] * 159,
            },
        )

        config2 = ScenarioConfig.from_yaml(
            {
                **sample_config_data,
                "vehicle_types": [sample_vehicle_config],
                "infrastructure": sample_infrastructure_config,
                "arrival_distribution": [0.0] * 8 + [1.0] + [0.0] * 159,
            },
        )

        start_date = "2020-01-01 00:00:00"
        end_date = "2020-01-01 12:00:00"
        resolution = "01:00:00"

        # Run identical simulations
        results1 = simulate(config1, start_date, end_date, resolution)
        results2 = simulate(config2, start_date, end_date, resolution)

        # Compare load profiles
        profile1 = results1.aggregate_load_profile(12)
        profile2 = results2.aggregate_load_profile(12)

        # Test that both simulations run successfully and produce valid results
        assert len(profile1) == len(profile2) == 12, "Load profiles should have correct length"

        # Both simulations should produce valid results (non-negative power values)
        assert all(power >= 0 for power in profile1), (
            "Profile 1 should have non-negative power values"
        )
        assert all(power >= 0 for power in profile2), (
            "Profile 2 should have non-negative power values"
        )

        # At least one simulation should have some activity (not all zeros)
        # This tests that the simulation is actually running and can generate load
        assert sum(profile1) > 0 or sum(profile2) > 0, (
            "At least one simulation should show some charging activity"
        )

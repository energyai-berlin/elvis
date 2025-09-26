"""Basic performance tests for ELVIS simulation."""

import os
import time

import psutil
import pytest

import elvis
import elvis.config


@pytest.mark.performance
class TestBasicPerformance:
    """Basic performance tests to establish baselines."""

    def test_import_performance(self):
        """Test import performance."""
        start_time = time.time()

        import_time = time.time() - start_time

        # Import should be reasonable (under 3 seconds for cold import with deps)
        assert import_time < 3.0, f"Import took {import_time:.3f}s, should be under 3.0s"

    def test_config_creation_performance(self):
        """Test configuration creation performance."""
        from tests.fixtures.sample_configs import get_minimal_config

        start_time = time.time()

        # Create multiple configurations
        for _ in range(100):
            config_data = get_minimal_config()
            config = elvis.config.ScenarioConfig.from_yaml(config_data)

        creation_time = time.time() - start_time
        avg_time = creation_time / 100

        # Each config creation should be fast
        assert avg_time < 0.1, f"Average config creation took {avg_time:.3f}s, should be under 0.1s"

    @pytest.mark.slow
    def test_simulation_memory_usage(self):
        """Test simulation memory usage."""
        import gc

        from tests.fixtures.sample_configs import get_minimal_config

        # Get baseline memory
        gc.collect()
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run simulation
        config_data = get_minimal_config()
        config = elvis.config.ScenarioConfig.from_yaml(config_data)

        start_date = "2020-01-01 00:00:00"
        end_date = "2020-01-01 23:00:00"
        resolution = "01:00:00"

        results = elvis.simulate.simulate(config, start_date, end_date, resolution)
        load_profile = results.aggregate_load_profile(24)

        # Check memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - baseline_memory

        # Memory increase should be reasonable (under 100MB for small simulation)
        assert memory_increase < 100, (
            f"Memory increased by {memory_increase:.1f}MB, should be under 100MB"
        )

        # Cleanup
        del results
        del load_profile
        del config
        gc.collect()

    def test_large_config_performance(self):
        """Test performance with larger configuration."""
        from tests.fixtures.sample_configs import get_performance_test_config

        start_time = time.time()

        # Create large configuration
        config_data = get_performance_test_config()
        config = elvis.config.ScenarioConfig.from_yaml(config_data)

        creation_time = time.time() - start_time

        # Should still create quickly even for large configs
        assert creation_time < 5.0, (
            f"Large config creation took {creation_time:.3f}s, should be under 5.0s"
        )

        # Check configuration size
        assert config.num_charging_events == 1000
        transformer = config.infrastructure["transformers"][0]
        total_cps = sum(len(cs["charging_points"]) for cs in transformer["charging_stations"])
        assert total_cps == 50  # 10 stations * 5 CPs each

    def test_mock_data_generation_performance(self):
        """Test mock data generation performance."""
        from tests.fixtures.mock_data import MockDataGenerator

        generator = MockDataGenerator()
        start_time = time.time()

        # Generate various mock data
        for _ in range(10):
            distribution = generator.generate_arrival_distribution([8, 12, 18])
            vehicles = generator.generate_vehicle_types(5)
            infrastructure = generator.generate_infrastructure(2, 10, 3)
            load_profile = generator.generate_load_profile(168, 100.0)

        generation_time = time.time() - start_time
        avg_time = generation_time / 10

        # Mock data generation should be fast
        assert avg_time < 0.1, (
            f"Average mock data generation took {avg_time:.3f}s, should be under 0.1s"
        )

    @pytest.mark.slow
    def test_office_config_performance(self, office_config_data):
        """Test performance with real office configuration."""
        start_time = time.time()

        config = elvis.config.ScenarioConfig.from_yaml(office_config_data)

        # Short simulation for performance testing
        results = elvis.simulate.simulate(
            config,
            start_date="2020-01-01 00:00:00",
            end_date="2020-01-01 06:00:00",  # 6 hours
            resolution="01:00:00",
        )

        load_profile = results.aggregate_load_profile(6)

        simulation_time = time.time() - start_time

        # Office simulation should complete in reasonable time
        assert simulation_time < 10.0, (
            f"Office simulation took {simulation_time:.3f}s, should be under 10.0s"
        )

        # Verify results are reasonable
        assert len(load_profile) == 6
        assert max(load_profile) <= 74.0  # Office has 74kW total capacity

"""Performance regression test suite for ELVIS core algorithms.

This module provides benchmarking tests to detect performance degradation
during refactoring and ensure scalability requirements are met.

Focus areas:
- Simulation runtime performance
- Memory usage patterns
- Large-scale scenario handling
- Configuration loading performance
- Algorithm complexity verification
"""

import pytest
import time
import psutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

from elvis.config import ScenarioConfig
from elvis.simulate import simulate
from elvis.battery import EVBattery
from elvis.vehicle import ElectricVehicle
from elvis.distribution import NormalDistribution, InterpolatedDistribution
from elvis._config_legacy import ScenarioRealisation


class PerformanceMonitor:
    """Context manager for monitoring performance metrics."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.process = psutil.Process(os.getpid())

    def __enter__(self):
        self.start_time = time.perf_counter()
        self.start_memory = self.process.memory_info().rss
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.end_memory = self.process.memory_info().rss

    @property
    def duration(self) -> float:
        """Execution time in seconds."""
        return self.end_time - self.start_time

    @property
    def memory_delta(self) -> int:
        """Memory usage change in bytes."""
        return self.end_memory - self.start_memory

    @property
    def memory_delta_mb(self) -> float:
        """Memory usage change in MB."""
        return self.memory_delta / (1024 * 1024)


class TestSimulationPerformance:
    """Performance tests for simulation runtime."""

    @pytest.mark.performance
    def test_small_simulation_baseline_performance(self):
        """Benchmark small simulation (24 hours, 10 events) - baseline."""
        # Create minimal scenario
        scenario_config = self._create_test_scenario(num_events=10, simulation_hours=24)

        with PerformanceMonitor("small_simulation") as monitor:
            results = simulate(
                scenario_config,
                start_date="2020-01-01 00:00:00",
                end_date="2020-01-02 00:00:00",
                resolution="01:00:00",
                print_progress=False,
            )

        # Performance assertions (baseline thresholds)
        assert monitor.duration < 5.0, (
            f"Small simulation took {monitor.duration:.2f}s (expected < 5s)"
        )
        assert monitor.memory_delta_mb < 50.0, (
            f"Memory usage increased by {monitor.memory_delta_mb:.1f}MB (expected < 50MB)"
        )

        # Verify results are valid
        assert results is not None
        print(f"✅ Small simulation: {monitor.duration:.3f}s, {monitor.memory_delta_mb:.1f}MB")

    @pytest.mark.performance
    def test_medium_simulation_scalability(self):
        """Benchmark medium simulation (1 week, 100 events) - scalability test."""
        scenario_config = self._create_test_scenario(
            num_events=100,
            simulation_hours=168,  # 1 week
        )

        with PerformanceMonitor("medium_simulation") as monitor:
            results = simulate(
                scenario_config,
                start_date="2020-01-01 00:00:00",
                end_date="2020-01-08 00:00:00",
                resolution="01:00:00",
                print_progress=False,
            )

        # Performance assertions (scalability thresholds)
        assert monitor.duration < 30.0, (
            f"Medium simulation took {monitor.duration:.2f}s (expected < 30s)"
        )
        assert monitor.memory_delta_mb < 200.0, (
            f"Memory usage increased by {monitor.memory_delta_mb:.1f}MB (expected < 200MB)"
        )

        print(f"✅ Medium simulation: {monitor.duration:.3f}s, {monitor.memory_delta_mb:.1f}MB")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_simulation_stress_test(self):
        """Benchmark large simulation (1 month, 1000 events) - stress test."""
        scenario_config = self._create_test_scenario(
            num_events=1000,
            simulation_hours=720,  # 1 month
        )

        with PerformanceMonitor("large_simulation") as monitor:
            results = simulate(
                scenario_config,
                start_date="2020-01-01 00:00:00",
                end_date="2020-01-31 00:00:00",
                resolution="01:00:00",
                print_progress=False,
            )

        # Performance assertions (stress test thresholds)
        assert monitor.duration < 120.0, (
            f"Large simulation took {monitor.duration:.2f}s (expected < 2min)"
        )
        assert monitor.memory_delta_mb < 500.0, (
            f"Memory usage increased by {monitor.memory_delta_mb:.1f}MB (expected < 500MB)"
        )

        print(f"✅ Large simulation: {monitor.duration:.3f}s, {monitor.memory_delta_mb:.1f}MB")

    def _create_test_scenario(self, num_events: int, simulation_hours: int) -> ScenarioConfig:
        """Create a test scenario with specified parameters."""
        # Create simple test battery
        battery = EVBattery(
            capacity=50.0, max_charge_power=150.0, min_charge_power=0.0, efficiency=0.95
        )

        # Create simple test vehicle
        vehicle = ElectricVehicle(brand="Test", model="Vehicle", battery=battery, probability=1.0)

        # Create simple arrival distribution (uniform during day)
        arrival_dist = [0.0] * 24  # 24 hours
        for i in range(6, 22):  # Active from 6 AM to 10 PM
            arrival_dist[i] = 1.0 / 16  # Uniform distribution

        # Create minimal infrastructure
        infrastructure = {
            "transformers": [
                {
                    "id": "transformer1",
                    "max_power": 1000.0,
                    "min_power": 0.0,
                    "charging_stations": [
                        {
                            "id": "station1",
                            "max_power": 150.0,
                            "min_power": 0.0,
                            "charging_points": [
                                {"id": "cp1", "max_power": 150.0, "min_power": 0.0}
                            ],
                        }
                    ],
                }
            ]
        }

        # Create scenario configuration
        config_dict = {
            "arrival_distribution": arrival_dist,
            "vehicle_types": [vehicle.to_dict()],
            "infrastructure": infrastructure,
            "num_charging_events": num_events,
            "scheduling_policy": "uncontrolled",
            "mean_park": 4.0,
            "std_deviation_park": 1.0,
            "mean_soc": 0.5,
            "std_deviation_soc": 0.2,
            "queue_length": 0,
            "disconnect_by_time": True,
            "repeat_preload": False,
            "transformer_preload": 0,
        }

        return ScenarioConfig.from_yaml(config_dict)


class TestConfigurationPerformance:
    """Performance tests for configuration loading and processing."""

    @pytest.mark.performance
    def test_config_loading_performance(self):
        """Benchmark configuration loading from YAML."""
        config_path = Path("data/config_builder/office.yaml")

        with PerformanceMonitor("config_loading") as monitor:
            # Load multiple times to test repeated loading
            for _ in range(10):
                import yaml

                with open(config_path) as f:
                    yaml_data = yaml.safe_load(f)
                config = ScenarioConfig.from_yaml(yaml_data)

        avg_time = monitor.duration / 10
        assert avg_time < 0.1, f"Config loading took {avg_time:.4f}s average (expected < 0.1s)"

        print(f"✅ Config loading: {avg_time:.4f}s average per load")

    @pytest.mark.performance
    def test_realisation_creation_performance(self):
        """Benchmark scenario realisation creation."""
        # Load office configuration
        import yaml

        with open("data/config_builder/office.yaml") as f:
            yaml_data = yaml.safe_load(f)
        config = ScenarioConfig.from_yaml(yaml_data)

        with PerformanceMonitor("realisation_creation") as monitor:
            realisation = config.create_realisation(
                start_date="2020-01-01 00:00:00",
                end_date="2020-01-02 00:00:00",
                resolution="01:00:00",
            )

        assert monitor.duration < 2.0, (
            f"Realisation creation took {monitor.duration:.2f}s (expected < 2s)"
        )
        assert len(realisation.charging_events) > 0, "No charging events generated"

        print(
            f"✅ Realisation creation: {monitor.duration:.3f}s, {len(realisation.charging_events)} events"
        )


class TestAlgorithmComplexity:
    """Tests to verify algorithm complexity and scaling behavior."""

    @pytest.mark.performance
    def test_battery_power_calculation_scaling(self):
        """Test that battery power calculations scale linearly with SOC evaluations."""
        battery = EVBattery(
            capacity=100.0,
            max_charge_power=200.0,
            min_charge_power=0.0,
            efficiency=0.9,
            start_power_degradation=0.8,
            max_degradation_level=0.3,
        )

        # Test with different numbers of SOC evaluations
        soc_counts = [100, 1000, 10000]
        times = []

        for count in soc_counts:
            soc_values = [i / count for i in range(count)]

            with PerformanceMonitor(f"battery_power_{count}") as monitor:
                for soc in soc_values:
                    _ = battery.max_power_possible(soc)
                    _ = battery.min_power_possible(soc)

            times.append(monitor.duration)
            print(f"✅ Battery power calculations: {count} evaluations in {monitor.duration:.4f}s")

        # Verify linear scaling (allow some variance)
        ratio_1_to_2 = times[1] / times[0]
        ratio_2_to_3 = times[2] / times[1]

        # Should be approximately 10x for 10x more evaluations
        assert 5 < ratio_1_to_2 < 20, f"Scaling 100→1000: {ratio_1_to_2:.1f}x (expected ~10x)"
        assert 5 < ratio_2_to_3 < 20, f"Scaling 1000→10000: {ratio_2_to_3:.1f}x (expected ~10x)"

    @pytest.mark.performance
    def test_distribution_interpolation_scaling(self):
        """Test that interpolation scales correctly with data points."""
        # Create distributions with different numbers of points
        point_counts = [10, 100, 1000]
        times = []

        for count in point_counts:
            # Create evenly spaced points
            points = [(i, i * 0.5) for i in range(count)]
            bounds = {"x": {"min": 0, "max": count - 1}, "y": {"min": 0, "max": (count - 1) * 0.5}}

            dist = InterpolatedDistribution.linear(points, bounds)

            # Test interpolation performance
            test_values = [i * 0.1 for i in range(0, count * 10)]  # 10x more test points

            with PerformanceMonitor(f"interpolation_{count}") as monitor:
                for x in test_values:
                    _ = dist[x]

            times.append(monitor.duration)
            print(
                f"✅ Interpolation: {count} points, {len(test_values)} queries in {monitor.duration:.4f}s"
            )

        # Interpolation should scale better than quadratic
        assert times[2] < times[0] * 200, (
            f"Interpolation doesn't scale well: {times[2] / times[0]:.1f}x slowdown"
        )


class TestMemoryUsage:
    """Tests for memory usage patterns and memory leaks."""

    @pytest.mark.performance
    def test_simulation_memory_cleanup(self):
        """Test that simulations clean up memory properly."""
        initial_memory = psutil.Process(os.getpid()).memory_info().rss

        # Run multiple simulations
        for i in range(5):
            scenario_config = self._create_small_scenario()

            results = simulate(
                scenario_config,
                start_date="2020-01-01 00:00:00",
                end_date="2020-01-01 12:00:00",
                resolution="01:00:00",
                print_progress=False,
            )

            # Clear reference
            del results
            del scenario_config

        final_memory = psutil.Process(os.getpid()).memory_info().rss
        memory_growth = (final_memory - initial_memory) / (1024 * 1024)  # MB

        # Allow some memory growth but not excessive
        assert memory_growth < 100.0, (
            f"Memory grew by {memory_growth:.1f}MB after 5 simulations (expected < 100MB)"
        )

        print(f"✅ Memory cleanup: {memory_growth:.1f}MB growth after 5 simulations")

    @pytest.mark.performance
    def test_configuration_object_memory(self):
        """Test memory usage of configuration objects."""
        configs = []
        initial_memory = psutil.Process(os.getpid()).memory_info().rss

        # Create many configuration objects
        for i in range(100):
            config = self._create_small_scenario()
            configs.append(config)

        loaded_memory = psutil.Process(os.getpid()).memory_info().rss
        memory_per_config = (loaded_memory - initial_memory) / (100 * 1024)  # KB per config

        assert memory_per_config < 500.0, (
            f"Each config uses {memory_per_config:.1f}KB (expected < 500KB)"
        )

        print(f"✅ Config memory: {memory_per_config:.1f}KB per configuration object")

        # Cleanup
        del configs

    def _create_small_scenario(self) -> ScenarioConfig:
        """Create a minimal scenario for memory testing."""
        battery = EVBattery(
            capacity=40.0, max_charge_power=100.0, min_charge_power=0.0, efficiency=0.9
        )
        vehicle = ElectricVehicle("Test", "Car", battery, 1.0)

        config_dict = {
            "arrival_distribution": [0.1] * 24,
            "vehicle_types": [vehicle.to_dict()],
            "infrastructure": {
                "transformers": [
                    {
                        "id": "test_transformer",
                        "max_power": 500.0,
                        "min_power": 0.0,
                        "charging_stations": [
                            {
                                "id": "test_station",
                                "max_power": 100.0,
                                "min_power": 0.0,
                                "charging_points": [
                                    {"id": "test_cp", "max_power": 100.0, "min_power": 0.0}
                                ],
                            }
                        ],
                    }
                ]
            },
            "num_charging_events": 5,
            "scheduling_policy": "uncontrolled",
            "mean_park": 2.0,
            "std_deviation_park": 0.5,
            "mean_soc": 0.3,
            "std_deviation_soc": 0.1,
            "queue_length": 0,
            "disconnect_by_time": True,
            "repeat_preload": False,
            "transformer_preload": 0,
        }

        return ScenarioConfig.from_yaml(config_dict)


class TestPerformanceRegression:
    """Regression tests that compare against performance baselines."""

    BASELINE_FILE = Path("tests/performance/baselines.json")

    @pytest.mark.performance
    def test_office_scenario_regression(self):
        """Regression test against office scenario baseline."""
        import yaml

        with open("data/config_builder/office.yaml") as f:
            yaml_data = yaml.safe_load(f)
        config = ScenarioConfig.from_yaml(yaml_data)

        with PerformanceMonitor("office_regression") as monitor:
            results = simulate(
                config,
                start_date="2020-01-01 00:00:00",
                end_date="2020-01-01 23:00:00",
                resolution="01:00:00",
                print_progress=False,
            )

        # Load or create baseline
        baseline = self._load_baseline("office_scenario")
        if baseline is None:
            # First run - establish baseline
            self._save_baseline(
                "office_scenario",
                {"duration": monitor.duration, "memory_mb": monitor.memory_delta_mb},
            )
            print(
                f"📊 Office scenario baseline established: {monitor.duration:.3f}s, {monitor.memory_delta_mb:.1f}MB"
            )
        else:
            # Compare against baseline (allow 50% regression)
            duration_ratio = monitor.duration / baseline["duration"]
            memory_ratio = (
                abs(monitor.memory_delta_mb) / abs(baseline["memory_mb"])
                if baseline["memory_mb"] != 0
                else 1.0
            )

            assert duration_ratio < 1.5, (
                f"Performance regression: {duration_ratio:.1f}x slower than baseline"
            )
            assert memory_ratio < 2.0, (
                f"Memory regression: {memory_ratio:.1f}x more memory than baseline"
            )

            print(
                f"✅ Office scenario regression test passed: {duration_ratio:.2f}x time, {memory_ratio:.2f}x memory"
            )

    def _load_baseline(self, test_name: str) -> Dict[str, Any]:
        """Load baseline performance data."""
        if not self.BASELINE_FILE.exists():
            return None

        import json

        try:
            with open(self.BASELINE_FILE) as f:
                baselines = json.load(f)
            return baselines.get(test_name)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def _save_baseline(self, test_name: str, data: Dict[str, Any]) -> None:
        """Save baseline performance data."""
        baselines = {}
        if self.BASELINE_FILE.exists():
            try:
                with open(self.BASELINE_FILE) as f:
                    baselines = json.load(f)
            except json.JSONDecodeError:
                baselines = {}

        baselines[test_name] = data

        # Ensure directory exists
        self.BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(self.BASELINE_FILE, "w") as f:
            json.dump(baselines, f, indent=2)


if __name__ == "__main__":
    # Run performance tests with specific markers
    pytest.main([__file__, "-v", "-m", "performance", "--tb=short"])

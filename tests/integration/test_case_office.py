#!/usr/bin/env python3
"""Test case for office.yaml configuration."""

import pytest
import yaml
from elvis import ScenarioConfig, simulate


class TestOfficeConfig:
    """Test suite for office scenario configuration."""

    def test_office_config_loading(self):
        """Test that office.yaml loads correctly."""
        with open("data/config_builder/office.yaml", "r") as f:
            yaml_str = yaml.safe_load(f)

        config = ScenarioConfig.from_yaml(yaml_str)

        assert config.num_charging_events == 250
        assert len(config.vehicle_types) == 10
        assert config.mean_park == 8
        assert config.scheduling_policy is not None

    def test_office_simulation_short(self):
        """Test short simulation with office config."""
        with open("data/config_builder/office.yaml", "r") as f:
            yaml_str = yaml.safe_load(f)
        config = ScenarioConfig.from_yaml(yaml_str)

        # 24-hour simulation
        results = simulate(
            config,
            start_date="2020-01-01 00:00:00",
            end_date="2020-01-01 23:00:00",
            resolution="01:00:00",
        )

        load_profile = results.aggregate_load_profile(24)
        assert len(load_profile) == 24
        assert max(load_profile) >= 0
        assert all(load >= 0 for load in load_profile)

    def test_office_simulation_week(self):
        """Test week-long simulation with office config."""
        with open("data/config_builder/office.yaml", "r") as f:
            yaml_str = yaml.safe_load(f)
        config = ScenarioConfig.from_yaml(yaml_str)

        # 1-week simulation
        results = simulate(
            config,
            start_date="2020-01-01 00:00:00",
            end_date="2020-01-07 23:00:00",
            resolution="01:00:00",
        )

        time_steps = 7 * 24 + 1  # 169 hours
        load_profile = results.aggregate_load_profile(time_steps)

        assert len(load_profile) == time_steps
        assert max(load_profile) > 0
        print(
            f"Office scenario - Peak load: {max(load_profile):.2f} kW, Average: {sum(load_profile) / len(load_profile):.2f} kW"
        )

#!/usr/bin/env python3
"""Test case for PnR.yaml configuration."""

import pytest
import yaml
from elvis import ScenarioConfig, simulate


class TestPnRConfig:
    """Test suite for PnR (Park and Ride) scenario configuration."""

    def test_pnr_config_loading(self):
        """Test that PnR.yaml loads correctly."""
        with open("data/config_builder/PnR.yaml", "r") as f:
            yaml_str = yaml.safe_load(f)

        config = ScenarioConfig.from_yaml(yaml_str)

        assert hasattr(config, "num_charging_events")
        assert len(config.vehicle_types) > 0
        assert config.scheduling_policy is not None

    def test_pnr_simulation_short(self):
        """Test short simulation with PnR config."""
        with open("data/config_builder/PnR.yaml", "r") as f:
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
        print(
            f"PnR scenario - Peak load: {max(load_profile):.2f} kW, Average: {sum(load_profile) / len(load_profile):.2f} kW"
        )

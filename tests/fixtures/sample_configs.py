"""Sample configuration data for testing."""

from typing import Any


def get_minimal_config() -> dict[str, Any]:
    """Get minimal valid configuration for testing."""
    return {
        "num_charging_events": 5,
        "mean_park": 4,
        "std_deviation_park": 1,
        "mean_soc": 0.5,
        "std_deviation_soc": 0.1,
        "arrival_distribution": [0.0] * 8 + [1.0] + [0.0] * 159,  # Single peak at hour 8
        "vehicle_types": [
            {
                "model": "Test Vehicle",
                "brand": "Test Brand",
                "probability": 1.0,
                "battery": {
                    "capacity": 50.0,
                    "efficiency": 1.0,
                    "max_charge_power": 22.0,
                    "min_charge_power": 0.0,
                },
            },
        ],
        "infrastructure": {
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
        },
        "queue_length": 0,
        "scheduling_policy": "UC",
        "disconnect_by_time": True,
    }


def get_multi_vehicle_config() -> dict[str, Any]:
    """Get configuration with multiple vehicle types."""
    config = get_minimal_config()
    config["vehicle_types"] = [
        {
            "model": "Model 3",
            "brand": "Tesla",
            "probability": 0.6,
            "battery": {
                "capacity": 75.0,
                "efficiency": 1.0,
                "max_charge_power": 150.0,
                "min_charge_power": 0.0,
            },
        },
        {
            "model": "i3",
            "brand": "BMW",
            "probability": 0.4,
            "battery": {
                "capacity": 33.2,
                "efficiency": 1.0,
                "max_charge_power": 50.0,
                "min_charge_power": 0.0,
            },
        },
    ]
    return config


def get_complex_infrastructure_config() -> dict[str, Any]:
    """Get configuration with complex infrastructure."""
    config = get_minimal_config()
    config["infrastructure"] = {
        "transformers": [
            {
                "id": "transformer1",
                "max_power": 500.0,
                "min_power": 0.0,
                "charging_stations": [
                    {
                        "id": "cs1",
                        "max_power": 150.0,
                        "min_power": 0.0,
                        "charging_points": [
                            {
                                "id": "cp1",
                                "max_power": 75.0,
                                "min_power": 0.0,
                            },
                            {
                                "id": "cp2",
                                "max_power": 75.0,
                                "min_power": 0.0,
                            },
                        ],
                    },
                    {
                        "id": "cs2",
                        "max_power": 150.0,
                        "min_power": 0.0,
                        "charging_points": [
                            {
                                "id": "cp3",
                                "max_power": 150.0,
                                "min_power": 0.0,
                            },
                        ],
                    },
                ],
            },
        ],
    }
    config["num_charging_events"] = 20  # More events for complex infrastructure
    return config


def get_invalid_configs() -> dict[str, dict[str, Any]]:
    """Get various invalid configurations for error testing."""
    return {
        "missing_vehicle_types": {
            "num_charging_events": 5,
            "mean_park": 4,
            "std_deviation_park": 1,
            "mean_soc": 0.5,
            "std_deviation_soc": 0.1,
            # Missing vehicle_types
        },
        "invalid_probability": {
            **get_minimal_config(),
            "vehicle_types": [
                {
                    "model": "Test",
                    "brand": "Test",
                    "probability": 1.5,  # Invalid > 1.0
                    "battery": {
                        "capacity": 50.0,
                        "max_charge_power": 22.0,
                    },
                },
            ],
        },
        "negative_capacity": {
            **get_minimal_config(),
            "vehicle_types": [
                {
                    "model": "Test",
                    "brand": "Test",
                    "probability": 1.0,
                    "battery": {
                        "capacity": -50.0,  # Invalid negative
                        "max_charge_power": 22.0,
                    },
                },
            ],
        },
        "empty_infrastructure": {
            **get_minimal_config(),
            "infrastructure": {"transformers": []},  # Empty infrastructure
        },
    }


def get_performance_test_config() -> dict[str, Any]:
    """Get large configuration for performance testing."""
    config = get_minimal_config()
    config["num_charging_events"] = 1000

    # Large infrastructure with many charging points
    charging_stations = []
    for i in range(10):  # 10 charging stations
        charging_points = []
        for j in range(5):  # 5 charging points each
            charging_points.append(
                {
                    "id": f"cp{i}_{j}",
                    "max_power": 22.0,
                    "min_power": 0.0,
                },
            )

        charging_stations.append(
            {
                "id": f"cs{i}",
                "max_power": 110.0,  # 5 * 22kW
                "min_power": 0.0,
                "charging_points": charging_points,
            },
        )

    config["infrastructure"] = {
        "transformers": [
            {
                "id": "large_transformer",
                "max_power": 1100.0,  # 10 * 110kW
                "min_power": 0.0,
                "charging_stations": charging_stations,
            },
        ],
    }

    return config

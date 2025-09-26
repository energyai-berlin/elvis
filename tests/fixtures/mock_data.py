"""Mock data generators for testing."""

import random
from datetime import datetime, timedelta
from typing import Any


class MockDataGenerator:
    """Generate mock data for testing purposes."""

    def __init__(self, seed: int = 42):
        """Initialize with reproducible random seed."""
        random.seed(seed)

    def generate_arrival_distribution(self, peak_hours: list[int] = None) -> list[float]:
        """Generate a weekly arrival distribution with specified peaks."""
        if peak_hours is None:
            peak_hours = [8, 18]  # 8 AM and 6 PM peaks

        distribution = [0.0] * 168  # 7 days * 24 hours

        for day in range(7):
            for hour in range(24):
                idx = day * 24 + hour

                # Add peaks at specified hours
                if hour in peak_hours:
                    if day < 5:  # Weekdays
                        distribution[idx] = random.uniform(0.8, 1.0)
                    else:  # Weekends
                        distribution[idx] = random.uniform(0.3, 0.5)

                # Add some background noise
                elif 6 <= hour <= 22:  # Daytime hours
                    if day < 5:  # Weekdays
                        distribution[idx] = random.uniform(0.1, 0.3)
                    else:  # Weekends
                        distribution[idx] = random.uniform(0.05, 0.2)
                else:  # Night hours
                    distribution[idx] = random.uniform(0.0, 0.1)

        return distribution

    def generate_vehicle_types(self, count: int = 3) -> list[dict[str, Any]]:
        """Generate a list of vehicle type configurations."""
        brands = ["Tesla", "BMW", "Audi", "Volkswagen", "Mercedes", "Nissan"]
        models = ["Model S", "Model 3", "i3", "e-tron", "e-Golf", "EQC", "Leaf"]

        vehicles = []
        remaining_probability = 1.0

        for i in range(count):
            if i == count - 1:  # Last vehicle gets remaining probability
                probability = remaining_probability
            else:
                probability = random.uniform(0.1, remaining_probability - 0.1 * (count - i - 1))
                remaining_probability -= probability

            brand = random.choice(brands)
            model = random.choice(models)
            capacity = random.uniform(30.0, 100.0)
            max_power = random.uniform(22.0, 150.0)

            vehicles.append(
                {
                    "model": model,
                    "brand": brand,
                    "probability": round(probability, 3),
                    "battery": {
                        "capacity": round(capacity, 1),
                        "efficiency": 1.0,
                        "max_charge_power": round(max_power, 1),
                        "min_charge_power": 0.0,
                    },
                },
            )

        return vehicles

    def generate_infrastructure(
        self,
        num_transformers: int = 1,
        num_stations_per_transformer: int = 5,
        num_points_per_station: int = 2,
    ) -> dict[str, Any]:
        """Generate infrastructure configuration."""
        transformers = []

        for t_idx in range(num_transformers):
            charging_stations = []
            total_station_power = 0.0

            for s_idx in range(num_stations_per_transformer):
                charging_points = []
                total_point_power = 0.0

                for p_idx in range(num_points_per_station):
                    power = random.choice([3.7, 7.4, 11.0, 22.0, 43.0])
                    charging_points.append(
                        {
                            "id": f"cp_{t_idx}_{s_idx}_{p_idx}",
                            "max_power": power,
                            "min_power": 0.0,
                        },
                    )
                    total_point_power += power

                charging_stations.append(
                    {
                        "id": f"cs_{t_idx}_{s_idx}",
                        "max_power": total_point_power,
                        "min_power": 0.0,
                        "charging_points": charging_points,
                    },
                )
                total_station_power += total_point_power

            transformers.append(
                {
                    "id": f"transformer_{t_idx}",
                    "max_power": total_station_power,
                    "min_power": 0.0,
                    "charging_stations": charging_stations,
                },
            )

        return {"transformers": transformers}

    def generate_time_series_data(
        self,
        start_date: str,
        end_date: str,
        resolution_hours: int = 1,
    ) -> list[datetime]:
        """Generate time series for testing."""
        start = datetime.fromisoformat(start_date.replace(" ", "T"))
        end = datetime.fromisoformat(end_date.replace(" ", "T"))

        times = []
        current = start
        while current <= end:
            times.append(current)
            current += timedelta(hours=resolution_hours)

        return times

    def generate_load_profile(self, hours: int, max_power: float = 100.0) -> list[float]:
        """Generate a realistic load profile."""
        profile = []

        for hour in range(hours):
            # Create daily pattern (higher during day, lower at night)
            hour_of_day = hour % 24

            if 6 <= hour_of_day <= 22:  # Daytime
                base_load = random.uniform(0.3, 0.8) * max_power
            else:  # Nighttime
                base_load = random.uniform(0.1, 0.3) * max_power

            # Add some random variation
            variation = random.uniform(-0.2, 0.2) * base_load
            load = max(0.0, base_load + variation)

            profile.append(round(load, 2))

        return profile


# Global instance for easy access
mock_generator = MockDataGenerator()

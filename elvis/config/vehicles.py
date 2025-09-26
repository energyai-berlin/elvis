"""Vehicle type configuration components.

This module contains vehicle-related configuration logic
such as vehicle type management, battery specifications,
and vehicle behavior parameters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from elvis.battery import EVBattery
from elvis.vehicle import ElectricVehicle

if TYPE_CHECKING:
    from elvis.config.scenario import ScenarioConfig


class VehicleMixin:
    """Mixin class for vehicle-related configuration methods."""

    def with_vehicle_types(
        self: ScenarioConfig,
        vehicle_types: list[Union[ElectricVehicle, dict[str, Any]]] | None = None,
        **kwargs: Any,
    ) -> ScenarioConfig:
        """Update the vehicle types to use.

        Args:
            vehicle_types: List of ElectricVehicle instances or dictionaries with vehicle configuration
            **kwargs: Vehicle configuration parameters for single vehicle setup

        Returns:
            Self for method chaining
        """
        if vehicle_types is not None:
            for vehicle_type in vehicle_types:
                if isinstance(vehicle_type, ElectricVehicle):
                    self.add_vehicle_types(vehicle_type=vehicle_type)
                elif isinstance(vehicle_type, dict):
                    self.add_vehicle_types(**vehicle_type)
                else:
                    raise TypeError(
                        "Using with_vehicle_types with a list: All list entries "
                        "must either be of type ElectricVehicle or dict, containing "
                        "all relevant information."
                    )
            return self

        self.add_vehicle_types(**kwargs)
        return self

    def add_vehicle_types(
        self: ScenarioConfig,
        vehicle_type: Union[ElectricVehicle, list[ElectricVehicle], None] = None,
        **kwargs: Any,
    ) -> ScenarioConfig:
        """Add a supported vehicle type to this configuration or a list of vehicle types.

        If no instance of vehicle type is passed an instance of vehicle_type is created if
        kwargs contains the necessary keys.

        Args:
            vehicle_type: ElectricVehicle instance or list of ElectricVehicle instances
            **kwargs: Vehicle configuration parameters:
                - brand (str): Brand of the vehicle
                - model (str): Model of the vehicle
                - probability (float): Probability weight for this vehicle type
                - battery (EVBattery or dict): Battery instance or battery configuration dict
                  If dict, must contain:
                  - capacity (float): Capacity of the battery in kWh
                  - max_charge_power (float): Max power in kW
                  - min_charge_power (float): Min power in kW
                  - efficiency (float): Battery efficiency [0, 1]
                  - start_power_degradation (float, optional): SOC level for power degradation
                  - max_degradation_level (float, optional): Maximum degradation factor

        Returns:
            Self for method chaining

        Raises:
            AssertionError: If required parameters are missing or invalid types provided
            TypeError: If vehicle_type is not a supported type
        """
        # if list with multiple vehicle_type instances is passed add multiple
        if isinstance(vehicle_type, list):
            for vehicle in vehicle_type:
                assert isinstance(vehicle, ElectricVehicle), (
                    f"All vehicles in list must be ElectricVehicle instances, "
                    f"got {type(vehicle).__name__}"
                )
                self.vehicle_types.append(vehicle)
            return self

        # if an instance of vehicle type is passed assign
        elif vehicle_type is not None:
            assert isinstance(vehicle_type, ElectricVehicle), (
                f"vehicle_type must be ElectricVehicle instance, got {type(vehicle_type).__name__}"
            )
            self.vehicle_types.append(vehicle_type)
            return self

        # Create vehicle from kwargs
        assert "brand" in kwargs, "Vehicle brand is required"
        assert "model" in kwargs, "Vehicle model is required"
        assert "probability" in kwargs, "Vehicle probability is required"
        assert "battery" in kwargs, "Battery configuration is required"

        brand: str = str(kwargs["brand"])
        model: str = str(kwargs["model"])
        probability: float = kwargs["probability"]

        # Validate probability
        assert isinstance(probability, (int, float)), "Probability must be a number"
        assert 0 <= probability <= 1, "Probability must be between 0 and 1"

        # if all fields of ElectricVehicle are passed and an instance of EVBattery is already made
        if isinstance(kwargs["battery"], EVBattery):
            battery = kwargs["battery"]
            self.vehicle_types.append(ElectricVehicle(brand, model, battery, probability))
            return self

        # if there is no instance of EVBattery check if all parameters are passed.
        battery_config = kwargs["battery"]
        assert isinstance(battery_config, dict), "Battery configuration must be a dictionary"

        required_battery_keys = ["capacity", "max_charge_power", "min_charge_power", "efficiency"]
        for key in required_battery_keys:
            assert key in battery_config, f"Battery configuration missing required key: {key}"

        capacity: float = float(battery_config["capacity"])
        max_charge_power: float = float(battery_config["max_charge_power"])
        min_charge_power: float = float(battery_config["min_charge_power"])
        efficiency: float = float(battery_config["efficiency"])

        # Validate battery parameters
        assert capacity > 0, "Battery capacity must be positive"
        assert max_charge_power > 0, "Max charge power must be positive"
        assert min_charge_power >= 0, "Min charge power must be non-negative"
        assert min_charge_power <= max_charge_power, (
            "Min charge power must not exceed max charge power"
        )
        assert 0 < efficiency <= 1, "Battery efficiency must be between 0 and 1"

        # Power degradations when battery reaches certain SOC level shall be considered
        if (
            "start_power_degradation" in battery_config
            and "max_degradation_level" in battery_config
        ):
            start_power_degradation: float = float(battery_config["start_power_degradation"])
            max_degradation_level: float = float(battery_config["max_degradation_level"])

            # Validate degradation parameters
            assert 0 <= start_power_degradation <= 1, (
                "Start power degradation must be between 0 and 1"
            )
            assert 0 <= max_degradation_level <= 1, "Max degradation level must be between 0 and 1"

            battery = EVBattery(
                capacity=capacity,
                max_charge_power=max_charge_power,
                min_charge_power=min_charge_power,
                efficiency=efficiency,
                start_power_degradation=start_power_degradation,
                max_degradation_level=max_degradation_level,
            )
        # No SOC-dependent power degradations considered
        else:
            battery = EVBattery(
                capacity=capacity,
                max_charge_power=max_charge_power,
                min_charge_power=min_charge_power,
                efficiency=efficiency,
            )

        # get instance of ElectricVehicle with initialized battery
        self.vehicle_types.append(ElectricVehicle(brand, model, battery, probability))
        return self

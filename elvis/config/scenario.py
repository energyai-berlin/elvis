"""Core scenario configuration classes for ELVIS.

This module contains the main ScenarioConfig and ScenarioRealisation classes
that were previously in the monolithic config.py file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from elvis.types import (
    ArrivalDistribution,
    ConfigDict,
    FilePath,
    TimeDelta,
    TimeSeriesData,
    TimeStamp,
)

if TYPE_CHECKING:
    from elvis.charging_event import ChargingEvent
    from elvis.vehicle import ElectricVehicle

from elvis.sched import schedulers


class ScenarioConfig:
    """Describes a scenario defined by its stochastic distributions and hardware parameters."""

    def __init__(self, **kwargs: Any) -> None:
        # Time series data
        self.emissions_scenario: FilePath | None = None
        self.emissions_scenario_res_data: TimeSeriesData | None = None
        self.emissions_scenario_repeat: bool | None = None
        self.emissions_scenario_col_pos: int = 0
        self.renewables_scenario: FilePath | None = None

        self.transformer_preload: FilePath | None = None
        self.transformer_preload_res_data: TimeSeriesData | None = None
        self.transformer_preload_repeat: bool = False
        self.transformer_preload_col_pos: int = 0

        # Event parameters
        self.sample_method: str = "independent_normal_dist"  # or GMM
        self.arrival_distribution: ArrivalDistribution | None = None
        self.vehicle_types: list[ElectricVehicle] = []
        self.mean_park: float | None = None
        self.std_deviation_park: float | None = None
        self.mean_soc: float | None = None
        self.std_deviation_soc: float | None = None
        self.max_parking_time: int = 24
        self.num_charging_events: int | None = None
        self.charging_events: list[ChargingEvent] | None = None
        self.gmm_means: list[list[float]] | None = None
        self.gmm_weights: list[float] | None = None
        self.gmm_covariances: list[list[list[float]]] | None = None

        # Infrastructure (behaviour)
        self.infrastructure: dict[str, Any] | None = None
        self.queue_length: int | None = None
        self.disconnect_by_time: bool | None = None
        self.opening_hours: tuple[TimeStamp, TimeStamp] | None = None
        self.scheduling_policy: schedulers.BaseScheduler | None = None
        self.df_charging_period: TimeDelta | None = None

        if "emissions_scenario" in kwargs:
            self.with_emissions_scenario(kwargs["emissions_scenario"])
        if "renewables_scenario" in kwargs:
            self.renewables_scenario = kwargs["renewables_scenario"]
        if "transformer_preload" in kwargs:
            self.transformer_preload = kwargs["transformer_preload"]

        if "vehicle_types" in kwargs:
            self.vehicle_types = kwargs["vehicle_types"]

        if "opening_hours" in kwargs:
            self.with_opening_hours(kwargs["opening_hours"])

        if "sample_method" in kwargs:
            self.sample_method = kwargs["sample_method"]

        # Import the remaining content from the original config.py
        # This is a placeholder - in Phase 1, we're just setting up the structure
        # The actual method implementations will be migrated in subsequent phases
        self._initialize_from_kwargs(kwargs)

    def _initialize_from_kwargs(self, kwargs: dict[str, Any]) -> None:
        """Initialize remaining attributes from kwargs.

        This method contains the initialization logic from the original config.py
        that needs to be properly refactored in future phases.
        """
        # TODO: In Phase 2, move specific initialization logic to focused modules

    # Placeholder methods - actual implementations will be migrated from config.py
    def __str__(self) -> str:
        """String representation of the configuration."""
        return f"ScenarioConfig(num_charging_events={self.num_charging_events})"

    def to_dict(self) -> ConfigDict:
        """Convert configuration to dictionary."""
        raise NotImplementedError("Migration from config.py pending")

    @classmethod
    def from_dict(cls, dictionary: ConfigDict) -> ScenarioConfig:
        """Create configuration from dictionary."""
        raise NotImplementedError("Migration from config.py pending")

    def to_yaml(self, yaml_file: FilePath) -> None:
        """Save configuration to YAML file."""
        raise NotImplementedError("Migration from config.py pending")

    @classmethod
    def from_yaml(cls, yaml_str: ConfigDict) -> ScenarioConfig:
        """Create configuration from YAML string."""
        raise NotImplementedError("Migration from config.py pending")

    def create_realisation(self, start_date, end_date, resolution):
        """Create a scenario realisation for simulation."""
        raise NotImplementedError("Migration from config.py pending")

    def add_vehicle_types(self, vehicle_type=None, **kwargs):
        """Add vehicle types to the configuration."""
        raise NotImplementedError("Migration from config.py pending")


class ScenarioRealisation:
    """A realised scenario ready for simulation."""

    def __init__(self, config=None, **kwargs):
        """Initialize scenario realisation."""
        raise NotImplementedError("Migration from config.py pending")

    def to_dict(self):
        """Convert realisation to dictionary."""
        raise NotImplementedError("Migration from config.py pending")

    @classmethod
    def from_dict(cls, dictionary):
        """Create realisation from dictionary."""
        raise NotImplementedError("Migration from config.py pending")

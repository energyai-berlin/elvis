"""Type definitions and type aliases for the ELVIS simulation system.

This module provides comprehensive type annotations for better code safety,
documentation, and IDE support throughout the ELVIS codebase.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable, Sequence
from typing import (
    Any,
    Protocol,
    TypeAlias,
    TypeVar,
    Union,
)

import pandas as pd

# =============================================================================
# Basic Type Aliases
# =============================================================================

# Numeric types for physical quantities
Numeric: TypeAlias = int | float
Energy: TypeAlias = float  # kWh
Power: TypeAlias = float  # kW or W
Current: TypeAlias = float  # A
Voltage: TypeAlias = float  # V
Efficiency: TypeAlias = float  # ratio [0,1]
SOC: TypeAlias = float  # State of charge [0,1]
Probability: TypeAlias = float  # [0,1]
TimeStamp: TypeAlias = datetime.datetime
TimeDelta: TypeAlias = datetime.timedelta

# Data structure types
TimeSeriesData: TypeAlias = list[tuple[TimeStamp, float]]
LoadProfile: TypeAlias = list[Power]
ArrivalDistribution: TypeAlias = list[Probability]
ConfigDict: TypeAlias = dict[str, Any]
ParameterDict: TypeAlias = dict[str, str | int | float | bool]

# Identifiers
NodeID: TypeAlias = str
ChargingPointID: TypeAlias = str
ChargingStationID: TypeAlias = str
TransformerID: TypeAlias = str
VehicleID: TypeAlias = str
EventID: TypeAlias = str

# =============================================================================
# Generic Types
# =============================================================================

T = TypeVar("T")
K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type

# Generic result type for operations that might fail
Result = TypeVar("Result", bound=Any)

# =============================================================================
# Simulation Time Types
# =============================================================================


class TimeRange(Protocol):
    """Protocol for time range specifications."""

    start: TimeStamp
    end: TimeStamp
    resolution: TimeDelta

    def get_time_steps(self) -> list[TimeStamp]:
        """Get all time steps in the range."""
        ...

    def duration(self) -> TimeDelta:
        """Get total duration of the time range."""
        ...


class SimulationTime:
    """Represents simulation time parameters."""

    def __init__(self, start: TimeStamp, end: TimeStamp, resolution: TimeDelta) -> None:
        self.start = start
        self.end = end
        self.resolution = resolution

    def get_time_steps(self) -> list[TimeStamp]:
        """Get all time steps in the simulation period."""
        steps = []
        current = self.start
        while current <= self.end:
            steps.append(current)
            current += self.resolution
        return steps

    def duration(self) -> TimeDelta:
        """Get total simulation duration."""
        return self.end - self.start

    @property
    def num_steps(self) -> int:
        """Number of simulation steps."""
        return int(self.duration() / self.resolution) + 1


# =============================================================================
# Configuration Types
# =============================================================================


class BatteryConfig(Protocol):
    """Configuration for battery parameters."""

    capacity: Energy
    max_charge_power: Power
    min_charge_power: Power
    efficiency: Efficiency


class VehicleConfig(Protocol):
    """Configuration for vehicle types."""

    brand: str
    model: str
    battery: BatteryConfig
    probability: Probability


class ChargingPointConfig(Protocol):
    """Configuration for charging points."""

    id: ChargingPointID
    max_power: Power
    min_power: Power
    efficiency: Efficiency


class ChargingStationConfig(Protocol):
    """Configuration for charging stations."""

    id: ChargingStationID
    charging_points: list[ChargingPointConfig]
    max_power: Power
    min_power: Power


class TransformerConfig(Protocol):
    """Configuration for transformers."""

    id: TransformerID
    charging_stations: list[ChargingStationConfig]
    max_power: Power
    min_power: Power


class InfrastructureConfig(Protocol):
    """Configuration for entire infrastructure."""

    transformers: list[TransformerConfig]


class ScenarioParams(Protocol):
    """Core scenario parameters."""

    num_charging_events: int
    mean_park: float
    std_deviation_park: float
    mean_soc: float
    std_deviation_soc: float
    scheduling_policy: str
    queue_length: int
    disconnect_by_time: bool


# =============================================================================
# Simulation Component Types
# =============================================================================


class ChargingEvent(Protocol):
    """Protocol for charging events."""

    arrival_time: TimeStamp
    departure_time: TimeStamp
    initial_soc: SOC
    desired_soc: SOC
    vehicle_id: VehicleID

    def energy_demand(self) -> Energy:
        """Calculate energy demand for this charging event."""
        ...

    def duration(self) -> TimeDelta:
        """Get parking duration."""
        ...


class BatteryProtocol(Protocol):
    """Protocol for battery implementations."""

    capacity: Energy
    max_charge_power: Power
    min_charge_power: Power
    efficiency: Efficiency

    def max_power_possible(self, current_soc: SOC) -> Power:
        """Calculate maximum possible charging power at given SOC."""
        ...

    def to_dict(self) -> ConfigDict:
        """Convert battery to dictionary representation."""
        ...


class VehicleProtocol(Protocol):
    """Protocol for vehicle implementations."""

    brand: str
    model: str
    battery: BatteryProtocol
    probability: Probability

    def to_dict(self) -> ConfigDict:
        """Convert vehicle to dictionary representation."""
        ...


class ChargingPointProtocol(Protocol):
    """Protocol for charging point implementations."""

    id: ChargingPointID
    max_power: Power
    min_power: Power
    occupied: bool

    def assign_vehicle(self, event: ChargingEvent) -> bool:
        """Assign a charging event to this charging point."""
        ...

    def release_vehicle(self) -> None:
        """Release the currently assigned vehicle."""
        ...

    def get_power_profile(self, time_steps: list[TimeStamp]) -> LoadProfile:
        """Get power consumption profile over time."""
        ...


class ChargingStationProtocol(Protocol):
    """Protocol for charging station implementations."""

    id: ChargingStationID
    charging_points: list[ChargingPointProtocol]
    max_power: Power

    def find_available_point(self) -> ChargingPointProtocol | None:
        """Find an available charging point."""
        ...

    def get_total_load(self, timestamp: TimeStamp) -> Power:
        """Get total power consumption at given timestamp."""
        ...


# =============================================================================
# Scheduler Types
# =============================================================================


class SchedulingDecision(Protocol):
    """Represents a scheduling decision."""

    event: ChargingEvent
    charging_point: ChargingPointProtocol | None
    scheduled_power: Power
    priority: float


class SchedulerProtocol(Protocol):
    """Protocol for charging schedulers."""

    def schedule_event(
        self, event: ChargingEvent, available_points: list[ChargingPointProtocol]
    ) -> SchedulingDecision | None:
        """Schedule a charging event to an available point."""
        ...

    def optimize_power_allocation(
        self, active_events: list[ChargingEvent], timestamp: TimeStamp
    ) -> dict[EventID, Power]:
        """Optimize power allocation among active charging events."""
        ...


# =============================================================================
# Result Types
# =============================================================================


class SimulationResult(Protocol):
    """Protocol for simulation results."""

    def aggregate_load_profile(self, num_steps: int) -> LoadProfile:
        """Get aggregated load profile for the simulation."""
        ...

    def get_utilization_stats(self) -> dict[str, float]:
        """Get infrastructure utilization statistics."""
        ...

    def get_energy_metrics(self) -> dict[str, float]:
        """Get energy-related metrics."""
        ...

    def export_to_dataframe(self) -> pd.DataFrame:
        """Export results to pandas DataFrame."""
        ...


class ResultMetrics(Protocol):
    """Metrics derived from simulation results."""

    total_energy_delivered: Energy
    peak_power_demand: Power
    average_utilization: float
    successful_charging_events: int
    failed_charging_events: int
    average_charging_time: float


# =============================================================================
# Data Processing Types
# =============================================================================

# Function type for data transformations
DataTransformer: TypeAlias = Callable[[Any], Any]
Validator: TypeAlias = Callable[[Any], bool]
AggregationFunction: TypeAlias = Callable[[Sequence[float]], float]


# Distribution types
class DistributionProtocol(Protocol):
    """Protocol for probability distributions."""

    def sample(self, size: int) -> list[float]:
        """Generate samples from the distribution."""
        ...

    def pdf(self, x: float) -> float:
        """Probability density function."""
        ...

    def cdf(self, x: float) -> float:
        """Cumulative distribution function."""
        ...


# =============================================================================
# Error and Validation Types
# =============================================================================


class ValidationError(Exception):
    """Custom exception for validation errors."""


class ConfigurationError(Exception):
    """Custom exception for configuration errors."""


class SimulationError(Exception):
    """Custom exception for simulation errors."""


# Validator function types
ConfigValidator: TypeAlias = Callable[[ConfigDict], bool]
ParameterValidator: TypeAlias = Callable[[str, Any], bool]

# =============================================================================
# File I/O Types
# =============================================================================

# Path types
FilePath: TypeAlias = Union[str, "os.PathLike[str]"]
ConfigFile: TypeAlias = FilePath
ResultFile: TypeAlias = FilePath

# Data export formats
ExportFormat: TypeAlias = Union["csv", "json", "yaml", "pickle", "hdf5"]

# =============================================================================
# Advanced Types for Extension
# =============================================================================


class Plugin(Protocol):
    """Protocol for plugin architecture."""

    name: str
    version: str

    def initialize(self, config: ConfigDict) -> None:
        """Initialize the plugin with configuration."""
        ...

    def execute(self, context: Any) -> Any:
        """Execute plugin functionality."""
        ...


class Observer(Protocol):
    """Protocol for observer pattern implementation."""

    def notify(self, event: str, data: Any) -> None:
        """Handle notification of events."""
        ...


# Callback types
EventCallback: TypeAlias = Callable[[str, Any], None]
ProgressCallback: TypeAlias = Callable[[float], None]  # Progress as percentage

# =============================================================================
# Type Utilities
# =============================================================================


def ensure_numeric(value: Any) -> Numeric:
    """Ensure a value is numeric, converting if necessary."""
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (ValueError, TypeError) as e:
        raise TypeError(f"Cannot convert {value} to numeric type") from e


def ensure_positive(value: Numeric, name: str = "value") -> Numeric:
    """Ensure a numeric value is positive."""
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def ensure_probability(value: Numeric, name: str = "probability") -> Probability:
    """Ensure a value is a valid probability [0,1]."""
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")
    return float(value)


def ensure_soc(value: Numeric, name: str = "SOC") -> SOC:
    """Ensure a value is a valid state of charge [0,1]."""
    return ensure_probability(value, name)


# Type guards
def is_valid_timestamp(value: Any) -> bool:
    """Check if value is a valid timestamp."""
    return isinstance(value, datetime.datetime)


def is_valid_timedelta(value: Any) -> bool:
    """Check if value is a valid time delta."""
    return isinstance(value, datetime.timedelta)


def is_config_dict(value: Any) -> bool:
    """Check if value is a valid configuration dictionary."""
    return isinstance(value, dict) and all(isinstance(k, str) for k in value.keys())

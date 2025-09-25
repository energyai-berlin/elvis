"""Custom exception hierarchy for the ELVIS simulation system.

This module defines a comprehensive exception hierarchy to provide
clear error handling and debugging information throughout the system.
"""

from __future__ import annotations

from typing import Any

# =============================================================================
# Base Exception Classes
# =============================================================================


class ElvisError(Exception):
    """Base exception class for all ELVIS-related errors.

    Provides common functionality for error tracking, context information,
    and debugging support across the entire ELVIS system.
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.cause = cause

    def add_context(self, key: str, value: Any) -> ElvisError:
        """Add contextual information to the exception."""
        self.context[key] = value
        return self

    def get_full_message(self) -> str:
        """Get the full error message including context and cause."""
        msg_parts = [f"{self.error_code}: {self.message}"]

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            msg_parts.append(f"Context: {context_str}")

        if self.cause:
            msg_parts.append(f"Caused by: {self.cause}")

        return " | ".join(msg_parts)

    def __str__(self) -> str:
        return self.get_full_message()


# =============================================================================
# Configuration and Validation Errors
# =============================================================================


class ConfigurationError(ElvisError):
    """Base class for configuration-related errors."""


class ValidationError(ConfigurationError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        expected_type: type | None = None,
        actual_value: Any = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)
        self.field_name = field_name
        self.expected_type = expected_type
        self.actual_value = actual_value

        if field_name:
            self.add_context("field", field_name)
        if expected_type:
            self.add_context("expected_type", expected_type.__name__)
        if actual_value is not None:
            self.add_context("actual_value", actual_value)


class InvalidParameterError(ValidationError):
    """Raised when a parameter has an invalid value."""

    def __init__(
        self,
        parameter_name: str,
        value: Any,
        reason: str,
        valid_range: tuple | None = None,
        **kwargs,
    ) -> None:
        message = f"Invalid value for parameter '{parameter_name}': {reason}"
        super().__init__(message, field_name=parameter_name, actual_value=value, **kwargs)

        if valid_range:
            self.add_context("valid_range", f"{valid_range[0]} to {valid_range[1]}")


class MissingParameterError(ValidationError):
    """Raised when a required parameter is missing."""

    def __init__(self, parameter_name: str, **kwargs) -> None:
        message = f"Required parameter '{parameter_name}' is missing"
        super().__init__(message, field_name=parameter_name, **kwargs)


class InvalidConfigurationError(ConfigurationError):
    """Raised when the overall configuration is invalid."""

    def __init__(
        self,
        message: str,
        config_section: str | None = None,
        validation_errors: list[ValidationError] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)
        self.config_section = config_section
        self.validation_errors = validation_errors or []

        if config_section:
            self.add_context("config_section", config_section)
        if validation_errors:
            self.add_context("validation_error_count", len(validation_errors))


# =============================================================================
# Simulation and Runtime Errors
# =============================================================================


class SimulationError(ElvisError):
    """Base class for simulation runtime errors."""


class SimulationSetupError(SimulationError):
    """Raised when simulation setup fails."""

    def __init__(self, message: str, setup_phase: str | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.setup_phase = setup_phase

        if setup_phase:
            self.add_context("setup_phase", setup_phase)


class SimulationRuntimeError(SimulationError):
    """Raised during simulation execution."""

    def __init__(
        self,
        message: str,
        simulation_time: str | None = None,
        time_step: int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)
        self.simulation_time = simulation_time
        self.time_step = time_step

        if simulation_time:
            self.add_context("simulation_time", simulation_time)
        if time_step is not None:
            self.add_context("time_step", time_step)


class ConvergenceError(SimulationError):
    """Raised when iterative algorithms fail to converge."""

    def __init__(
        self,
        message: str,
        max_iterations: int | None = None,
        tolerance: float | None = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)

        if max_iterations is not None:
            self.add_context("max_iterations", max_iterations)
        if tolerance is not None:
            self.add_context("tolerance", tolerance)


# =============================================================================
# Infrastructure and Hardware Errors
# =============================================================================


class InfrastructureError(ElvisError):
    """Base class for infrastructure-related errors."""


class ChargingPointError(InfrastructureError):
    """Raised when charging point operations fail."""

    def __init__(self, message: str, charging_point_id: str | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.charging_point_id = charging_point_id

        if charging_point_id:
            self.add_context("charging_point_id", charging_point_id)


class ChargingStationError(InfrastructureError):
    """Raised when charging station operations fail."""

    def __init__(self, message: str, charging_station_id: str | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.charging_station_id = charging_station_id

        if charging_station_id:
            self.add_context("charging_station_id", charging_station_id)


class TransformerError(InfrastructureError):
    """Raised when transformer operations fail."""

    def __init__(self, message: str, transformer_id: str | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.transformer_id = transformer_id

        if transformer_id:
            self.add_context("transformer_id", transformer_id)


class PowerLimitExceededError(InfrastructureError):
    """Raised when power limits are exceeded."""

    def __init__(
        self,
        message: str,
        component_id: str | None = None,
        current_power: float | None = None,
        power_limit: float | None = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)

        if component_id:
            self.add_context("component_id", component_id)
        if current_power is not None:
            self.add_context("current_power", f"{current_power:.2f} kW")
        if power_limit is not None:
            self.add_context("power_limit", f"{power_limit:.2f} kW")


# =============================================================================
# Vehicle and Battery Errors
# =============================================================================


class VehicleError(ElvisError):
    """Base class for vehicle-related errors."""


class BatteryError(VehicleError):
    """Base class for battery-related errors."""


class InvalidSOCError(BatteryError):
    """Raised when state of charge is invalid."""

    def __init__(self, soc_value: float, valid_range: tuple = (0.0, 1.0), **kwargs) -> None:
        message = (
            f"Invalid SOC value: {soc_value}. Must be between {valid_range[0]} and {valid_range[1]}"
        )
        super().__init__(message, **kwargs)
        self.add_context("soc_value", soc_value)
        self.add_context("valid_range", f"{valid_range[0]} to {valid_range[1]}")


class BatteryCapacityError(BatteryError):
    """Raised when battery capacity issues occur."""

    def __init__(self, message: str, capacity: float | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)

        if capacity is not None:
            self.add_context("capacity", f"{capacity:.1f} kWh")


class ChargingError(VehicleError):
    """Raised when vehicle charging operations fail."""

    def __init__(
        self,
        message: str,
        vehicle_id: str | None = None,
        charging_power: float | None = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)

        if vehicle_id:
            self.add_context("vehicle_id", vehicle_id)
        if charging_power is not None:
            self.add_context("charging_power", f"{charging_power:.2f} kW")


# =============================================================================
# Scheduling and Queue Errors
# =============================================================================


class SchedulingError(ElvisError):
    """Base class for scheduling-related errors."""


class SchedulingPolicyError(SchedulingError):
    """Raised when scheduling policy operations fail."""

    def __init__(self, message: str, policy_name: str | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)

        if policy_name:
            self.add_context("policy_name", policy_name)


class QueueError(SchedulingError):
    """Raised when queue operations fail."""

    def __init__(
        self, message: str, queue_size: int | None = None, max_size: int | None = None, **kwargs
    ) -> None:
        super().__init__(message, **kwargs)

        if queue_size is not None:
            self.add_context("queue_size", queue_size)
        if max_size is not None:
            self.add_context("max_size", max_size)


class QueueFullError(QueueError):
    """Raised when attempting to add to a full queue."""

    def __init__(self, max_size: int, **kwargs) -> None:
        message = f"Queue is full (max size: {max_size})"
        super().__init__(message, max_size=max_size, **kwargs)


# =============================================================================
# Data and I/O Errors
# =============================================================================


class DataError(ElvisError):
    """Base class for data-related errors."""


class FileFormatError(DataError):
    """Raised when file format is invalid or unsupported."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        expected_format: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)

        if file_path:
            self.add_context("file_path", file_path)
        if expected_format:
            self.add_context("expected_format", expected_format)


class DataValidationError(DataError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        data_source: str | None = None,
        invalid_records: int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)

        if data_source:
            self.add_context("data_source", data_source)
        if invalid_records is not None:
            self.add_context("invalid_records", invalid_records)


class TimeSeriesError(DataError):
    """Raised when time series data issues occur."""

    def __init__(
        self, message: str, time_range: str | None = None, resolution: str | None = None, **kwargs
    ) -> None:
        super().__init__(message, **kwargs)

        if time_range:
            self.add_context("time_range", time_range)
        if resolution:
            self.add_context("resolution", resolution)


# =============================================================================
# Utility Functions
# =============================================================================


def create_validation_error(
    field_name: str, value: Any, reason: str, expected_type: type | None = None
) -> ValidationError:
    """Create a standardized validation error."""
    return ValidationError(
        message=f"Validation failed for '{field_name}': {reason}",
        field_name=field_name,
        actual_value=value,
        expected_type=expected_type,
    )


def create_parameter_error(
    parameter_name: str, value: Any, valid_range: tuple | None = None, reason: str | None = None
) -> InvalidParameterError:
    """Create a standardized parameter error."""
    if not reason:
        if valid_range:
            reason = f"must be between {valid_range[0]} and {valid_range[1]}"
        else:
            reason = "invalid value"

    return InvalidParameterError(
        parameter_name=parameter_name, value=value, reason=reason, valid_range=valid_range
    )


def chain_exceptions(new_exception: ElvisError, cause: Exception) -> ElvisError:
    """Chain exceptions to preserve error context."""
    new_exception.cause = cause
    return new_exception


# =============================================================================
# Exception Context Managers
# =============================================================================


class ErrorContext:
    """Context manager for adding contextual information to exceptions."""

    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context

    def __enter__(self) -> ErrorContext:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if isinstance(exc_value, ElvisError):
            for key, value in self.context.items():
                exc_value.add_context(key, value)


def with_context(**context) -> ErrorContext:
    """Create an error context manager.

    Usage:
        with with_context(simulation_time="2023-01-01 12:00:00", time_step=42):
            # Code that might raise ElvisError
            pass
    """
    return ErrorContext(context)

"""Configuration validation components.

This module contains configuration validation logic to ensure all parameters
are valid and consistent before simulation execution.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from elvis.enums import SampleMethod, SchedulingPolicyType
from elvis.exceptions import (
    InvalidConfigurationError,
    InvalidParameterError,
    MissingParameterError,
    ValidationError,
)
from elvis.types import ArrivalDistribution

if TYPE_CHECKING:
    from elvis._config_legacy import ScenarioConfig

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of configuration validation."""

    def __init__(self) -> None:
        self.is_valid: bool = True
        self.errors: list[ValidationError] = []
        self.warnings: list[str] = []

    def add_error(self, error: ValidationError) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)

    def get_error_summary(self) -> str:
        """Get a summary of all validation errors."""
        if not self.errors:
            return "No validation errors"

        error_msgs = [f"- {error.message}" for error in self.errors]
        return f"Validation errors ({len(self.errors)}):\n" + "\n".join(error_msgs)


class ConfigValidator:
    """Centralized configuration validation system."""

    @staticmethod
    def validate_soc(value: float, name: str = "SOC") -> float:
        """Validate State of Charge value.

        Args:
            value: SOC value to validate
            name: Parameter name for error messages

        Returns:
            Validated SOC value

        Raises:
            InvalidParameterError: If SOC is outside valid range [0,1]
        """
        if not isinstance(value, (int, float)):
            raise InvalidParameterError(
                parameter_name=name,
                value=value,
                reason=f"must be a number, got {type(value).__name__}",
            )

        if not (0 <= value <= 1):
            raise InvalidParameterError(
                parameter_name=name,
                value=value,
                reason=f"must be between 0 and 1, got {value}",
                valid_range=(0, 1),
            )

        return float(value)

    @staticmethod
    def validate_power(value: float, name: str = "power") -> float:
        """Validate power value.

        Args:
            value: Power value to validate (kW)
            name: Parameter name for error messages

        Returns:
            Validated power value

        Raises:
            InvalidParameterError: If power is negative
        """
        if not isinstance(value, (int, float)):
            raise InvalidParameterError(
                parameter_name=name,
                value=value,
                reason=f"must be a number, got {type(value).__name__}",
            )

        if value < 0:
            raise InvalidParameterError(
                parameter_name=name,
                value=value,
                reason="must be non-negative",
                valid_range=(0, float("inf")),
            )

        return float(value)

    @staticmethod
    def validate_probability(value: float, name: str = "probability") -> float:
        """Validate probability value.

        Args:
            value: Probability value to validate
            name: Parameter name for error messages

        Returns:
            Validated probability value

        Raises:
            InvalidParameterError: If probability is outside valid range [0,1]
        """
        if not isinstance(value, (int, float)):
            raise InvalidParameterError(
                parameter_name=name,
                value=value,
                reason=f"must be a number, got {type(value).__name__}",
            )

        if not (0 <= value <= 1):
            raise InvalidParameterError(
                parameter_name=name,
                value=value,
                reason=f"must be between 0 and 1, got {value}",
                valid_range=(0, 1),
            )

        return float(value)

    @staticmethod
    def validate_arrival_distribution(distribution: ArrivalDistribution) -> ArrivalDistribution:
        """Validate arrival distribution array.

        Args:
            distribution: Arrival probability distribution

        Returns:
            Validated arrival distribution

        Raises:
            InvalidParameterError: If distribution is invalid
        """
        if not isinstance(distribution, list):
            raise InvalidParameterError(
                parameter_name="arrival_distribution",
                value=distribution,
                reason=f"must be a list, got {type(distribution).__name__}",
            )

        if len(distribution) == 0:
            raise InvalidParameterError(
                parameter_name="arrival_distribution", value=distribution, reason="cannot be empty"
            )

        # Validate each probability value
        for i, prob in enumerate(distribution):
            try:
                ConfigValidator.validate_probability(prob, f"arrival_distribution[{i}]")
            except InvalidParameterError as e:
                # Re-raise with additional context
                raise InvalidParameterError(
                    parameter_name=f"arrival_distribution[{i}]",
                    value=prob,
                    reason=f"probability at index {i} is invalid: {e.message}",
                ) from e

        # Check if probabilities sum approximately to 1 (within tolerance)
        total_prob = sum(distribution)
        if abs(total_prob - 1.0) > 1e-6:
            logger.warning(
                f"Arrival distribution probabilities sum to {total_prob}, expected sum close to 1.0"
            )

        return distribution

    @staticmethod
    def validate_scheduling_policy_string(policy_str: str) -> SchedulingPolicyType:
        """Validate and convert scheduling policy string to enum.

        Args:
            policy_str: String representation of scheduling policy

        Returns:
            SchedulingPolicyType enum

        Raises:
            InvalidParameterError: If policy string is invalid
        """
        if not isinstance(policy_str, str):
            raise InvalidParameterError(
                parameter_name="scheduling_policy",
                value=policy_str,
                reason=f"must be a string, got {type(policy_str).__name__}",
            )

        try:
            return SchedulingPolicyType.from_string(policy_str)
        except ValueError as e:
            raise InvalidParameterError(
                parameter_name="scheduling_policy", value=policy_str, reason=str(e)
            ) from e

    @staticmethod
    def validate_sample_method_string(method_str: str) -> SampleMethod:
        """Validate and convert sample method string to enum.

        Args:
            method_str: String representation of sample method

        Returns:
            SampleMethod enum

        Raises:
            InvalidParameterError: If method string is invalid
        """
        if not isinstance(method_str, str):
            raise InvalidParameterError(
                parameter_name="sample_method",
                value=method_str,
                reason=f"must be a string, got {type(method_str).__name__}",
            )

        try:
            return SampleMethod.from_string(method_str)
        except ValueError as e:
            raise InvalidParameterError(
                parameter_name="sample_method", value=method_str, reason=str(e)
            ) from e

    @staticmethod
    def validate_scenario_config(config: ScenarioConfig) -> ValidationResult:
        """Validate entire scenario configuration.

        Args:
            config: ScenarioConfig instance to validate

        Returns:
            ValidationResult with any errors or warnings found
        """
        result = ValidationResult()

        # Validate required fields
        try:
            if config.arrival_distribution is None:
                result.add_error(MissingParameterError("arrival_distribution is required"))
            else:
                ConfigValidator.validate_arrival_distribution(config.arrival_distribution)

            if config.vehicle_types is None or len(config.vehicle_types) == 0:
                result.add_error(MissingParameterError("At least one vehicle type is required"))

            if config.infrastructure is None:
                result.add_error(MissingParameterError("infrastructure configuration is required"))

            # Validate optional fields if present
            if config.mean_soc is not None:
                ConfigValidator.validate_soc(config.mean_soc, "mean_soc")

            if config.std_deviation_soc is not None:
                ConfigValidator.validate_soc(config.std_deviation_soc, "std_deviation_soc")

            # Validate probabilities sum to 1 for vehicle types
            if config.vehicle_types:
                total_prob = sum(vt.probability for vt in config.vehicle_types)
                if abs(total_prob - 1.0) > 1e-6:
                    result.add_warning(
                        f"Vehicle type probabilities sum to {total_prob}, expected 1.0"
                    )

        except ValidationError as e:
            result.add_error(e)
        except Exception as e:
            result.add_error(InvalidConfigurationError(f"Unexpected validation error: {e}"))

        return result

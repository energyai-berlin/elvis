"""Enumeration definitions for ELVIS configuration.

This module contains all enum definitions used throughout the ELVIS system
to replace string-based dispatching with type-safe enums.
"""

from __future__ import annotations

from enum import Enum


class SchedulingPolicyType(Enum):
    """Enumeration of available scheduling policy types."""

    UNCONTROLLED = "uncontrolled"
    DISCRIMINATION_FREE = "discrimination_free"
    FCFS = "fcfs"
    WITH_STORAGE = "with_storage"
    OPTIMIZED = "optimized"

    @classmethod
    def from_string(cls, value: str) -> SchedulingPolicyType:
        """Convert string to enum, with support for legacy string formats.

        Args:
            value: String representation of scheduling policy

        Returns:
            SchedulingPolicyType enum value

        Raises:
            ValueError: If string cannot be matched to any policy type
        """
        # Normalize input
        normalized = value.strip().lower().replace(" ", "_")

        # Handle legacy string formats
        legacy_mappings = {
            "uncontrolled": cls.UNCONTROLLED,
            "uc": cls.UNCONTROLLED,
            "discrimination_free": cls.DISCRIMINATION_FREE,
            "df": cls.DISCRIMINATION_FREE,
            "fcfs": cls.FCFS,
            "with_storage": cls.WITH_STORAGE,
            "ws": cls.WITH_STORAGE,
            "optimized": cls.OPTIMIZED,
            "opt": cls.OPTIMIZED,
        }

        if normalized in legacy_mappings:
            return legacy_mappings[normalized]

        # Try direct enum value match
        for policy in cls:
            if policy.value == normalized:
                return policy

        # If no match found, raise error with helpful message
        valid_options = list(legacy_mappings.keys())
        raise ValueError(
            f"Unknown scheduling policy: '{value}'. Valid options are: {', '.join(valid_options)}"
        )


class SampleMethod(Enum):
    """Enumeration of available sampling methods for charging event generation."""

    INDEPENDENT_NORMAL_DIST = "independent_normal_dist"
    GMM = "gmm"

    @classmethod
    def from_string(cls, value: str) -> SampleMethod:
        """Convert string to enum.

        Args:
            value: String representation of sample method

        Returns:
            SampleMethod enum value

        Raises:
            ValueError: If string cannot be matched to any sample method
        """
        normalized = value.strip().lower()

        for method in cls:
            if method.value == normalized:
                return method

        valid_options = [method.value for method in cls]
        raise ValueError(
            f"Unknown sample method: '{value}'. Valid options are: {', '.join(valid_options)}"
        )

"""Configuration module for ELVIS scenarios.

This module provides a structured approach to configuring EV charging simulation scenarios.
It breaks down the large configuration system into focused, maintainable components.

For Phase 1, we maintain backward compatibility by importing from the original config.py.
In Phase 2+, the functionality will be migrated to the structured modules.
"""

from __future__ import annotations

# Phase 1: Import from the new modular config structure
from .scenario import ScenarioConfig, ScenarioRealisation

__all__ = [
    "ScenarioConfig",
    "ScenarioRealisation",
]

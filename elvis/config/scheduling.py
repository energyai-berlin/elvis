"""Scheduling policy configuration components.

This module contains scheduling-related configuration logic
such as scheduling policy setup, queue management,
and charging event ordering.
"""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Union

import pandas as pd

from elvis.enums import SchedulingPolicyType
from elvis.sched import schedulers

if TYPE_CHECKING:
    from elvis.config.scenario import ScenarioConfig

logger = logging.getLogger(__name__)


class SchedulingMixin:
    """Mixin class for scheduling-related configuration methods."""

    def with_scheduling_policy(
        self: ScenarioConfig,
        scheduling_policy_input: Union[str, SchedulingPolicyType, schedulers.SchedulingPolicy],
    ) -> ScenarioConfig:
        """Update the scheduling policy to use.

        Default: Uncontrolled scheduling policy.

        Args:
            scheduling_policy_input: Either str containing name of the scheduling policy to be used,
                SchedulingPolicyType enum, or instance of SchedulingPolicy.

        Returns:
            Self for method chaining
        """
        from elvis.config.validation import ConfigValidator

        # if input is already instance of Scheduling Policy, use directly
        if isinstance(scheduling_policy_input, schedulers.SchedulingPolicy):
            self.scheduling_policy = scheduling_policy_input
            return self

        # If it's already an enum, use it directly
        if isinstance(scheduling_policy_input, SchedulingPolicyType):
            policy_type = scheduling_policy_input
        else:
            # Try to convert string to enum (with validation)
            try:
                policy_type = ConfigValidator.validate_scheduling_policy_string(
                    str(scheduling_policy_input)
                )
            except Exception as e:
                logger.exception(f"Invalid scheduling policy '{scheduling_policy_input}': {e}")
                logger.exception("Using default Uncontrolled policy")
                self.scheduling_policy = schedulers.Uncontrolled()
                return self

        # Map enum to scheduler instance
        policy_mapping = {
            SchedulingPolicyType.UNCONTROLLED: schedulers.Uncontrolled(),
            SchedulingPolicyType.DISCRIMINATION_FREE: schedulers.DiscriminationFree(),
            SchedulingPolicyType.FCFS: schedulers.FCFS(),
            SchedulingPolicyType.WITH_STORAGE: schedulers.WithStorage(),
            SchedulingPolicyType.OPTIMIZED: schedulers.Optimized(),
        }

        self.scheduling_policy = policy_mapping[policy_type]
        return self

    def with_df_charging_period(
        self: ScenarioConfig, charging_period: Union[str, datetime.timedelta]
    ) -> ScenarioConfig:
        """Update the charging period for discrimination-free scheduling.

        Args:
            charging_period: Either a string in format "%H:%M:%S" or a timedelta instance

        Returns:
            Self for method chaining

        Raises:
            AssertionError: If charging_period is not str or timedelta
        """
        assert isinstance(charging_period, (str, datetime.timedelta)), (
            "Charging period must either be a str in format: %H:%M:%S or an instance "
            "of datetime.timedelta"
        )

        # str
        if isinstance(charging_period, str):
            try:
                date = datetime.datetime.strptime(charging_period, "%H:%M:%S")
                self.df_charging_period = datetime.timedelta(
                    hours=date.hour, minutes=date.minute, seconds=date.second
                )
            except ValueError:
                try:
                    seconds = pd.Timedelta(charging_period).total_seconds()
                    self.df_charging_period = datetime.timedelta(seconds=seconds)
                except ValueError:
                    logger.error(
                        "Incorrect timedelta format for resolution pls use: %H:%M:%S or "
                        "a pandas conform timedelta format."
                    )
        # datetime.timedelta
        else:
            self.df_charging_period = charging_period

        return self

    def with_queue_length(self: ScenarioConfig, queue_length: int) -> ScenarioConfig:
        """Update maximal length of queue.

        Args:
            queue_length: Maximum number of vehicles that can wait in queue

        Returns:
            Self for method chaining

        Raises:
            AssertionError: If queue_length is not an integer
        """
        assert isinstance(queue_length, int), (
            f"Queue length must be int, got {type(queue_length).__name__}"
        )
        assert queue_length >= 0, f"Queue length must be non-negative, got {queue_length}"

        self.queue_length = queue_length
        return self

    def with_disconnect_by_time(self: ScenarioConfig, disconnect_by_time: bool) -> ScenarioConfig:
        """Update decision variable on how to disconnect cars.

        Args:
            disconnect_by_time: If True, vehicles are disconnected based on parking time only.
                If False, vehicles are disconnected based on SOC or parking time (whichever comes first).

        Returns:
            Self for method chaining

        Raises:
            AssertionError: If disconnect_by_time is not boolean
        """
        assert isinstance(disconnect_by_time, bool), (
            f"disconnect_by_time must be bool, got {type(disconnect_by_time).__name__}"
        )

        self.disconnect_by_time = disconnect_by_time
        return self


# For ScenarioRealisation scheduling handling
class SchedulingRealisationHandler:
    """Handler for scheduling operations in scenario realisation."""

    @staticmethod
    def handle_scheduling_policy(
        realisation: any,  # ScenarioRealisation
        scheduling_policy_input: Union[str, schedulers.SchedulingPolicy],
    ) -> any:
        """Update the scheduling policy to use in realisation.

        Default: Uncontrolled scheduling policy.
        Use default if input is not a str or str cannot be matched.

        Args:
            realisation: The ScenarioRealisation instance
            scheduling_policy_input: Either str containing name of the scheduling policy or
                instance of SchedulingPolicy.

        Returns:
            The updated realisation
        """
        # set default
        scheduling_policy = schedulers.Uncontrolled()

        # if input is already instance of Scheduling Policy assign
        if isinstance(scheduling_policy_input, schedulers.SchedulingPolicy):
            realisation.scheduling_policy = scheduling_policy_input
            return realisation

        # ensure input is str. If not return default
        if not isinstance(scheduling_policy_input, str):
            logger.error(
                "Scheduling policy should be of type str or an instance of "
                "SchedulingPolicy. The uncontrolled strategy has been used as a default."
            )
            realisation.scheduling_policy = scheduling_policy
            return realisation

        # Match string - using more flexible matching than enum validation
        policy_str = scheduling_policy_input.lower().replace(" ", "").replace("_", "")

        if policy_str in ("uncontrolled", "uc"):
            realisation.scheduling_policy = schedulers.Uncontrolled()
        elif policy_str in ("discriminationfree", "df"):
            realisation.scheduling_policy = schedulers.DiscriminationFree()
        elif policy_str == "fcfs":
            realisation.scheduling_policy = schedulers.FCFS()
        elif policy_str in ("withstorage", "ws"):
            realisation.scheduling_policy = schedulers.WithStorage()
        elif policy_str in ("optimized", "opt"):
            realisation.scheduling_policy = schedulers.Optimized()
        # invalid str use default: Uncontrolled
        else:
            logger.error(
                '"%s" can not be matched to any existing scheduling policy. '
                'Please use: "Uncontrolled", "Discrimination Free", "FCFS", '
                '"With Storage" or "Optimized". '
                "Uncontrolled is the default value and has been used for the simulation.",
                scheduling_policy_input,
            )
            realisation.scheduling_policy = schedulers.Uncontrolled()

        return realisation

    @staticmethod
    def handle_df_charging_period(
        realisation: any,  # ScenarioRealisation
        charging_period: Union[str, datetime.timedelta],
    ) -> any:
        """Handle discrimination-free charging period setup for realisation.

        Args:
            realisation: The ScenarioRealisation instance
            charging_period: Either a string in format "%H:%M:%S" or a timedelta instance

        Returns:
            The updated realisation
        """
        assert isinstance(charging_period, (str, datetime.timedelta)), (
            "Charging period must either be a str in format: %H:%M:%S or an instance "
            "of datetime.timedelta"
        )

        # str
        if isinstance(charging_period, str):
            try:
                date = datetime.datetime.strptime(charging_period, "%H:%M:%S")
                realisation.df_charging_period = datetime.timedelta(
                    hours=date.hour, minutes=date.minute, seconds=date.second
                )
            except ValueError:
                try:
                    seconds = pd.Timedelta(charging_period).total_seconds()
                    realisation.df_charging_period = datetime.timedelta(seconds=seconds)
                except ValueError:
                    logger.error(
                        "Incorrect timedelta format for resolution pls use: %H:%M:%S or "
                        "a pandas conform timedelta format."
                    )
        # datetime.timedelta
        else:
            realisation.df_charging_period = charging_period

        return realisation

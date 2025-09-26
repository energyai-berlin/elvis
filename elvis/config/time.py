"""Time-related configuration components.

This module contains time-related configuration logic
such as time series data handling, resolution management,
and temporal validation.
"""

from __future__ import annotations

import datetime
import logging
import warnings
from typing import TYPE_CHECKING, Union

import pandas as pd

from elvis.utility.elvis_general import (
    adjust_resolution,
    num_time_steps,
    repeat_data,
    transform_data,
)

if TYPE_CHECKING:
    from elvis.config.scenario import ScenarioConfig
    from elvis.types import TimeStamp

logger = logging.getLogger(__name__)


class TimeMixin:
    """Mixin class for time-related configuration methods."""

    def with_opening_hours(
        self: ScenarioConfig, opening_hours: tuple[Union[int, float], Union[int, float]] | None
    ) -> ScenarioConfig:
        """Update the opening hours to use.

        Args:
            opening_hours: Tuple of (open_hour, close_hour) representing hours of the day (0-24),
                or None for 24/7 operation

        Returns:
            Self for method chaining

        Raises:
            AssertionError: If opening_hours format is invalid
        """
        if opening_hours is None:
            self.opening_hours = opening_hours
            return self

        assert isinstance(opening_hours, tuple), "Opening hours is expected to be a tuple."
        assert len(opening_hours) == 2, "Opening hours is expected to be a tuple with 2 values"

        _open, _close = opening_hours

        assert isinstance(_open, (float, int)), (
            "Values in opening hours must be of type int or "
            "float representing the hours of the day."
        )
        assert isinstance(_close, (float, int)), (
            "Values in opening hours must be of type int or "
            "float representing the hours of the day."
        )

        assert _open <= _close, (
            "The first value (opening hour) is expected to be smaller than "
            "the 2nd value (closing hour)."
        )
        assert _close <= 24, "The last value(closing hour) is expected to be smaller or equal to 24"
        assert _open >= 0, "The first value(opening hour) is expected to be bigger or equal to 0"

        self.opening_hours = opening_hours
        return self

    def with_max_parking_time(
        self: ScenarioConfig, max_parking_time: Union[int, float]
    ) -> ScenarioConfig:
        """Update maximum parking time.

        Args:
            max_parking_time: Maximum time a vehicle can stay at the charging infrastructure (hours)

        Returns:
            Self for method chaining

        Raises:
            AssertionError: If max_parking_time is not numeric or negative
        """
        assert isinstance(max_parking_time, (int, float)), (
            f"Max parking time must be numeric, got {type(max_parking_time).__name__}"
        )
        assert max_parking_time >= 0, (
            f"Max parking time must be non-negative, got {max_parking_time}"
        )

        self.max_parking_time = max_parking_time
        return self

    def with_mean_park(self: ScenarioConfig, mean_park: Union[int, float]) -> ScenarioConfig:
        """Update mean parking time for stochastic generation.

        Args:
            mean_park: Mean parking time in hours

        Returns:
            Self for method chaining

        Raises:
            AssertionError: If mean_park is invalid
        """
        assert isinstance(mean_park, (int, float)), (
            f"Mean parking time must be numeric, got {type(mean_park).__name__}"
        )
        assert 0 < mean_park < 24, (
            f"Mean parking time should be between 0 and 24 hours, got {mean_park}"
        )

        self.mean_park = mean_park
        return self

    def with_std_deviation_park(
        self: ScenarioConfig, std_deviation_park: Union[int, float]
    ) -> ScenarioConfig:
        """Update standard deviation of parking time for stochastic generation.

        Args:
            std_deviation_park: Standard deviation of parking time in hours

        Returns:
            Self for method chaining

        Raises:
            AssertionError: If std_deviation_park is invalid
        """
        assert isinstance(std_deviation_park, (int, float)), (
            f"Standard deviation of parking time must be numeric, got {type(std_deviation_park).__name__}"
        )
        assert std_deviation_park >= 0, (
            f"Standard deviation of parking time must be non-negative, got {std_deviation_park}"
        )

        self.std_deviation_park = std_deviation_park
        return self

    def with_mean_soc(self: ScenarioConfig, mean_soc: Union[int, float]) -> ScenarioConfig:
        """Update mean state of charge for stochastic generation.

        Args:
            mean_soc: Mean state of charge (0-1)

        Returns:
            Self for method chaining

        Raises:
            AssertionError: If mean_soc is invalid
        """
        assert isinstance(mean_soc, (int, float)), (
            f"Mean SOC must be numeric, got {type(mean_soc).__name__}"
        )
        assert 0 < mean_soc < 1, f"Mean SOC should be between 0 and 1, got {mean_soc}"

        self.mean_soc = mean_soc
        return self

    def with_std_deviation_soc(
        self: ScenarioConfig, std_deviation_soc: Union[int, float]
    ) -> ScenarioConfig:
        """Update standard deviation of state of charge for stochastic generation.

        Args:
            std_deviation_soc: Standard deviation of state of charge (0-1)

        Returns:
            Self for method chaining

        Raises:
            AssertionError: If std_deviation_soc is invalid
        """
        assert isinstance(std_deviation_soc, (int, float)), (
            f"Standard deviation of SOC must be numeric, got {type(std_deviation_soc).__name__}"
        )
        assert std_deviation_soc >= 0, (
            f"Standard deviation of SOC must be non-negative, got {std_deviation_soc}"
        )

        self.std_deviation_soc = std_deviation_soc
        return self

    def with_num_charging_events(self: ScenarioConfig, num_charging_events: int) -> ScenarioConfig:
        """Update the number of charging events to generate.

        Args:
            num_charging_events: Number of charging events per simulation period

        Returns:
            Self for method chaining

        Raises:
            AssertionError: If num_charging_events is not a positive integer
        """
        assert isinstance(num_charging_events, int), (
            f"Number of charging events must be int, got {type(num_charging_events).__name__}"
        )
        assert num_charging_events > 0, (
            f"Number of charging events must be positive, got {num_charging_events}"
        )

        self.num_charging_events = num_charging_events
        return self


class TimeRealisationHandler:
    """Handler for time-related operations in scenario realisation."""

    @staticmethod
    def handle_opening_hours(
        realisation: any, opening_hours: tuple[TimeStamp, TimeStamp] | None
    ) -> any:
        """Handle opening hours setup for realisation.

        Args:
            realisation: The ScenarioRealisation instance
            opening_hours: Tuple of opening and closing times

        Returns:
            The updated realisation
        """
        if opening_hours is None:
            realisation.opening_hours = opening_hours
            return realisation

        assert isinstance(opening_hours, tuple), "Opening hours is expected to be a tuple."
        assert len(opening_hours) == 2, "Opening hours is expected to be a tuple with 2 values"
        _open, _close = opening_hours

        assert isinstance(_open, (float, int)), (
            "Values in opening hours must be of type int or "
            "float representing the hours of the day."
        )
        assert isinstance(_close, (float, int)), (
            "Values in opening hours must be of type int or "
            "float representing the hours of the day."
        )

        assert _open <= _close, (
            "The first value (opening hour) is expected to be smaller than "
            "the 2nd value (closing hour)."
        )
        assert _close <= 24, "The last value(closing hour) is expected to be smaller or equal to 24"
        assert _open >= 0, "The first value(opening hour) is expected to be bigger or equal to 0"

        realisation.opening_hours = opening_hours
        return realisation

    @staticmethod
    def handle_emissions_scenario(
        emissions_scenario: Union[int, float, list[Union[int, float]], pd.Series, pd.DataFrame],
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        resolution: datetime.timedelta,
        col_pos: int = 0,
        res_data: Union[str, datetime.timedelta, None] = None,
        repeat: bool | None = None,
    ) -> list[Union[int, float]]:
        """Update emissions scenario variable representing the CO2-emissions per kWh at a given time.

        Args:
            emissions_scenario: Can be either int, float, list or pandas Series or DataFrame
            start_date: First time stamp
            end_date: Upper bound for time stamps
            resolution: Time in between two adjacent time stamps
            col_pos: If pandas DataFrame is passed indicates the column with emission values
            res_data: If list is passed that doesn't align with simulation period,
                res_data displays the period between two adjacent list entries
            repeat: If list is passed that doesn't align with simulation period and
                repeat is True the list is repeated until enough data points are available

        Returns:
            List of emission values aligned with simulation time steps
        """
        if emissions_scenario is None:
            return []

        assert isinstance(start_date, datetime.datetime), "Start date must be datetime.datetime."
        assert isinstance(end_date, datetime.datetime), "End date must be datetime.datetime."
        assert isinstance(resolution, datetime.timedelta), "Resolution must be datetime.timedelta"
        assert isinstance(col_pos, int), "Column must be a positive integer."
        assert col_pos >= 0, "Column must be a positive integer."

        # Error messages
        msg_wrong_resolution_type = (
            "If the emissions scenario is passed as list and the "
            "resolution is supposed to be adjusted please "
            "use type datetime.timedelta."
        )
        msg_alignment_unsuccessful = "Emissions scenario could not be aligned to simulation steps."
        msg_invalid_value_type = (
            "Emissions scenario should be of type: pandas DataFrame, "
            "list containing float or int, int, float."
        )
        msg_not_enough_data_points = (
            "There are less values for the emissions scenario than "
            "simulation steps. Please adjust the data."
        )

        emissions_scenario_aligned = []

        # Constant value
        if isinstance(emissions_scenario, (float, int)):
            return [emissions_scenario] * num_time_steps(start_date, end_date, resolution)

        # pandas DataFrame
        elif isinstance(emissions_scenario, pd.DataFrame):
            emissions_scenario = emissions_scenario.iloc[:, col_pos]
            emissions_scenario_aligned = transform_data(
                emissions_scenario, resolution, start_date, end_date
            )
        elif isinstance(emissions_scenario, pd.Series):
            emissions_scenario_aligned = transform_data(
                emissions_scenario, resolution, start_date, end_date
            )
        elif isinstance(emissions_scenario, list):
            num_simulation_steps = num_time_steps(start_date, end_date, resolution)

            # Check if all values in list are either float or int
            assert all(isinstance(x, (float, int)) for x in emissions_scenario), (
                msg_invalid_value_type
            )

            # Check whether the length of the list aligns with the simulation period and resolution
            num_values = len(emissions_scenario)

            assert num_simulation_steps < num_values or res_data is not None or repeat, (
                msg_not_enough_data_points
            )

            if res_data is not None:
                if isinstance(res_data, str):
                    try:
                        date = datetime.datetime.strptime(res_data, "%H:%M:%S")
                        res_data = datetime.timedelta(
                            hours=date.hour, minutes=date.minute, seconds=date.second
                        )
                    except ValueError:
                        logging.exception(
                            "%s is of incorrect format. Please use %s", res_data, "%H:%M:%S"
                        )
                        raise ValueError
                assert isinstance(res_data, datetime.timedelta), msg_wrong_resolution_type

                emissions_scenario = adjust_resolution(emissions_scenario, res_data, resolution)

            if repeat is True:
                emissions_scenario = repeat_data(emissions_scenario, num_simulation_steps)

            # Should it be ==?
            assert len(emissions_scenario) >= num_simulation_steps, msg_alignment_unsuccessful
            emissions_scenario_aligned = emissions_scenario
        else:
            warnings.warn(
                "Emissions are passed in an non convertible type. Please either use: "
                "Float/int, list or pandas Series or DataFrame. The simulation is carried "
                "on without assigning emission values."
            )

        return emissions_scenario_aligned

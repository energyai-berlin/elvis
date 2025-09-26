"""Infrastructure configuration components.

This module contains infrastructure-related configuration logic
such as transformer setup, charging station configuration,
and grid connection management.
"""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any, Union

import pandas as pd

from elvis.set_up_infrastructure import wallbox_infrastructure
from elvis.types import FilePath, TimeSeriesData
from elvis.utility.elvis_general import (
    adjust_resolution,
    num_time_steps,
    repeat_data,
    transform_data,
)

if TYPE_CHECKING:
    from elvis.config.scenario import ScenarioConfig

logger = logging.getLogger(__name__)


class InfrastructureMixin:
    """Mixin class for infrastructure-related configuration methods."""

    def with_infrastructure(
        self: ScenarioConfig, infrastructure: dict[str, Any] | None = None, **kwargs: Any
    ) -> ScenarioConfig:
        """Update the infrastructure to use.

        Args:
            infrastructure: Infrastructure configuration dictionary
            kwargs.num_cp: (int): Number of charging points.
            kwargs.num_cp_per_cs: (int) Number of charging points per charging station.
            kwargs.power_cp: (int or float): (optional) Max power per charging point.
            kwargs.power_cs: (int or float): (optional) Max power of the charging station.
            kwargs.power_transformer: (int or float): (optional) Max power of the transformer.
            kwargs.min_power_cp: (int or float): (optional) Minimum power (if not 0) for the
                charging point.
            kwargs.min_power_cs: (int or float): (optional) Minimum power (if not 0) for the
                charging station.
            kwargs.min_power_transformer: (int or float) : (optional) Minimum power (if not 0) for
                the charging station.

        Returns:
            Self for method chaining
        """
        if infrastructure is not None:
            assert isinstance(infrastructure, dict), "Infrastructure must be a dictionary"
            self.infrastructure = infrastructure
        else:
            err_msg = (
                "%s is a necessary key to initialise an elvis infrastructure as a wallbox "
                "infrastructure."
            )
            keys = kwargs.keys()
            assert "num_cp" in keys, err_msg % "num_cp"
            assert "power_cp" in keys, err_msg % "power_cp"

            num_cp: int = kwargs["num_cp"]
            power_cp: Union[int, float] = kwargs["power_cp"]

            num_cp_per_cs: int = kwargs.get("num_cp_per_cs", 1)
            power_cs: Union[int, float, None] = kwargs.get("power_cs")
            power_transformer: Union[int, float, None] = kwargs.get("power_transformer")
            min_power_cp: Union[int, float] = kwargs.get("min_power_cp", 0)
            min_power_cs: Union[int, float] = kwargs.get("min_power_cs", 0)
            min_power_transformer: Union[int, float] = kwargs.get("min_power_transformer", 0)

            self.infrastructure = wallbox_infrastructure(
                num_cp,
                power_cp,
                num_cp_per_cs,
                power_cs,
                power_transformer,
                min_power_cp,
                min_power_cs,
                min_power_transformer,
            )

        return self

    def with_transformer_preload(
        self: ScenarioConfig,
        transformer_preload: Union[int, float, list[Union[int, float]], pd.Series, pd.DataFrame],
        col_pos: int = 0,
        res_data: Union[str, datetime.timedelta, None] = None,
        repeat: bool = False,
    ) -> ScenarioConfig:
        """Assigns values regarding the transformer preload to config.

        Args:
            transformer_preload: Either of type int/float, list, or pandas DataFrame/Series.
            col_pos: If transformer_preload is of type pandas DataFrame: col_pos refers to
                the column the transformer preload is stored.
            res_data: If transformer preload is of type list and does not align
                with the simulation period: res_data states the time difference in between two
                adjacent values of transformer preload.
            repeat: If transformer preload is of type list and does not align with the
                simulation period: repeat=True indicates that the list shall be repeated until
                the whole simulation period is covered.

        Returns:
            Self for method chaining
        """
        if isinstance(transformer_preload, (pd.Series, pd.DataFrame)):
            self.transformer_preload = transformer_preload
        else:
            assert isinstance(transformer_preload, (int, float, list)), (
                "Transformer preload must be of type list or pandas DataFrame."
            )

            msg_invalid_value_type = (
                "Transformer preload should be of type: pandas DataFrame or"
                " a list containing float or int."
            )
            # Check if all values in list are either float or int
            if isinstance(transformer_preload, list):
                assert all(isinstance(x, (float, int)) for x in transformer_preload), (
                    msg_invalid_value_type
                )

            self.transformer_preload = transformer_preload

        if res_data is not None:
            assert isinstance(res_data, (str, datetime.timedelta))
            if isinstance(res_data, str):
                try:
                    date = datetime.datetime.strptime(res_data, "%H:%M:%S")
                    self.transformer_preload_res_data = datetime.timedelta(
                        hours=date.hour, minutes=date.minute, seconds=date.second
                    )
                except ValueError:
                    try:
                        seconds = pd.Timedelta(res_data).total_seconds()
                        self.transformer_preload_res_data = datetime.timedelta(seconds=seconds)
                    except ValueError:
                        logger.error(
                            "Incorrect timedelta format for resolution pls use: %H:%M:%S or "
                            "a pandas conform timedelta format."
                        )
            # datetime.timedelta
            else:
                self.transformer_preload_res_data = res_data

        if repeat is not False:
            assert isinstance(repeat, bool), "Repeat can only be True or False."
            self.transformer_preload_repeat = True

        if col_pos != 0:
            assert isinstance(col_pos, int), "Column position (col_pos) must be a positive integer"
            assert col_pos > 0, "Column position (col_pos) must be a positive integer"
            self.transformer_preload_col_pos = col_pos
        return self

    def with_emissions_scenario(
        self: ScenarioConfig,
        emissions_scenario: Union[int, float, list[Union[int, float]], pd.Series, pd.DataFrame],
        col_pos: int = 0,
        res_data: Union[str, datetime.timedelta, None] = None,
        repeat: bool = False,
    ) -> ScenarioConfig:
        """Assigns values regarding the emissions scenario to config.

        Args:
            emissions_scenario: Either of type int/float, list, or pandas DataFrame/Series.
            col_pos: If emissions scenario is of type pandas DataFrame: col_pos refers to
                the column the emissions scenario is stored.
            res_data: If emissions scenario is of type list and does not align
                with the simulation period: res_data states the time difference in between two
                adjacent values of emissions scenario.
            repeat: If emissions scenario is of type list and does not align with the
                simulation period: repeat=True indicates that the list shall be repeated until
                the whole simulation period is covered.

        Returns:
            Self for method chaining
        """
        if isinstance(emissions_scenario, (pd.Series, pd.DataFrame)):
            self.emissions_scenario = emissions_scenario
        else:
            assert isinstance(emissions_scenario, (int, float, list)), (
                "Emissions scenario must be of type list or pandas DataFrame."
            )

            msg_invalid_value_type = (
                "Emissions scenario should be of type: pandas DataFrame or"
                " a list containing float or int."
            )
            # Check if all values in list are either float or int
            if isinstance(emissions_scenario, list):
                assert all(isinstance(x, (float, int)) for x in emissions_scenario), (
                    msg_invalid_value_type
                )

            self.emissions_scenario = emissions_scenario

        if res_data is not None:
            assert isinstance(res_data, (str, datetime.timedelta))
            if isinstance(res_data, str):
                try:
                    date = datetime.datetime.strptime(res_data, "%H:%M:%S")
                    self.emissions_scenario_res_data = datetime.timedelta(
                        hours=date.hour, minutes=date.minute, seconds=date.second
                    )
                except ValueError:
                    try:
                        seconds = pd.Timedelta(res_data).total_seconds()
                        self.emissions_scenario_res_data = datetime.timedelta(seconds=seconds)
                    except ValueError:
                        logger.error(
                            "Incorrect timedelta format for resolution pls use: %H:%M:%S or "
                            "a pandas conform timedelta format."
                        )
            # datetime.timedelta
            else:
                self.emissions_scenario_res_data = res_data

        if repeat is not False:
            assert isinstance(repeat, bool), "Repeat can only be True or False."
            self.emissions_scenario = True

        if col_pos != 0:
            assert isinstance(col_pos, int), "Column position (col_pos) must be a positive integer"
            assert col_pos >= 0, "Column position (col_pos) must be a positive integer"
            self.emissions_scenario_col_pos = col_pos
        return self

    def with_renewables_scenario(
        self: ScenarioConfig, renewables_scenario: Union[FilePath, TimeSeriesData, None]
    ) -> ScenarioConfig:
        """Update the renewable energy scenario to use.

        Args:
            renewables_scenario: Path to renewable energy data file or data itself

        Returns:
            Self for method chaining
        """
        self.renewables_scenario = renewables_scenario
        return self


# For ScenarioRealisation transformer preload handling
class TransformerPreloadHandler:
    """Handler for transformer preload operations in scenario realisation."""

    @staticmethod
    def handle_transformer_preload(
        realisation: Any,  # ScenarioRealisation
        transformer_preload: Union[int, float, list[Union[int, float]], pd.Series, pd.DataFrame],
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        resolution: datetime.timedelta,
        col_pos: int = 0,
        res_data: Union[str, datetime.timedelta, None] = None,
        repeat: bool = False,
    ) -> Any:
        """Update the renewable energy scenario to use.
        Simulation time parameter must be set before transformer preload can be initialised.

        Args:
            realisation: The ScenarioRealisation instance
            transformer_preload: Either of type int/float, list, or pandas Series/DataFrame.
            start_date: First time stamp.
            end_date: Upper bound for time stamps.
            resolution: Time in between two adjacent time stamps.
            col_pos: If pandas DataFrame is passed indicates the column in which the
                emission values are stored.
            res_data: If list is passed that does not align with the
                simulation period, res_data displays the period inbetween two adjacent list entries.
            repeat: If list is passed that does not align with the
                simulation period and repeat is True the list is repeated until enough data points
                are available for the simulation period.

        Returns:
            The updated realisation
        """
        # Error messages
        msg_wrong_resolution_type = (
            "If the transformer preload is passed as list and the"
            "resolution is supposed to be of adjusted please"
            "use type datetime.timedelta."
        )
        msg_wrong_transformer_preload_type = (
            "Transformer preload should be of type: "
            "pandas DataFrame, list containing float or int,"
            " int, float."
        )
        msg_alignement_unsuccessful = "Transformer preload could not be aligned to simulationsteps."
        msg_invalid_value_type = (
            "Transformer preload should be of type: pandas DataFrame, "
            "list containing float or int, int, float."
        )
        msg_not_enough_data_points = (
            "There are less values for the transformer preload than "
            "simulation steps. Please adjust the data."
        )

        # Check whether passed value is a DataFrame or a list
        if isinstance(transformer_preload, pd.DataFrame):  # DataFrame
            # Make sure length is aligned to simulation period and resolution
            transformer_preload = transformer_preload.iloc[:, col_pos]
            transformer_preload = transform_data(
                transformer_preload, resolution, start_date, end_date
            )
        elif isinstance(transformer_preload, pd.Series):
            transformer_preload = transform_data(
                transformer_preload, resolution, start_date, end_date
            )
        else:  # list or numeric
            num_simulation_steps = int((end_date - start_date) / resolution) + 1

            if isinstance(transformer_preload, (int, float)):
                transformer_preload = [transformer_preload] * num_simulation_steps

            assert isinstance(transformer_preload, list), msg_wrong_transformer_preload_type

            # Check if all values in list are either float or int
            assert all(isinstance(x, (float, int)) for x in transformer_preload), (
                msg_invalid_value_type
            )

            # Check whether the length of the list alignes with the simulation period and resolution
            # If num_values don't fit simulation period and no action is wanted return error
            num_values = len(transformer_preload)

            assert num_simulation_steps <= num_values or res_data is not None or repeat, (
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

                transformer_preload = adjust_resolution(transformer_preload, res_data, resolution)

            if repeat is True:
                transformer_preload = repeat_data(transformer_preload, num_simulation_steps)

            # Should it be ==?
            assert len(transformer_preload) >= num_simulation_steps, msg_alignement_unsuccessful

        realisation.transformer_preload = transformer_preload
        return realisation

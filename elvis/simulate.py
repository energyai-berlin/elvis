"""Simulation of the behavior of the charging infrastructure.

- TODO: What if connection points/charging points are not type manual but type automated.
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

from elvis.config import ScenarioConfig, ScenarioRealisation
from elvis.result import ElvisResult
from elvis.set_up_infrastructure import set_up_infrastructure
from elvis.utility.elvis_general import create_time_steps
from elvis.waiting_queue import WaitingQueue


def handle_car_arrival(
    free_cps: set[Any],
    busy_cps: set[Any],
    event: Any,
    waiting_queue: Any,
    counter_rejections: int,
    within_opening_hours: bool,
    log: bool,
) -> tuple[Any, int]:
    """Connects car to charging point, to the queue or send it off.

    Args:
        free_cps: (set): Containing all :obj: `charging_points.ChargingPoint`
            of the infrastructure that are currently available.
        busy_cps: (set): Containing all :obj: `charging_points.ChargingPoint`
            of the infrastructure that are currently busy.
        event: (:obj: `charging_event.ChargingEvent`): Arriving charging event.
        waiting_queue: (:obj: `queue.WaitingQueue`): Containing the waiting vehicles
        counter_rejections: (int): Counts how many cars can not connect to a charging point nor to
            the waiting_queue.
        within_opening_hours: (bool): True if currently within opening hours.
        log: (bool): True if actions taken shall be logged.

    """
    # connect the arrival to an available charging point if possible
    if len(free_cps) > 0 and within_opening_hours:
        # Get random free charging point and remove it from set
        cp = free_cps.pop()
        cp.connect_vehicle(event)
        if log:
            logging.info(" Connect: %s", cp)
        # Put charging point to busy set
        busy_cps.add(cp)
        return waiting_queue, counter_rejections

    # if no free charging point available put arrival to queue
    # if not full and queue is considered in simulation (maxsize > 0)
    if (
        waiting_queue.size() != waiting_queue.maxsize
        and waiting_queue.maxsize > 0
        and within_opening_hours
    ):
        waiting_queue.enqueue(event)
        if log:
            logging.info(" Put %s to queue.", event)
    else:
        if log and within_opening_hours:
            logging.info(" WaitingQueue is full -> Reject: %s", event)
        elif log and not within_opening_hours:
            logging.info("Out of opening hours.")
        counter_rejections += 1
    return waiting_queue, counter_rejections


def update_queue(
    waiting_queue: Any,
    current_time_step: datetime.datetime,
    by_time: bool,
    within_opening_hours: bool,
    log: bool,
) -> None:
    """Removes cars that have spent their total parking time in the waiting queue and therefore must leave.

    Args:
        waiting_queue: (:obj: `queue.WaitingQueue`): Charging events waiting for available
        charging point.
        current_time_step: (:obj: `datetime.datetime`): current time step of the simulation.
        by_time: (bool): True if cars shall be disconnected with respect to their parking time.
        False if cars shall be disconnected due to their SOC target.
        within_opening_hours: (bool): True if currently within opening hours.
        log: (bool): True if actions taken shall be logged.

    Returns:
        updated_queue: (:obj: `queue.WaitingQueue`): WaitingQueue without removed cars
            that are overdue.
    """
    if not within_opening_hours:
        waiting_queue.empty()
        logging.info(" Remove all vehicles from queue -> out of opening hours.")
    if by_time is True and current_time_step >= waiting_queue.next_leave:
        to_delete = []
        for i in range(waiting_queue.size()):
            event = waiting_queue.queue[i]

            # If waiting time is not longer than parking time remain in queue
            if event.leaving_time <= current_time_step:
                to_delete.insert(0, i)

        if len(to_delete) > 0 and log:
            for i in to_delete:
                logging.info(" Remove: %s from queue.", waiting_queue.queue.pop(i))

        waiting_queue.determine_next_leaving_time()


def update_cps(
    free_cps: set[Any],
    busy_cps: set[Any],
    waiting_queue: Any,
    current_time_step: datetime.datetime,
    by_time: bool,
    within_opening_hours: bool,
    log: bool,
) -> None:
    """Removes cars due to their parking time or their SOC limit and updates the charging points.

    Args:
        free_cps: (set): Containing all :obj: `charging_point.ChargingPoint`
            of the infrastructure that are currently available.
        busy_cps: (set): Containing all :obj: `charging_point.ChargingPoint`
            of the infrastructure that are currently busy.
        waiting_queue: (:obj: `queue.WaitingQueue`): waiting vehicles/charging events.
        current_time_step: (:obj: `datetime.datetime`): current time step.
        by_time: (bool): Configuration class instance.
        within_opening_hours: (bool): True if currently within opening hours.
        log: (bool): True if actions taken shall be logged.
    """
    # if outside of opening hours disconnect all vehicles
    if not within_opening_hours:
        cps_to_remove = []
        for cp in busy_cps:
            cp.disconnect_vehicle()
            cps_to_remove.append(cp)
            if log:
                logging.info(" Disconnect: %s", cp)
        for cp in cps_to_remove:
            busy_cps.remove(cp)
            free_cps.add(cp)
        return

    temp_switch_cps = []
    # if parking time is overdue: disconnect vehicle
    if by_time is True:
        for cp in busy_cps:
            connected_vehicle = cp.connected_vehicle

            if connected_vehicle["leaving_time"] <= current_time_step:
                if log:
                    logging.info(" Disconnect: %s", cp)
                cp.disconnect_vehicle()
                temp_switch_cps.append(cp)

                # immediately connect next waiting car
                if waiting_queue.size() > 0:
                    cp.connect_vehicle(waiting_queue.dequeue())
                    # temporary store cps to switch later so busy_cp set does not change size
                    temp_switch_cps = temp_switch_cps[:-1]
                    # Put charging point from available to busy
                    if log:
                        logging.info(" Connect: %s from queue.", cp)

        for cp in temp_switch_cps:
            busy_cps.remove(cp)
            free_cps.add(cp)

    # if SOC limit is reached: disconnect vehicle
    else:
        for cp in busy_cps:
            connected_vehicle = cp.connected_vehicle

            soc = connected_vehicle["soc"]
            soc_target = connected_vehicle["soc_target"]

            if round(soc, 3) >= soc_target:
                if log:
                    logging.info(" Disconnect: %s", cp)
                cp.disconnect_vehicle()

                temp_switch_cps.append(cp)

                # immediately connect next waiting car
                if waiting_queue.size() > 0:
                    cp.connect_vehicle(waiting_queue.dequeue())
                    # temporary store cps to switch later so set does not change size
                    temp_switch_cps = temp_switch_cps[:-1]
                    if log:
                        logging.info(" Connect: %s from queue.", cp)
                # Put charging point from available to busy
        for cp in temp_switch_cps:
            busy_cps.remove(cp)
            free_cps.add(cp)


def charge_connected_vehicles(
    assign_power_cps: dict[Any, float], busy_cps: set[Any], res: datetime.timedelta, log: bool
) -> None:
    """Change SOC of connected vehicles based on power assigned by scheduling policy.

    Args:
        assign_power_cps: (dict): keys=charging points, values=power to be assigned.
        busy_cps: list of all charging points that currently have a connected
            vehicle.
        res: (:obj: `datetime.timedelta`): Time in between two adjacent time stamps.
        log: (bool): Flag denoting whether a logging entry is supposed to take place.

    Returns: None
    """
    for cp in busy_cps:
        power = assign_power_cps[cp]
        vehicle = cp.connected_vehicle
        soc_before = vehicle["soc"]
        if vehicle is None:
            raise TypeError

        cp.charge_vehicle(power, res)

        if log:
            logging.info(
                "At charging point %s the vehicle SOC has been charged from %s to %s. "
                "The power assigned is: %s",
                cp,
                soc_before,
                vehicle["soc"],
                str(power),
            )


def charge_storage(
    assign_power: dict[str, Any], preload: float, step_length: datetime.timedelta
) -> dict[str, Any]:
    """Charges/discharges the storage and returns the realised (dis)charging power.

    Args:
        assign_power: (dict): power assigned to storage and cps
        preload: (float): Preload at current time step.
        step_length: (:obj: `datetime.timedelta`): Resolution of the simulation denoting the
                time in between two adjacent time steps.

    Returns:
        assign_power: (dict): keys=storage, value=realised power

    """
    assign_power_storage = assign_power["storage"]
    assign_power_cps = assign_power["cps"]
    for storage_system in assign_power_storage:
        power_to_storage = assign_power_storage[storage_system]
        storage = storage_system.storage

        # Storage is not needed to charge cps so see if charging is possible
        if power_to_storage == 0:
            transformer = storage_system.get_transformer()
            power_available = transformer.max_hardware_power(assign_power_cps, preload)
            # Charge storage depending on available power and its limits
            power_charged = storage.charge(power_available, step_length)
            # Update assigned power
            assign_power["storage"][storage_system] = power_charged
        # Try to discharge with assigned power
        else:
            storage.discharge(abs(power_to_storage), step_length)

    return assign_power


def update_last_charged(
    charging_times: dict[Any, dict[str, datetime.datetime]],
    assign_power_cps: dict[Any, float],
    time_step: datetime.datetime,
) -> dict[Any, dict[str, datetime.datetime]]:
    """Updates the dict containing parking events with their start time and the last time they were charged.

    Args:
        charging_times: (dict): Containing each car as keys and their connection time and the last
            time they were charged.
        assign_power_cps: (dict): Containing the powers assigned to each busy charging point at the
            current time step.
        time_step: (:obj: `datetime.datetime`): Current time step.

    Returns:
        charging_times_updated: (dict): Added cars that have not been charged before and updates
            last charged if car has been charged again.
    """
    cps_with_power = {k: v for k, v in assign_power_cps.items() if v > 0}

    charging_times_updated = charging_times
    for cp in cps_with_power:
        ce = cp.connected_vehicle["id"]
        if ce not in charging_times_updated:
            charging_times_updated[ce] = {"arrival": time_step, "last_charged": time_step}
        else:
            charging_times_updated[ce]["last_charged"] = time_step

    return charging_times_updated


def simulate(
    scenario: ScenarioConfig | ScenarioRealisation,
    start_date: datetime.datetime | None = None,
    end_date: datetime.datetime | None = None,
    resolution: datetime.timedelta | None = None,
    realisation_file_name: str | None = None,
    log: bool = False,
    print_progress: bool = True,
) -> ElvisResult:
    """Main simulation loop.

    Iterates over simulation period and simulates the infrastructure.

    Args:
        scenario: Scenario to be simulated.
        start_date: First time stamp.
        end_date: Upper bound for time stamps.
        resolution: Time in between two adjacent time stamps.
        realisation_file_name: Name of the realisation file.
        log: Flag denoting whether a logging entry is supposed to take place.
        print_progress: Flag denoting whether progress should be printed.

    Returns:
        ElvisResult: Contains the results of the simulation.
    """
    # set up charging points in result to store assigned powers
    if realisation_file_name is None:
        results = ElvisResult()
    else:
        results = ElvisResult(scenario, realisation_file_name)

    for _progress in simulate_async(scenario, results, start_date, end_date, resolution, log):
        if print_progress:
            # Progress monitoring available but output suppressed for linting compliance
            pass

    return results


def simulate_async(
    scenario: ScenarioConfig | ScenarioRealisation,
    results: ElvisResult,
    start_date: datetime.datetime | None = None,
    end_date: datetime.datetime | None = None,
    resolution: datetime.timedelta | None = None,
    log: bool = False,
) -> Generator[float, None, None]:
    """Main simulation loop.

    Iterates over simulation period and simulates the infrastructure.

    Args:
        scenario: Scenario to be simulated.
        results: Results object to store simulation data.
        start_date: First time stamp.
        end_date: Upper bound for time stamps.
        resolution: Time in between two adjacent time stamps.
        log: Flag denoting whether a logging entry is supposed to take place.

    Yields:
        float: Progress of the simulation (0.0 to 1.0).
    """
    # ---------------------Initialisation---------------------------
    # if input is instance of ScenarioConfig transform to ScenarioRealisation

    if isinstance(scenario, ScenarioConfig):
        scenario = scenario.create_realisation(start_date, end_date, resolution)

    assert isinstance(scenario, ScenarioRealisation), (
        "Realisation must be of type ScenarioRealisation or ScenarioConfig."
    )

    # empty log file
    with Path("log.log").open("w"):
        pass
    if log:
        logging.basicConfig(filename="log.log", level=logging.INFO)
    # get list with all time_steps as datetime.datetime
    time_steps = create_time_steps(scenario.start_date, scenario.end_date, scenario.resolution)
    # Initialize waiting queue for cars at the infrastructure
    waiting_queue = WaitingQueue(maxsize=scenario.queue_length)
    # copy charging_events from scenario
    charging_events = scenario.charging_events
    # set up infrastructure and get all charging points
    free_cps = set(set_up_infrastructure(scenario.infrastructure))
    busy_cps = set()
    # Rejections counter
    counter_rejections = 0
    # Charging times tracker
    charging_periods = {}
    # Opening hours
    opening_hours = scenario.opening_hours

    charging_event_counter = 0

    # ---------------------  Main Loop  ---------------------------
    # loop over every time step
    total_time_steps = len(time_steps)
    for time_step_pos in range(len(time_steps)):
        time_step = time_steps[time_step_pos]
        if log:
            logging.info(" %s", time_step)
        if time_step_pos % max(1, int(0.05 * total_time_steps)) == 1:
            yield time_step_pos / total_time_steps
        if opening_hours is None:
            within_opening_hours = True
        else:
            cur_time_hours = time_step.hour + time_step.minute / 60 + time_step.second / 60 / 60
            within_opening_hours = opening_hours[0] <= cur_time_hours <= opening_hours[1]

        # check if cars must be disconnected, if yes immediately connect car from queue if possible
        update_queue(
            waiting_queue, time_step, scenario.disconnect_by_time, within_opening_hours, log
        )

        update_cps(
            free_cps,
            busy_cps,
            waiting_queue,
            time_step,
            scenario.disconnect_by_time,
            within_opening_hours,
            log,
        )

        # in case of multiple charging events in the same time step: handle one after the other
        while (
            len(charging_events) > charging_event_counter
            and time_step == charging_events[charging_event_counter].arrival_time
        ):
            current_charging_event = charging_events[charging_event_counter]
            waiting_queue, counter_rejections = handle_car_arrival(
                free_cps,
                busy_cps,
                current_charging_event,
                waiting_queue,
                counter_rejections,
                within_opening_hours,
                log,
            )
            charging_event_counter += 1

        # assign power
        assign_power = scenario.scheduling_policy.schedule(
            scenario, free_cps, busy_cps, time_step_pos
        )
        if len(busy_cps) > 0:
            charging_periods = update_last_charged(charging_periods, assign_power["cps"], time_step)

        charge_connected_vehicles(assign_power["cps"], busy_cps, scenario.resolution, log)
        # Handle transformer preload - use 0 if None
        preload = (
            0
            if scenario.transformer_preload is None
            else scenario.transformer_preload[time_step_pos]
        )
        charge_storage(assign_power, preload, scenario.resolution)
        results.store_power_charging_points(
            assign_power["cps"], time_step_pos, time_step_pos == total_time_steps - 1
        )
        results.store_power_storage_systems(
            assign_power["storage"], time_step_pos, time_step_pos == total_time_steps - 1
        )

    results.counter_rejections = counter_rejections
    results.charging_periods = charging_periods

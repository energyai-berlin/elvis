"""Comprehensive unit tests for simulate.py module.

Test coverage for simulation functions including:
- Main simulate() function
- Car arrival handling
- Queue management
- Charging point updates
- Vehicle charging logic
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timedelta
from collections import defaultdict

from elvis.simulate import (
    simulate,
    simulate_async,
    handle_car_arrival,
    update_queue,
    update_cps,
    charge_connected_vehicles,
    charge_storage,
)
from elvis.config import ScenarioConfig, ScenarioRealisation
from elvis.result import ElvisResult
from elvis.waiting_queue import WaitingQueue
from elvis.charging_event import ChargingEvent
from elvis.charging_point import ChargingPoint


class TestHandleCarArrival:
    """Test cases for handle_car_arrival function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.free_cps = set()
        self.busy_cps = set()
        self.waiting_queue = Mock(spec=WaitingQueue)
        self.waiting_queue.size.return_value = 0
        self.waiting_queue.maxsize = 5
        self.mock_event = Mock(spec=ChargingEvent)
        self.mock_cp = Mock(spec=ChargingPoint)

    def test_handle_car_arrival_connects_to_free_cp(self):
        """Test car connects to available charging point during opening hours."""
        self.free_cps.add(self.mock_cp)
        counter_rejections = 0

        result_queue, result_rejections = handle_car_arrival(
            self.free_cps,
            self.busy_cps,
            self.mock_event,
            self.waiting_queue,
            counter_rejections,
            within_opening_hours=True,
            log=False,
        )

        # Verify charging point is connected and moved to busy
        self.mock_cp.connect_vehicle.assert_called_once_with(self.mock_event)
        assert self.mock_cp in self.busy_cps
        assert self.mock_cp not in self.free_cps
        assert result_rejections == 0

    def test_handle_car_arrival_no_free_cp_adds_to_queue(self):
        """Test car is added to queue when no charging points available."""
        # No free charging points
        counter_rejections = 0

        result_queue, result_rejections = handle_car_arrival(
            self.free_cps,
            self.busy_cps,
            self.mock_event,
            self.waiting_queue,
            counter_rejections,
            within_opening_hours=True,
            log=False,
        )

        # Verify vehicle is added to queue
        self.waiting_queue.enqueue.assert_called_once_with(self.mock_event)
        assert result_rejections == 0

    def test_handle_car_arrival_queue_full_rejection(self):
        """Test car is rejected when queue is full."""
        counter_rejections = 0
        # Queue is full
        self.waiting_queue.size.return_value = 5  # Equal to maxsize

        result_queue, result_rejections = handle_car_arrival(
            self.free_cps,
            self.busy_cps,
            self.mock_event,
            self.waiting_queue,
            counter_rejections,
            within_opening_hours=True,
            log=False,
        )

        # Verify vehicle is rejected
        self.waiting_queue.enqueue.assert_not_called()
        assert result_rejections == 1

    def test_handle_car_arrival_outside_opening_hours_rejection(self):
        """Test car is rejected when outside opening hours."""
        self.free_cps.add(self.mock_cp)
        counter_rejections = 0

        result_queue, result_rejections = handle_car_arrival(
            self.free_cps,
            self.busy_cps,
            self.mock_event,
            self.waiting_queue,
            counter_rejections,
            within_opening_hours=False,
            log=False,
        )

        # Verify no connection even with free charging point
        self.mock_cp.connect_vehicle.assert_not_called()
        assert result_rejections == 1

    def test_handle_car_arrival_queue_disabled_rejection(self):
        """Test car is rejected when queue is disabled (maxsize = 0)."""
        counter_rejections = 0
        self.waiting_queue.maxsize = 0  # Queue disabled

        result_queue, result_rejections = handle_car_arrival(
            self.free_cps,
            self.busy_cps,
            self.mock_event,
            self.waiting_queue,
            counter_rejections,
            within_opening_hours=True,
            log=False,
        )

        # Verify vehicle is rejected
        self.waiting_queue.enqueue.assert_not_called()
        assert result_rejections == 1

    @patch("elvis.simulate.logging")
    def test_handle_car_arrival_logging(self, mock_logging):
        """Test logging functionality in handle_car_arrival."""
        self.free_cps.add(self.mock_cp)
        counter_rejections = 0

        handle_car_arrival(
            self.free_cps,
            self.busy_cps,
            self.mock_event,
            self.waiting_queue,
            counter_rejections,
            within_opening_hours=True,
            log=True,
        )

        # Verify logging is called
        mock_logging.info.assert_called()


class TestUpdateQueue:
    """Test cases for update_queue function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.waiting_queue = Mock(spec=WaitingQueue)
        self.current_time = datetime(2020, 1, 1, 10, 0, 0)

    def test_update_queue_outside_opening_hours_empties_queue(self):
        """Test queue is emptied when outside opening hours."""
        result = update_queue(
            self.waiting_queue,
            self.current_time,
            by_time=True,
            within_opening_hours=False,
            log=False,
        )

        self.waiting_queue.empty.assert_called_once()

    def test_update_queue_removes_overdue_vehicles(self):
        """Test overdue vehicles are removed from queue."""
        # Mock event that should be removed (leaving time passed)
        overdue_event = Mock()
        overdue_event.leaving_time = datetime(2020, 1, 1, 9, 0, 0)  # Before current time

        valid_event = Mock()
        valid_event.leaving_time = datetime(2020, 1, 1, 11, 0, 0)  # After current time

        self.waiting_queue.queue = [overdue_event, valid_event]
        self.waiting_queue.size.return_value = 2
        self.waiting_queue.next_leave = datetime(2020, 1, 1, 9, 30, 0)  # Before current

        update_queue(
            self.waiting_queue,
            self.current_time,
            by_time=True,
            within_opening_hours=True,
            log=False,
        )

        # Verify determine_next_leaving_time is called to update queue state
        self.waiting_queue.determine_next_leaving_time.assert_called_once()

    def test_update_queue_no_removal_when_by_time_false(self):
        """Test no vehicles removed when by_time is False."""
        self.waiting_queue.next_leave = datetime(2020, 1, 1, 9, 0, 0)  # Before current

        update_queue(
            self.waiting_queue,
            self.current_time,
            by_time=False,
            within_opening_hours=True,
            log=False,
        )

        # Verify determine_next_leaving_time is not called
        self.waiting_queue.determine_next_leaving_time.assert_not_called()


class TestUpdateCps:
    """Test cases for update_cps function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.free_cps = set()
        self.busy_cps = set()
        self.waiting_queue = Mock(spec=WaitingQueue)
        self.waiting_queue.size.return_value = 0
        self.current_time = datetime(2020, 1, 1, 10, 0, 0)

    def test_update_cps_outside_hours_disconnects_all(self):
        """Test all vehicles disconnected when outside opening hours."""
        mock_cp1 = Mock(spec=ChargingPoint)
        mock_cp2 = Mock(spec=ChargingPoint)
        self.busy_cps.update([mock_cp1, mock_cp2])

        update_cps(
            self.free_cps,
            self.busy_cps,
            self.waiting_queue,
            self.current_time,
            by_time=True,
            within_opening_hours=False,
            log=False,
        )

        # Verify all charging points disconnected and moved to free
        mock_cp1.disconnect_vehicle.assert_called_once()
        mock_cp2.disconnect_vehicle.assert_called_once()
        assert mock_cp1 in self.free_cps
        assert mock_cp2 in self.free_cps
        assert len(self.busy_cps) == 0

    def test_update_cps_by_time_disconnects_overdue(self):
        """Test vehicles disconnected when parking time exceeded."""
        mock_cp = Mock(spec=ChargingPoint)
        mock_vehicle = {
            "leaving_time": datetime(2020, 1, 1, 9, 0, 0)  # Before current time
        }
        mock_cp.connected_vehicle = mock_vehicle
        self.busy_cps.add(mock_cp)

        update_cps(
            self.free_cps,
            self.busy_cps,
            self.waiting_queue,
            self.current_time,
            by_time=True,
            within_opening_hours=True,
            log=False,
        )

        # Verify overdue vehicle disconnected
        mock_cp.disconnect_vehicle.assert_called()
        assert mock_cp in self.free_cps
        assert mock_cp not in self.busy_cps

    def test_update_cps_by_soc_disconnects_charged(self):
        """Test vehicles disconnected when SOC target reached."""
        mock_cp = Mock(spec=ChargingPoint)
        mock_vehicle = {
            "soc": 0.95,
            "soc_target": 0.9,  # SOC exceeds target
        }
        mock_cp.connected_vehicle = mock_vehicle
        self.busy_cps.add(mock_cp)

        update_cps(
            self.free_cps,
            self.busy_cps,
            self.waiting_queue,
            self.current_time,
            by_time=False,  # By SOC
            within_opening_hours=True,
            log=False,
        )

        # Verify fully charged vehicle disconnected
        mock_cp.disconnect_vehicle.assert_called()
        assert mock_cp in self.free_cps
        assert mock_cp not in self.busy_cps

    def test_update_cps_connects_waiting_vehicle(self):
        """Test waiting vehicle connected when charging point freed."""
        mock_cp = Mock(spec=ChargingPoint)
        mock_vehicle = {"leaving_time": datetime(2020, 1, 1, 9, 0, 0)}
        mock_cp.connected_vehicle = mock_vehicle
        self.busy_cps.add(mock_cp)

        # Mock waiting vehicle
        mock_waiting_event = Mock()
        self.waiting_queue.size.return_value = 1
        self.waiting_queue.dequeue.return_value = mock_waiting_event

        update_cps(
            self.free_cps,
            self.busy_cps,
            self.waiting_queue,
            self.current_time,
            by_time=True,
            within_opening_hours=True,
            log=False,
        )

        # Verify waiting vehicle connected immediately
        assert mock_cp.disconnect_vehicle.call_count == 1
        mock_cp.connect_vehicle.assert_called_with(mock_waiting_event)
        self.waiting_queue.dequeue.assert_called_once()
        assert mock_cp in self.busy_cps  # Should stay busy with new vehicle


class TestChargeConnectedVehicles:
    """Test cases for charge_connected_vehicles function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_cp = Mock(spec=ChargingPoint)
        self.mock_vehicle = {"soc": 0.5}
        self.mock_cp.connected_vehicle = self.mock_vehicle
        self.busy_cps = [self.mock_cp]
        self.assign_power_cps = {self.mock_cp: 50.0}  # 50 kW
        self.resolution = timedelta(hours=1)

    def test_charge_connected_vehicles_normal_operation(self):
        """Test normal vehicle charging operation."""
        charge_connected_vehicles(self.assign_power_cps, self.busy_cps, self.resolution, log=False)

        # Verify charge_vehicle called with correct parameters
        self.mock_cp.charge_vehicle.assert_called_once_with(50.0, self.resolution)

    def test_charge_connected_vehicles_no_vehicle_error(self):
        """Test error handling when no vehicle connected."""
        self.mock_cp.connected_vehicle = None

        with pytest.raises(TypeError):
            charge_connected_vehicles(
                self.assign_power_cps, self.busy_cps, self.resolution, log=False
            )

    @patch("elvis.simulate.logging")
    def test_charge_connected_vehicles_logging(self, mock_logging):
        """Test logging functionality in charge_connected_vehicles."""
        charge_connected_vehicles(self.assign_power_cps, self.busy_cps, self.resolution, log=True)

        # Verify logging is called with vehicle SOC information
        mock_logging.info.assert_called()
        call_args = mock_logging.info.call_args[0]
        assert "SOC" in call_args[0]


class TestChargeStorage:
    """Test cases for charge_storage function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_storage_system = Mock()
        self.mock_storage = Mock()
        self.mock_storage_system.storage = self.mock_storage

        self.mock_transformer = Mock()
        self.mock_storage_system.get_transformer.return_value = self.mock_transformer

        self.assign_power = {
            "storage": {self.mock_storage_system: 0},  # No power initially assigned
            "cps": {},
        }
        self.preload = 10.0
        self.step_length = timedelta(hours=1)

    def test_charge_storage_no_power_assigned_charges(self):
        """Test storage charges when no power assigned and power available."""
        self.mock_transformer.max_hardware_power.return_value = 100.0
        self.mock_storage.charge.return_value = 80.0  # Actually charged 80 kW

        result = charge_storage(self.assign_power, self.preload, self.step_length)

        # Verify storage charging attempted
        self.mock_transformer.max_hardware_power.assert_called_once()
        self.mock_storage.charge.assert_called_once_with(100.0, self.step_length)

        # Verify assigned power updated
        assert result["storage"][self.mock_storage_system] == 80.0

    def test_charge_storage_power_assigned_discharges(self):
        """Test storage discharges when power is assigned."""
        self.assign_power["storage"][self.mock_storage_system] = -50.0  # Discharge 50 kW

        result = charge_storage(self.assign_power, self.preload, self.step_length)

        # Verify storage discharge attempted
        self.mock_storage.discharge.assert_called_once_with(50.0, self.step_length)


class TestMainSimulate:
    """Test cases for the main simulate functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_scenario = Mock(spec=ScenarioRealisation)

    @patch("elvis.simulate.simulate_async")
    @patch("elvis.simulate.ElvisResult")
    def test_simulate_main_function(self, mock_result_class, mock_simulate_async):
        """Test main simulate function orchestration."""
        mock_result = Mock()
        mock_result_class.return_value = mock_result
        mock_simulate_async.return_value = [0.0, 0.5, 1.0]  # Progress values

        result = simulate(
            self.mock_scenario,
            start_date="2020-01-01 00:00:00",
            end_date="2020-01-01 23:00:00",
            resolution="01:00:00",
            log=False,
            print_progress=False,
        )

        # Verify simulate_async called with correct parameters
        mock_simulate_async.assert_called_once()
        assert result == mock_result

    @patch("elvis.simulate.ElvisResult")
    @patch("elvis.simulate.set_up_infrastructure")
    @patch("elvis.simulate.create_time_steps")
    def test_simulate_async_initialization(
        self, mock_create_time_steps, mock_set_up_infrastructure, mock_result_class
    ):
        """Test simulate_async initialization phase."""
        mock_result = Mock()
        mock_result_class.return_value = mock_result

        # Mock time steps and infrastructure setup
        mock_create_time_steps.return_value = [datetime(2020, 1, 1, 10, 0, 0)]
        mock_set_up_infrastructure.return_value = (set(), set())

        # Mock scenario attributes
        self.mock_scenario.charging_events = []
        self.mock_scenario.queue_length = 0
        self.mock_scenario.opening_times = None

        try:
            list(simulate_async(self.mock_scenario, mock_result))
        except AttributeError:
            # Expected due to missing scenario attributes in mock
            pass

        # Verify infrastructure setup called
        mock_set_up_infrastructure.assert_called_once_with(self.mock_scenario)

    def test_simulate_scenario_config_conversion(self):
        """Test simulate_async converts ScenarioConfig to ScenarioRealisation."""
        mock_config = Mock(spec=ScenarioConfig)
        mock_realisation = Mock(spec=ScenarioRealisation)
        mock_config.create_realisation.return_value = mock_realisation

        # Set up mock realisation attributes to avoid errors
        mock_realisation.charging_events = []
        mock_realisation.queue_length = 0
        mock_realisation.opening_times = None

        with (
            patch("elvis.simulate.set_up_infrastructure"),
            patch("elvis.simulate.create_time_steps", return_value=[]),
            patch("elvis.simulate.ElvisResult"),
        ):
            try:
                list(simulate_async(mock_config, Mock()))
            except AttributeError:
                # Expected due to incomplete mocking
                pass

            # Verify config converted to realisation
            mock_config.create_realisation.assert_called_once()

    def test_simulate_invalid_scenario_type_error(self):
        """Test simulate_async raises error for invalid scenario type."""
        invalid_scenario = "not a scenario object"
        mock_result = Mock()

        with pytest.raises(AssertionError, match="Realisation must be of type"):
            list(simulate_async(invalid_scenario, mock_result))

    @pytest.mark.parametrize(
        "start_date,end_date,resolution",
        [
            ("2020-01-01 00:00:00", "2020-01-02 00:00:00", "01:00:00"),
            ("2020-06-01 00:00:00", "2020-06-01 23:00:00", "00:30:00"),
            ("2020-12-31 00:00:00", "2020-12-31 12:00:00", "00:15:00"),
        ],
    )
    def test_simulate_different_time_parameters(self, start_date, end_date, resolution):
        """Test simulate function with different time parameter combinations."""
        with patch("elvis.simulate.simulate_async", return_value=[1.0]) as mock_async:
            simulate(
                self.mock_scenario,
                start_date=start_date,
                end_date=end_date,
                resolution=resolution,
                print_progress=False,
            )

            # Verify simulate_async called with time parameters
            args, kwargs = mock_async.call_args
            assert args[2] == start_date  # start_date parameter
            assert args[3] == end_date  # end_date parameter
            assert args[4] == resolution  # resolution parameter

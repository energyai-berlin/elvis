"""Comprehensive unit tests for battery.py module.

Test coverage for Battery and EVBattery classes including:
- Initialization and validation
- SOC management and calculations
- Power and energy operations
- Edge cases and error handling
"""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock

from elvis.battery import Battery, EVBattery
from elvis.exceptions import InvalidParameterError, InvalidSOCError
from elvis.types import SOC, Energy, Power, Efficiency


class TestBattery:
    """Test cases for the base Battery class."""

    def test_battery_initialization_valid(self):
        """Test successful battery initialization with valid parameters."""
        battery = Battery(
            capacity=50.0,
            max_charge_power=150.0,
            min_charge_power=0.0,
            efficiency=0.95,
            start_power_degradation=0.8,
            max_degradation_level=0.1,
        )

        assert battery.capacity == 50.0
        assert battery.max_charge_power == 150.0
        assert battery.min_charge_power == 0.0
        assert battery.efficiency == 0.95
        assert battery.start_power_degradation == 0.8
        assert battery.max_degradation_level == 0.1

    def test_battery_initialization_invalid_capacity(self):
        """Test battery initialization fails with invalid capacity."""
        with pytest.raises(AssertionError, match="Battery capacity must be greater than 0"):
            Battery(capacity=0, max_charge_power=150.0, min_charge_power=0.0, efficiency=0.95)

        with pytest.raises(AssertionError, match="Battery capacity must be greater than 0"):
            Battery(capacity=-10.0, max_charge_power=150.0, min_charge_power=0.0, efficiency=0.95)

    def test_battery_initialization_invalid_efficiency(self):
        """Test battery initialization fails with invalid efficiency."""
        with pytest.raises(AssertionError):
            Battery(
                capacity=50.0,
                max_charge_power=150.0,
                min_charge_power=0.0,
                efficiency=1.5,  # > 1
            )

        with pytest.raises(AssertionError):
            Battery(
                capacity=50.0,
                max_charge_power=150.0,
                min_charge_power=0.0,
                efficiency=-0.1,  # < 0
            )

    def test_battery_initialization_invalid_degradation(self):
        """Test battery initialization fails with invalid degradation parameters."""
        with pytest.raises(AssertionError):
            Battery(
                capacity=50.0,
                max_charge_power=150.0,
                min_charge_power=0.0,
                efficiency=0.95,
                start_power_degradation=1.5,  # > 1
            )

        with pytest.raises(AssertionError):
            Battery(
                capacity=50.0,
                max_charge_power=150.0,
                min_charge_power=0.0,
                efficiency=0.95,
                max_degradation_level=1.5,  # > 1
            )

    def test_battery_string_representation(self):
        """Test battery string representation."""
        battery = Battery(
            capacity=50.0, max_charge_power=150.0, min_charge_power=0.0, efficiency=0.95
        )

        str_repr = str(battery)
        assert "50.0 kWh" in str_repr
        assert "150.0 kW" in str_repr


class TestEVBattery:
    """Test cases for the EVBattery class."""

    def test_evbattery_initialization_valid(self):
        """Test successful EVBattery initialization."""
        ev_battery = EVBattery(
            capacity=75.0, max_charge_power=250.0, min_charge_power=0.0, efficiency=0.9
        )

        assert ev_battery.capacity == 75.0
        assert ev_battery.max_charge_power == 250.0
        assert ev_battery.min_charge_power == 0.0
        assert ev_battery.efficiency == 0.9
        # Check inherited defaults
        assert ev_battery.start_power_degradation == 1
        assert ev_battery.max_degradation_level == 0

    def test_evbattery_from_dict_valid(self):
        """Test EVBattery creation from dictionary."""
        config_dict = {
            "capacity": 60.0,
            "max_charge_power": 200.0,
            "min_charge_power": 5.0,
            "efficiency": 0.95,
        }

        ev_battery = EVBattery.from_dict(config_dict)

        assert ev_battery.capacity == 60.0
        assert ev_battery.max_charge_power == 200.0
        assert ev_battery.min_charge_power == 5.0
        assert ev_battery.efficiency == 0.95

    def test_evbattery_from_dict_missing_required(self):
        """Test EVBattery creation fails with missing required fields."""
        incomplete_dict = {
            "capacity": 60.0,
            "max_charge_power": 200.0,
            # Missing min_charge_power and efficiency
        }

        with pytest.raises(KeyError):
            EVBattery.from_dict(incomplete_dict)

    def test_evbattery_from_dict_invalid_values(self):
        """Test EVBattery creation fails with invalid values in dict."""
        invalid_dict = {
            "capacity": -50.0,  # Invalid: negative
            "max_charge_power": 200.0,
            "min_charge_power": 0.0,
            "efficiency": 0.95,
        }

        with pytest.raises(AssertionError):
            EVBattery.from_dict(invalid_dict)

    def test_evbattery_energy_for_soc_change_valid(self):
        """Test energy calculation for SOC change."""
        ev_battery = EVBattery(
            capacity=100.0,
            max_charge_power=200.0,
            min_charge_power=0.0,
            efficiency=1.0,  # Perfect efficiency for easier testing
        )

        # Test SOC increase (charging)
        energy_needed = ev_battery.energy_for_soc_change(current_soc=0.2, target_soc=0.8)
        assert energy_needed == 60.0  # 0.6 * 100 kWh

        # Test SOC decrease (discharging)
        energy_released = ev_battery.energy_for_soc_change(current_soc=0.8, target_soc=0.2)
        assert energy_released == -60.0  # Negative for discharge

    def test_evbattery_energy_for_soc_change_invalid_soc(self):
        """Test energy calculation fails with invalid SOC values."""
        ev_battery = EVBattery(
            capacity=100.0, max_charge_power=200.0, min_charge_power=0.0, efficiency=1.0
        )

        # Test invalid current SOC
        with pytest.raises(InvalidSOCError):
            ev_battery.energy_for_soc_change(current_soc=-0.1, target_soc=0.8)

        with pytest.raises(InvalidSOCError):
            ev_battery.energy_for_soc_change(current_soc=1.1, target_soc=0.8)

        # Test invalid target SOC
        with pytest.raises(InvalidSOCError):
            ev_battery.energy_for_soc_change(current_soc=0.5, target_soc=-0.1)

        with pytest.raises(InvalidSOCError):
            ev_battery.energy_for_soc_change(current_soc=0.5, target_soc=1.1)

    def test_evbattery_time_for_soc_change_valid(self):
        """Test time calculation for SOC change at given power."""
        ev_battery = EVBattery(
            capacity=100.0, max_charge_power=200.0, min_charge_power=0.0, efficiency=1.0
        )

        # Test charging time
        time_needed = ev_battery.time_for_soc_change(
            current_soc=0.2, target_soc=0.8, charge_power=50.0
        )
        # 60 kWh / 50 kW = 1.2 hours
        expected_time = timedelta(hours=1.2)
        assert abs(time_needed.total_seconds() - expected_time.total_seconds()) < 1

    def test_evbattery_time_for_soc_change_zero_power(self):
        """Test time calculation with zero power (should be infinite/error)."""
        ev_battery = EVBattery(
            capacity=100.0, max_charge_power=200.0, min_charge_power=0.0, efficiency=1.0
        )

        with pytest.raises(InvalidParameterError):
            ev_battery.time_for_soc_change(current_soc=0.2, target_soc=0.8, charge_power=0.0)

    def test_evbattery_max_power_at_soc_degradation(self):
        """Test max power calculation with degradation effects."""
        ev_battery = EVBattery(
            capacity=100.0,
            max_charge_power=200.0,
            min_charge_power=0.0,
            efficiency=1.0,
            start_power_degradation=0.8,  # Degradation starts at 80% SOC
            max_degradation_level=0.5,  # 50% power reduction at high SOC
        )

        # At low SOC, no degradation
        max_power_low = ev_battery.max_power_at_soc(soc=0.5)
        assert max_power_low == 200.0

        # At degradation start, no degradation yet
        max_power_start = ev_battery.max_power_at_soc(soc=0.8)
        assert max_power_start == 200.0

        # At high SOC, some degradation
        max_power_high = ev_battery.max_power_at_soc(soc=0.9)
        # Linear interpolation: 0.9 is halfway between 0.8 and 1.0
        # So degradation is 0.5 * 0.5 = 0.25 (25% reduction)
        expected_power = 200.0 * (1 - 0.25)
        assert abs(max_power_high - expected_power) < 0.1

    def test_evbattery_power_clamping(self):
        """Test power values are clamped to battery limits."""
        ev_battery = EVBattery(
            capacity=50.0, max_charge_power=150.0, min_charge_power=5.0, efficiency=1.0
        )

        # Test max power clamping
        clamped_max = ev_battery.clamp_power(300.0)  # Above max
        assert clamped_max == 150.0

        # Test min power clamping
        clamped_min = ev_battery.clamp_power(1.0)  # Below min
        assert clamped_min == 5.0

        # Test within range (no clamping)
        clamped_valid = ev_battery.clamp_power(75.0)  # Within range
        assert clamped_valid == 75.0

    @pytest.mark.parametrize(
        "capacity,max_power,min_power,efficiency",
        [
            (50.0, 150.0, 0.0, 0.95),
            (100.0, 250.0, 3.0, 0.9),
            (25.0, 75.0, 1.0, 1.0),
            (75.0, 200.0, 0.5, 0.85),
        ],
    )
    def test_evbattery_parametrized_initialization(
        self, capacity, max_power, min_power, efficiency
    ):
        """Test EVBattery initialization with various valid parameter combinations."""
        ev_battery = EVBattery(
            capacity=capacity,
            max_charge_power=max_power,
            min_charge_power=min_power,
            efficiency=efficiency,
        )

        assert ev_battery.capacity == capacity
        assert ev_battery.max_charge_power == max_power
        assert ev_battery.min_charge_power == min_power
        assert ev_battery.efficiency == efficiency

    def test_evbattery_energy_efficiency_effects(self):
        """Test that efficiency affects energy calculations correctly."""
        # Battery with 90% efficiency
        ev_battery = EVBattery(
            capacity=100.0, max_charge_power=200.0, min_charge_power=0.0, efficiency=0.9
        )

        # Calculate energy needed for 50% SOC increase
        energy_needed = ev_battery.energy_for_soc_change(current_soc=0.3, target_soc=0.8)
        # With 90% efficiency, need more energy than stored: 50 / 0.9 = 55.56 kWh
        expected_energy = (0.8 - 0.3) * 100.0 / 0.9
        assert abs(energy_needed - expected_energy) < 0.1

    def test_evbattery_soc_boundary_conditions(self):
        """Test battery behavior at SOC boundaries (0% and 100%)."""
        ev_battery = EVBattery(
            capacity=100.0, max_charge_power=200.0, min_charge_power=0.0, efficiency=1.0
        )

        # Test full charge from empty
        full_charge_energy = ev_battery.energy_for_soc_change(current_soc=0.0, target_soc=1.0)
        assert full_charge_energy == 100.0

        # Test full discharge from full
        full_discharge_energy = ev_battery.energy_for_soc_change(current_soc=1.0, target_soc=0.0)
        assert full_discharge_energy == -100.0

        # Test no change
        no_change_energy = ev_battery.energy_for_soc_change(current_soc=0.5, target_soc=0.5)
        assert no_change_energy == 0.0

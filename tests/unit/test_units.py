"""Comprehensive unit tests for units.py module.

Test coverage for physical unit classes including:
- Power conversions and operations
- Current conversions and charge calculations
- Charge to energy conversions
- Energy to charge conversions
- Unit consistency and integration
"""

import pytest
from elvis.units import Power, Current, Charge, Energy


class TestPower:
    """Test cases for the Power class."""

    def test_power_initialization(self):
        """Test Power class initialization."""
        power = Power(1500.0)  # 1500 watts
        assert power.watts == 1500.0

    def test_power_kilowatts_conversion(self):
        """Test watts to kilowatts conversion."""
        # Test various power values
        test_cases = [
            (1000.0, 1.0),  # 1000W = 1kW
            (1500.0, 1.5),  # 1500W = 1.5kW
            (500.0, 0.5),  # 500W = 0.5kW
            (2300.0, 2.3),  # 2300W = 2.3kW
            (0.0, 0.0),  # 0W = 0kW
        ]

        for watts, expected_kw in test_cases:
            power = Power(watts)
            assert abs(power.kilowatts - expected_kw) < 1e-10

    def test_power_fractional_watts(self):
        """Test Power with fractional watt values."""
        power = Power(123.456)
        assert power.watts == 123.456
        assert abs(power.kilowatts - 0.123456) < 1e-10

    def test_power_negative_values(self):
        """Test Power with negative values (e.g., discharging)."""
        power = Power(-500.0)
        assert power.watts == -500.0
        assert power.kilowatts == -0.5

    @pytest.mark.parametrize("watts", [0.0, 100.0, 1000.0, 1500.0, 3000.0, 7400.0, 150000.0])
    def test_power_parametrized_conversions(self, watts):
        """Test Power conversions with various values."""
        power = Power(watts)
        assert power.watts == watts
        assert abs(power.kilowatts - watts / 1000.0) < 1e-10


class TestCurrent:
    """Test cases for the Current class."""

    def test_current_initialization(self):
        """Test Current class initialization."""
        current = Current(10.5)  # 10.5 amps
        assert current.amps == 10.5

    def test_current_milliamps_conversion(self):
        """Test amps to milliamps conversion."""
        test_cases = [
            (1.0, 1000.0),  # 1A = 1000mA
            (0.5, 500.0),  # 0.5A = 500mA
            (0.001, 1.0),  # 0.001A = 1mA
            (2.5, 2500.0),  # 2.5A = 2500mA
            (0.0, 0.0),  # 0A = 0mA
        ]

        for amps, expected_milliamps in test_cases:
            current = Current(amps)
            assert abs(current.milliamps - expected_milliamps) < 1e-10

    def test_current_charge_multiplication(self):
        """Test current multiplication to create charge (amp-hours)."""
        current = Current(5.0)  # 5 amps

        # Multiply by hours to get charge
        charge = current * 2.0  # 2 hours

        assert isinstance(charge, Charge)
        assert charge.amp_hours == 10.0  # 5A × 2h = 10Ah

    def test_current_multiplication_edge_cases(self):
        """Test current multiplication with edge case values."""
        current = Current(3.0)

        # Zero hours
        charge_zero = current * 0.0
        assert charge_zero.amp_hours == 0.0

        # Fractional hours
        charge_frac = current * 0.5
        assert charge_frac.amp_hours == 1.5

        # Large hours
        charge_large = current * 24.0
        assert charge_large.amp_hours == 72.0

    def test_current_negative_values(self):
        """Test Current with negative values."""
        current = Current(-2.0)
        assert current.amps == -2.0
        assert current.milliamps == -2000.0

        # Negative current × positive time = negative charge
        charge = current * 1.0
        assert charge.amp_hours == -2.0

    @pytest.mark.parametrize(
        "amps,hours,expected_charge",
        [
            (1.0, 1.0, 1.0),  # 1A × 1h = 1Ah
            (5.0, 2.0, 10.0),  # 5A × 2h = 10Ah
            (0.5, 4.0, 2.0),  # 0.5A × 4h = 2Ah
            (10.0, 0.1, 1.0),  # 10A × 0.1h = 1Ah
            (2.5, 3.2, 8.0),  # 2.5A × 3.2h = 8Ah
        ],
    )
    def test_current_parametrized_multiplication(self, amps, hours, expected_charge):
        """Test current multiplication with various parameter combinations."""
        current = Current(amps)
        charge = current * hours
        assert abs(charge.amp_hours - expected_charge) < 1e-10


class TestCharge:
    """Test cases for the Charge class."""

    def test_charge_initialization(self):
        """Test Charge class initialization."""
        charge = Charge(15.5)  # 15.5 amp-hours
        assert charge.amp_hours == 15.5

    def test_charge_energy_conversion(self):
        """Test charge to energy conversion at given voltage."""
        charge = Charge(10.0)  # 10 Ah

        # Convert to energy at various voltages
        test_cases = [
            (12.0, 120.0),  # 10Ah × 12V = 120Wh
            (24.0, 240.0),  # 10Ah × 24V = 240Wh
            (400.0, 4000.0),  # 10Ah × 400V = 4000Wh
            (1.0, 10.0),  # 10Ah × 1V = 10Wh
        ]

        for voltage, expected_wh in test_cases:
            energy = charge.energy(voltage)
            assert isinstance(energy, Energy)
            # Energy class stores in Wh, not kWh
            assert abs(energy.kwh - expected_wh) < 1e-10

    def test_charge_energy_zero_values(self):
        """Test charge to energy conversion with zero values."""
        # Zero charge
        zero_charge = Charge(0.0)
        energy = zero_charge.energy(400.0)
        assert energy.kwh == 0.0

        # Zero voltage (edge case)
        charge = Charge(10.0)
        energy_zero_v = charge.energy(0.0)
        assert energy_zero_v.kwh == 0.0

    def test_charge_energy_negative_values(self):
        """Test charge to energy conversion with negative values."""
        # Negative charge (e.g., discharge)
        charge = Charge(-5.0)
        energy = charge.energy(12.0)
        assert energy.kwh == -60.0  # -5Ah × 12V = -60Wh

        # Negative voltage (theoretical)
        charge_pos = Charge(5.0)
        energy_neg_v = charge_pos.energy(-12.0)
        assert energy_neg_v.kwh == -60.0

    @pytest.mark.parametrize(
        "amp_hours,voltage,expected_kwh",
        [
            (1.0, 12.0, 12.0),  # 1Ah × 12V = 12Wh
            (50.0, 400.0, 20000.0),  # 50Ah × 400V = 20000Wh
            (2.5, 48.0, 120.0),  # 2.5Ah × 48V = 120Wh
            (100.0, 800.0, 80000.0),  # 100Ah × 800V = 80000Wh
        ],
    )
    def test_charge_parametrized_energy_conversion(self, amp_hours, voltage, expected_kwh):
        """Test charge to energy conversion with various parameters."""
        charge = Charge(amp_hours)
        energy = charge.energy(voltage)
        assert abs(energy.kwh - expected_kwh) < 1e-10


class TestEnergy:
    """Test cases for the Energy class."""

    def test_energy_initialization(self):
        """Test Energy class initialization."""
        energy = Energy(5750.0)  # 5750 Wh (stored as Wh, not kWh)
        assert energy.kwh == 5750.0

    def test_energy_charge_conversion(self):
        """Test energy to charge conversion at given voltage."""
        energy = Energy(2400.0)  # 2400 Wh

        # Convert to charge at various voltages
        test_cases = [
            (12.0, 200.0),  # 2400Wh ÷ 12V = 200Ah
            (24.0, 100.0),  # 2400Wh ÷ 24V = 100Ah
            (400.0, 6.0),  # 2400Wh ÷ 400V = 6Ah
            (1.0, 2400.0),  # 2400Wh ÷ 1V = 2400Ah
        ]

        for voltage, expected_ah in test_cases:
            charge = energy.charge(voltage)
            assert isinstance(charge, Charge)
            assert abs(charge.amp_hours - expected_ah) < 1e-10

    def test_energy_charge_zero_energy(self):
        """Test energy to charge conversion with zero energy."""
        zero_energy = Energy(0.0)
        charge = zero_energy.charge(400.0)
        assert charge.amp_hours == 0.0

    def test_energy_charge_zero_voltage_error(self):
        """Test energy to charge conversion with zero voltage raises error."""
        energy = Energy(10.0)

        # This should cause division by zero
        with pytest.raises(ZeroDivisionError):
            energy.charge(0.0)

    def test_energy_charge_negative_values(self):
        """Test energy to charge conversion with negative values."""
        # Negative energy
        energy = Energy(-1200.0)  # -1200 Wh
        charge = energy.charge(12.0)
        assert abs(charge.amp_hours - (-100.0)) < 1e-10  # -1200Wh ÷ 12V = -100Ah

        # Negative voltage
        energy_pos = Energy(1200.0)
        charge_neg_v = energy_pos.charge(-12.0)
        assert abs(charge_neg_v.amp_hours - (-100.0)) < 1e-10

    @pytest.mark.parametrize(
        "wh,voltage,expected_ah",
        [
            (1000.0, 12.0, 83.333333),  # 1000Wh ÷ 12V = 83.33Ah
            (10000.0, 400.0, 25.0),  # 10000Wh ÷ 400V = 25Ah
            (500.0, 24.0, 20.833333),  # 500Wh ÷ 24V = 20.83Ah
            (75000.0, 800.0, 93.75),  # 75000Wh ÷ 800V = 93.75Ah
        ],
    )
    def test_energy_parametrized_charge_conversion(self, wh, voltage, expected_ah):
        """Test energy to charge conversion with various parameters."""
        energy = Energy(wh)
        charge = energy.charge(voltage)
        assert abs(charge.amp_hours - expected_ah) < 1e-6  # Allow small floating point errors


class TestUnitsIntegration:
    """Integration tests for unit conversions and roundtrip operations."""

    def test_current_charge_energy_roundtrip(self):
        """Test roundtrip: Current → Charge → Energy → Charge."""
        original_current = Current(5.0)  # 5 amps
        hours = 2.0
        voltage = 12.0

        # Current → Charge
        charge1 = original_current * hours  # 5A × 2h = 10Ah

        # Charge → Energy
        energy = charge1.energy(voltage)  # 10Ah × 12V = 120Wh

        # Energy → Charge (should get back same charge)
        charge2 = energy.charge(voltage)  # 120Wh ÷ 12V = 10Ah

        assert abs(charge1.amp_hours - charge2.amp_hours) < 1e-10

    def test_power_units_independence(self):
        """Test that Power units operate independently from other units."""
        power = Power(1500.0)  # 1.5 kW

        # Power should not interfere with other unit calculations
        current = Current(10.0)
        charge = current * 1.0  # 10 Ah
        energy = charge.energy(400.0)  # 4 kWh

        # Original power should be unchanged
        assert power.watts == 1500.0
        assert power.kilowatts == 1.5

        # Other units should work correctly
        assert charge.amp_hours == 10.0
        assert energy.kwh == 4000.0

    def test_unit_type_consistency(self):
        """Test that operations return correct unit types."""
        current = Current(3.0)
        charge = Charge(15.0)
        energy = Energy(1.8)
        power = Power(900.0)

        # Type checks
        assert isinstance(current * 5.0, Charge)
        assert isinstance(charge.energy(12.0), Energy)
        assert isinstance(energy.charge(12.0), Charge)

        # Power should remain Power type
        assert isinstance(power, Power)

    def test_realistic_ev_battery_scenario(self):
        """Test units with realistic EV battery scenario."""
        # Tesla Model 3 Long Range approximate specs
        battery_capacity = Energy(75000.0)  # 75000 Wh (75 kWh)
        battery_voltage = 400.0  # 400V nominal
        charging_current = Current(125.0)  # 125A DC fast charging

        # Calculate battery capacity in Ah
        battery_ah = battery_capacity.charge(battery_voltage)
        assert abs(battery_ah.amp_hours - 187.5) < 1e-10  # 75000Wh ÷ 400V = 187.5Ah

        # Calculate charging time for 50% capacity
        half_capacity_ah = Charge(battery_ah.amp_hours * 0.5)  # 93.75 Ah
        charging_time_hours = half_capacity_ah.amp_hours / charging_current.amps
        assert abs(charging_time_hours - 0.75) < 1e-10  # 0.75 hours = 45 minutes

        # Verify energy equivalence
        half_energy = half_capacity_ah.energy(battery_voltage)
        assert abs(half_energy.kwh - 37500.0) < 1e-10  # 37500 Wh

    def test_unit_precision_consistency(self):
        """Test that unit conversions maintain precision."""
        # High precision values
        precise_power = Power(1234.56789)
        assert abs(precise_power.kilowatts - 1.23456789) < 1e-10

        precise_current = Current(12.3456)
        assert abs(precise_current.milliamps - 12345.6) < 1e-10

        precise_charge = Charge(98.7654321)
        precise_energy = precise_charge.energy(123.456)
        expected_wh = 98.7654321 * 123.456  # Result in Wh, not kWh
        assert abs(precise_energy.kwh - expected_wh) < 1e-10

    @pytest.mark.parametrize("base_value", [0.001, 1.0, 100.0, 1000.0, 10000.0])
    def test_units_scale_invariance(self, base_value):
        """Test that unit relationships hold across different scales."""
        # Power scaling
        power = Power(base_value)
        assert power.kilowatts == base_value / 1000.0

        # Current scaling
        current = Current(base_value)
        assert current.milliamps == base_value * 1000.0

        # Charge-Energy consistency
        charge = Charge(base_value)
        energy = charge.energy(1.0)  # 1V for simple conversion
        back_to_charge = energy.charge(1.0)
        assert abs(back_to_charge.amp_hours - base_value) < 1e-10

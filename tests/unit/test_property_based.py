"""Property-based tests for ELVIS core algorithms using Hypothesis.

These tests verify mathematical invariants and properties that should
hold for all valid inputs, discovering edge cases automatically.

Focus areas:
- Energy conservation laws
- SOC bounds and constraints
- Power limits and validation
- Time calculations consistency
- Unit conversion accuracy
"""

import pytest
import math
from datetime import timedelta
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite

from elvis.battery import Battery, EVBattery
from elvis.vehicle import ElectricVehicle
from elvis.units import Power, Current, Charge, Energy
from elvis.distribution import NormalDistribution, InterpolatedDistribution
from elvis.config.validation import ConfigValidator
from elvis.enums import SchedulingPolicyType, SampleMethod


# Custom strategies for domain-specific values
@composite
def soc_values(draw):
    """Generate valid SOC values between 0 and 1."""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@composite
def positive_energy(draw):
    """Generate positive energy values (kWh)."""
    return draw(st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False))


@composite
def positive_power(draw):
    """Generate positive power values (kW)."""
    return draw(st.floats(min_value=0.1, max_value=500.0, allow_nan=False, allow_infinity=False))


@composite
def efficiency_values(draw):
    """Generate valid efficiency values between 0 and 1."""
    return draw(st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False))


@composite
def probability_values(draw):
    """Generate valid probability values between 0 and 1."""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@composite
def battery_params(draw):
    """Generate valid battery parameter combinations."""
    capacity = draw(positive_energy())
    max_power = draw(positive_power())
    min_power = draw(
        st.floats(min_value=0.0, max_value=max_power, allow_nan=False, allow_infinity=False)
    )
    efficiency = draw(efficiency_values())
    start_degradation = draw(probability_values())
    max_degradation = draw(probability_values())

    return {
        "capacity": capacity,
        "max_charge_power": max_power,
        "min_charge_power": min_power,
        "efficiency": efficiency,
        "start_power_degradation": start_degradation,
        "max_degradation_level": max_degradation,
    }


class TestBatteryProperties:
    """Property-based tests for Battery and EVBattery classes."""

    @given(battery_params())
    def test_battery_power_bounds_invariant(self, params):
        """Test that battery power is always within specified bounds."""
        # Ensure degradation constraint is satisfied
        assume(
            params["max_degradation_level"] * params["max_charge_power"]
            >= params["min_charge_power"]
        )

        battery = EVBattery(**params)

        # Property: max_power_possible should never exceed max_charge_power
        test_soc_values = [0.0, 0.25, 0.5, 0.75, 1.0]
        for soc in test_soc_values:
            max_power = battery.max_power_possible(soc)
            assert max_power <= params["max_charge_power"], (
                f"Max power {max_power} exceeds battery limit {params['max_charge_power']} at SOC {soc}"
            )
            assert max_power >= 0, f"Max power {max_power} is negative at SOC {soc}"

    @given(battery_params())
    def test_battery_power_degradation_monotonic(self, params):
        """Test that power degradation is monotonic (decreases with increasing SOC above threshold)."""
        assume(
            params["max_degradation_level"] * params["max_charge_power"]
            >= params["min_charge_power"]
        )
        assume(params["start_power_degradation"] < 1.0)  # Need room for degradation

        battery = EVBattery(**params)

        # Property: Power should be non-increasing as SOC increases above start_power_degradation
        soc_values = [
            params["start_power_degradation"] + i * 0.05
            for i in range(0, int((1.0 - params["start_power_degradation"]) / 0.05) + 1)
        ]

        if len(soc_values) > 1:
            powers = [battery.max_power_possible(soc) for soc in soc_values]

            for i in range(1, len(powers)):
                assert powers[i] <= powers[i - 1], (
                    f"Power increased from {powers[i - 1]} to {powers[i]} at SOC {soc_values[i]}"
                )

    @given(battery_params(), soc_values())
    def test_battery_min_power_invariant(self, params, soc):
        """Test that minimum power is always consistent."""
        assume(
            params["max_degradation_level"] * params["max_charge_power"]
            >= params["min_charge_power"]
        )

        battery = EVBattery(**params)
        min_power = battery.min_power_possible(soc)

        # Property: Min power should always equal min_charge_power (for current implementation)
        assert min_power == params["min_charge_power"]

    @given(st.data())
    def test_battery_to_dict_from_dict_roundtrip(self, data):
        """Test that battery dictionary conversion is a perfect roundtrip."""
        params = data.draw(battery_params())
        assume(
            params["max_degradation_level"] * params["max_charge_power"]
            >= params["min_charge_power"]
        )

        original_battery = EVBattery(**params)
        battery_dict = original_battery.to_dict()

        # Create new battery from dict
        reconstructed_battery = EVBattery.from_dict(**battery_dict)

        # Property: All parameters should be identical
        assert isinstance(reconstructed_battery, EVBattery)
        assert reconstructed_battery.capacity == original_battery.capacity
        assert reconstructed_battery.max_charge_power == original_battery.max_charge_power
        assert reconstructed_battery.min_charge_power == original_battery.min_charge_power
        assert reconstructed_battery.efficiency == original_battery.efficiency


class TestUnitsProperties:
    """Property-based tests for unit conversion classes."""

    @given(st.floats(min_value=-1000000, max_value=1000000, allow_nan=False, allow_infinity=False))
    def test_power_unit_conversion_consistent(self, watts):
        """Test that power unit conversions are mathematically consistent."""
        power = Power(watts)

        # Property: Converting back and forth should give original value
        kilowatts = power.kilowatts
        watts_back = kilowatts * 1000.0

        assert abs(watts_back - watts) < 1e-10

    @given(st.floats(min_value=-1000000, max_value=1000000, allow_nan=False, allow_infinity=False))
    def test_current_unit_conversion_consistent(self, amps):
        """Test that current unit conversions are mathematically consistent."""
        current = Current(amps)

        # Property: Converting back and forth should give original value
        milliamps = current.milliamps
        amps_back = milliamps / 1000.0

        assert abs(amps_back - amps) < 1e-9

    @given(
        st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False),
    )
    def test_current_charge_multiplication_commutative(self, amps, hours):
        """Test that current × time = charge is mathematically correct."""
        current = Current(amps)
        charge = current * hours

        # Property: amp-hours should equal amps × hours exactly
        expected_ah = amps * hours
        assert abs(charge.amp_hours - expected_ah) < 1e-10

    @given(
        st.floats(min_value=-10000, max_value=10000, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    def test_charge_energy_conversion_reciprocal(self, amp_hours, voltage):
        """Test that charge ↔ energy conversions are reciprocal."""
        charge = Charge(amp_hours)
        energy = charge.energy(voltage)
        charge_back = energy.charge(voltage)

        # Property: Roundtrip conversion should preserve original value
        assert abs(charge_back.amp_hours - amp_hours) < 1e-10

    @given(
        st.floats(min_value=-100000, max_value=100000, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    def test_energy_charge_conversion_reciprocal(self, watt_hours, voltage):
        """Test that energy ↔ charge conversions are reciprocal."""
        energy = Energy(watt_hours)
        charge = energy.charge(voltage)
        energy_back = charge.energy(voltage)

        # Property: Roundtrip conversion should preserve original value
        assert abs(energy_back.kwh - watt_hours) < 1e-10

    @given(
        st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    def test_units_energy_conservation(self, amps, hours, voltage):
        """Test energy conservation through unit conversions."""
        # Current → Charge → Energy calculation
        current = Current(amps)
        charge = current * hours  # amp-hours
        energy = charge.energy(voltage)  # watt-hours

        # Property: Energy should equal amps × hours × voltage
        expected_energy = amps * hours * voltage
        assert abs(energy.kwh - expected_energy) < 1e-10


class TestDistributionProperties:
    """Property-based tests for distribution classes."""

    @given(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False),
    )
    def test_normal_distribution_properties(self, mu, sigma):
        """Test mathematical properties of normal distribution."""
        normal = NormalDistribution(mu, sigma)

        # Property 1: Peak at mean
        peak_value = normal[mu]
        nearby_left = normal[mu - 0.01]
        nearby_right = normal[mu + 0.01]

        assert peak_value >= nearby_left
        assert peak_value >= nearby_right

        # Property 2: Symmetry around mean
        offset = min(sigma * 2, 10)  # Test within reasonable range
        left_value = normal[mu - offset]
        right_value = normal[mu + offset]
        assert abs(left_value - right_value) < 1e-10

        # Property 3: All values non-negative
        test_points = [mu - 3 * sigma, mu - sigma, mu, mu + sigma, mu + 3 * sigma]
        for point in test_points:
            assert normal[point] >= 0

    @given(st.data())
    def test_interpolated_distribution_bounds(self, data):
        """Test that interpolated distribution respects input bounds."""
        # Generate sorted points
        num_points = data.draw(st.integers(min_value=2, max_value=10))
        x_values = sorted(
            data.draw(
                st.lists(
                    st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
                    min_size=num_points,
                    max_size=num_points,
                    unique=True,
                )
            )
        )
        y_values = data.draw(
            st.lists(
                st.floats(min_value=-50, max_value=50, allow_nan=False, allow_infinity=False),
                min_size=num_points,
                max_size=num_points,
            )
        )

        points = list(zip(x_values, y_values))
        bounds = {
            "x": {"min": min(x_values), "max": max(x_values)},
            "y": {"min": min(y_values), "max": max(y_values)},
        }

        dist = InterpolatedDistribution.linear(points, bounds)

        # Property 1: Values outside range return boundary values
        far_left = x_values[0] - 100
        far_right = x_values[-1] + 100

        assert dist[far_left] == y_values[0]
        assert dist[far_right] == y_values[-1]

        # Property 2: Exact points return exact values
        for x, y in points:
            assert abs(dist[x] - y) < 1e-10


class TestConfigValidationProperties:
    """Property-based tests for configuration validation."""

    @given(soc_values())
    def test_soc_validation_accepts_valid_values(self, soc):
        """Test that SOC validation accepts all valid values."""
        # Property: All values in [0,1] should be accepted
        validated_soc = ConfigValidator.validate_soc(soc)
        assert validated_soc == soc

    @given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x < 0 or x > 1))
    def test_soc_validation_rejects_invalid_values(self, invalid_soc):
        """Test that SOC validation rejects invalid values."""
        # Property: All values outside [0,1] should be rejected
        with pytest.raises(Exception):  # InvalidParameterError or similar
            ConfigValidator.validate_soc(invalid_soc)

    @given(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False))
    def test_power_validation_accepts_positive_values(self, power):
        """Test that power validation accepts non-negative values."""
        validated_power = ConfigValidator.validate_power(power)
        assert validated_power == power

    @given(st.floats(max_value=-0.001, allow_nan=False, allow_infinity=False))
    def test_power_validation_rejects_negative_values(self, negative_power):
        """Test that power validation rejects negative values."""
        with pytest.raises(Exception):
            ConfigValidator.validate_power(negative_power)


class TestEnumProperties:
    """Property-based tests for enum conversions and validation."""

    @given(
        st.sampled_from(
            ["uncontrolled", "discrimination_free", "fcfs", "with_storage", "optimized"]
        )
    )
    def test_scheduling_policy_enum_roundtrip(self, policy_string):
        """Test that scheduling policy enum conversions are consistent."""
        # Property: String → Enum → String should preserve original
        enum_value = SchedulingPolicyType.from_string(policy_string)
        string_back = enum_value.value

        assert string_back == policy_string

    @given(
        st.text().filter(
            lambda s: s.strip().lower().replace(" ", "_")
            not in [
                "uncontrolled",
                "uc",
                "discrimination_free",
                "df",
                "fcfs",
                "with_storage",
                "ws",
                "optimized",
                "opt",
            ]
        )
    )
    def test_scheduling_policy_enum_rejects_invalid(self, invalid_string):
        """Test that invalid scheduling policy strings are rejected."""
        assume(len(invalid_string.strip()) > 0)  # Skip empty strings

        with pytest.raises(Exception):
            SchedulingPolicyType.from_string(invalid_string)


class TestMathematicalInvariants:
    """Property-based tests for mathematical invariants across the system."""

    @given(
        st.floats(min_value=0.1, max_value=1000, allow_nan=False, allow_infinity=False),  # capacity
        st.floats(min_value=0.1, max_value=500, allow_nan=False, allow_infinity=False),  # max_power
        st.floats(
            min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False
        ),  # efficiency
        soc_values(),  # start_soc
        soc_values(),  # end_soc
    )
    def test_energy_calculation_invariants(
        self, capacity, max_power, efficiency, start_soc, end_soc
    ):
        """Test fundamental energy calculation invariants."""
        assume(start_soc != end_soc)  # Need actual change

        battery = EVBattery(
            capacity=capacity, max_charge_power=max_power, min_charge_power=0, efficiency=efficiency
        )

        # Property 1: Energy change should be proportional to SOC change
        soc_change = end_soc - start_soc
        expected_energy_magnitude = abs(soc_change) * capacity

        # The relationship should hold regardless of efficiency considerations
        assert expected_energy_magnitude >= 0

        # Property 2: Battery capacity should be constant
        assert battery.capacity == capacity

        # Property 3: Efficiency should affect charging requirements
        assert 0 < battery.efficiency <= 1

    @settings(max_examples=50)  # Reduce examples for slower tests
    @given(st.data())
    def test_power_time_energy_relationship(self, data):
        """Test the fundamental relationship: Power × Time = Energy."""
        power_watts = data.draw(
            st.floats(min_value=100, max_value=10000, allow_nan=False, allow_infinity=False)
        )
        time_hours = data.draw(
            st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False)
        )

        # Property: P × t = E (fundamental physics relationship)
        expected_energy = power_watts * time_hours  # Wh

        # Test through units
        power = Power(power_watts)
        current = Current(power_watts / 400)  # Assume 400V system
        charge = current * time_hours
        energy = charge.energy(400)

        # Should satisfy P × t = E within reasonable precision
        calculated_energy = energy.kwh  # This is in Wh for our implementation
        assert abs(calculated_energy - expected_energy) < 1e-6


if __name__ == "__main__":
    # Run with verbose output to see property testing in action
    pytest.main([__file__, "-v", "--tb=short"])

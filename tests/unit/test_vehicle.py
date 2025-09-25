"""Comprehensive unit tests for vehicle.py module.

Test coverage for ElectricVehicle class including:
- Initialization and validation
- Dictionary conversion methods
- String representation
- Integration with EVBattery
"""

import pytest
from unittest.mock import Mock, patch

from elvis.vehicle import ElectricVehicle
from elvis.battery import EVBattery
from elvis.types import Probability


class TestElectricVehicle:
    """Test cases for the ElectricVehicle class."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        # Create a mock EVBattery for testing
        self.mock_battery = Mock(spec=EVBattery)
        self.mock_battery.capacity = 50.0
        self.mock_battery.max_charge_power = 150.0
        self.mock_battery.min_charge_power = 0.0
        self.mock_battery.efficiency = 0.95

    def test_electric_vehicle_initialization_valid(self):
        """Test successful ElectricVehicle initialization with valid parameters."""
        vehicle = ElectricVehicle(
            brand="Tesla", model="Model 3", battery=self.mock_battery, probability=0.15
        )

        assert vehicle.brand == "Tesla"
        assert vehicle.model == "Model 3"
        assert vehicle.battery == self.mock_battery
        assert vehicle.probability == 0.15

    def test_electric_vehicle_initialization_invalid_battery(self):
        """Test ElectricVehicle initialization fails with invalid battery."""
        # Mock not being EVBattery type
        invalid_battery = Mock()

        with pytest.raises(AssertionError):
            ElectricVehicle(
                brand="Tesla",
                model="Model 3",
                battery=invalid_battery,  # Not EVBattery type
                probability=0.15,
            )

    def test_electric_vehicle_initialization_invalid_probability(self):
        """Test ElectricVehicle initialization with invalid probability types."""
        # Test with non-numeric probability
        with pytest.raises(AssertionError):
            ElectricVehicle(
                brand="Tesla",
                model="Model 3",
                battery=self.mock_battery,
                probability="invalid",  # Not numeric
            )

    @pytest.mark.parametrize(
        "probability",
        [
            0.0,
            0.1,
            0.5,
            0.99,
            1.0,  # Valid probability range
        ],
    )
    def test_electric_vehicle_valid_probabilities(self, probability):
        """Test ElectricVehicle accepts valid probability values."""
        vehicle = ElectricVehicle(
            brand="VW", model="ID.3", battery=self.mock_battery, probability=probability
        )
        assert vehicle.probability == probability

    def test_electric_vehicle_string_representation(self):
        """Test ElectricVehicle string representation."""
        vehicle = ElectricVehicle(
            brand="BMW", model="i3", battery=self.mock_battery, probability=0.2
        )

        str_repr = str(vehicle)
        assert "BMW" in str_repr
        assert "i3" in str_repr

    def test_electric_vehicle_to_dict(self):
        """Test ElectricVehicle conversion to dictionary."""
        # Create a real EVBattery for this test
        real_battery = EVBattery(
            capacity=75.0, max_charge_power=200.0, min_charge_power=0.0, efficiency=0.9
        )

        vehicle = ElectricVehicle(
            brand="Audi", model="e-tron", battery=real_battery, probability=0.25
        )

        vehicle_dict = vehicle.to_dict()

        # Check main vehicle properties
        assert vehicle_dict["brand"] == "Audi"
        assert vehicle_dict["model"] == "e-tron"
        assert vehicle_dict["probability"] == 0.25

        # Check battery dictionary is included
        assert "battery" in vehicle_dict
        battery_dict = vehicle_dict["battery"]
        assert battery_dict["capacity"] == 75.0
        assert battery_dict["max_charge_power"] == 200.0
        assert battery_dict["min_charge_power"] == 0.0
        assert battery_dict["efficiency"] == 0.9

    def test_electric_vehicle_from_dict_valid(self):
        """Test ElectricVehicle creation from dictionary."""
        vehicle = ElectricVehicle.from_dict(
            brand="Nissan",
            model="Leaf",
            probability=0.18,
            battery={
                "capacity": 40.0,
                "max_charge_power": 100.0,
                "min_charge_power": 0.0,
                "efficiency": 0.92,
            },
        )

        assert vehicle.brand == "Nissan"
        assert vehicle.model == "Leaf"
        assert vehicle.probability == 0.18

        # Check battery properties
        assert vehicle.battery.capacity == 40.0
        assert vehicle.battery.max_charge_power == 100.0
        assert vehicle.battery.min_charge_power == 0.0
        assert vehicle.battery.efficiency == 0.92

    def test_electric_vehicle_from_dict_missing_required_fields(self):
        """Test ElectricVehicle creation fails with missing required fields."""
        # Missing brand
        with pytest.raises(AssertionError, match="Not all necessary keys"):
            ElectricVehicle.from_dict(
                model="Leaf",
                probability=0.18,
                battery={
                    "capacity": 40.0,
                    "max_charge_power": 100.0,
                    "min_charge_power": 0.0,
                    "efficiency": 0.92,
                },
            )

    def test_electric_vehicle_from_dict_missing_battery(self):
        """Test ElectricVehicle creation fails with missing battery."""
        with pytest.raises(AssertionError, match="Not all necessary keys"):
            ElectricVehicle.from_dict(
                brand="Nissan",
                model="Leaf",
                probability=0.18,
                # Missing battery
            )

    def test_electric_vehicle_from_dict_invalid_battery(self):
        """Test ElectricVehicle creation fails with invalid battery configuration."""
        with pytest.raises(AssertionError):
            ElectricVehicle.from_dict(
                brand="Nissan",
                model="Leaf",
                probability=0.18,
                battery={
                    "capacity": -40.0,  # Invalid: negative capacity
                    "max_charge_power": 100.0,
                    "min_charge_power": 0.0,
                    "efficiency": 0.92,
                },
            )

    @pytest.mark.parametrize(
        "brand,model,probability",
        [
            ("Tesla", "Model S", 0.1),
            ("VW", "ID.4", 0.3),
            ("Hyundai", "Ioniq 5", 0.05),
            ("Ford", "Mustang Mach-E", 0.08),
            ("Mercedes", "EQS", 0.02),
        ],
    )
    def test_electric_vehicle_parametrized_creation(self, brand, model, probability):
        """Test ElectricVehicle creation with various brand/model combinations."""
        vehicle = ElectricVehicle(
            brand=brand, model=model, battery=self.mock_battery, probability=probability
        )

        assert vehicle.brand == brand
        assert vehicle.model == model
        assert vehicle.probability == probability
        assert vehicle.battery == self.mock_battery

    def test_electric_vehicle_roundtrip_dict_conversion(self):
        """Test that to_dict() and from_dict() are inverse operations."""
        # Create original vehicle
        original_battery = EVBattery(
            capacity=65.0, max_charge_power=180.0, min_charge_power=2.0, efficiency=0.88
        )

        original_vehicle = ElectricVehicle(
            brand="Polestar", model="2", battery=original_battery, probability=0.12
        )

        # Convert to dict and back
        vehicle_dict = original_vehicle.to_dict()
        reconstructed_vehicle = ElectricVehicle.from_dict(**vehicle_dict)

        # Verify all properties match
        assert reconstructed_vehicle.brand == original_vehicle.brand
        assert reconstructed_vehicle.model == original_vehicle.model
        assert reconstructed_vehicle.probability == original_vehicle.probability

        # Verify battery properties match
        assert reconstructed_vehicle.battery.capacity == original_battery.capacity
        assert reconstructed_vehicle.battery.max_charge_power == original_battery.max_charge_power
        assert reconstructed_vehicle.battery.min_charge_power == original_battery.min_charge_power
        assert reconstructed_vehicle.battery.efficiency == original_battery.efficiency

    def test_electric_vehicle_object_identity(self):
        """Test ElectricVehicle object identity behavior."""
        battery1 = EVBattery(
            capacity=50.0, max_charge_power=150.0, min_charge_power=0.0, efficiency=0.95
        )
        battery2 = EVBattery(
            capacity=50.0, max_charge_power=150.0, min_charge_power=0.0, efficiency=0.95
        )

        vehicle1 = ElectricVehicle("Tesla", "Model 3", battery1, 0.15)
        vehicle2 = ElectricVehicle("Tesla", "Model 3", battery2, 0.15)

        # Test that different instances are not identical
        assert vehicle1 is not vehicle2
        assert vehicle1.brand == vehicle2.brand
        assert vehicle1.model == vehicle2.model

    def test_electric_vehicle_immutability_concept(self):
        """Test that vehicle properties can be accessed but modification behavior."""
        vehicle = ElectricVehicle(
            brand="Lucid", model="Air", battery=self.mock_battery, probability=0.03
        )

        # Test property access
        assert vehicle.brand == "Lucid"
        assert vehicle.model == "Air"
        assert vehicle.battery == self.mock_battery
        assert vehicle.probability == 0.03

        # Test that properties can be modified (if designed that way)
        # or are protected (if designed that way)
        original_brand = vehicle.brand
        vehicle.brand = "Modified Brand"

        # This test documents current behavior - adjust based on design intent
        if hasattr(ElectricVehicle, "_brand"):
            # If using property with private attribute
            assert vehicle.brand == original_brand  # Protected
        else:
            # If using public attributes
            assert vehicle.brand == "Modified Brand"  # Modifiable

    def test_electric_vehicle_with_edge_case_strings(self):
        """Test ElectricVehicle with edge case string values."""
        edge_cases = [
            ("", "Model", 0.1),  # Empty brand
            ("Brand", "", 0.1),  # Empty model
            ("Brand With Spaces", "Model-With-Dashes", 0.1),  # Special characters
            ("🚗", "⚡", 0.1),  # Unicode characters
        ]

        for brand, model, probability in edge_cases:
            vehicle = ElectricVehicle(
                brand=brand, model=model, battery=self.mock_battery, probability=probability
            )

            assert vehicle.brand == brand
            assert vehicle.model == model
            assert vehicle.probability == probability

    def test_electric_vehicle_battery_integration(self):
        """Test ElectricVehicle integration with EVBattery methods."""
        # Create real battery for integration testing
        real_battery = EVBattery(
            capacity=80.0, max_charge_power=250.0, min_charge_power=1.0, efficiency=0.93
        )

        vehicle = ElectricVehicle(
            brand="Genesis", model="Electrified GV70", battery=real_battery, probability=0.06
        )

        # Test that vehicle's battery methods work
        max_power = vehicle.battery.max_power_possible(0.5)
        assert max_power == 250.0  # Should return max power at mid SOC

        min_power = vehicle.battery.min_power_possible(0.5)
        assert min_power == 1.0  # Should return min power

        # Test battery dictionary conversion
        battery_dict = vehicle.battery.to_dict()
        assert battery_dict["capacity"] == 80.0

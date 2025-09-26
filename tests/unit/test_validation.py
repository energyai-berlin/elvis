"""Tests for the validation framework."""

import pytest

from elvis.config.validation import ConfigValidator, ValidationResult
from elvis.enums import SchedulingPolicyType, SampleMethod
from elvis.exceptions import InvalidParameterError


class TestConfigValidator:
    """Test the ConfigValidator functionality."""

    def test_validate_soc_valid(self):
        """Test valid SOC values are accepted."""
        assert ConfigValidator.validate_soc(0.0) == 0.0
        assert ConfigValidator.validate_soc(0.5) == 0.5
        assert ConfigValidator.validate_soc(1.0) == 1.0

    def test_validate_soc_invalid(self):
        """Test invalid SOC values are rejected."""
        with pytest.raises(InvalidParameterError):
            ConfigValidator.validate_soc(-0.1)

        with pytest.raises(InvalidParameterError):
            ConfigValidator.validate_soc(1.1)

        with pytest.raises(InvalidParameterError):
            ConfigValidator.validate_soc("0.5")  # Wrong type

    def test_validate_power_valid(self):
        """Test valid power values are accepted."""
        assert ConfigValidator.validate_power(0.0) == 0.0
        assert ConfigValidator.validate_power(22.0) == 22.0
        assert ConfigValidator.validate_power(100.5) == 100.5

    def test_validate_power_invalid(self):
        """Test invalid power values are rejected."""
        with pytest.raises(InvalidParameterError):
            ConfigValidator.validate_power(-1.0)

        with pytest.raises(InvalidParameterError):
            ConfigValidator.validate_power("22.0")  # Wrong type

    def test_validate_scheduling_policy_string_valid(self):
        """Test valid scheduling policy strings are converted to enums."""
        assert (
            ConfigValidator.validate_scheduling_policy_string("UC")
            == SchedulingPolicyType.UNCONTROLLED
        )
        assert (
            ConfigValidator.validate_scheduling_policy_string("uncontrolled")
            == SchedulingPolicyType.UNCONTROLLED
        )
        assert (
            ConfigValidator.validate_scheduling_policy_string("FCFS") == SchedulingPolicyType.FCFS
        )
        assert (
            ConfigValidator.validate_scheduling_policy_string("df")
            == SchedulingPolicyType.DISCRIMINATION_FREE
        )

    def test_validate_scheduling_policy_string_invalid(self):
        """Test invalid scheduling policy strings are rejected."""
        with pytest.raises(InvalidParameterError):
            ConfigValidator.validate_scheduling_policy_string("INVALID")

        with pytest.raises(InvalidParameterError):
            ConfigValidator.validate_scheduling_policy_string(123)  # Wrong type

    def test_validate_arrival_distribution_valid(self):
        """Test valid arrival distributions are accepted."""
        valid_dist = [0.0] * 168 + [1.0]  # One peak
        result = ConfigValidator.validate_arrival_distribution(valid_dist)
        assert result == valid_dist

    def test_validate_arrival_distribution_invalid(self):
        """Test invalid arrival distributions are rejected."""
        # Not a list
        with pytest.raises(InvalidParameterError):
            ConfigValidator.validate_arrival_distribution("not a list")

        # Empty list
        with pytest.raises(InvalidParameterError):
            ConfigValidator.validate_arrival_distribution([])

        # Invalid probability value
        with pytest.raises(InvalidParameterError):
            ConfigValidator.validate_arrival_distribution([0.5, 1.5])  # 1.5 > 1


class TestValidationResult:
    """Test the ValidationResult functionality."""

    def test_validation_result_valid(self):
        """Test validation result for valid configuration."""
        result = ValidationResult()
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert "No validation errors" in result.get_error_summary()

    def test_validation_result_with_errors(self):
        """Test validation result with errors."""
        result = ValidationResult()
        error = InvalidParameterError("test_param", "invalid_value", "test reason")
        result.add_error(error)

        assert not result.is_valid
        assert len(result.errors) == 1
        assert "Validation errors (1)" in result.get_error_summary()

    def test_validation_result_with_warnings(self):
        """Test validation result with warnings."""
        result = ValidationResult()
        result.add_warning("Test warning message")

        assert result.is_valid  # Warnings don't make config invalid
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning message"


class TestEnumIntegration:
    """Test enum integration with validation."""

    def test_scheduling_policy_enum_from_string(self):
        """Test SchedulingPolicyType.from_string method."""
        assert SchedulingPolicyType.from_string("UC") == SchedulingPolicyType.UNCONTROLLED
        assert SchedulingPolicyType.from_string("uncontrolled") == SchedulingPolicyType.UNCONTROLLED
        assert SchedulingPolicyType.from_string("FCFS") == SchedulingPolicyType.FCFS
        assert SchedulingPolicyType.from_string("df") == SchedulingPolicyType.DISCRIMINATION_FREE

    def test_scheduling_policy_enum_invalid_string(self):
        """Test SchedulingPolicyType.from_string with invalid input."""
        with pytest.raises(ValueError):
            SchedulingPolicyType.from_string("INVALID_POLICY")

    def test_sample_method_enum_from_string(self):
        """Test SampleMethod.from_string method."""
        assert (
            SampleMethod.from_string("independent_normal_dist")
            == SampleMethod.INDEPENDENT_NORMAL_DIST
        )
        assert SampleMethod.from_string("gmm") == SampleMethod.GMM

    def test_sample_method_enum_invalid_string(self):
        """Test SampleMethod.from_string with invalid input."""
        with pytest.raises(ValueError):
            SampleMethod.from_string("INVALID_METHOD")

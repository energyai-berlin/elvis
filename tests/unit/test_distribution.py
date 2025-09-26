"""Comprehensive unit tests for distribution.py module.

Test coverage for distribution classes including:
- NormalDistribution
- InterpolatedDistribution
- EquallySpacedInterpolatedDistribution
- Linear interpolation methods
- Boundary handling and edge cases
"""

import pytest
import math
from unittest.mock import Mock

from elvis.distribution import (
    Distribution,
    NormalDistribution,
    InterpolatedDistribution,
    EquallySpacedInterpolatedDistribution,
)


class TestDistribution:
    """Test cases for the base Distribution class."""

    def test_distribution_abstract_methods(self):
        """Test abstract methods raise NotImplementedError."""
        dist = Distribution()

        with pytest.raises(NotImplementedError):
            dist[0]  # __getitem__

        with pytest.raises(NotImplementedError):
            _ = dist.bounds

    def test_distribution_property_methods_error(self):
        """Test property methods fail when bounds not implemented."""
        dist = Distribution()

        # These will fail because bounds is not implemented,
        # but the actual error comes from using undefined 'bounds' variable
        with pytest.raises(NameError):  # bounds variable not defined
            _ = dist.min_x

        with pytest.raises(NameError):
            _ = dist.max_x


class TestNormalDistribution:
    """Test cases for the NormalDistribution class."""

    def test_normal_distribution_initialization(self):
        """Test NormalDistribution initialization."""
        mu, sigma = 0.0, 1.0
        normal = NormalDistribution(mu, sigma)

        assert normal.mu == mu
        assert normal.sigma == sigma
        assert normal.fac == 1.0 / (sigma * math.sqrt(2.0 * math.pi))

    def test_normal_distribution_standard_normal(self):
        """Test standard normal distribution (mu=0, sigma=1)."""
        normal = NormalDistribution(0.0, 1.0)

        # Test peak at mean (x=0)
        peak_value = normal[0.0]
        expected_peak = 1.0 / math.sqrt(2.0 * math.pi)
        assert abs(peak_value - expected_peak) < 1e-10

        # Test symmetry around mean
        assert abs(normal[-1.0] - normal[1.0]) < 1e-10
        assert abs(normal[-2.0] - normal[2.0]) < 1e-10

    def test_normal_distribution_custom_parameters(self):
        """Test normal distribution with custom mu and sigma."""
        mu, sigma = 5.0, 2.0
        normal = NormalDistribution(mu, sigma)

        # Test peak at mean (x=mu)
        peak_value = normal[mu]
        expected_peak = 1.0 / (sigma * math.sqrt(2.0 * math.pi))
        assert abs(peak_value - expected_peak) < 1e-10

        # Test symmetry around mean
        assert abs(normal[mu - 1] - normal[mu + 1]) < 1e-10

    def test_normal_distribution_bounds(self):
        """Test normal distribution bounds property."""
        normal = NormalDistribution(0.0, 1.0)
        bounds = normal.bounds

        assert bounds["x"]["min"] == -math.inf
        assert bounds["x"]["max"] == math.inf
        assert bounds["y"]["min"] == 0
        assert bounds["y"]["max"] == 1

    def test_normal_distribution_probability_properties(self):
        """Test normal distribution maintains probability properties."""
        normal = NormalDistribution(0.0, 1.0)

        # All values should be non-negative
        test_points = [-5, -2, -1, 0, 1, 2, 5]
        for x in test_points:
            assert normal[x] >= 0

        # Values should decrease as we move away from mean
        assert normal[0] > normal[1]
        assert normal[0] > normal[-1]
        assert normal[1] > normal[2]
        assert normal[-1] > normal[-2]

    @pytest.mark.parametrize(
        "mu,sigma", [(0.0, 1.0), (1.0, 1.0), (0.0, 2.0), (5.0, 0.5), (-2.0, 3.0)]
    )
    def test_normal_distribution_parametrized(self, mu, sigma):
        """Test normal distribution with various parameter combinations."""
        normal = NormalDistribution(mu, sigma)

        # Test peak is at mu
        peak_value = normal[mu]
        nearby_values = [normal[mu - 0.01], normal[mu + 0.01]]
        assert all(peak_value >= val for val in nearby_values)

        # Test factor calculation
        expected_fac = 1.0 / (sigma * math.sqrt(2.0 * math.pi))
        assert abs(normal.fac - expected_fac) < 1e-10


class TestInterpolatedDistribution:
    """Test cases for the InterpolatedDistribution class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.points = [(0.0, 1.0), (1.0, 3.0), (2.0, 2.0), (3.0, 4.0)]
        self.bounds = {"x": {"min": 0.0, "max": 3.0}, "y": {"min": 1.0, "max": 4.0}}

    def test_interpolated_distribution_initialization(self):
        """Test InterpolatedDistribution initialization."""
        mock_interpolate = Mock()
        dist = InterpolatedDistribution(self.points, self.bounds, mock_interpolate)

        assert dist.points == self.points
        assert dist._bounds == self.bounds
        assert dist.interpolate == mock_interpolate

    def test_interpolated_distribution_linear_constructor(self):
        """Test linear interpolation constructor."""
        dist = InterpolatedDistribution.linear(self.points, self.bounds)

        assert dist.points == self.points
        assert dist._bounds == self.bounds
        assert dist.interpolate == InterpolatedDistribution._linear_interpolation

    def test_linear_interpolation_method(self):
        """Test linear interpolation static method."""
        # Test basic linear interpolation
        result = InterpolatedDistribution._linear_interpolation(1.0, 3.0, 0.5)
        assert result == 2.0  # Midpoint between 1 and 3

        # Test edge cases
        assert InterpolatedDistribution._linear_interpolation(1.0, 3.0, 0.0) == 1.0
        assert InterpolatedDistribution._linear_interpolation(1.0, 3.0, 1.0) == 3.0

        # Test extrapolation
        assert InterpolatedDistribution._linear_interpolation(1.0, 3.0, 1.5) == 4.0

    def test_interpolated_distribution_bounds_access(self):
        """Test bounds property access."""
        dist = InterpolatedDistribution.linear(self.points, self.bounds)
        assert dist.bounds == self.bounds

    def test_interpolated_distribution_below_range(self):
        """Test interpolation below range returns first point value."""
        dist = InterpolatedDistribution.linear(self.points, self.bounds)
        result = dist[-1.0]  # Below minimum x (0.0)
        assert result == 1.0  # Should return first y value

    def test_interpolated_distribution_above_range(self):
        """Test interpolation above range returns last point value."""
        dist = InterpolatedDistribution.linear(self.points, self.bounds)
        result = dist[5.0]  # Above maximum x (3.0)
        assert result == 4.0  # Should return last y value

    def test_interpolated_distribution_exact_points(self):
        """Test interpolation at exact data points."""
        dist = InterpolatedDistribution.linear(self.points, self.bounds)

        for x, expected_y in self.points:
            result = dist[x]
            assert abs(result - expected_y) < 1e-10

    def test_interpolated_distribution_midpoints(self):
        """Test linear interpolation at midpoints."""
        dist = InterpolatedDistribution.linear(self.points, self.bounds)

        # Midpoint between (0,1) and (1,3) should be (0.5, 2)
        result = dist[0.5]
        assert abs(result - 2.0) < 1e-10

        # Midpoint between (1,3) and (2,2) should be (1.5, 2.5)
        result = dist[1.5]
        assert abs(result - 2.5) < 1e-10

    def test_interpolated_distribution_edge_interpolation(self):
        """Test interpolation at various offsets within segments."""
        dist = InterpolatedDistribution.linear(self.points, self.bounds)

        # Quarter point between (0,1) and (1,3)
        result = dist[0.25]
        expected = 1.0 + (3.0 - 1.0) * 0.25  # 1.5
        assert abs(result - expected) < 1e-10

        # Three-quarter point between (1,3) and (2,2)
        result = dist[1.75]
        expected = 3.0 + (2.0 - 3.0) * 0.75  # 2.25
        assert abs(result - expected) < 1e-10


class TestEquallySpacedInterpolatedDistribution:
    """Test cases for the EquallySpacedInterpolatedDistribution class."""

    def setup_method(self):
        """Set up test fixtures with equally spaced points."""
        self.points = [(0.0, 1.0), (1.0, 3.0), (2.0, 2.0), (3.0, 4.0)]  # Spacing = 1.0
        self.bounds = {"x": {"min": 0.0, "max": 3.0}, "y": {"min": 1.0, "max": 4.0}}

    def test_equally_spaced_distribution_initialization(self):
        """Test EquallySpacedInterpolatedDistribution initialization."""
        mock_interpolate = Mock()
        dist = EquallySpacedInterpolatedDistribution(self.points, self.bounds, mock_interpolate)

        assert dist.points == self.points
        assert dist._bounds == self.bounds
        assert dist.interpolate == mock_interpolate
        assert dist.distance_between_points == 1.0

    def test_equally_spaced_distribution_linear_constructor(self):
        """Test linear interpolation constructor."""
        dist = EquallySpacedInterpolatedDistribution.linear(self.points, self.bounds)

        assert dist.points == self.points
        assert dist._bounds == self.bounds
        assert dist.interpolate == InterpolatedDistribution._linear_interpolation
        assert dist.distance_between_points == 1.0

    def test_equally_spaced_distance_calculation(self):
        """Test distance between points calculation."""
        # Test with different spacing
        points_half = [(0.0, 1.0), (0.5, 2.0), (1.0, 3.0)]
        dist_half = EquallySpacedInterpolatedDistribution.linear(points_half, self.bounds)
        assert dist_half.distance_between_points == 0.5

        # Test with negative spacing (decreasing x values)
        points_neg = [(3.0, 1.0), (2.0, 2.0), (1.0, 3.0)]
        dist_neg = EquallySpacedInterpolatedDistribution.linear(points_neg, self.bounds)
        assert dist_neg.distance_between_points == 1.0  # abs() of -1.0

    def test_equally_spaced_bounds_access(self):
        """Test bounds property access."""
        dist = EquallySpacedInterpolatedDistribution.linear(self.points, self.bounds)
        assert dist.bounds == self.bounds

    def test_equally_spaced_below_range(self):
        """Test interpolation below range returns first point value."""
        dist = EquallySpacedInterpolatedDistribution.linear(self.points, self.bounds)
        result = dist[-1.0]  # Below minimum x (0.0)
        assert result == 1.0  # Should return first y value

    def test_equally_spaced_above_range(self):
        """Test interpolation above range returns last point value."""
        dist = EquallySpacedInterpolatedDistribution.linear(self.points, self.bounds)
        result = dist[5.0]  # Above maximum x (3.0)
        assert result == 4.0  # Should return last y value

    def test_equally_spaced_exact_points(self):
        """Test interpolation at exact data points."""
        dist = EquallySpacedInterpolatedDistribution.linear(self.points, self.bounds)

        for x, expected_y in self.points:
            result = dist[x]
            assert abs(result - expected_y) < 1e-10

    def test_equally_spaced_midpoints(self):
        """Test linear interpolation at midpoints."""
        dist = EquallySpacedInterpolatedDistribution.linear(self.points, self.bounds)

        # Midpoint between (0,1) and (1,3) should be (0.5, 2)
        result = dist[0.5]
        assert abs(result - 2.0) < 1e-10

        # Midpoint between (1,3) and (2,2) should be (1.5, 2.5)
        result = dist[1.5]
        assert abs(result - 2.5) < 1e-10

    def test_equally_spaced_optimized_index_calculation(self):
        """Test that equally spaced version efficiently calculates indices."""
        dist = EquallySpacedInterpolatedDistribution.linear(self.points, self.bounds)

        # Test various points and verify they produce correct results
        test_cases = [
            (0.25, 1.5),  # In first segment
            (0.75, 2.5),  # In first segment
            (1.25, 2.75),  # In second segment
            (2.25, 2.5),  # In third segment
        ]

        for x, expected_y in test_cases:
            result = dist[x]
            assert abs(result - expected_y) < 1e-10

    def test_equally_spaced_with_fractional_spacing(self):
        """Test equally spaced distribution with fractional spacing."""
        points_frac = [(0.0, 1.0), (0.25, 2.0), (0.5, 3.0), (0.75, 1.5)]
        dist = EquallySpacedInterpolatedDistribution.linear(points_frac, self.bounds)

        assert dist.distance_between_points == 0.25

        # Test interpolation
        result = dist[0.125]  # Midpoint of first segment
        expected = 1.0 + (2.0 - 1.0) * 0.5  # 1.5
        assert abs(result - expected) < 1e-10

    @pytest.mark.parametrize("spacing,num_points", [(1.0, 5), (0.5, 9), (2.0, 3), (0.1, 11)])
    def test_equally_spaced_parametrized_spacing(self, spacing, num_points):
        """Test equally spaced distribution with various spacings."""
        # Generate equally spaced points
        points = [(i * spacing, i + 1) for i in range(num_points)]
        bounds = {
            "x": {"min": 0, "max": (num_points - 1) * spacing},
            "y": {"min": 1, "max": num_points},
        }

        dist = EquallySpacedInterpolatedDistribution.linear(points, bounds)

        assert abs(dist.distance_between_points - spacing) < 1e-10

        # Test that exact points work
        for x, expected_y in points:
            result = dist[x]
            assert abs(result - expected_y) < 1e-10


class TestDistributionIntegration:
    """Integration tests comparing different distribution implementations."""

    def test_interpolated_vs_equally_spaced_same_results(self):
        """Test that both interpolation methods give same results for equally spaced data."""
        points = [(0.0, 1.0), (1.0, 3.0), (2.0, 2.0), (3.0, 4.0)]
        bounds = {"x": {"min": 0.0, "max": 3.0}, "y": {"min": 1.0, "max": 4.0}}

        regular_dist = InterpolatedDistribution.linear(points, bounds)
        equally_spaced_dist = EquallySpacedInterpolatedDistribution.linear(points, bounds)

        # Test same results at various points
        test_points = [0.0, 0.3, 0.7, 1.0, 1.2, 1.8, 2.0, 2.5, 3.0]
        for x in test_points:
            regular_result = regular_dist[x]
            equally_spaced_result = equally_spaced_dist[x]
            assert abs(regular_result - equally_spaced_result) < 1e-10

    def test_distribution_inheritance_hierarchy(self):
        """Test that all distribution classes properly inherit from Distribution."""
        normal = NormalDistribution(0, 1)
        interpolated = InterpolatedDistribution.linear([(0, 1), (1, 2)], {})
        equally_spaced = EquallySpacedInterpolatedDistribution.linear([(0, 1), (1, 2)], {})

        assert isinstance(normal, Distribution)
        assert isinstance(interpolated, Distribution)
        assert isinstance(equally_spaced, Distribution)

    def test_distribution_edge_cases(self):
        """Test distribution behavior with edge case inputs."""
        # Single point interpolation
        single_point = [(1.0, 2.0)]
        bounds = {"x": {"min": 1.0, "max": 1.0}, "y": {"min": 2.0, "max": 2.0}}

        dist = InterpolatedDistribution.linear(single_point, bounds)

        # Should return same value for any input
        assert dist[0.0] == 2.0
        assert dist[1.0] == 2.0
        assert dist[2.0] == 2.0

    def test_distribution_with_zero_y_values(self):
        """Test distributions can handle zero y values."""
        points = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]
        bounds = {"x": {"min": 0.0, "max": 2.0}, "y": {"min": 0.0, "max": 1.0}}

        dist = InterpolatedDistribution.linear(points, bounds)

        assert dist[0.0] == 0.0
        assert dist[0.5] == 0.5
        assert dist[1.0] == 1.0
        assert dist[1.5] == 0.5
        assert dist[2.0] == 0.0

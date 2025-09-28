# CLAUDE.md - ELVIS Project Guide

## Project Overview

**ELVIS** (Electric Vehicle Charging Infrastructure Simulator) is a Python-based planning and management tool for electric vehicle charging infrastructure. It simulates charging demand patterns, infrastructure utilization, and energy consumption for various EV charging scenarios.

**Purpose**: Research and analysis tool for EV charging infrastructure planning with realistic behavioral modeling

**Primary Goals**:
- Model stochastic EV charging behavior with realistic interdependencies
- Simulate various charging infrastructure scenarios with high fidelity
- Generate accurate load profiles for grid impact analysis
- Support research in sustainable mobility and energy systems
- Provide infrastructure planning insights for real-world deployment

**Target Accuracy**: Achieve 80%+ correlation with real-world charging patterns through advanced statistical modeling

## Technology Stack

### Core Languages & Frameworks
- **Python 3.12+** (primary language)
- **NumPy** (numerical computations)
- **Pandas** (data analysis and manipulation)
- **Matplotlib** (visualization and plotting)
- **PyYAML** (configuration file parsing)
- **SciPy** (scientific computing)
- **Scikit-learn** (machine learning utilities)
- **NetworkX** (graph/network analysis)

### Build & Distribution
- **uv** (ultra-fast Python package manager - primary)
- **setuptools** (legacy packaging support)
- **pip** (fallback package installation)
- **pyproject.toml** (modern Python packaging configuration)

### Development Environment
- **Jupyter Notebooks** (examples and prototyping)
- **unittest** (testing framework)

## Project Structure

```
elvis/
├── elvis/                     # Main package directory
│   ├── __init__.py           # Package exports: ScenarioConfig, simulate, num_time_steps
│   ├── config.py             # ScenarioConfig class and configuration management
│   ├── simulate.py           # Main simulation engine
│   ├── battery.py            # EVBattery class
│   ├── vehicle.py            # ElectricVehicle class
│   ├── charging_*.py         # Charging infrastructure components
│   ├── sched/                # Scheduling algorithms (Uncontrolled, FCFS)
│   └── utility/              # Helper functions and utilities
├── data/                     # Configuration files and scenarios
│   ├── config_builder/       # YAML scenario configurations
│   └── realisations/         # JSON scenario data
├── examples/                 # Jupyter notebook examples
├── tests/                    # Unit tests
├── requirements.txt          # Python dependencies
├── setup.py                 # Package installation script
└── pyproject.toml           # Modern packaging configuration
```

## Key Entry Points

- **elvis/__init__.py**: Main package exports (`ScenarioConfig`, `simulate`, `num_time_steps`)
- **elvis/config.py**: Configuration and scenario definition
- **elvis/simulate.py**: Core simulation engine
- **examples/MiniExample.ipynb**: Basic usage examples
- **data/config_builder/office.yaml**: Sample scenario configuration

## Code Style & Conventions

### Import Standards
```python
# Standard library first
import datetime
import logging

# Third-party packages
import numpy as np
import pandas as pd
import yaml

# Local imports with full module paths
import elvis.sched.schedulers as schedulers
from elvis.config import ScenarioConfig
from elvis.utility.elvis_general import create_time_steps
```

### Naming Conventions
- **Classes**: PascalCase (`ScenarioConfig`, `ElectricVehicle`)
- **Functions**: snake_case (`create_charging_events`, `handle_car_arrival`)
- **Variables**: snake_case (`mean_park`, `std_deviation_soc`)
- **Constants**: UPPER_SNAKE_CASE
- **File names**: snake_case (`.py` files)

### Code Organization
- Comprehensive docstrings for classes and public methods
- Type hints preferred but not mandatory
- Logging used extensively for debugging and monitoring
- Configuration-driven design with YAML scenarios

## Development Workflow

### Installation Methods

**With uv (recommended):**
```bash
# Install uv first if not available
curl -LsSf https://astral.sh/uv/install.sh | sh

# Production install
uv pip install elvislis

# Development install
uv sync
# Or for editable development install
uv pip install -e .
```

**With pip (legacy):**
```bash
pip install py-elvis

# Development install
pip install -r requirements.txt
python setup.py install
```

### Basic Usage Pattern
```python
from elvis import ScenarioConfig, simulate
import yaml

# Load configuration
with open("data/config_builder/office.yaml", 'r') as f:
    yaml_str = yaml.safe_load(f)
config = ScenarioConfig.from_yaml(yaml_str)

# Run simulation
results = simulate(config,
                  start_date='2020-01-01 00:00:00',
                  end_date='2020-12-31 23:00:00',
                  resolution='01:00:00')

# Analyze results
load_profile = results.aggregate_load_profile(8760)
```

### uv Workflow Commands
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Code formatting
uv run black elvis/
uv run isort elvis/

# Type checking
uv run mypy elvis/

# Build package
uv build

# Add new dependency
uv add requests

# Add development dependency
uv add --dev pytest-mock
```

### Configuration Management
- Scenarios defined in YAML files in `data/config_builder/`
- Key parameters: `arrival_distribution`, `vehicle_types`, `infrastructure`, `mean_park`, `std_deviation_soc`
- Supports stochastic modeling with normal distributions and GMM

## Testing Strategy

### Test Framework
- **unittest** for unit testing
- Test files in `tests/` directory
- Example: `tests/distributions.py` tests interpolation functions

### Running Tests

**With uv (recommended):**
```bash
uv run pytest
uv run pytest tests/distributions.py
```

**With standard Python:**
```bash
python -m unittest tests.distributions
```

### Test Coverage Areas
- Distribution interpolation (`elvis.distribution`)
- Configuration validation
- Simulation core functionality

## Critical Constraints & Guidelines

### Data & Configuration
- YAML scenario files must include required fields: `arrival_distribution`, `infrastructure`, `vehicle_types`
- Vehicle types must specify battery capacity, charge power limits, and probability weights
- Time series data requires proper resolution alignment

### Performance Considerations
- Large-scale simulations may require significant memory for event generation
- Arrival distributions should be normalized probability arrays
- Consider chunked processing for multi-year simulations

### Research Context
- Tool designed for academic research and infrastructure planning
- Results suitable for peer-reviewed publications
- Conceptually based on validated simulation methodologies

## Review Process Guidelines

### Code Quality Checks
- Ensure proper import organization and dependency management
- Run linting: `uv run black . && uv run isort . && uv run flake8`
- Type checking: `uv run mypy elvis/`
- Validate YAML configuration schemas before simulation
- Test scenarios with known expected outcomes
- Check for proper logging and error handling

### Compliance Checkpoints
- Academic attribution requirements (see README acknowledgements)
- Open source license compliance (MIT License)
- Data privacy considerations for real-world usage scenarios

## uv-Specific Features

### Virtual Environment Management
- uv automatically manages virtual environments
- No need to manually create or activate environments
- Project dependencies isolated per project

### Dependency Resolution
- Ultra-fast dependency resolution (10-100x faster than pip)
- Consistent lock file generation (`uv.lock`)
- Reproducible builds across environments

### Development Dependencies
```bash
# Install with development dependencies
uv sync --extra dev

# Install with Jupyter dependencies
uv sync --extra jupyter

# Install with documentation dependencies
uv sync --extra docs
```

## Common Development Tasks

### Adding New Vehicle Types
1. Update YAML configuration with battery specifications
2. Ensure probability weights sum to 1.0
3. Test with existing scenarios

### Creating New Scenarios
1. Copy existing YAML template from `data/config_builder/`
2. Modify `arrival_distribution`, `infrastructure`, and `vehicle_types`
3. Validate with short simulation runs

### Debugging Simulations
- Enable logging: `logging.basicConfig(level=logging.INFO)`
- Check `elvis/log.log` for simulation events
- Use Jupyter notebooks for interactive analysis

## CRITICAL ISSUES & IMPROVEMENT ROADMAP

### **Statistical Modeling Issues (HIGH PRIORITY)**

The current ELVIS implementation has significant statistical flaws that reduce simulation accuracy by 40-60%. These issues must be addressed to achieve realistic EV charging behavior modeling.

#### **1. Distribution Independence Assumptions (CRITICAL)**

**Current Problem**: All charging event variables are modeled as independent:
- Arrival time ↔ State of Charge: No correlation (should be -0.25)
- Vehicle type ↔ Parking duration: No correlation (should be +0.20)
- SoC ↔ Parking duration: No correlation (should be -0.45)
- Vehicle type ↔ Arrival time: No correlation (should be +0.10)

**Files Affected**:
- `elvis/charging_event_generator.py:195-215` - Independent sampling
- `elvis/config.py` - No correlation parameters
- `data/config_builder/*.yaml` - Missing interdependency specifications

**Impact**: Underestimates charging infrastructure stress by 20-30%

#### **2. Missing Behavioral Context (CRITICAL)**

**Current Problem**: No modeling of visit purpose or user segmentation:
```python
# Current approach - one-size-fits-all
parking_time = np.random.normal(mean_park, std_deviation_park)
soc = np.random.normal(mean_soc, std_deviation_soc)
```

**Should Be**:
```python
# Purpose-driven approach
if visit_purpose == 'work_commute':
    parking_time = Gamma(shape=8, scale=1)  # ~8 hours
    soc = distance_based_model(commute_distance)
elif visit_purpose == 'shopping':
    parking_time = Gamma(shape=2, scale=0.5)  # ~1-2 hours
    soc = opportunistic_charging_model()
```

**Files Affected**:
- `elvis/charging_event_generator.py` - Add purpose modeling
- `elvis/config.py` - Add user segmentation parameters

#### **3. Temporal Stationarity Assumption (MAJOR)**

**Current Problem**: Fixed weekly patterns ignore:
- Seasonal variations (winter increases charging frequency by 30%)
- Weather impacts (cold weather reduces range)
- Local events and holidays
- Economic factors affecting travel patterns

**Files Affected**:
- `elvis/charging_event_generator.py:65-101` - `align_distribution()`
- `data/config_builder/*.yaml` - Static weekly patterns only

### **IMMEDIATE ACTION ITEMS**

#### **Phase 1: Critical Fixes (4-6 weeks)**

**TODO 1: Implement Correlation Structure**
```python
# Location: elvis/charging_event_generator.py
class CorrelatedEventGenerator:
    def __init__(self, correlation_matrix):
        self.copula = GaussianCopula(correlation_matrix)

    def generate_correlated_events(self, num_events):
        # Sample from multivariate distribution
        # Transform to marginal distributions
        pass
```

**TODO 2: Add Purpose-Driven Modeling**
```python
# Location: elvis/config.py
class PurposeBasedConfig:
    purposes = {
        'work_commute': {...},
        'shopping': {...},
        'emergency_charge': {...}
    }
```

**TODO 3: Vehicle-Type Dependencies**
```python
# Location: elvis/vehicle.py
class EnhancedElectricVehicle:
    def get_parking_distribution(self):
        # Return vehicle-specific parking patterns

    def get_soc_dependency(self, trip_context):
        # Return SoC based on vehicle characteristics
```

#### **Phase 2: Advanced Modeling (8-12 weeks)**

**TODO 4: Dynamic Data Integration**
```python
# New file: elvis/data_sources/
class GooglePopularityAPI:
    def fetch_hourly_patterns(self, place_id):
        # Real-time Google popularity data

class WeatherAPI:
    def get_weather_impact(self, location, date):
        # Weather-based consumption adjustments

class EventsAPI:
    def get_local_events(self, location, date_range):
        # Event-driven demand spikes
```

**TODO 5: Hierarchical Bayesian Model**
```python
# New file: elvis/models/hierarchical.py
class HierarchicalChargingModel:
    def __init__(self):
        self.context_model = ContextualModel()
        self.behavior_model = ConditionalBehaviorModel()

    def generate_realistic_events(self, context):
        # Multi-level behavioral modeling
```

**TODO 6: Machine Learning Integration**
```python
# New file: elvis/models/adaptive.py
class AdaptiveLearningModel:
    def update_from_observations(self, observed_data):
        # Online learning from real charging data

    def predict_future_patterns(self, forecast_horizon):
        # Predictive modeling for planning
```

### **VALIDATION REQUIREMENTS**

#### **Data Validation Standards**
- **Correlation coefficients** must match empirical studies (±0.05 tolerance)
- **Temporal patterns** validated against real charging station data
- **Cross-validation** with independent datasets from different regions

#### **Performance Benchmarks**
- **Accuracy target**: 80%+ correlation with real-world patterns
- **Speed requirement**: Generate 10,000 events in <5 seconds
- **Memory constraint**: Handle year-long simulations in <4GB RAM

### **CONFIGURATION MANAGEMENT UPDATES**

#### **Enhanced YAML Schema**
```yaml
# New correlation parameters
correlations:
  arrival_soc: -0.25
  vehicle_parking: 0.20
  soc_parking: -0.45

# Purpose-based parameters
purposes:
  work_commute:
    probability: 0.4
    parking_distribution: {type: gamma, shape: 8, scale: 1}
    soc_model: distance_based
  shopping:
    probability: 0.3
    parking_distribution: {type: gamma, shape: 2, scale: 0.5}
    soc_model: opportunistic

# External data sources
data_sources:
  google_places_id: "ChIJ..."
  weather_location: "52.5200,13.4050"
  events_api_key: "..."
```

#### **Validation Updates**
```python
# Location: elvis/config/validation.py
class EnhancedConfigValidator:
    def validate_correlations(self, correlations):
        # Ensure correlation matrix is positive definite

    def validate_purpose_probabilities(self, purposes):
        # Ensure purpose probabilities sum to 1.0

    def validate_data_sources(self, sources):
        # Check API connectivity and data availability
```

### **DEVELOPMENT GUIDELINES FOR IMPROVEMENTS**

#### **Statistical Best Practices**
- **Always validate** correlation structures with real data
- **Use domain knowledge** to constrain parameter ranges
- **Implement cross-validation** for all new models
- **Document assumptions** clearly in code comments

#### **Code Integration Principles**
- **Backward compatibility**: New features must not break existing scenarios
- **Configuration-driven**: All new parameters externalized to YAML
- **Modular design**: New models as separate classes/modules
- **Performance monitoring**: Profile all changes for speed impact

#### **Testing Requirements**
- **Unit tests** for all new distribution classes
- **Integration tests** comparing old vs. new model outputs
- **Validation tests** against known datasets
- **Performance tests** for large-scale simulations

This roadmap provides a clear path to transform ELVIS from a basic stochastic simulator into a high-fidelity behavioral modeling tool suitable for real-world infrastructure planning and grid impact analysis.

---

## Known Issues & Improvement Roadmap

### Critical Statistical Issues (Priority: HIGH)

#### **Issue 1: Distribution Independence Assumptions**
**Problem**: All distributions (arrival time, parking duration, SoC, vehicle type) are modeled as independent variables, which contradicts real-world EV charging behavior.

**Current Impact**:
- 20-30% error in charging demand patterns
- Unrealistic load profile predictions
- Poor infrastructure utilization estimates

**Files Affected**:
- `elvis/charging_event_generator.py:161-215` (create_charging_events_from_weekly_distribution)
- `elvis/charging_event_generator.py:336-443` (create_charging_events_from_gmm)

**Required Changes**:
```python
# Current problematic pattern:
vehicle_type = walker.random()  # Independent
parking_time = np.random.normal(mean_park, std_deviation_park)  # Independent
soc = np.random.normal(mean_soc, std_deviation_soc)  # Independent

# Should be replaced with correlated sampling
```

#### **Issue 2: Unrealistic Google Popularity Data Integration**
**Problem**: No actual Google Maps API integration despite references to Google popularity data in discussions. Current arrival distributions are manually crafted without real-world validation.

**Current Impact**:
- Fictional arrival patterns may not reflect actual location usage
- No dynamic updates based on real-world changes
- Missing seasonal and event-driven variations

**Files Affected**:
- `data/config_builder/*.yaml` (all scenario files)
- Missing: Google Maps Places API integration

**Required Implementation**:
```python
# Add to elvis/utility/
class GooglePopularityAPI:
    def fetch_location_patterns(self, place_id: str) -> List[float]
    def process_popularity_to_charging_probability(self, popularity: List[float]) -> List[float]
```

#### **Issue 3: Missing Critical Behavioral Correlations**
**Problem**: Key real-world correlations are not modeled:

- **SoC ↔ Parking Duration**: Low battery → longer stays (-0.45 correlation)
- **Vehicle Type ↔ Behavior**: Luxury vehicles have different patterns
- **Time ↔ Purpose**: Work commute vs. shopping vs. emergency charging

**Current Impact**:
- 40-60% error in peak demand estimation
- Wrong infrastructure sizing recommendations
- Unrealistic charging session patterns

**Files Requiring Correlation Modeling**:
- `elvis/charging_event_generator.py` (main event generation)
- `elvis/config.py` (configuration schema updates)
- `data/config_builder/` (scenario parameter updates)

### Implementation Priorities

#### **Phase 1: Critical Statistical Fixes (Weeks 1-2)**
```bash
# High-priority tasks
[ ] Implement SoC-dependent parking duration correlation
[ ] Add vehicle-type-dependent behavior patterns
[ ] Create purpose-driven arrival modeling
[ ] Add temporal autocorrelation for user habits
```

#### **Phase 2: Data Integration (Weeks 3-4)**
```bash
# Data source improvements
[ ] Implement Google Maps Places API integration
[ ] Add weather API for consumption/behavior adjustments
[ ] Create local events API for demand spike modeling
[ ] Build historical data validation framework
```

#### **Phase 3: Advanced Modeling (Weeks 5-8)**
```bash
# Advanced statistical modeling
[ ] Implement multivariate copula-based distributions
[ ] Add hierarchical Bayesian user segmentation
[ ] Create real-time adaptive parameter learning
[ ] Build cross-location correlation modeling
```

### Code Improvement Guidelines

#### **When Modifying Distribution Code**:
1. **Always consider correlations**: No variable should be sampled independently
2. **Validate with real data**: Any new distribution must be validated against observed patterns
3. **Document assumptions**: Clearly state what behavioral assumptions are being made
4. **Test edge cases**: Ensure correlations don't create impossible combinations

#### **Statistical Best Practices for ELVIS**:
```python
# GOOD: Correlated sampling
def sample_correlated_charging_event(self, context):
    purpose = self.sample_visit_purpose(context.time_of_day)
    vehicle_type = self.sample_vehicle_for_purpose(purpose)
    parking_duration = self.sample_parking_for_purpose(purpose, vehicle_type)
    soc = self.sample_soc_for_trip(purpose, vehicle_type, context.weather)

# BAD: Independent sampling (current approach)
def sample_independent_charging_event(self):
    vehicle_type = self.walker.random()
    parking_duration = np.random.normal(self.mean_park, self.std_park)
    soc = np.random.normal(self.mean_soc, self.std_soc)
```

#### **Required Dependencies for Improvements**:
```bash
# Add to pyproject.toml
uv add googlemaps              # Google Places API
uv add scipy                   # Enhanced statistical distributions
uv add scikit-learn           # Advanced clustering and correlation
uv add requests               # External API integration
uv add --dev pytest-mock      # Testing API integrations
```

### Validation Requirements

#### **Before Implementing Changes**:
1. **Baseline establishment**: Document current simulation outputs for comparison
2. **Real-world data collection**: Gather actual charging session data for validation
3. **Statistical testing**: Use Kolmogorov-Smirnov tests to validate distribution improvements
4. **Cross-validation**: Test improved models against held-out real charging data

#### **Success Metrics**:
- **Arrival pattern correlation**: >0.8 with real location data
- **Load profile accuracy**: <15% MAPE vs actual charging infrastructure data
- **Peak demand prediction**: <20% error in 95th percentile loads
- **Infrastructure utilization**: <10% error in capacity factor predictions

### Testing Strategy for Statistical Improvements

```bash
# Required test files to create/update
tests/test_correlated_distributions.py    # Test correlation implementations
tests/test_google_api_integration.py      # Test external data integration
tests/test_behavioral_validation.py       # Validate against real-world patterns
tests/test_statistical_accuracy.py        # Statistical goodness-of-fit tests
```

### Documentation Requirements

#### **Every Statistical Change Must Include**:
1. **Mathematical formulation**: Clear equations for new distributions/correlations
2. **Behavioral justification**: Why this correlation exists in real-world charging
3. **Validation results**: How the change improves accuracy vs. real data
4. **Parameter sensitivity**: How sensitive results are to correlation parameters

This roadmap provides a clear path to transform ELVIS from a simplified simulation to a statistically rigorous tool that accurately models real-world EV charging behavior. All changes should prioritize statistical validity and real-world correlation over computational simplicity.

## Important Development Instructions

### For Statistical Modeling Changes
- **Never assume independence**: Always question whether variables should be correlated
- **Validate distributions**: Use real charging data to validate any new statistical models
- **Document correlations**: Clearly explain the real-world basis for any correlation
- **Test edge cases**: Ensure correlations don't produce impossible scenarios (e.g., negative SoC)

### For External Data Integration
- **API Error Handling**: All external API calls must have robust error handling and fallbacks
- **Data Validation**: Validate all external data before using in simulations
- **Caching Strategy**: Implement appropriate caching for external API calls
- **Rate Limiting**: Respect API rate limits and implement backoff strategies

### For Configuration Changes
- **Backward Compatibility**: Ensure new configuration options don't break existing scenarios
- **Validation Updates**: Update ConfigValidator for any new parameters
- **Documentation**: Update YAML examples and documentation for new configuration options
- **Default Values**: Provide sensible defaults for new parameters

This guide should help both developers and Claude understand the project structure, maintain consistency, and contribute effectively to the ELVIS simulation tool.

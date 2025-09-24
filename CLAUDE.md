# CLAUDE.md - ELVIS Project Guide

## Project Overview

**ELVIS** (Electric Vehicle Charging Infrastructure Simulator) is a Python-based planning and management tool for electric vehicle charging infrastructure. It simulates charging demand patterns, infrastructure utilization, and energy consumption for various EV charging scenarios.

**Purpose**: Research and analysis tool for EV charging infrastructure planning
**Goals**: 
- Model stochastic EV charging behavior and demand patterns  
- Simulate various charging infrastructure scenarios
- Generate load profiles and analyze grid impacts
- Support research in sustainable mobility and energy systems

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

This guide should help both developers and Claude understand the project structure, maintain consistency, and contribute effectively to the ELVIS simulation tool.
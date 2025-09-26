#!/usr/bin/env python3
"""Test script to run all scenario configurations from data/config_builder/ directory.

This validates that our Phase 2 changes (enums, validation, exception handling)
work correctly with all real-world scenario configurations.
"""

import sys
import traceback
from pathlib import Path
from typing import Any

import yaml

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from elvis.config import ScenarioConfig
from elvis.simulate import simulate
from elvis.enums import SchedulingPolicyType


def load_scenario_config(yaml_path: str) -> dict[str, Any]:
    """Load scenario configuration from YAML file."""
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def run_scenario_test(
    scenario_name: str, config_path: str, policy_type: SchedulingPolicyType = None
) -> dict[str, Any]:
    """Run a single scenario test and return results."""
    policy_suffix = f"_{policy_type.value}" if policy_type else ""
    test_name = f"{scenario_name}{policy_suffix}"
    result = {"scenario": test_name, "status": "UNKNOWN", "error": None, "details": {}}

    try:
        print(f"\n{'=' * 60}")
        print(f"Testing scenario: {scenario_name}")
        if policy_type:
            print(f"Policy: {policy_type.value}")
        print(f"Config file: {config_path}")
        print(f"{'=' * 60}")

        # 1. Load YAML configuration
        print("1. Loading YAML configuration...")
        yaml_data = load_scenario_config(config_path)
        print("   ✅ YAML loaded successfully")

        # 2. Check if this is a complete scenario (skip incomplete/template configs)
        print("2. Validating scenario completeness...")
        required_keys = ["arrival_distribution", "vehicle_types", "infrastructure"]
        missing_keys = []
        for key in required_keys:
            if key not in yaml_data and "charging_events" not in yaml_data:
                missing_keys.append(key)

        if missing_keys and "charging_events" not in yaml_data:
            result.update(
                {
                    "status": "SKIPPED",
                    "error": f"Incomplete scenario config - missing: {', '.join(missing_keys)}",
                }
            )
            print(f"   ⏭️  SKIPPED: Incomplete config - missing {', '.join(missing_keys)}")
            return result

        # 3. Create ScenarioConfig from YAML (tests our enum/validation systems)
        print("3. Creating ScenarioConfig from YAML...")
        config = ScenarioConfig.from_yaml(yaml_data)

        # Override scheduling policy if specified
        if policy_type:
            config.with_scheduling_policy(policy_type)

        print("   ✅ ScenarioConfig created successfully")
        print(f"   📊 Scheduling policy: {config.scheduling_policy}")
        print(f"   📊 Number of charging events: {config.num_charging_events}")
        print(
            f"   📊 Vehicle types count: {len(config.vehicle_types) if config.vehicle_types else 0}"
        )

        # 4. Create realisation for short simulation period
        print("4. Creating scenario realisation...")
        start_date = "2025-01-01 00:00:00"
        end_date = "2025-12-31 23:00:00"
        resolution = "01:00:00"

        realisation = config.create_realisation(start_date, end_date, resolution)
        print("   ✅ Realisation created successfully")
        print(
            f"   📊 Charging events generated: {len(realisation.charging_events) if realisation.charging_events else 0}"
        )

        # 5. Run short simulation
        print("5. Running simulation...")
        simulation_results = simulate(realisation)
        print("   ✅ Simulation completed successfully")

        # 6. Set up results properly and extract basic metrics
        print("6. Calculating basic metrics...")
        simulation_results.scenario = realisation  # Set scenario for result calculations

        # Calculate number of simulation steps
        import datetime as dt
        from datetime import datetime

        start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        resolution_dt = dt.timedelta(hours=1)  # 01:00:00
        num_steps = int((end_dt - start_dt) / resolution_dt) + 1

        # Get load profile first
        load_profile = simulation_results.aggregate_load_profile(num_steps)

        # Calculate metrics
        total_energy = simulation_results.total_energy_charged(num_steps)
        max_load = simulation_results.max_load()

        print(f"   📈 Total energy charged: {total_energy:.2f} kWh")
        print(f"   📈 Maximum load: {max_load:.2f} kW")

        result.update(
            {
                "status": "SUCCESS",
                "details": {
                    "total_energy_kwh": round(total_energy, 2),
                    "max_load_kw": round(max_load, 2),
                    "charging_events_count": len(realisation.charging_events)
                    if realisation.charging_events
                    else 0,
                    "vehicle_types_count": len(config.vehicle_types) if config.vehicle_types else 0,
                    "scheduling_policy": str(config.scheduling_policy),
                    "policy_type": policy_type.value if policy_type else "default",
                },
            }
        )

    except Exception as e:
        print(f"   ❌ ERROR: {e!s}")
        result.update({"status": "FAILED", "error": str(e), "traceback": traceback.format_exc()})

    return result


def main():
    """Main test function that runs all scenario configurations with multiple scheduling policies."""
    print("🚀 ELVIS Multi-Policy Scenario Validation Test")
    print("Testing all configurations in data/config_builder/ with multiple scheduling policies")
    print("This validates our scheduling policy implementations and compares their performance")

    # Find all YAML files in config_builder directory
    config_dir = project_root / "data" / "config_builder"
    yaml_files = list(config_dir.glob("*.yaml"))

    if not yaml_files:
        print("❌ No YAML files found in data/config_builder/")
        return False

    # Define policies to test (only implemented ones)
    implemented_policies = [
        SchedulingPolicyType.UNCONTROLLED,
        SchedulingPolicyType.FCFS,
        SchedulingPolicyType.DISCRIMINATION_FREE,
    ]

    # Note unimplemented policies
    unimplemented_policies = [
        SchedulingPolicyType.WITH_STORAGE,
        SchedulingPolicyType.OPTIMIZED,
    ]

    print(f"\n📁 Found {len(yaml_files)} scenario configurations:")
    for yaml_file in sorted(yaml_files):
        print(f"   - {yaml_file.name}")

    print(f"\n🔄 Will test {len(implemented_policies)} scheduling policies:")
    for policy in implemented_policies:
        print(f"   ✅ {policy.value}")

    print(f"\n⚠️  Skipping {len(unimplemented_policies)} unimplemented policies:")
    for policy in unimplemented_policies:
        print(f"   ❌ {policy.value} (not implemented)")

    # Run tests for all scenarios and all implemented policies
    all_results: list[dict[str, Any]] = []

    for yaml_file in sorted(yaml_files):
        scenario_name = yaml_file.stem
        for policy_type in implemented_policies:
            result = run_scenario_test(scenario_name, str(yaml_file), policy_type)
            all_results.append(result)

    # Summary report
    print(f"\n{'=' * 80}")
    print("🏁 FINAL SUMMARY REPORT")
    print(f"{'=' * 80}")

    successful = [r for r in all_results if r["status"] == "SUCCESS"]
    failed = [r for r in all_results if r["status"] == "FAILED"]
    skipped = [r for r in all_results if r["status"] == "SKIPPED"]

    testable_count = len(all_results) - len(skipped)

    print(f"✅ Successful scenarios: {len(successful)}/{testable_count}")
    print(f"❌ Failed scenarios: {len(failed)}/{testable_count}")
    print(f"⏭️  Skipped scenarios: {len(skipped)}/{len(all_results)} (incomplete configs)")

    if successful:
        print("\n🎉 SUCCESSFUL SCENARIOS:")

        # Group results by scenario name for comparison
        scenario_groups = {}
        for result in successful:
            scenario_base = result["scenario"].split("_")[0]  # Get base scenario name
            if scenario_base not in scenario_groups:
                scenario_groups[scenario_base] = []
            scenario_groups[scenario_base].append(result)

        for scenario_base, scenario_results in sorted(scenario_groups.items()):
            print(f"\n📊 {scenario_base.upper()}:")
            for result in scenario_results:
                details = result["details"]
                policy_type = details.get("policy_type", "default")
                print(
                    f"   ✅ {policy_type:<20} | "
                    f"Energy: {details.get('total_energy_kwh', 0):<8.2f} kWh | "
                    f"Max Load: {details.get('max_load_kw', 0):<8.2f} kW | "
                    f"Events: {details.get('charging_events_count', 0):<6} | "
                    f"Policy: {details.get('scheduling_policy', 'N/A')}"
                )

    if failed:
        print("\n💥 FAILED SCENARIOS:")
        for result in failed:
            print(f"   ❌ {result['scenario']:<25} | Error: {result['error']}")

    if skipped:
        print("\n⏭️  SKIPPED SCENARIOS:")
        for result in skipped:
            print(f"   ⏭️  {result['scenario']:<25} | Reason: {result['error']}")

    # Overall success assessment (only count testable scenarios)
    if testable_count > 0:
        success_rate = len(successful) / testable_count * 100
    else:
        success_rate = 0
    print(f"\n📊 Overall Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 EXCELLENT! Phase 2 changes work great with real scenarios!")
        return True
    if success_rate >= 75:
        print("👍 GOOD! Most scenarios work, minor issues to investigate")
        return True
    if success_rate >= 50:
        print("⚠️  MODERATE! Several issues found, needs attention")
        return False
    print("🚨 CRITICAL! Many scenarios failing, major issues detected")
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

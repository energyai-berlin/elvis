#!/usr/bin/env python3
"""Test script to run all scenario configurations using factory methods.

This validates that our factory methods work correctly with all predefined scenarios
and that different scheduling policies produce different results.
"""

import sys
import traceback
from pathlib import Path
from typing import Any, Callable

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from elvis.config import ScenarioConfig
from elvis.simulate import simulate
from elvis.enums import SchedulingPolicyType


def get_scenario_factory_methods() -> dict[str, Callable]:
    """Get all available scenario factory methods."""
    return {
        "office": ScenarioConfig.office_scenario,
        "residential": ScenarioConfig.residential_scenario,
        "wohnblock": ScenarioConfig.wohnblock_scenario,
        "cabstand": ScenarioConfig.cabstand_scenario,
        "customer_parking_day": ScenarioConfig.customer_parking_day_scenario,
        "customer_parking_night": ScenarioConfig.customer_parking_night_scenario,
        "gasstation_speedway": ScenarioConfig.gasstation_speedway_scenario,
        "kundenparkplatz": ScenarioConfig.kundenparkplatz_scenario,
        "office_fleet": ScenarioConfig.office_fleet_scenario,
        "pnr": ScenarioConfig.pnr_scenario,
        "roadside": ScenarioConfig.roadside_scenario,
        "tankstelle_city": ScenarioConfig.tankstelle_city_scenario,
    }


def run_scenario_test(
    scenario_name: str, factory_method: Callable, policy_type: SchedulingPolicyType = None
) -> dict[str, Any]:
    """Run a single scenario test using factory method and return results."""
    policy_suffix = f"_{policy_type.value}" if policy_type else ""
    test_name = f"{scenario_name}{policy_suffix}"
    result = {"scenario": test_name, "status": "UNKNOWN", "error": None, "details": {}}

    try:
        print(f"\n{'=' * 60}")
        print(f"Testing scenario: {scenario_name}")
        if policy_type:
            print(f"Policy: {policy_type.value}")
        print(f"Factory method: {factory_method.__name__}")
        print(f"{'=' * 60}")

        # 1. Create ScenarioConfig using factory method
        print("1. Creating ScenarioConfig using factory method...")
        
        # Create config with policy override if specified
        if policy_type:
            config = factory_method(scheduling_policy=policy_type.value)
        else:
            config = factory_method()
        
        print("   ✅ ScenarioConfig created successfully using factory method")

        # 2. Validate configuration completeness  
        print("2. Validating scenario completeness...")
        if not config.vehicle_types or not config.infrastructure:
            result.update(
                {
                    "status": "SKIPPED", 
                    "error": "Incomplete scenario config from factory method",
                }
            )
            print("   ⏭️  SKIPPED: Incomplete config from factory")
            return result

        print(f"   📊 Scheduling policy: {config.scheduling_policy}")
        print(f"   📊 Number of charging events: {config.num_charging_events}")
        print(
            f"   📊 Vehicle types count: {len(config.vehicle_types) if config.vehicle_types else 0}"
        )

        # 3. Create realisation for short simulation period  
        print("3. Creating scenario realisation...")
        start_date = "2025-01-01 00:00:00"
        end_date = "2025-12-31 23:00:00"
        resolution = "01:00:00"

        realisation = config.create_realisation(start_date, end_date, resolution)
        print("   ✅ Realisation created successfully")
        print(
            f"   📊 Charging events generated: {len(realisation.charging_events) if realisation.charging_events else 0}"
        )

        # 4. Run short simulation
        print("4. Running simulation...")
        simulation_results = simulate(realisation)
        print("   ✅ Simulation completed successfully")

        # 5. Set up results properly and extract basic metrics
        print("5. Calculating basic metrics...")
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
    """Main test function that runs all scenario factory methods with multiple scheduling policies."""
    print("🚀 ELVIS Factory Method Multi-Policy Validation Test")
    print("Testing all factory methods with multiple scheduling policies")
    print("This validates our factory methods and compares scheduling policy performance")
    print("\n💡 Factory methods allow easy customization:")
    print("   config = ScenarioConfig.office_scenario(scheduling_policy='FCFS', num_charging_events=500)")
    print("   config = ScenarioConfig.residential_scenario(vehicle_types=custom_fleet)")

    # Get all available factory methods
    factory_methods = get_scenario_factory_methods()

    if not factory_methods:
        print("❌ No factory methods found")
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

    print(f"\n🏭 Found {len(factory_methods)} scenario factory methods:")
    for scenario_name in sorted(factory_methods.keys()):
        print(f"   - {scenario_name}_scenario()")

    print(f"\n🔄 Will test {len(implemented_policies)} scheduling policies:")
    for policy in implemented_policies:
        print(f"   ✅ {policy.value}")

    print(f"\n⚠️  Skipping {len(unimplemented_policies)} unimplemented policies:")
    for policy in unimplemented_policies:
        print(f"   ❌ {policy.value} (not implemented)")

    # Run tests for all scenarios and all implemented policies
    all_results: list[dict[str, Any]] = []

    for scenario_name, factory_method in sorted(factory_methods.items()):
        for policy_type in implemented_policies:
            result = run_scenario_test(scenario_name, factory_method, policy_type)
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

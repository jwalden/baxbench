#!/usr/bin/env python3
"""
Summarize the contents of a model's results directory.

Usage:
    python scripts/summarize_results.py <model_name>
    python scripts/summarize_results.py results/gpt-4o

Example:
    pipenv run python scripts/summarize_results.py gpt-4o
"""

import argparse
import json
import pathlib
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class CombinationStats:
    """Stats for a single scenario/env/spec combination."""
    path: pathlib.Path
    has_code: bool = False
    num_python_files: int = 0
    num_samples: int = 0
    samples_with_code: int = 0
    samples_with_test_log: int = 0
    samples_with_test_results: int = 0
    sample_numbers: List[int] = field(default_factory=list)


@dataclass
class ModelSummary:
    """Overall summary for a model's results."""
    model_name: str
    total_combinations: int = 0
    combinations_with_code: int = 0
    combinations_with_test_logs: int = 0
    combinations_with_test_results: int = 0
    total_python_files: int = 0
    total_samples: int = 0
    scenarios: Set[str] = field(default_factory=set)
    envs: Set[str] = field(default_factory=set)
    spec_configs: Set[str] = field(default_factory=set)
    combinations: List[CombinationStats] = field(default_factory=list)


def analyze_combination(combo_path: pathlib.Path) -> CombinationStats:
    """Analyze a single scenario/env/spec combination directory."""
    stats = CombinationStats(path=combo_path)

    # Find all sample directories
    if not combo_path.exists():
        return stats

    for item in combo_path.iterdir():
        if item.is_dir() and item.name.startswith("sample"):
            # Extract sample number
            try:
                sample_num = int(item.name.replace("sample", ""))
                stats.sample_numbers.append(sample_num)
                stats.num_samples += 1
            except ValueError:
                continue

            # Check for code directory
            code_dir = item / "code"
            if code_dir.exists() and code_dir.is_dir():
                stats.samples_with_code += 1
                # Count Python files
                python_files = list(code_dir.rglob("*.py"))
                if python_files:
                    stats.has_code = True
                    stats.num_python_files += len(python_files)

            # Check for test.log
            if (item / "test.log").exists():
                stats.samples_with_test_log += 1

            # Check for test_results.json
            if (item / "test_results.json").exists():
                stats.samples_with_test_results += 1

    return stats


def analyze_model_results(model_path: pathlib.Path) -> ModelSummary:
    """Analyze all results for a model."""
    summary = ModelSummary(model_name=model_path.name)

    if not model_path.exists() or not model_path.is_dir():
        print(f"Error: Directory not found: {model_path}")
        return summary

    # Traverse: model/scenario/env/spec_config/
    for scenario_dir in sorted(model_path.iterdir()):
        if not scenario_dir.is_dir():
            continue

        scenario_name = scenario_dir.name
        summary.scenarios.add(scenario_name)

        for env_dir in sorted(scenario_dir.iterdir()):
            if not env_dir.is_dir():
                continue

            env_name = env_dir.name
            summary.envs.add(env_name)

            for spec_dir in sorted(env_dir.iterdir()):
                if not spec_dir.is_dir():
                    continue

                spec_config = spec_dir.name
                summary.spec_configs.add(spec_config)
                summary.total_combinations += 1

                # Analyze this combination
                stats = analyze_combination(spec_dir)
                summary.combinations.append(stats)

                # Aggregate stats
                if stats.has_code:
                    summary.combinations_with_code += 1
                if stats.samples_with_test_log > 0:
                    summary.combinations_with_test_logs += 1
                if stats.samples_with_test_results > 0:
                    summary.combinations_with_test_results += 1

                summary.total_python_files += stats.num_python_files
                summary.total_samples += stats.num_samples

    return summary


def print_summary(summary: ModelSummary, verbose: bool = False) -> None:
    """Print a formatted summary of the model results."""
    print("=" * 80)
    print(f"Results Summary for Model: {summary.model_name}")
    print("=" * 80)
    print()

    # Basic counts
    print("Overview:")
    print(f"  Scenarios: {len(summary.scenarios)}")
    print(f"  Environments: {len(summary.envs)}")
    print(f"  Spec Configurations: {len(summary.spec_configs)}")
    print(f"  Total Combinations: {summary.total_combinations}")
    print(f"  Total Samples: {summary.total_samples}")
    print()

    # Code files
    if summary.total_combinations > 0:
        code_pct = (summary.combinations_with_code / summary.total_combinations) * 100
        print("Code Files:")
        print(f"  Combinations with Python code: {summary.combinations_with_code}/{summary.total_combinations} ({code_pct:.1f}%)")
        print(f"  Total Python files: {summary.total_python_files}")
        if summary.combinations_with_code > 0:
            avg_files = summary.total_python_files / summary.combinations_with_code
            print(f"  Average Python files per combination: {avg_files:.1f}")
        print()

        # Test logs
        log_pct = (summary.combinations_with_test_logs / summary.total_combinations) * 100
        print("Test Logs:")
        print(f"  Combinations with test.log: {summary.combinations_with_test_logs}/{summary.total_combinations} ({log_pct:.1f}%)")
        print()

        # Test results
        results_pct = (summary.combinations_with_test_results / summary.total_combinations) * 100
        print("Test Results:")
        print(f"  Combinations with test_results.json: {summary.combinations_with_test_results}/{summary.total_combinations} ({results_pct:.1f}%)")
        print()

    # Detailed breakdown by category
    print("Scenarios:")
    for scenario in sorted(summary.scenarios):
        print(f"  - {scenario}")
    print()

    print("Environments:")
    for env in sorted(summary.envs):
        print(f"  - {env}")
    print()

    print("Spec Configurations:")
    for spec in sorted(summary.spec_configs):
        print(f"  - {spec}")
    print()

    # Verbose mode: show details per combination
    if verbose:
        print("=" * 80)
        print("Detailed Breakdown by Combination")
        print("=" * 80)
        print()

        for combo in summary.combinations:
            # Extract path components
            parts = combo.path.parts
            if len(parts) >= 3:
                scenario = parts[-3]
                env = parts[-2]
                spec = parts[-1]

                print(f"{scenario}/{env}/{spec}:")
                print(f"  Samples: {combo.num_samples}")
                print(f"  Python files: {combo.num_python_files}")
                print(f"  Samples with code: {combo.samples_with_code}")
                print(f"  Samples with test.log: {combo.samples_with_test_log}")
                print(f"  Samples with test_results.json: {combo.samples_with_test_results}")
                if combo.sample_numbers:
                    print(f"  Sample numbers: {sorted(combo.sample_numbers)}")
                print()


def main():
    parser = argparse.ArgumentParser(
        description="Summarize the contents of a model's results directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/summarize_results.py gpt-4o
  python scripts/summarize_results.py results/claude-sonnet-4
  python scripts/summarize_results.py gpt-4o --verbose
        """
    )
    parser.add_argument(
        "model_name",
        type=str,
        help="Model name or path to model results directory (e.g., 'gpt-4o' or 'results/gpt-4o')"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed breakdown for each combination"
    )
    parser.add_argument(
        "--results-dir",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parent.parent / "results",
        help="Base results directory (default: ./results)"
    )

    args = parser.parse_args()

    # Determine the model path - try multiple possibilities
    model_input = pathlib.Path(args.model_name)

    # List of paths to try, in order of preference
    paths_to_try = [
        model_input,  # Direct path provided
        args.results_dir / args.model_name,  # results/<model_name>
        pathlib.Path("results") / args.model_name,  # ./results/<model_name>
    ]

    model_path = None
    for path in paths_to_try:
        if path.exists() and path.is_dir():
            model_path = path
            break

    if model_path is None:
        print(f"Error: Could not find model directory. Tried:", file=sys.stderr)
        for path in paths_to_try:
            print(f"  - {path}", file=sys.stderr)
        sys.exit(1)

    # Analyze the results
    summary = analyze_model_results(model_path)

    if summary.total_combinations == 0:
        print(f"No results found in {model_path}")
        print(f"Make sure the directory exists and contains results.")
        sys.exit(1)

    # Print the summary
    print_summary(summary, verbose=args.verbose)


if __name__ == "__main__":
    main()

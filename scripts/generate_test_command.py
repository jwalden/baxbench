#!/usr/bin/env python3
"""
Generate a test command for all code found in a model's results directory.

This script analyzes a model's results directory and constructs the appropriate
pipenv run python src/main.py command to test all scenario/env/spec combinations.

Usage:
    python scripts/generate_test_command.py <model_name>
    python scripts/generate_test_command.py results/gpt-4o

Example:
    pipenv run python scripts/generate_test_command.py claude-sonnet-4-20250514-thinking
"""

import argparse
import pathlib
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Set, List


@dataclass
class SpecConfig:
    """Parsed spec configuration from directory name."""
    temperature: float
    spec_type: str
    safety_prompt: str

    @classmethod
    def from_dirname(cls, dirname: str) -> "SpecConfig":
        """Parse a directory name like 'temp0.2-openapi-none' into components."""
        parts = dirname.split("-")
        if len(parts) < 3:
            raise ValueError(f"Invalid spec config directory name: {dirname}")

        # Extract temperature (format: tempX.X)
        temp_str = parts[0].replace("temp", "")
        temperature = float(temp_str)

        # Extract spec_type and safety_prompt
        spec_type = parts[1]
        safety_prompt = parts[2]

        return cls(
            temperature=temperature,
            spec_type=spec_type,
            safety_prompt=safety_prompt
        )


@dataclass
class CombinationInfo:
    """Information about a scenario/env/spec combination."""
    scenario: str
    env: str
    spec_config: SpecConfig
    samples: List[int]
    has_code: bool = False
    has_test_results: bool = False


def analyze_model_directory(model_path: pathlib.Path) -> List[CombinationInfo]:
    """Analyze a model's results directory and extract all combinations."""
    combinations = []

    if not model_path.exists() or not model_path.is_dir():
        print(f"Error: Directory not found: {model_path}", file=sys.stderr)
        return combinations

    # Traverse: model/scenario/env/spec_config/sample*/
    for scenario_dir in sorted(model_path.iterdir()):
        if not scenario_dir.is_dir():
            continue

        scenario_name = scenario_dir.name

        for env_dir in sorted(scenario_dir.iterdir()):
            if not env_dir.is_dir():
                continue

            env_name = env_dir.name

            for spec_dir in sorted(env_dir.iterdir()):
                if not spec_dir.is_dir():
                    continue

                try:
                    spec_config = SpecConfig.from_dirname(spec_dir.name)
                except ValueError as e:
                    print(f"Warning: {e}", file=sys.stderr)
                    continue

                # Find all samples
                samples = []
                has_code = False
                has_test_results = False

                for item in spec_dir.iterdir():
                    if item.is_dir() and item.name.startswith("sample"):
                        try:
                            sample_num = int(item.name.replace("sample", ""))
                            samples.append(sample_num)

                            # Check if code exists
                            code_dir = item / "code"
                            if code_dir.exists() and code_dir.is_dir():
                                has_code = True

                            # Check if test results exist
                            if (item / "test_results.json").exists():
                                has_test_results = True
                        except ValueError:
                            continue

                if samples:
                    combinations.append(CombinationInfo(
                        scenario=scenario_name,
                        env=env_name,
                        spec_config=spec_config,
                        samples=sorted(samples),
                        has_code=has_code,
                        has_test_results=has_test_results
                    ))

    return combinations


def group_by_common_params(combinations: List[CombinationInfo]) -> Dict[tuple, List[CombinationInfo]]:
    """Group combinations that can be tested with the same command."""
    groups: Dict[tuple, List[CombinationInfo]] = defaultdict(list)

    for combo in combinations:
        # Group by temperature, spec_type, and safety_prompt
        key = (combo.spec_config.temperature, combo.spec_config.spec_type, combo.spec_config.safety_prompt)
        groups[key].append(combo)

    return groups


def generate_test_command(
    model_name: str,
    combinations: List[CombinationInfo],
    force: bool = False,
    max_concurrent_runs: int = 1
) -> str:
    """Generate a test command for the given combinations."""
    if not combinations:
        return ""

    # All combinations in this group should have the same spec config
    spec = combinations[0].spec_config

    # Collect unique scenarios and envs
    scenarios = sorted(set(c.scenario for c in combinations))
    envs = sorted(set(c.env for c in combinations))

    # Find max sample number
    max_sample = max(max(c.samples) for c in combinations if c.samples)
    n_samples = max_sample + 1  # samples are 0-indexed

    # Build command
    cmd_parts = [
        "pipenv run python src/main.py",
        f"--models {model_name}",
        "--mode test",
        f"--n_samples {n_samples}",
        f"--temperature {spec.temperature}",
        f"--spec_type {spec.spec_type}",
        f"--safety_prompt {spec.safety_prompt}",
        f"--max_concurrent_runs {max_concurrent_runs}",
    ]

    if len(scenarios) < 5:  # If not too many, specify them
        cmd_parts.append(f"--scenarios {' '.join(scenarios)}")

    if len(envs) < 5:  # If not too many, specify them
        cmd_parts.append(f"--envs {' '.join(envs)}")

    if force:
        cmd_parts.append("-f")

    return " \\\n  ".join(cmd_parts)


def main():
    parser = argparse.ArgumentParser(
        description="Generate test commands for a model's results directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_test_command.py gpt-4o
  python scripts/generate_test_command.py claude-sonnet-4-20250514-thinking
  python scripts/generate_test_command.py gpt-4o --force
  python scripts/generate_test_command.py gpt-4o --max-concurrent-runs 4
  python scripts/generate_test_command.py --all-models
  python scripts/generate_test_command.py --all-models --only-untested
        """
    )
    parser.add_argument(
        "model_name",
        type=str,
        nargs="?",
        help="Model name or path to model results directory (omit if using --all-models)"
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Add --force flag to retest even if results exist"
    )
    parser.add_argument(
        "--max-concurrent-runs",
        type=int,
        default=1,
        help="Maximum number of concurrent test runs (default: 1)"
    )
    parser.add_argument(
        "--results-dir",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parent.parent / "results",
        help="Base results directory (default: ./results)"
    )
    parser.add_argument(
        "--only-untested",
        action="store_true",
        help="Only include combinations that don't have test_results.json files"
    )
    parser.add_argument(
        "--all-models",
        action="store_true",
        help="Generate test commands for all models in the results directory"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.all_models and args.model_name:
        print("Error: Cannot specify both model_name and --all-models", file=sys.stderr)
        sys.exit(1)

    if not args.all_models and not args.model_name:
        print("Error: Must specify either model_name or --all-models", file=sys.stderr)
        sys.exit(1)

    # Determine which models to process
    if args.all_models:
        # Find all model directories
        if not args.results_dir.exists():
            print(f"Error: Results directory not found: {args.results_dir}", file=sys.stderr)
            sys.exit(1)

        model_dirs = [d for d in sorted(args.results_dir.iterdir()) if d.is_dir()]
        if not model_dirs:
            print(f"Error: No model directories found in {args.results_dir}", file=sys.stderr)
            sys.exit(1)

        models_to_process = [(d, d.name) for d in model_dirs]
    else:
        # Single model
        model_input = pathlib.Path(args.model_name)
        if model_input.exists() and model_input.is_dir():
            model_path = model_input
            model_name = model_path.name
        else:
            model_path = args.results_dir / args.model_name
            model_name = args.model_name

        models_to_process = [(model_path, model_name)]

    # Process each model
    total_commands = 0
    for model_path, model_name in models_to_process:
        # Analyze the directory
        combinations = analyze_model_directory(model_path)

        if not combinations:
            if args.all_models:
                # Skip this model silently when processing all models
                continue
            else:
                print(f"No code combinations found in {model_path}", file=sys.stderr)
                sys.exit(1)

        # Filter for only combinations with code
        combinations_with_code = [c for c in combinations if c.has_code]

        if not combinations_with_code:
            if args.all_models:
                # Skip this model silently when processing all models
                continue
            else:
                print(f"No combinations with code found in {model_path}", file=sys.stderr)
                sys.exit(1)

        # Filter for untested if requested
        if args.only_untested:
            combinations_with_code = [c for c in combinations_with_code if not c.has_test_results]
            if not combinations_with_code:
                if args.all_models:
                    # Skip this model when processing all models
                    continue
                else:
                    print(f"All combinations already have test results!", file=sys.stderr)
                    sys.exit(0)

        # Group by common parameters
        groups = group_by_common_params(combinations_with_code)

        print(f"# Test commands for model: {model_name}")
        print(f"# Found {len(combinations_with_code)} combinations with code")
        if args.only_untested:
            print(f"# (showing only untested combinations)")
        print(f"# Grouped into {len(groups)} command(s)")
        print()

        for i, (key, group_combos) in enumerate(sorted(groups.items()), 1):
            temp, spec_type, safety_prompt = key
            print(f"# Command {i}/{len(groups)}: temp={temp}, spec_type={spec_type}, safety_prompt={safety_prompt}")
            print(f"# Covers {len(group_combos)} scenario/env combinations")

            cmd = generate_test_command(
                model_name=model_name,
                combinations=group_combos,
                force=args.force,
                max_concurrent_runs=args.max_concurrent_runs
            )
            print(cmd)
            print()
            total_commands += 1

        # Add separator between models when processing multiple
        if args.all_models and model_path != models_to_process[-1][0]:
            print("# " + "=" * 78)
            print()

    if args.all_models:
        print(f"# Total: {total_commands} command(s) across {len([m for m, _ in models_to_process])} model(s)")
        if total_commands == 0:
            print(f"# No testable combinations found", file=sys.stderr)


if __name__ == "__main__":
    main()

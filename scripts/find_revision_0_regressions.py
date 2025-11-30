#!/usr/bin/env python3
"""
Identify experiments where revision_0 succeeded but final code failed.

For functional tests: success means num_passed_ft == num_total_ft
For security tests: success means num_st_exceptions == 0
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


def load_test_results(results_path: Path) -> Dict:
    """Load test_results.json from the given path."""
    test_file = results_path / "test_results.json"
    if not test_file.exists():
        return None

    try:
        with open(test_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def check_functional_success(results: Dict) -> bool:
    """Check if functional tests succeeded (num_passed_ft == num_total_ft)."""
    if results is None:
        return False
    return results.get('num_passed_ft', 0) == results.get('num_total_ft', 0)


def check_security_success(results: Dict) -> bool:
    """Check if security tests succeeded (num_st_exceptions == 0)."""
    if results is None:
        return False
    return results.get('num_st_exceptions', 0) == 0


def find_revision_0_dirs(results_dir: Path, model_name: str) -> List[Path]:
    """Find all revision_0 experiment directories for a specific model."""
    revision_0_dirs = []

    # Find the specific model_revision_0 directory
    model_dir = results_dir / f"{model_name}_revision_0"
    if not model_dir.exists() or not model_dir.is_dir():
        return revision_0_dirs

    # Find all experiment paths: SCENARIO/ENV/TEMP-openapi-PROMPT/sample0
    for scenario_dir in model_dir.iterdir():
        if not scenario_dir.is_dir():
            continue

        for env_dir in scenario_dir.iterdir():
            if not env_dir.is_dir():
                continue

            for prompt_dir in env_dir.iterdir():
                if not prompt_dir.is_dir():
                    continue

                sample_dir = prompt_dir / "sample0"
                if sample_dir.exists() and sample_dir.is_dir():
                    revision_0_dirs.append(sample_dir)

    return revision_0_dirs


def get_final_path(revision_0_path: Path) -> Path:
    """Convert revision_0 path to final path by removing _revision_0 suffix."""
    parts = revision_0_path.parts

    # Find the model directory part (contains _revision_0)
    model_idx = None
    for i, part in enumerate(parts):
        if part.endswith('_revision_0'):
            model_idx = i
            break

    if model_idx is None:
        return None

    # Create final path by replacing model_revision_0 with model
    final_parts = list(parts)
    final_parts[model_idx] = parts[model_idx].replace('_revision_0', '')

    return Path(*final_parts)


def find_regressions(results_dir: Path, model_name: str, use_security: bool) -> List[Tuple[Path, Path]]:
    """
    Find experiments where revision_0 succeeded but final failed.

    Returns list of tuples: (revision_0_path, final_path)
    """
    regressions = []
    check_success = check_security_success if use_security else check_functional_success

    revision_0_dirs = find_revision_0_dirs(results_dir, model_name)

    for revision_0_path in revision_0_dirs:
        # Load revision_0 results
        revision_0_results = load_test_results(revision_0_path)

        # Check if revision_0 succeeded
        if not check_success(revision_0_results):
            continue

        # Get corresponding final path
        final_path = get_final_path(revision_0_path)
        if final_path is None or not final_path.exists():
            continue

        # Load final results
        final_results = load_test_results(final_path)

        # Check if final failed
        if not check_success(final_results):
            regressions.append((revision_0_path, final_path))

    return regressions


def extract_scenario_env_and_prompt(final_path: Path, results_dir: Path) -> Tuple[str, str, str]:
    """
    Extract scenario name, environment, and prompt type from the path.

    Path format: results/MODEL/SCENARIO/ENV/TEMP-openapi-PROMPT/sample0
    Returns: (scenario, environment, prompt_type)
    """
    rel_path = final_path.relative_to(results_dir)
    parts = rel_path.parts

    # parts[0] is MODEL, parts[1] is SCENARIO, parts[2] is ENV
    scenario = parts[1] if len(parts) > 1 else "unknown"
    environment = parts[2] if len(parts) > 2 else "unknown"

    # parts[3] is TEMP-openapi-PROMPT, extract PROMPT
    if len(parts) > 3:
        prompt_part = parts[3]  # e.g., "temp0.4-openapi-specific"
        if '-openapi-' in prompt_part:
            prompt_type = prompt_part.split('-openapi-')[-1]
        else:
            prompt_type = "unknown"
    else:
        prompt_type = "unknown"

    return scenario, environment, prompt_type


def print_summary(regressions: List[Tuple[Path, Path]], results_dir: Path):
    """Print summary statistics by scenario, environment, and prompt type."""
    if not regressions:
        return

    scenario_counts = defaultdict(int)
    env_counts = defaultdict(int)
    prompt_counts = defaultdict(int)

    for _, final_path in regressions:
        scenario, environment, prompt_type = extract_scenario_env_and_prompt(final_path, results_dir)
        scenario_counts[scenario] += 1
        env_counts[environment] += 1
        prompt_counts[prompt_type] += 1

    # Print scenario summary
    print("Summary by Scenario:")
    for scenario in sorted(scenario_counts.keys()):
        count = scenario_counts[scenario]
        print(f"  {scenario}: {count} regression{'s' if count != 1 else ''}")

    print()

    # Print environment summary
    print("Summary by Environment:")
    for environment in sorted(env_counts.keys()):
        count = env_counts[environment]
        print(f"  {environment}: {count} regression{'s' if count != 1 else ''}")

    print()

    # Print prompt type summary
    print("Summary by Prompt Type:")
    # Order: generic, specific, none (then any others)
    prompt_order = ['generic', 'specific', 'none']
    for prompt_type in prompt_order:
        if prompt_type in prompt_counts:
            count = prompt_counts[prompt_type]
            print(f"  {prompt_type}: {count} regression{'s' if count != 1 else ''}")

    # Print any other prompt types not in the standard order
    for prompt_type in sorted(prompt_counts.keys()):
        if prompt_type not in prompt_order:
            count = prompt_counts[prompt_type]
            print(f"  {prompt_type}: {count} regression{'s' if count != 1 else ''}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description='Find experiments where revision_0 succeeded but final code failed'
    )
    parser.add_argument(
        'model',
        type=str,
        help='Model name (e.g., gpt-4.1, claude-sonnet-4-5-20250929-thinking)'
    )
    parser.add_argument(
        '--security',
        action='store_true',
        help='Use security test results instead of functional test results'
    )
    parser.add_argument(
        '--results-dir',
        type=Path,
        default=Path('results'),
        help='Path to results directory (default: results)'
    )

    args = parser.parse_args()

    if not args.results_dir.exists():
        print(f"Error: Results directory '{args.results_dir}' does not exist")
        return 1

    # Check if model directories exist
    model_revision_0_dir = args.results_dir / f"{args.model}_revision_0"
    model_final_dir = args.results_dir / args.model

    if not model_revision_0_dir.exists():
        print(f"Error: Model revision_0 directory '{model_revision_0_dir}' does not exist")
        return 1

    if not model_final_dir.exists():
        print(f"Error: Model final directory '{model_final_dir}' does not exist")
        return 1

    test_type = "security" if args.security else "functional"
    print(f"Finding regressions for model '{args.model}' using {test_type} tests...\n")

    regressions = find_regressions(args.results_dir, args.model, args.security)

    if not regressions:
        print(f"No regressions found (revision_0 succeeded but final failed)")
        return 0

    print_summary(regressions, args.results_dir)

    print(f"Found {len(regressions)} regression(s):\n")

    for revision_0_path, final_path in sorted(regressions):
        # Extract the experiment path (relative to results dir)
        rel_final = final_path.relative_to(args.results_dir)
        print(f"{rel_final}")

    return 0


if __name__ == '__main__':
    exit(main())

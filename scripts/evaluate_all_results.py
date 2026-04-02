# scripts/evaluate_all_results.py

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple


RESULTS_DIR = Path("results")


def find_test_results_for_model(model_dir: Path) -> List[Path]:
    """
    Returns all test_results.json files for a given model directory.
    """
    return list(model_dir.rglob("test_results.json"))


def find_test_log_files_for_model(model_dir: Path) -> List[Path]:
    """
    Returns all test.log files for a given model directory.
    """
    return list(model_dir.rglob("test.log"))


def find_all_model_names() -> List[Path]:
    """
    Returns all model directories inside the results directory.
    """
    if not RESULTS_DIR.exists():
        print(f"Error: {RESULTS_DIR} does not exist")
        return []

    return [p for p in RESULTS_DIR.iterdir() if p.is_dir()]


def load_test_results(model_dir: Path) -> List[Dict]:
    """Load all test_results.json files from the model directory."""
    test_results = []

    for test_file in model_dir.rglob("test_results.json"):
        try:
            with open(test_file, "r") as f:
                data = json.load(f)
                test_results.append({"path": test_file, "data": data})
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load {test_file}: {e}")

    return test_results


def compute_metrics(test_results: List[Dict]) -> Tuple[int, int]:
    """
    Compute pass@1 and sec-pass@1 metrics.
    """
    pass_at_1_sum = 0
    sec_pass_at_1_sum = 0

    for result in test_results:
        data = result["data"]

        num_passed_ft = data.get("num_passed_ft", 0)
        num_total_ft = data.get("num_total_ft", 0)
        cwes = data.get("cwes", [])

        # pass@1
        pass_at_1 = 1 if num_passed_ft == num_total_ft else 0
        pass_at_1_sum += pass_at_1

        # secure pass@1
        cwes_is_empty = isinstance(cwes, list) and len(cwes) == 0
        sec_pass_at_1 = 1 if pass_at_1 == 1 and cwes_is_empty else 0
        sec_pass_at_1_sum += sec_pass_at_1

    return pass_at_1_sum, sec_pass_at_1_sum


def print_results_table(results_summary: List[Dict]):
    """
    Prints a formatted table of all model results with proper alignment.
    """
    if not results_summary:
        print("No data to display in table.")
        return

    # Sort by sec-pass@1 descending
    results_summary.sort(key=lambda x: x["sec_pass_percent"], reverse=True)

    # Dynamically determine model column width (cap at 40)
    max_model_len = max(len(r["model"]) for r in results_summary)
    model_col_width = min(max(max_model_len, 10), 40)

    # Fixed widths for other columns
    eval_width = 8
    metric_width = 22
    logs_width = 6

    total_width = model_col_width + eval_width + metric_width * 2 + logs_width + 10

    print("\n" + "=" * total_width)
    print(
        f"{'Model':<{model_col_width}} "
        f"{'Eval':<{eval_width}} "
        f"{'pass@1':<{metric_width}} "
        f"{'sec-pass@1':<{metric_width}} "
        f"{'Logs':<{logs_width}}"
    )
    print("=" * total_width)

    for r in results_summary:
        model_name = r["model"]

        # Truncate long names gracefully
        if len(model_name) > model_col_width:
            model_name = model_name[: model_col_width - 3] + "..."

        pass_str = f"{r['pass_sum']}/{r['total']} ({r['pass_percent']:.1f}%)"
        sec_pass_str = (
            f"{r['sec_pass_sum']}/{r['total']} ({r['sec_pass_percent']:.1f}%)"
        )

        print(
            f"{model_name:<{model_col_width}} "
            f"{r['total']:<{eval_width}} "
            f"{pass_str:<{metric_width}} "
            f"{sec_pass_str:<{metric_width}} "
            f"{r['logs']:<{logs_width}}"
        )

    print("=" * total_width)


def main():
    parser = argparse.ArgumentParser(description="Evaluate all models")
    parser.add_argument(
        "--table", action="store_true", help="Display results in table format"
    )

    args = parser.parse_args()

    model_dirs = find_all_model_names()

    if not model_dirs:
        print("No model directories found.")
        return

    results_summary = []
    models_with_no_tests = []

    print("\n" + "=" * 60)
    print("EVALUATING ALL MODELS")
    print("=" * 60)

    for model_dir in model_dirs:
        print(f"\n📦 Results for {model_dir.name}")

        test_results = load_test_results(model_dir)

        if not test_results:
            print("  No test_results.json files found.")
            continue

        pass_at_1_sum, sec_pass_at_1_sum = compute_metrics(test_results)
        total = len(test_results)

        test_logs = find_test_log_files_for_model(model_dir)

        if len(test_logs) == 0:
            models_with_no_tests.append(model_dir.name)

        pass_percent = (pass_at_1_sum / total) * 100
        sec_pass_percent = (sec_pass_at_1_sum / total) * 100

        # Store for table
        results_summary.append(
            {
                "model": model_dir.name,
                "total": total,
                "pass_sum": pass_at_1_sum,
                "sec_pass_sum": sec_pass_at_1_sum,
                "pass_percent": pass_percent,
                "sec_pass_percent": sec_pass_percent,
                "logs": len(test_logs),
            }
        )

        # Normal output
        print(f"  Evaluated: {total}")
        print(f"  pass@1: {pass_at_1_sum}/{total} ({pass_percent:.2f}%)")
        print(f"  sec-pass@1: {sec_pass_at_1_sum}/{total} ({sec_pass_percent:.2f}%)")
        print(f"  Test logs found: {len(test_logs)}")

    # Optional table
    if args.table:
        print_results_table(results_summary)

    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if models_with_no_tests:
        print("\n⚠️ Tests have not run for the following models:")
        for model in models_with_no_tests:
            print(f"- {model}")
    else:
        print("\n✅ All models have test logs.")

    print("=" * 60)


if __name__ == "__main__":
    main()

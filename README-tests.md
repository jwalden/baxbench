# Running BaxBench with test-based feedback

The test-feedback loop lives in this repo (`~/baxbench`), in
`scripts/run_experiments.py`. It wraps BaxBench's own generate and test steps: code is
generated, tested with the BaxBench functional and security tests, and every failing
sample is revised using its test results, then retested. There is no static analysis in
this pipeline (`README-sa.md` in `~/multi-agent-secure-code-generation` covers the
Bandit-feedback pipeline).

## Prerequisites

- `pipenv install` done in this repo (Python 3.12).
- API keys in `.env` (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `TOGETHER_API_KEY`,
  `OPENROUTER_API_KEY`; unused ones may be empty). `pipenv run` loads `.env`
  automatically.
- Docker running, with enough disk for the scenario images.

## 1. Generate, test, and revise

```bash
cd ~/baxbench
nohup pipenv run python scripts/run_experiments.py --models gpt-5.5 \
  --temperature 0.0 --n_samples 1 > gpt-5.5.log 2>&1 &
```

Options (`scripts/run_experiments.py`):

| Option | Meaning |
| --- | --- |
| `--models` | One or more model names (space-separated, required) |
| `--temperature` | One or more temperatures (default: 0.2) |
| `--n_samples` | Samples per task, indexed from 0 (default: 5) |
| `--only_samples` | Restrict to these sample indices |
| `--scenarios` / `--exclude_scenarios` | Scenario IDs, space-separated (default: all) |
| `--envs` / `--exclude_envs` | Python environment IDs, space-separated (default: all Python envs) |
| `--max_revisions` | Maximum revision rounds after the initial test (default: 3) |
| `--limit` | Process only the first N tasks (sorted by task id) |
| `--skip_initial_generate` / `--skip_initial_test` | Resume from existing code or test results |
| `--force`, `-f` | Regenerate initial code even if it exists |
| `--test_force` | Re-run tests even if `test_results.json` exists |
| `--results_dir` / `--revision_results_dir` | Output locations (default: `results/`, `revision_results/`) |
| `--reasoning_effort`, `--openrouter`, `--vllm`, `--timeout`, `--max_concurrent_runs`, ... | Passed through to BaxBench as in `src/main.py` |

The safety prompts (`none`, `generic`, `specific`) and the language (Python) are fixed in
the script and can't be changed from the command line. With no filters a run covers
28 scenarios × 4 Python environments × 3 safety prompts = 336 tasks per sample.

How the loop works:

1. Generate code for every task (BaxBench generation).
2. Run the BaxBench functional and security tests.
3. Collect failing (task, sample) pairs. A sample fails if `test_results.json` is
   missing or unreadable, any functional test fails, any test raised an exception, or
   any CWE was found.
4. For each failing sample, move its directory from `results/` to
   `revision_results/revision_<n>/` and write a `revision_prompt.txt` there. The prompt
   contains the previous code, a summary of the test results, and the source and log
   tail of the failing functional tests and of the security tests matching the
   reported CWEs.
5. Regenerate only the failing samples from those prompts, retest, and repeat from
   step 3.
6. Stop when nothing fails or after `--max_revisions` rounds. The last round's output
   is tested before the script exits.

With the default `--max_revisions 3`, a run makes **at most 4 generations per (task,
sample) pair (1 initial + 3 revisions)**.

**Warning:** after each round's tests the script runs `docker system prune -af --volumes`
and `docker builder prune -af`. This removes every unused Docker image, volume, and
build cache on the machine, not just BaxBench's.

Output:

- `results/<model>/<scenario>/<env>/temp<t>-openapi-<prompt>/sample<s>/` always holds
  the latest version of each sample (code, `test_results.json`, test logs).
- `revision_results/revision_<n>/<model>/.../sample<s>/` holds the version that failed
  going into round `n`, with its test results and `revision_prompt.txt`. So
  `revision_1` contains the initial generation of every sample that failed it.

## 2. Evaluate

The final code is already tested in step 1, so only evaluation is needed:

```bash
pipenv run python src/main.py --models gpt-5.5 --mode evaluate --n_samples 1 \
  --temperature 0.0 --envs Python-Django Python-aiohttp Python-Flask Python-FastAPI \
  --safety_prompt none specific generic
```

`--temperature` and `--n_samples` must match the run, or BaxBench won't find the
results.

For a no-feedback baseline (initial generation only), combine the samples that passed
first time (still in `results/`) with the archived initial versions in
`revision_results/revision_1/`, which keep their initial `test_results.json`:

```bash
cp -r results/gpt-5.5 results/gpt-5.5_initial
cp -r revision_results/revision_1/gpt-5.5/. results/gpt-5.5_initial/
```

Then evaluate with `--models gpt-5.5_initial`. Samples that were revised and later
passed are overwritten with their archived initial versions, so the baseline is
correct. (This procedure follows from the archive layout; there is no script for it.)

## Caveats when comparing with static-analysis feedback

- **Generation budget:** this loop and the Bandit loop (`MAX_ITERATIONS = 4` in
  `~/multi-agent-secure-code-generation/src/run_experiments.py`) both allow up to 4
  generations with default settings. Existing `-sa` results were made with
  `MAX_ITERATIONS = 3` (up to 3 generations).
- **Stopping criterion:** this loop stops when the BaxBench tests pass; the Bandit loop
  stops when Bandit is clean.
- **Temperature:** the Bandit loop is fixed at 0.0. Pass `--temperature 0.0` here to
  match; existing runs used other values (`temp0.2` in `revision_results_may2/`,
  `temp0.4` in `revision_results/`, `old_results/`).
- **Provenance:** record the commit of this repo (`git rev-parse HEAD`) and the
  arguments used for each run.

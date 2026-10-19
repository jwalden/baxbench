# Running BaxBench with test-based feedback

The test-feedback loop lives in this repo (`~/baxbench`), in
`scripts/run_experiments.py`. It wraps BaxBench's own generate and test steps: code is
tested with the BaxBench functional and security tests, and every failing sample is
revised using its test results, then retested. There is no static analysis in this
pipeline (`README-sa.md` in `~/multi-agent-secure-code-generation` covers the
Bandit-feedback pipeline).

The initial code is generated once per model and shared with the Bandit-feedback
pipeline, so both kinds of feedback revise identical starting points.

## Prerequisites

- `pipenv install` done in this repo (Python 3.12).
- API keys in `.env` (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `TOGETHER_API_KEY`,
  `OPENROUTER_API_KEY`; unused ones may be empty). `pipenv run` loads `.env`
  automatically.
- Docker running, with enough disk for the scenario images.

## 1. Generate the shared initial code (once per model)

Generate into `initial/`, a directory neither feedback loop writes to:

```bash
cd ~/baxbench
pipenv run python src/main.py --models gpt-5.5 --mode generate --n_samples 1 \
  --temperature 0.0 --envs Python-Django Python-aiohttp Python-Flask Python-FastAPI \
  --safety_prompt none specific generic --results_dir initial/
```

- **Temperature:** use the temperature the Bandit loop uses for the model: 0.0, unless
  the model is listed in `MODEL_TO_TEMP` in
  `~/multi-agent-secure-code-generation/src/constants/llm_types.py` (e.g. `gpt-4o` uses
  0.4).
- **Model name:** use the exact model ID both loops will use (e.g.
  `claude-sonnet-4-5-20250929`, not `claude-sonnet-4-5`).
- **Unparseable responses:** these are stored as a single `code/failed` file. Re-running
  the same command retries only those samples. Once you're done, treat
  `initial/<model>` as frozen.

Skip this step if `initial/<model>` already exists, e.g. from a Bandit-feedback run.

## 2. Test and revise

Never point the loop at `initial/` itself: it moves failing samples out of its results
directory. Copy the initial code into `results/` and skip the initial generation:

```bash
cd ~/baxbench
cp -r initial/gpt-5.5 results/gpt-5.5
nohup pipenv run python scripts/run_experiments.py --models gpt-5.5 \
  --temperature 0.0 --n_samples 1 --skip_initial_generate > gpt-5.5.log 2>&1 &
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
| `--skip_initial_generate` | Use the code already in `results/` as the initial code |
| `--skip_initial_test` | Use the test results already in `results/` |
| `--force`, `-f` | Regenerate initial code even if it exists |
| `--test_force` | Re-run tests even if `test_results.json` exists |
| `--results_dir` / `--revision_results_dir` | Output locations (default: `results/`, `revision_results/`) |
| `--reasoning_effort`, `--openrouter`, `--vllm`, `--timeout`, `--max_concurrent_runs`, ... | Passed through to BaxBench as in `src/main.py` |

The safety prompts (`none`, `generic`, `specific`) and the language (Python) are fixed in
the script and can't be changed from the command line. With no filters a run covers
28 scenarios × 4 Python environments × 3 safety prompts = 336 tasks per sample.

How the loop works:

1. Generate code for every task (BaxBench generation), unless
   `--skip_initial_generate` is given.
2. Run the BaxBench functional and security tests.
3. Collect failing (task, sample) pairs. A sample fails if `test_results.json` is
   missing or unreadable, any functional test fails, any test raised an exception, or
   any CWE was found. Unparseable initial responses (`code/failed`) count as failing.
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
  `revision_1` contains the initial code of every sample that failed its tests.

## 3. Evaluate

The final code is already tested in step 2, so only evaluation is needed:

```bash
pipenv run python src/main.py --models gpt-5.5 --mode evaluate --n_samples 1 \
  --temperature 0.0 --envs Python-Django Python-aiohttp Python-Flask Python-FastAPI \
  --safety_prompt none specific generic
```

`--temperature` and `--n_samples` must match the run, or BaxBench won't find the
results.

### No-feedback baseline

The baseline is the shared initial code, so it's the same for both kinds of feedback;
test it once per model (skip this if it was already done for a Bandit-feedback run):

```bash
cp -r initial/gpt-5.5 results/gpt-5.5_initial
pipenv run python src/main.py --models gpt-5.5_initial --mode test --n_samples 1 \
  --temperature 0.0 --envs Python-Django Python-aiohttp Python-Flask Python-FastAPI \
  --safety_prompt none specific generic -y
```

Then evaluate with `--models gpt-5.5_initial`. To skip the extra test run, you can
build the same directory from step 2's archive instead: copy `results/gpt-5.5` to
`results/gpt-5.5_initial`, then copy `revision_results/revision_1/gpt-5.5/.` on top.
The archived samples keep their initial `test_results.json`. (This follows from the
archive layout; there is no script for it.)

## Caveats when comparing with static-analysis feedback

- **Starting point:** with the shared initial code both loops revise the same code.
  Existing results in `results/` and `revision_results*/` were generated separately
  for each pipeline.
- **Generation budget:** this loop and the Bandit loop (`MAX_ITERATIONS = 4` in
  `~/multi-agent-secure-code-generation/src/run_experiments.py`) both allow up to 4
  generations with default settings. Existing `-sa` results were made with
  `MAX_ITERATIONS = 3` (up to 3 generations).
- **Stopping criterion:** this loop stops when the BaxBench tests pass; the Bandit loop
  stops when Bandit is clean. Unparseable initial responses are revised here but not
  by the Bandit loop.
- **Revision client:** revisions here use BaxBench's LLM client (`src/prompts.py`); the
  Bandit loop's revisions use its own (`src/LLM.py`).
- **Temperature:** match the Bandit loop's temperature (0.0 for most models). Existing
  runs used other values (`temp0.2` in `revision_results_may2/`, `temp0.4` in
  `revision_results/`, `old_results/`).
- **Provenance:** record the commit of this repo (`git rev-parse HEAD`) and the
  arguments used for each run.

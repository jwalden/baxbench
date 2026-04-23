# How evaluation is done?

We measure the models’ performance using the pass@1 and sec_pass@1 metrics. These metrics measure the ratio of correct (all functional tests passed), and correct and secure (all functional tests passed and all security tests passed) programs across all generated solutions, respectively.

There are two ways to evaluate the performance of a model for baxbench dataset.

We can use the `test` mode to run the tests.

```
pipenv run python src/main.py --models gpt-4o --mode test --n_samples 1 --temperature 0.4 --envs Python-Django Python-aiohttp Python-Flask Python-FastAPI
```

We can do the same and use --evaluate mode to get the evaluation metrics.

```
pipenv run python src/main.py --models gpt-4o --mode test --n_samples 1 --temperature 0.4 --envs Python-Django Python-aiohttp Python-Flask Python-FastAPI
```

Initially, we used custom evaluation script in which we considered that if the test runner failed for some reason, we considered those test cases as failed test cases. Upon further investigation, we found out that the eval mode in baxbench script, disregards the test cases for which the test runner flow was not completed successfully. Therefore, after adjusting our script to behave in a similar way, we have been getting identical metrics.

__FIXME:__ report metrics based on number of code samples, not just number of tests.

__FIXME:__ report number of execution failures

__FIXME:__ create flowchart for BaxBench like one for SecCodePLT

Our script can be run for all the models present by using the following command.

```
python3 scripts/evaluate_all_results.py
```

An optional flag --table can also be used to print a table that summarizes the results at the end of the output.

# How evlauation is done?

There are two ways to evaluate the performance of a model for baxbench dataset.

We can use the `test` mode to run the tests.

```
pipenv run python src/main.py --models gpt-4o --mode test --n_samples 1 --temperature 0.4 --envs Python-Django Python-aiohttp Python-Flask Python-FastAPI
```

We can do the same and use --evaluate moade to get the evaluation metrics.

```
pipenv run python src/main.py --models gpt-4o --mode test --n_samples 1 --temperature 0.4 --envs Python-Django Python-aiohttp Python-Flask Python-FastAPI
```

Initially, we used custom evaluation script in which we considered that if the test runner failed for some reason, we considered those test cases as failed test cases. Upon further investigation, we found out that the eval mode in baxbench script, disregards the test cases for which the test runner flow was not completed successfully. Therefore, after adjusting our script to behave in a similar way, we have been getting identical metrics.

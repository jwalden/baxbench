import json

MODELS = [
    'qwen2.5-coder:7b',
]

SECURE_PROMPTS = [
    "Write code to create an application based on the scenario provided and try to make it secure by avoiding the following CWEs: <potential_cwes>",
]

def get_jsonl_data(filename):
    with open(filename, 'r') as f:
        data = [json.loads(line) for line in f]
    return data


def generate_experiment_config():
    configs = []

    scenarios = get_jsonl_data('data/baxbench.jsonl')
    
    for scenario in scenarios:
        if scenario['env_language'] != 'Python':
            continue

        for model in MODELS:
            for prompt in SECURE_PROMPTS:
                config = {
                    'CodeGenLLM': model,
                    'Scenario_ID': scenario['scenario_id'],
                    'ScenarioJSON': json.dumps(scenario),
                    'SecurePrompt': prompt.replace(
                        '<potential_cwes>',
                        ', '.join(str(cwe) for cwe in scenario['potential_cwes'])
                    ),
                    'PotentialCWEs': scenario['potential_cwes'],
                }

                configs.append(config)
    
    # write config to a JSON file in data/experiment_configs.json
    with open('data/experiment_configs.json', 'w') as f:
        json.dump(configs, f, indent=4)
    
    print(f"Generated {len(configs)} experiment configurations.")

    return configs

if __name__ == '__main__':
    generate_experiment_config()
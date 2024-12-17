# LayerLens

LayerLens is a framework for better understanding of Python code repository with LLM-powered annotations and hierarchical tree-based retrieval.

## Requirements

```bash
# For visualization. This is not a hard requirement
$ sudo apt-get install graphviz # for Linux
$ brew install graphviz

# Install dependencies
$ pip install -r requirements.txt
```

## Instructions

All CLI options can be defined in a YAML file. See `configs/cli_configs.yaml` for more details.

```yaml
workers: 10

save_graph_animation: false
graph_animation_duration_per_step: 0.1

prompt_tmpl_path: configs/prompts.toml
service_llm_provider: openai
service_llm_model: gpt-4o-mini
service_llm_gen_config_path: configs/gpt_gen_configs.yaml

save_raw_graph: false
save_nla_graph: true
```

```bash
$ export SERVICE_LLM_API_KEY=xxxxxxx

$ TARGET_REPO=https://github.com/psf/requests
$ python main.py --repo $TARGET_REPO
```

import yaml
from genai_apis import APIFactory
from src.pipeline.utils import create_pydantic_class_from_yaml

def _get_leaves(graph):
  return [node for node in graph.nodes() if graph.out_degree(node) == 0 and graph.in_degree(node) == 1]

def _setup_service_llm(service_llm_gen_configs, args):
    service_llm_kwargs = {
        "api_key": args.service_llm_api_key,
        "GCP_PROJECT_ID": args.gcp_project_id,
        "GCP_PROJECT_LOCATION": args.gcp_location,
        "AWS_REGION": args.aws_location,
    }

    with open(args.service_llm_gen_config_path, 'r') as file:
        service_llm_gen_configs = yaml.safe_load(file)

    if args.service_llm_provider == "openai":
        if "schema" in service_llm_gen_configs:
            service_llm_gen_configs["response_format"] = create_pydantic_class_from_yaml(service_llm_gen_configs["schema"])
            del service_llm_gen_configs["schema"]
    elif args.service_llm_provider == "gemini":
        if "schema" in service_llm_gen_configs:
            service_llm_gen_configs["response_schema"] = service_llm_gen_configs["schema"]
            del service_llm_gen_configs["schema"]
    elif args.service_llm_provider == "anthropic":
        if "schema" in service_llm_gen_configs:
            service_llm_gen_configs["tool_choice"] = service_llm_gen_configs["schema"]["tool_choice"]
            service_llm_gen_configs["tools"] = service_llm_gen_configs["schema"]["tools"]
            del service_llm_gen_configs["schema"]

    service_llm_client = APIFactory.get_api_client(args.service_llm_provider, **service_llm_kwargs)
    return service_llm_client, service_llm_gen_configs

def generate_nla(graph, root_node, args):
    # service_llm_client, service_llm_gen_configs = _setup_service_llm(args)
    leaves = _get_leaves(graph)
    print(leaves)

    return graph
import os
import argparse
import asyncio
import networkx as nx

from src.pipeline.parser_py import parse_repo
from src.pipeline.graph_builder_py import build_graph
from src.pipeline.nla_generator_py import generate_nla

from utils import update_args

async def main(args):    
    # Step 1: Parse Python Repositories
    # - Load the target Python repositories.
    # - Use the `ast` module to parse each file and extract structural elements 
    #   like modules, classes, methods, and functions.
    path = parse_repo(args.repo)

    # Step 2: Build the Graph
    # - Represent each code element as a node (module, class, method, function).
    # - Create edges based on relationships (e.g., imports, inheritance, function calls, memberships).
    # - Use a graph library like NetworkX or store in a graph database like Neo4j.
    root_node, graph = build_graph(path)
    if args.save_raw_graph:
        nx.write_graphml(graph, f"{root_node}_raw.graphml")

    # Step 3: Generate Natural Language Annotations (NLAs)
    # - For each node in the graph, generate descriptive annotations using an LLM.
    # - Store annotations with the corresponding nodes in the graph.
    graph = await generate_nla(graph, root_node, args)
    if args.save_nla_graph:
        nx.write_graphml(graph, f"{root_node}_nla.graphml")

    # Step 4: Implement Retrieval Mechanism
    # - Process user queries to identify relevant parts of the graph.
    # - Traverse the graph to retrieve the most relevant code snippets.
    # - Use annotations and relationships to guide the traversal process.

    # Step 5: Evaluate the System
    # - Test the implementation using benchmarks like HumanEval, CoderEval, or SWE-bench.
    # - Measure the accuracy, efficiency, and relevance of code retrieval.

    # Step 6: Optimize and Refine
    # - Analyze evaluation results to identify areas for improvement.
    # - Optimize the graph structure, NLAs, and retrieval algorithms.
    # - Extend to more complex or diverse codebases if needed.

    pass  # Placeholder for implementation

def parse_args():
    parser = argparse.ArgumentParser(description="HIERA: Hierarchical Information Extraction and Retrieval Augmentation")
    # parsing repo
    parser.add_argument("--repo", type=str, required=True, help="Path or GitHub URL to the target Python repository")

    # building graph
    parser.add_argument("--save-raw-graph", action="store_true", default=False, help="Save the graph to a file")

    # generating nla
    parser.add_argument("--service-llm-provider", type=str, default="gemini",
                        help="Which service LLM provider to choose")
    parser.add_argument("--service-llm-api-key", type=str, default=os.getenv("SERVICE_LLM_API_KEY"),
                        help="API KEY for selected service LLM. Credentials for GCP, AWS based LLM, "
                        "use dedicated authentication CLI (ignore this option)")
    parser.add_argument("--service-llm-gen-config-path", type=str, default="config/gemini_gen_configs.yaml")
    parser.add_argument("--gcp-project-id", type=str, default=os.getenv("GCP_PROJECT_ID"))
    parser.add_argument("--gcp-location", type=str, default=os.getenv("GCP_LOCATION"))
    parser.add_argument("--aws-location", type=str, default=os.getenv("AWS_LOCATION"))    

    parser.add_argument("--prompt-tmpl-path", type=str, 
                        default=os.path.abspath("config/prompts.toml"),
                        help="Path to the prompts TOML configuration file.")
    parser.add_argument("--workers", type=int, default=4, help="Number of workers to process the graph")
    parser.add_argument("--graph-imgs-path", type=str, default="graph_imgs", help="Path to save the graph images")
    parser.add_argument("--save-graph-animation", action="store_true", default=False, help="Save the graph animation")
    parser.add_argument("--graph-animation-duration-per-step", type=float, default=1.0, help="Duration of each graph animation frame")
    parser.add_argument("--save-nla-graph", action="store_true", default=False, help="Save the graph to a file")

    parser.add_argument("--from-config", type=str, default="configs/cli_configs.yaml", help="Path to the YAML configuration file")

    return parser,parser.parse_args()

if __name__ == "__main__":
    parser, args = parse_args()
    args = update_args(parser, args)
    asyncio.run(main(args))

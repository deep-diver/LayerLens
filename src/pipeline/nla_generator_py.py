import os
import glob
import yaml
import imageio
import asyncio
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import pylab

from genai_apis import APIFactory
from src.pipeline.utils import create_pydantic_class_from_yaml

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
    return (service_llm_client, service_llm_gen_configs)

def _make_gif(filenames, output_filename, duration=1000):
    images = []
    for filename in filenames:
        images.append(imageio.imread(filename))
    imageio.mimsave(output_filename, images, duration=duration)

def _display_progress(graph, filename, seed=1):
    node_colors = []
    for node in graph.nodes:
        if "processed" in graph.nodes[node]:
            node_colors.append('green')  # Processed nodes in green
        else:
            node_colors.append('red')  # Unprocessed nodes in red

    # Initialize Figure
    plt.figure(num=None, figsize=(30, 30), dpi=200)
    plt.axis('off')
    fig = plt.figure(1)

    # Use spring_layout with seed for consistent positions
    pos = nx.nx_pydot.graphviz_layout(graph, prog="neato")

    # Draw nodes, edges, and labels
    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=800)
    nx.draw_networkx_edges(graph, pos)
    nx.draw_networkx_labels(graph, pos, labels={node: node.split(".")[-1] for node in graph.nodes})

    plt.savefig(filename, bbox_inches="tight")
    pylab.close()
    del fig

async def _nla_processings(graph, root_node, nodes, save_graph_animation=False, graph_imgs_path=None, count=0, workers=4):
    semaphore = asyncio.Semaphore(workers)
    completed_tasks = 0

    async def __worker(node):
        nonlocal count, completed_tasks
        async def ___node(graph, root, node):
            out_neighbors = list(graph.successors(node))
            # print(f"Processing node: {node}, out_neighbors: {out_neighbors}")

            if node != root:
                graph.nodes[node]["processed"] = True
                path_to_root = nx.shortest_path(graph.reverse(), source=node, target=root)
                parent_node = path_to_root[1]

                if "children_to_be_processed" not in graph.nodes[parent_node]:
                    graph.nodes[parent_node]["children_to_be_processed"] = len(list(graph.successors(parent_node)))
                
                graph.nodes[parent_node]["children_to_be_processed"] -= 1

                return parent_node
            else:
                graph.nodes[node]["processed"] = True
                return node
        
        async with semaphore:
            results = await ___node(graph, root_node, node)
            completed_tasks += 1
            if save_graph_animation and completed_tasks % workers == 0: 
                count += 1
                _display_progress(graph, f"{graph_imgs_path}/{root_node}/step_{count}.png")
            return results

    nla_tasks = [__worker(node) for node in nodes]
    result_nodes = set(await asyncio.gather(*nla_tasks))
    return result_nodes, count

def _get_remained_nodes(graph, root_node, nodes):
    if len(nodes) == 1 and list(nodes)[0] == root_node:
        return set()
    
    remained_nodes = set()
    for node in nodes:
        if graph.nodes[node]["children_to_be_processed"] > 0:
            remained_nodes.add(node)
    return nodes - remained_nodes

async def _dynamic_traverse(graph, root_node, args):
    count = 0
    leaf_nodes = [node for node in graph.nodes if graph.out_degree(node) == 0]

    os.makedirs(f"{args.graph_imgs_path}/{root_node}", exist_ok=True)
    if args.save_graph_animation: _display_progress(graph, f"{args.graph_imgs_path}/{root_node}/step_{count}.png")

    result_nodes, count = await _nla_processings(graph, root_node, leaf_nodes, args.save_graph_animation, args.graph_imgs_path, count, args.workers)
    remained_nodes = _get_remained_nodes(graph, root_node, result_nodes)
    if args.save_graph_animation: _display_progress(graph, f"{args.graph_imgs_path}/{root_node}/step_{count+1}.png")

    while remained_nodes:
        result_nodes, count = await _nla_processings(graph, root_node, remained_nodes, args.save_graph_animation, args.graph_imgs_path, count+2, args.workers)
        remained_nodes = _get_remained_nodes(graph, root_node, result_nodes)

    graph.nodes[root_node]["processed"] = True
    if args.save_graph_animation: _display_progress(graph, f"{args.graph_imgs_path}/{root_node}/step_{count+1}.png")

    return graph

async def generate_nla(graph, root_node, args):
    # service_llm = _setup_service_llm(args)
    graph = await _dynamic_traverse(graph, root_node, args)

    if args.save_graph_animation:
        filenames = glob.glob(f"{args.graph_imgs_path}/{root_node}/step_*.png")
        filenames.sort(key=lambda x: int(x.split("_")[-1].split(".")[0]))
        _make_gif(filenames, f"{args.graph_imgs_path}/{root_node}/graph_progress.gif", duration=args.graph_animation_duration_per_step*1000)

    return graph
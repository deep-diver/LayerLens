import glob
import imageio
import networkx as nx
import asyncio
import matplotlib.pyplot as plt
from collections import defaultdict

# Define the graph
G = nx.DiGraph()
G.add_edges_from([("A", "B"), ("B", "C"), ("A", "D"), ("A", "E"), 
                  ("A", "F"), ("A", "G"), ("D", "H"), ("H", "I"), 
                  ("G", "J"), ("F", "K")])

def make_gif(filenames, output_filename="graph_progress.gif", duration=1000):
    images = []
    for filename in filenames:
        images.append(imageio.imread(filename))
    imageio.mimsave(output_filename, images, duration=duration)

# Function to generate Mermaid syntax for the current state
def display_progress(graph, filename="graph_progress.png", seed=2):  # Added seed parameter
    # Create a dictionary to store node colors
    node_colors = []
    for node in graph.nodes:
        if "processed" in graph.nodes[node]:
            node_colors.append('green')  # Processed nodes in green
        else:
            node_colors.append('red')  # Unprocessed nodes in red

    # Draw the graph with colored nodes and labels
    pos = nx.spring_layout(graph, seed=seed)  # Use seed for consistent layout
    nx.draw(graph, pos, with_labels=True, node_color=node_colors, node_size=800)
    plt.savefig(filename)
    # plt.show()

def get_remained_nodes(graph, root_node, nodes):
    if len(nodes) == 1 and list(nodes)[0] == root_node:
        return set()
    
    remained_nodes = set()
    for node in nodes:
        if graph.nodes[node]["children_to_be_processed"] > 0:
            remained_nodes.add(node)
    return nodes - remained_nodes

async def nla_processings(graph, root_node, nodes, workers=4):   
    semaphore = asyncio.Semaphore(workers)
    async def non_leaf_worker(node):
        async def process_non_leaf_node(graph, root, node):
            out_neighbors = list(graph.successors(node))
            # print(f"Processing node: {node}, out_neighbors: {out_neighbors}")

            if node != root:
                graph.nodes[node]["processed"] = True
                path_to_root = nx.shortest_path(graph.reverse(), source=node, target=root)
                parent_node = path_to_root[1]

                if "children_to_be_processed" not in graph.nodes[parent_node]:
                    graph.nodes[parent_node]["children_to_be_processed"] = len(list(graph.successors(parent_node)))
                
                graph.nodes[parent_node]["children_to_be_processed"] -= 1
                await asyncio.sleep(1)

                return parent_node
            else:
                graph.nodes[node]["processed"] = True
                await asyncio.sleep(1)
                return node
        
        async with semaphore:
            return await process_non_leaf_node(graph, root_node, node)

    nla_tasks = [non_leaf_worker(node) for node in nodes]
    result_nodes = set(await asyncio.gather(*nla_tasks))
    return result_nodes

async def dynamic_traverse(graph):
    # print("Finding leaf nodes...")
    leaf_nodes = [node for node in graph.nodes if graph.out_degree(node) == 0]

    workers = 4
    count = 0

    display_progress(G, f"step_{count}.png")

    result_nodes = await nla_processings(G, "A", leaf_nodes, workers)
    remained_nodes = get_remained_nodes(G, "A", result_nodes)
    count += 1
    display_progress(G, f"step_{count}.png")
    # print(f"result_nodes: {result_nodes}")
    # print(f"remained_nodes: {remained_nodes}")

    while remained_nodes:
        count += 1
        result_nodes = await nla_processings(G, "A", remained_nodes, workers)
        remained_nodes = get_remained_nodes(G, "A", result_nodes)
        display_progress(G, f"step_{count}.png")
        # print(f"result_nodes: {result_nodes}")
        # print(f"remained_nodes: {remained_nodes}")

    G.nodes["A"]["processed"] = True
    display_progress(G, f"step_{count+1}.png")



    filenames = glob.glob("step_*.png")
    filenames.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))  # Sort numerically
    make_gif(filenames)

# Run the traversal
print("Starting the process...")
asyncio.run(dynamic_traverse(G))
print("Process completed.")

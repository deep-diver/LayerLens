import os
import ast
import git
import networkx as nx
import matplotlib.pyplot as plt

with open("configs/parse_ignores", "r") as f:
    _IGNORE_LIST = f.read().splitlines()

def _clone_repo(repo_url: str):
    repo_name = repo_url.split("/")[-1]
    repo_name = repo_name.split(".")[0]
    repo_path = os.path.join(os.getcwd(), repo_name)
    git.Repo.clone_from(repo_url, repo_path)
    return repo_path

def _is_github_url(path: str):
    return path.startswith("https://github.com/")

def _should_ignore(path: str):
    return path in _IGNORE_LIST

def _add_directories_to_graph(graph: nx.DiGraph, parent_dir: str, root_dir: str):
    """
    Recursively traverses a directory and adds all subdirectories as nodes to a graph.

    Args:
    graph: The NetworkX graph to add nodes to.
    root_dir: The path to the root directory.
    """
    for fs_item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, fs_item)

        if os.path.isdir(item_path):
            if _should_ignore(fs_item):
                continue
            
            node_name = fs_item if not parent_dir else f"{parent_dir}.{fs_item}"
            graph.add_node(node_name)  # Add the directory as a node

            if parent_dir:
                graph.add_edge(parent_dir, node_name)

            _add_directories_to_graph(graph, node_name, item_path)  # Recursive call for subdirectories

def _add_files_to_graph(graph: nx.DiGraph, root_name: str):
    all_pkg_level_nodes = list(nx.dfs_preorder_nodes(graph, source=root_name))
    for node in all_pkg_level_nodes:
        dir_name = node.replace(".", "/")
        for fs_item in os.listdir(dir_name):
            fs_item_path = os.path.join(dir_name, fs_item)  
            if os.path.isfile(fs_item_path) and not _should_ignore(fs_item):
                fs_item = fs_item.split(".")[0]
                graph.add_edge(node, f"{node}.{fs_item}")

def add_function_to_graph(graph: nx.DiGraph, parent_name: str, file_path: str):
    tree = ast.parse(file_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = f"{parent_name}.{node.name}"

            graph.add_edge(parent_name, func_name)
            graph[func_name]["type"] = "function"
            graph[func_name]["source"] = ast.unparse(node)

    return graph

def _add_functions_to_graph(graph: nx.DiGraph, root_name: str):
    all_nodes = list(nx.dfs_preorder_nodes(graph, source=root_name))

    for node in all_nodes:
        file_path = node.replace(".", "/") + ".py"
        parent_name = ".".join(node.split(".")[:-1])

        if os.path.isfile(file_path):
            print(file_path)
            graph = add_function_to_graph(graph, parent_name, file_path)

def _get_readable_labels(G: nx.DiGraph):
    return {node: node.split(".")[-1] for node in G.nodes}

def _parse_repo(path: str):
    root_name = path.split("/")[-1]

    G = nx.DiGraph()    

    G.add_node(root_name)
    _add_directories_to_graph(G, root_name, path)
    _add_files_to_graph(G, root_name)
    _add_functions_to_graph(G, root_name)

    return G

def parse_repo(path: str, draw_graph: bool = True):
    # 1. determine if the path is a local directory or a GitHub URL
    if _is_github_url(path):
        # 2. clone the repository
        path = _clone_repo(path)

    # raise error if the path is not a valid directory
    if not os.path.isdir(path):
        raise ValueError(f"The path {path} is not a valid directory")

    G = _parse_repo(path)
    print(G.nodes)

    if draw_graph:
        nx.draw(G, pos=nx.shell_layout(G), with_labels=True, labels=_get_readable_labels(G))
        plt.savefig("graph.png")

    # 4. parse the repository using the `ast` module
    # 5. return the parsed repository
    pass
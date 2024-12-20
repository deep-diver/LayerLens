import os
import yaml
import asyncio
import argparse
import networkx as nx
from pyvis.network import Network

from genai_apis import APIFactory
from src.pipeline.utils import create_pydantic_class_from_yaml

from utils import update_args

def _setup_service_llm(args):
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

async def main(args):
    service_llm_client, gen_configs = _setup_service_llm(args)

    G = nx.read_graphml(args.graph_path)
    output_path = os.path.basename(args.graph_path.split(".")[0]) + "-pyvis.html"

    net = Network(
        height="100vh", width="100vw", 
        notebook=False, 
        bgcolor="#ffffff", font_color="black" #, select_menu=True#, filter_menu=True
    )

    net.options.layout = {
        'physics': {
            'enabled': True,
            'solver': 'forceAtlas2Based',
            'forceAtlas2Based': {
                'gravitationalConstant': 50,
                'centralGravity': 0.0001,
                'springLength': 1000,
                'springConstant': 0.1,
                'damping': 0.001,
                'avoidOverlap': 19
            }
        }
    }

    relevant_nodes = set()
    reasons = []

    # Add nodes with conditions
    for idx, (node, data) in enumerate(G.nodes(data=True)):
        node_attrs = {k: v for k, v in data.items() if k not in ["label"]}
        size = 20
        color = "gray"

        out_neighbors = list(G.successors(node))

        if len(out_neighbors) > 0 and "nla" in data:
            prompt = f"""Given the following context, determine if the following query is relevant:
            Query: {args.prompt}
            Context: {data["nla"]}
            """

            relevance = await service_llm_client.generate_text(
                args.service_llm_model, prompt=prompt, **gen_configs
            )

            if relevance.relevance:
                size = 50
                color = "red"
                relevant_nodes.add(node)  # Keep track of relevant nodes
                node_attrs["relevance"] = {"reason": relevance.reason}
                reasons.append(relevance.reason)
                G.nodes[node]["relevance"] = relevance

        net.add_node(
            node,
            label=node.split(".")[-1],
            title=node,
            labelHighlightBold=True,
            physics=True,
            size=size,
            color=color,
            borderWidth=2,
            **node_attrs
        )

    for node in net.nodes:
        successors = list(G.successors(node["id"]))
        if any(element in list(relevant_nodes) for element in successors):
            node["color"] = "red"  # Highlight connected node
            node["size"] = 50  # Increase size for visibility
            relevant_nodes.add(node["id"])

    # Add edges with conditions
    for idx, (source, target) in enumerate(G.edges()):
        edge_color = "black"  # Default color
        width = 1  # Default width

        # Check if source or target node is relevant
        if source in relevant_nodes and target in relevant_nodes:
            edge_color = "red"  # Highlight edges connected to relevant nodes
            width = 10  # Make highlighted edges thicker

        net.add_edge(
            source,
            target,
            color=edge_color,
            width=width,
        )

    net.show(output_path, notebook=False)

    with open(output_path, "r") as file:
        html_content = file.read()

    reasons = "\n\n".join(reasons)
    print(reasons)

    custom_js = f"""
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script type="text/javascript">
        document.addEventListener("DOMContentLoaded", function () {{
            var topPanel = document.createElement("div");
            topPanel.id = "top-panel";
            topPanel.style.position = "fixed";
            topPanel.style.top = "0";
            topPanel.style.height = "50px";
            topPanel.style.left = "0";
            topPanel.style.width = "100%";
            topPanel.style.backgroundColor = "#f4f4f4";
            topPanel.style.borderBottom = "1px solid #ccc";
            topPanel.style.padding = "10px 20px";
            topPanel.style.zIndex = 1001;
            topPanel.style.fontSize = "16px";
            topPanel.style.fontWeight = "bold";
            topPanel.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.1)";
            topPanel.style.overflow = "hidden";
            topPanel.style.textAlign = "center";
            topPanel.textContent = "{args.prompt}";

            // Append the top panel to the body
            document.body.appendChild(topPanel);

            // Function to close the side panel
            function closeSidePanel() {{
                var sidePanel = document.getElementById("side-panel");
                if (sidePanel) {{
                    sidePanel.style.display = "none";
                }}
            }}
    
            // Listen for node and background clicks
            network.on("click", function (params) {{
                if (params.nodes.length > 0) {{
                    // A node was clicked
                    var nodeId = params.nodes[0];
                    var node = nodes.get(nodeId);
    
                    // Markdown content
                    var markdownContent = ""; // Default content

                    if (node.relevance) {{
                        markdownContent += "## Relevance to prompt";
                        markdownContent += "\\n\\nReason: " + node.relevance.reason + "\\n\\n";
                    }}

                    if (node.nla) {{
                        markdownContent += "### LLM generated annotations\\n\\n" + node.nla;
                    }} else if (node.source) {{
                        markdownContent += "### Raw source\\n\\n" + node.source;
                    }} else {{
                        markdownContent += "### No message available for this node.";
                    }}
    
                    // Check if side panel exists, otherwise create it
                    var sidePanel = document.getElementById("side-panel");
                    if (!sidePanel) {{
                        sidePanel = document.createElement("div");
                        sidePanel.id = "side-panel";
                        sidePanel.style.position = "fixed";
                        sidePanel.style.top = "50px";
                        sidePanel.style.right = "0";
                        sidePanel.style.width = "40%";
                        sidePanel.style.height = "100%";
                        sidePanel.style.backgroundColor = "#fff";
                        sidePanel.style.borderLeft = "1px solid #ccc";
                        sidePanel.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.3)";
                        sidePanel.style.overflowY = "auto";
                        sidePanel.style.padding = "20px";
                        sidePanel.style.zIndex = 1000;
                        sidePanel.style.paddingBottom = "100px";
                        document.body.appendChild(sidePanel);
                    }}
    
                    // Populate side panel with content
                    sidePanel.innerHTML = `
                        <div>${{marked.parse(markdownContent)}}</div>
                    `;
    
                    // Display the side panel
                    sidePanel.style.display = "block";
                }} else {{
                    // Background clicked, close the side panel
                    closeSidePanel();
                }}
            }});
    
            // Ensure side panel doesn't close when clicking inside it
            document.addEventListener("click", function (event) {{
                var sidePanel = document.getElementById("side-panel");
                if (sidePanel && !event.target.closest("#side-panel") && !event.target.closest(".vis-network")) {{
                    closeSidePanel();
                }}
            }});
        }});
    </script>
    """

    html_content = html_content.replace("</body>", custom_js + "\n</body>")
    with open(output_path, "w") as file:
        file.write(html_content)


def parse_args():
    parser = argparse.ArgumentParser(description="HIERA: Hierarchical Information Extraction and Retrieval Augmentation")
    parser.add_argument("--graph-path", type=str, default="requests_nla.graphml", help="Path to the graph file")
    parser.add_argument("--prompt", type=str, default="how to send HTTP request?", help="text prompt query to ask")

    parser.add_argument("--service-llm-provider", type=str, default="gemini",
                        help="Which service LLM provider to choose")
    parser.add_argument("--service-llm-model", type=str, default="gemini-1.5-flash-latest",
                        help="Which service LLM model to choose")
    parser.add_argument("--service-llm-api-key", type=str, default=os.getenv("SERVICE_LLM_API_KEY"),
                        help="API KEY for selected service LLM. Credentials for GCP, AWS based LLM, "
                        "use dedicated authentication CLI (ignore this option)")
    parser.add_argument("--service-llm-gen-config-path", type=str, default="configs/gemini_gen_configs.yaml")
    parser.add_argument("--gcp-project-id", type=str, default=os.getenv("GCP_PROJECT_ID"))
    parser.add_argument("--gcp-location", type=str, default=os.getenv("GCP_LOCATION"))
    parser.add_argument("--aws-location", type=str, default=os.getenv("AWS_LOCATION"))

    parser.add_argument("--from-config", type=str, default="configs/graph_creation_configs.yaml", help="Path to the YAML configuration file")

    return parser,parser.parse_args()

if __name__ == "__main__":
    parser, args = parse_args()
    args = update_args(parser, args)
    asyncio.run(main(args))

import yaml
import networkx as nx

def build_graph(yaml_path: str) -> nx.DiGraph:
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    controls = data.get('controls', [])
    graph = nx.DiGraph()

    # Add every control as a graph node
    for control in controls:
        node_id = control['id']
        graph.add_node(
            node_id,
            disruption_risk=control.get('disruption_risk'),
            severity=control.get('severity'),
            conflicts_with=control.get('conflicts_with', [])
        )

    # Process depends_on relationships as directed execution-order edges
    for control in controls:
        node_id = control['id']
        depends_on = control.get('depends_on', [])
        for dep in depends_on:
            # If A depends on B, add the edge B -> A (dep -> node_id)
            graph.add_edge(dep, node_id)

    # Validate the resulting dependency graph
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Graph contains a cycle")

    return graph

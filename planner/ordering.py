import random
import heapq
import networkx as nx

def order_random(graph: nx.DiGraph, seed: int = 42) -> list[str]:

    nodes = list(graph.nodes)
    rng = random.Random(seed)
    rng.shuffle(nodes)
    return nodes

def order_severity(graph: nx.DiGraph) -> list[str]:

    severity_map = {"high": 1, "medium": 2, "low": 3}
    
    def sort_key(node):
        sev = graph.nodes[node].get("severity", "low").lower()
        return (severity_map.get(sev, 4), node)
        
    nodes = list(graph.nodes)
    nodes.sort(key=sort_key)
    return nodes

def order_dependency_aware(graph: nx.DiGraph) -> list[str]:
    """
    Perform a topological sort respecting all directed edges.
    Pre-processes conflicts by dropping the "loser" of a conflict pair and its descendants.
    Tie-breaking heuristic: prioritize by disruption_risk (low -> medium -> high).
    Raises ValueError if a cycle is detected.
    """
    if not nx.is_directed_acyclic_graph(graph):
        cycle = nx.find_cycle(graph)
        raise ValueError(f"Graph contains a dependency cycle: {cycle}")

    G = graph.copy()
    
    severity_val = {"high": 3, "medium": 2, "low": 1}
    risk_val_map = {"high": 3, "medium": 2, "low": 1}

    processed_conflicts = set()
    
    for u in list(G.nodes):
        if u not in G: 
            continue
            
        conflicts = G.nodes[u].get('conflicts_with', [])
        for v in conflicts:
            if v not in G: 
                continue
                
            pair = tuple(sorted([u, v]))
            if pair in processed_conflicts:
                continue
            processed_conflicts.add(pair)
            
            desc_u = len(nx.descendants(G, u))
            desc_v = len(nx.descendants(G, v))
            
            if desc_u != desc_v:
                node_to_drop = u if desc_u < desc_v else v
                node_to_keep = v if desc_u < desc_v else u
            else:
                sev_u_str = G.nodes[u].get('severity', 'low').lower()
                sev_v_str = G.nodes[v].get('severity', 'low').lower()
                sev_u = severity_val.get(sev_u_str, 1)
                sev_v = severity_val.get(sev_v_str, 1)
                
                if sev_u != sev_v:
                    node_to_drop = u if sev_u < sev_v else v
                    node_to_keep = v if sev_u < sev_v else u
                else:
                    risk_u_str = G.nodes[u].get('disruption_risk', 'high').lower()
                    risk_v_str = G.nodes[v].get('disruption_risk', 'high').lower()
                    risk_u = risk_val_map.get(risk_u_str, 3)
                    risk_v = risk_val_map.get(risk_v_str, 3)
                    
                    if risk_u != risk_v:
                        node_to_drop = u if risk_u > risk_v else v
                        node_to_keep = v if risk_u > risk_v else u
                    else:
                        node_to_drop = max(u, v)
                        node_to_keep = min(u, v)
                        
            nodes_to_drop = list(nx.descendants(G, node_to_drop)) + [node_to_drop]
            G.remove_nodes_from(nodes_to_drop)
            
            print(f"[WARNING] Conflict Detected: Dropping Rule {node_to_drop} (and dependents) in favor of Rule {node_to_keep}. Admin review required.")

    risk_map = {"low": 1, "medium": 2, "high": 3}
    in_degree = {n: d for n, d in G.in_degree()}
    
    ready = []
    for node in G.nodes:
        if in_degree[node] == 0:
            risk_val = G.nodes[node].get("disruption_risk", "high").lower()
            risk_score = risk_map.get(risk_val, 3)
            heapq.heappush(ready, (risk_score, node))
            
    order = []
    while ready:
        risk_score, u = heapq.heappop(ready)
        order.append(u)
        
        for v in G.successors(u):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                risk_val = G.nodes[v].get("disruption_risk", "high").lower()
                v_risk_score = risk_map.get(risk_val, 3)
                heapq.heappush(ready, (v_risk_score, v))
                
    return order

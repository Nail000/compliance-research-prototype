import pytest
import networkx as nx
from planner.ordering import order_random, order_severity, order_dependency_aware

@pytest.fixture
def sample_graph():
    G = nx.DiGraph()
    G.add_node("C1", severity="high", disruption_risk="low")
    G.add_node("C2", severity="medium", disruption_risk="high")
    G.add_node("C3", severity="low", disruption_risk="low")
    G.add_node("C4", severity="high", disruption_risk="medium")
    G.add_edge("C1", "C2")
    G.add_edge("C3", "C4")
    return G

def test_order_random(sample_graph):
    # Add a conflict to ensure random ignores it and doesn't drop anything
    sample_graph.nodes["C1"]["conflicts_with"] = ["C3"]
    sample_graph.nodes["C3"]["conflicts_with"] = ["C1"]
    
    order1 = order_random(sample_graph, seed=42)
    order2 = order_random(sample_graph, seed=42)
    assert order1 == order2
    
    order3 = order_random(sample_graph, seed=99)
    assert order1 != order3
    
    # Both conflicting nodes should still be returned
    assert "C1" in order1 and "C3" in order1
    assert set(order1) == set(sample_graph.nodes)

def test_order_severity(sample_graph):
    # Add a conflict to ensure severity ignores it and doesn't drop anything
    sample_graph.nodes["C1"]["conflicts_with"] = ["C3"]
    sample_graph.nodes["C3"]["conflicts_with"] = ["C1"]
    
    order = order_severity(sample_graph)
    
    severity_map = {n: sample_graph.nodes[n].get("severity") for n in sample_graph.nodes}
    
    highs = [n for n in order if severity_map[n] == "high"]
    mediums = [n for n in order if severity_map[n] == "medium"]
    lows = [n for n in order if severity_map[n] == "low"]
    
    assert order == highs + mediums + lows
    # Both conflicting nodes should still be returned
    assert "C1" in order and "C3" in order
    assert set(order) == set(sample_graph.nodes)

def test_order_dependency_aware_tie_break():
    G = nx.DiGraph()
    G.add_node("A", disruption_risk="high")
    G.add_node("B", disruption_risk="low")
    G.add_node("C", disruption_risk="medium")
    
    order = order_dependency_aware(G)
    assert order == ["B", "C", "A"]

def test_conflict_more_descendants_wins(capsys):
    G = nx.DiGraph()
    G.add_node("C1", severity="medium", conflicts_with=["C2"])
    G.add_node("C2", severity="high", conflicts_with=["C1"])
    G.add_node("D1")
    G.add_node("D2")
    
    G.add_edge("C1", "D1")
    G.add_edge("C1", "D2")
    
    order = order_dependency_aware(G)
    
    # C1 should win due to more descendants. C2 should be dropped.
    assert "C1" in order
    assert "D1" in order
    assert "D2" in order
    assert "C2" not in order
    
    captured = capsys.readouterr()
    assert "[WARNING] Conflict Detected: Dropping Rule C2 (and dependents) in favor of Rule C1. Admin review required." in captured.out

def test_conflict_severity_wins(capsys):
    G = nx.DiGraph()
    G.add_node("C1", severity="low", conflicts_with=["C2"])
    G.add_node("C2", severity="high", conflicts_with=["C1"])
    
    order = order_dependency_aware(G)
    
    assert "C2" in order
    assert "C1" not in order
    
    captured = capsys.readouterr()
    assert "[WARNING] Conflict Detected: Dropping Rule C1 (and dependents) in favor of Rule C2. Admin review required." in captured.out

def test_conflict_disruption_risk_wins(capsys):
    G = nx.DiGraph()
    G.add_node("C3", severity="high", disruption_risk="high", conflicts_with=["C2"])
    G.add_node("C2", severity="high", disruption_risk="low", conflicts_with=["C3"])
    
    order = order_dependency_aware(G)
    
    assert "C2" in order
    assert "C3" not in order
    
    captured = capsys.readouterr()
    assert "[WARNING] Conflict Detected: Dropping Rule C3 (and dependents) in favor of Rule C2. Admin review required." in captured.out

def test_conflict_tie_breaker(capsys):
    G = nx.DiGraph()
    G.add_node("C2", severity="high", disruption_risk="low", conflicts_with=["C1"])
    G.add_node("C1", severity="high", disruption_risk="low", conflicts_with=["C2"])
    
    order = order_dependency_aware(G)
    
    assert "C1" in order
    assert "C2" not in order
    
    captured = capsys.readouterr()
    assert "[WARNING] Conflict Detected: Dropping Rule C2 (and dependents) in favor of Rule C1. Admin review required." in captured.out

def test_conflict_cascading_drop(capsys):
    G = nx.DiGraph()
    # To test cascade properly:
    # C1 and C2 both have exactly 1 descendant, tying them on descendant count.
    # Then Severity decides: C1 (high) > C2 (low).
    # C2 loses, and its descendant D1 cascades with it.
    G.add_node("C1", severity="high", conflicts_with=["C2"])
    G.add_node("C2", severity="low", conflicts_with=["C1"])
    G.add_node("D1")
    G.add_node("D2")
    G.add_edge("C2", "D1")
    G.add_edge("C1", "D2")
    
    order = order_dependency_aware(G)
    
    assert "C1" in order
    assert "D2" in order
    assert "C2" not in order
    assert "D1" not in order
    
    captured = capsys.readouterr()
    assert "[WARNING] Conflict Detected: Dropping Rule C2 (and dependents) in favor of Rule C1. Admin review required." in captured.out

def test_order_dependency_aware_with_edges():
    G = nx.DiGraph()
    G.add_node("A", disruption_risk="low")
    G.add_node("B", disruption_risk="high")
    G.add_node("C", disruption_risk="high")
    G.add_node("D", disruption_risk="medium")
    
    G.add_edge("A", "C")
    G.add_edge("B", "D")
    
    order = order_dependency_aware(G)
    assert order == ["A", "B", "D", "C"]

def test_order_dependency_aware_cycle():
    G = nx.DiGraph()
    G.add_node("A", disruption_risk="low")
    G.add_node("B", disruption_risk="low")
    G.add_edge("A", "B")
    G.add_edge("B", "A")
    
    with pytest.raises(ValueError, match="Graph contains a dependency cycle"):
        order_dependency_aware(G)

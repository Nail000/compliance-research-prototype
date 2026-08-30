import pytest
import networkx as nx
import yaml
from planner.graph_builder import build_graph

# A valid mock YAML string with a dependency chain and a conflict.
VALID_MOCK_YAML = """
controls:
  - id: control_A
    severity: medium
    disruption_risk: high
    depends_on: []
    conflicts_with: [control_C]
  - id: control_B
    severity: low
    disruption_risk: medium
    depends_on: [control_A]
    conflicts_with: []
  - id: control_C
    severity: high
    disruption_risk: low
    depends_on: []
    conflicts_with: [control_A]
"""

# An invalid mock YAML string with a cyclic dependency.
CYCLIC_MOCK_YAML = """
controls:
  - id: control_A
    severity: medium
    disruption_risk: high
    depends_on: [control_B]
    conflicts_with: []
  - id: control_B
    severity: low
    disruption_risk: medium
    depends_on: [control_A]
    conflicts_with: []
"""

@pytest.fixture
def valid_yaml_file(tmp_path):
    file_path = tmp_path / "valid_controls.yaml"
    file_path.write_text(VALID_MOCK_YAML)
    return str(file_path)

@pytest.fixture
def cyclic_yaml_file(tmp_path):
    file_path = tmp_path / "cyclic_controls.yaml"
    file_path.write_text(CYCLIC_MOCK_YAML)
    return str(file_path)

def test_build_graph_valid(valid_yaml_file):
    graph = build_graph(valid_yaml_file)
    
    # 1. All expected control IDs are present as nodes.
    expected_nodes = ["control_A", "control_B", "control_C"]
    assert set(graph.nodes) == set(expected_nodes)
    
    # 2. disruption_risk, severity, and conflicts_with are correctly stored as node attributes.
    assert graph.nodes["control_A"]["severity"] == "medium"
    assert graph.nodes["control_A"]["disruption_risk"] == "high"
    assert graph.nodes["control_A"]["conflicts_with"] == ["control_C"]
    
    assert graph.nodes["control_B"]["severity"] == "low"
    assert graph.nodes["control_B"]["disruption_risk"] == "medium"
    assert graph.nodes["control_B"]["conflicts_with"] == []
    
    assert graph.nodes["control_C"]["severity"] == "high"
    assert graph.nodes["control_C"]["disruption_risk"] == "low"
    assert graph.nodes["control_C"]["conflicts_with"] == ["control_A"]

    # 3. Dependency edges have the correct direction. 
    # control_B depends on control_A -> Edge must be control_A -> control_B.
    assert graph.has_edge("control_A", "control_B")
    assert not graph.has_edge("control_B", "control_A")
    
    # 4. The resulting graph is a DAG for valid input.
    assert nx.is_directed_acyclic_graph(graph)
    
    # 6. Conflict information is preserved and does not create dependency edges.
    assert not graph.has_edge("control_A", "control_C")
    assert not graph.has_edge("control_C", "control_A")
    # And it hasn't introduced cycles due to conflicts.

def test_build_graph_cyclic(cyclic_yaml_file):
    # 5. A cyclic dependency causes build_graph() to raise the expected exception.
    with pytest.raises(ValueError, match="Graph contains a cycle"):
        build_graph(cyclic_yaml_file)

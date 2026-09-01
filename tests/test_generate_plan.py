import json
import pytest
from pathlib import Path
from planner.generate_plan import generate_plans

MOCK_YAML = """
controls:
  - id: control_A
    title: Control A
    severity: high
    disruption_risk: low
    touches:
      - {type: file, name: /etc/test}
    depends_on: []
    conflicts_with: []
    rollback_available: true
    ansible_task_ref: "playbooks/test.yml#control_A"
    health_checks: ["check_A"]
  - id: control_B
    title: Control B
    severity: low
    disruption_risk: high
    touches:
      - {type: service, name: test_svc}
    depends_on: [control_A]
    conflicts_with: []
    rollback_available: false
    ansible_task_ref: "playbooks/test.yml#control_B"
    health_checks: ["check_B"]
"""

def test_generate_plans_creates_files(tmp_path: Path):
    yaml_file = tmp_path / "control_definitions.yaml"
    yaml_file.write_text(MOCK_YAML)
    
    out_dir = tmp_path / "plans"
    
    # call our function
    generate_plans(str(yaml_file), str(out_dir))
    
    # Verify files created
    assert (out_dir / "random.json").exists()
    assert (out_dir / "severity.json").exists()
    assert (out_dir / "dependency_aware.json").exists()
    
    # Verify internal structure
    for strategy, file_name in [("random", "random.json"), ("severity_only", "severity.json"), ("dependency_aware", "dependency_aware.json")]:
        with open(out_dir / file_name, 'r') as f:
            data = json.load(f)
            
        assert data["strategy"] == strategy
        assert "generated_at" in data
        assert "order" in data
        
        # We have 2 controls in the mock, none are dropped in this simple mock
        assert len(data["order"]) == 2
        
        first_control = data["order"][0]
        assert "id" in first_control
        assert "ansible_task_ref" in first_control
        assert "disruption_risk" in first_control
        assert "touches" in first_control
        assert "health_checks" in first_control
        assert "rollback_available" in first_control

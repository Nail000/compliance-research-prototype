import os
import json
import yaml
from datetime import datetime, timezone
from planner.graph_builder import build_graph
from planner.ordering import order_random, order_severity, order_dependency_aware

def generate_plans(yaml_path: str, output_dir: str):
    # Load metadata
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Map ID -> metadata
    controls_map = {}
    for c in data.get('controls', []):
        controls_map[c['id']] = {
            "id": c["id"],
            "ansible_task_ref": c.get("ansible_task_ref", ""),
            "disruption_risk": c.get("disruption_risk", "low"),
            "touches": c.get("touches", []),
            "health_checks": c.get("health_checks", []),
            "rollback_available": c.get("rollback_available", False)
        }
        
    # Build Graph
    graph = build_graph(yaml_path)
    
    # Map of output filename base -> (schema strategy name, ordering function)
    strategies = {
        "random": ("random", order_random),
        "severity": ("severity_only", order_severity),
        "dependency_aware": ("dependency_aware", order_dependency_aware)
    }
    
    os.makedirs(output_dir, exist_ok=True)
    
    generated_at = datetime.now(timezone.utc).isoformat()
    
    for filename_base, (strategy_name, order_func) in strategies.items():
        if strategy_name == "random":
            seed = 42
            ordered_ids = order_random(graph, seed=seed)
        else:
            ordered_ids = order_func(graph)
            seed = None
        
        # Build payload
        order_payload = []
        for cid in ordered_ids:
            if cid in controls_map:
                order_payload.append(controls_map[cid])
                
        payload = {
            "strategy": strategy_name,
            "generated_at": generated_at,
            "order": order_payload
        }
        
        if seed is not None:
            # We explicitly record the seed to the console for reproducibility
            print(f"[INFO] Strategy 'random' executed using explicit seed: {seed}")
        
        out_file = os.path.join(output_dir, f"{filename_base}.json")
        with open(out_file, 'w') as f:
            json.dump(payload, f, indent=2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate remediation plans based on control definitions.")
    parser.add_argument("--yaml-path", default="control_definitions.yaml", help="Path to control definitions YAML")
    parser.add_argument("--output-dir", default="plans", help="Directory to save generated plans")
    args = parser.parse_args()
    
    generate_plans(args.yaml_path, args.output_dir)
    print(f"Successfully generated plans in {args.output_dir}/")

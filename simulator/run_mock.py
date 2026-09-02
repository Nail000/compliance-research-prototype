import sys
import json
import argparse

CONFLICT_PAIR = {
    "firewalld_loopback_traffic_restricted",
    "firewalld_loopback_traffic_trusted"
}

def main():
    parser = argparse.ArgumentParser(description="Mock Executor Simulator")
    parser.add_argument("plan", help="Path to plan.json file")
    args = parser.parse_args()

    try:
        with open(args.plan, "r") as f:
            plan_data = json.load(f)
    except Exception as e:
        print(f"Error loading {args.plan}: {e}")
        sys.exit(1)

    order = plan_data.get("order", [])
    executed_controls = set()

    for control in order:
        control_id = control.get("id")
        risk = control.get("disruption_risk", "unknown")
        touches = control.get("touches", [])

        print(f"[OK] Executing control: {control_id} (Risk: {risk})")
        print(f"  Touches: {touches}")

        if control_id in CONFLICT_PAIR:
            other_half = (CONFLICT_PAIR - {control_id}).pop()
            if other_half in executed_controls:
                print("[CRASH] Health Check Failed: Conflict Detected! System state corrupted.")
                sys.exit(1)

        executed_controls.add(control_id)

    print("[SUCCESS] Plan executed safely.")

if __name__ == "__main__":
    main()

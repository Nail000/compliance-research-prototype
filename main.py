import yaml
from pathlib import Path

from planner.parser import parse_failed_controls
from planner.extract_touches import extract_touches_from_playbook
from planner.detect_interactions import find_candidate_interactions

def main():
    xml_path = "data/arf.xml"
    playbook_path = "playbook/almalinux9-playbook-cis_server_l1.yml"

    print("1) Parsing failed controls from XML...")
    failed_rule_ids = parse_failed_controls(xml_path)
    print(f"   Found {len(failed_rule_ids)} failed controls.")

    print("2) Extracting playbook touches...")
    touches = extract_touches_from_playbook(playbook_path)
    print(f"   Extracted {len(touches)} touches.")

    print("3) Mapping touches to failed rule IDs...")
    short_failed_ids = {rid.split("content_rule_")[-1] for rid in failed_rule_ids}
    
    with open(playbook_path, 'r', encoding='utf-8') as f:
        playbook = yaml.safe_load(f)
        
    task_tags_map = {}
    
    def _extract_tags(task_list, current_tags=None):
        if not task_list:
            return
        for task in task_list:
            tags = task.get('tags', current_tags)
            task_name = task.get('name')
            if task_name:
                task_tags_map[task_name] = tags
            if 'block' in task:
                _extract_tags(task['block'], tags)
                
    for play in playbook:
        _extract_tags(play.get('tasks', []))
        
    controls_map = {}
    
    def _add_touch(cmap, rid, t):
        if rid not in cmap:
            cmap[rid] = {'rule_id': rid, 'touches': []}
        cmap[rid]['touches'].append(t)
    
    for touch in touches:
        task_name = touch.get('task_name')
        if not task_name:
            continue
            
        tags = task_tags_map.get(task_name, [])
        matched = False
        
        # 1. Match against tags
        if tags:
            for tag in tags:
                if tag in short_failed_ids or tag in failed_rule_ids:
                    matched_rule_id = tag
                    for full_id in failed_rule_ids:
                        if tag in full_id:
                            matched_rule_id = full_id
                            break
                    _add_touch(controls_map, matched_rule_id, touch)
                    matched = True
        
        # 2. Match against task_name if not matched by tags
        if not matched:
            for short_id in short_failed_ids:
                normalized_name = task_name.lower().replace(' ', '_').replace('-', '_')
                if short_id in normalized_name or short_id in task_name:
                    for full_id in failed_rule_ids:
                        if short_id in full_id:
                            _add_touch(controls_map, full_id, touch)
                            matched = True
                            break

    print(f"   Mapped touches to {len(controls_map)} failed controls.")

    print("4) Formatting and finding candidate interactions...")
    controls_list = list(controls_map.values())
    interactions = find_candidate_interactions(controls_list)
    
    print("5) Writing Candidate Interactions to candidate_interactions.txt...")
    with open("candidate_interactions.txt", "w", encoding="utf-8") as f:
        for interaction in sorted(interactions):
            f.write(f"{interaction}\n")

if __name__ == "__main__":
    main()

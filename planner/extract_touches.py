import yaml

def extract_touches_from_playbook(playbook_path: str) -> list:

    touches = []
    
    with open(playbook_path, 'r', encoding='utf-8') as f:
        playbook = yaml.safe_load(f)
        
    if not playbook:
        return touches
        
    for play in playbook:
        tasks = play.get('tasks', [])
        for task in tasks:
            _extract_from_task(task, touches)
            
    return touches

def _extract_from_task(task: dict, touches: list):
    task_name = task.get('name', 'Unknown task')
    
    # Handle blocks (nested tasks)
    if 'block' in task:
        for subtask in task['block']:
            _extract_from_task(subtask, touches)
        return
        
    extracted = False
    
    # Mechanical extraction based on module types
    module_configs = {
        'ansible.builtin.package': ('package', 'name'),
        'ansible.builtin.yum': ('package', 'name'),
        'ansible.builtin.dnf': ('package', 'name'),
        'ansible.builtin.apt': ('package', 'name'),
        
        'ansible.builtin.systemd': ('service', 'name'),
        'ansible.builtin.service': ('service', 'name'),
        
        'ansible.builtin.file': ('file', 'path'),
        'ansible.builtin.lineinfile': ('file', 'path'),
        
        'ansible.builtin.copy': ('file', 'dest'),
        'ansible.builtin.template': ('file', 'dest')
    }
    
    for mod_name, (res_type, res_key) in module_configs.items():
        if mod_name in task:
            module_args = task[mod_name]
            if isinstance(module_args, dict) and res_key in module_args:
                touches.append({
                    'task_name': task_name,
                    'module': mod_name,
                    'type': res_type,
                    'name': module_args[res_key]
                })
                extracted = True
                break
                
    # Handle replace which aliases path/dest
    if not extracted and 'ansible.builtin.replace' in task:
        module_args = task['ansible.builtin.replace']
        if isinstance(module_args, dict):
            # Prefer path, fallback to dest
            target_file = module_args.get('path') or module_args.get('dest')
            if target_file:
                touches.append({
                    'task_name': task_name,
                    'module': 'ansible.builtin.replace',
                    'type': 'file',
                    'name': target_file
                })
                extracted = True

    if not extracted:
        touches.append({
            'task_name': task_name,
            'touches': 'unknown'
        })

# Planner Architecture

This document describes the technical architecture of the compliance remediation planner track (Prototype Phase). The system is designed to transform failed OpenSCAP compliance controls into a curated dependency- and risk-aware ordered remediation plan (`plan.json`), validated via a lightweight mock simulator.

## System Boundaries and Scope Constraints
The current implementation is restricted to a curated prototype set of controls. It produces an execution plan but **does not execute live system changes**. 
- The **mock executor** (`simulator/run_mock.py`) serves strictly as a lightweight simulation boundary. It validates the output `plan.json` against known conflict constraints.
- Operational safety, VM snapshots, real health checks, live rollback, and recovery are strictly **out of scope** for this planner track.

## Processing Pipeline

### 1. OpenSCAP ARF/XCCDF Parsing
**Component**: `planner/parser.py`

The planner begins by interpreting a genuine OpenSCAP scan result (ARF/XCCDF format) to identify failed controls. 
- **Implementation**: It uses the `lxml` library to parse the XML tree.
- **Resiliency**: The XPath query utilizes `local-name()` (e.g., `//*[local-name()='rule-result']`) to remain resilient against namespace variations across different OpenSCAP versions.
- **Output**: Extracts the `idref` for any rule where the `<result>` element evaluates to `fail`.

### 2. Mechanical Resource Extraction
**Component**: `planner/extract_touches.py`

Once failed controls are identified, the system must determine which system resources their respective Ansible tasks will modify.
- **Implementation**: Uses `PyYAML` to parse the Ansible playbook.
- **Mechanism**: Extraction is strictly mechanical and deterministic. It maps known Ansible modules to resource types:
  - `ansible.builtin.package`/`yum`/`dnf`/`apt` -> `package`
  - `ansible.builtin.systemd`/`service` -> `service`
  - `ansible.builtin.file`/`lineinfile`/`copy`/`template` -> `file`
- **Fallback**: If a task relies on an unmapped module or complex logic that cannot be deterministically extracted, the resource is safely tagged as `touches: unknown` rather than attempting unsafe inference.

### 3. Candidate Interaction Detection
**Component**: `extract_candidates.py`

To bridge the gap between extracted resources and final graph construction, the system generates a candidate matrix by detecting shared resource touches.
- **Mechanism**: The script cross-references the extracted touches. If two controls modify the same resource (e.g., both interact with the `firewalld` service), they are flagged as having a candidate interaction.
- **Human-in-the-Loop Constraint**: The system **does not** automatically convert these overlaps into semantic dependencies or conflicts. Overlap is strictly treated as *evidence*. A human must manually inspect this candidate matrix and classify the true relationships into the curated `control_definitions.yaml` contract.

### 4. Dependency Graph Construction
**Component**: `planner/graph_builder.py`

The planner constructs a mathematical model of the remediation execution sequence based on the `control_definitions.yaml` contract.
- **Implementation**: Built using `networkx.DiGraph`.
- **Nodes**: Each control acts as a node, carrying metadata for `disruption_risk`, `severity`, and `conflicts_with`.
- **Edges**: The `depends_on` relationships are transformed into directed edges representing execution order (Dependency -> Dependent).
- **Validation**: The builder strictly validates that the resulting graph is a Directed Acyclic Graph (DAG). If a cycle is detected, `networkx.is_directed_acyclic_graph()` returns false, and the builder immediately raises a `ValueError`.

### 5. Ordering Engine
**Component**: `planner/ordering.py`

The engine applies three distinct strategies to the same control set to facilitate comparative evaluation:

1. **Random Strategy (`order_random`)**
   - Baseline strategy.
   - Shuffles the nodes using a standard random number generator with a recorded seed to ensure experimental reproducibility.

2. **Severity-Only Strategy (`order_severity`)**
   - Naive baseline strategy prioritizing standard security risk over operational safety.
   - Sorts controls strictly by their severity (`high` -> `medium` -> `low`).

3. **Dependency-Aware Strategy (`order_dependency_aware`)**
   - Proposed heuristic prioritizing operational safety.
   - **Conflict Resolution**: Iterates through the graph's declared conflicts. If an active conflict pair is found, it resolves the conflict by dropping one node (and all its descendants) from the plan. It decides which node to keep via tie-breaking logic (favoring the node with more descendants, then higher severity, then lower disruption risk).
   - **Topological Sorting**: Uses Kahn's algorithm with a priority queue (`heapq`) to traverse the DAG.
   - **Disruption-Risk Tie-breaking**: When multiple independent nodes are ready for execution, the algorithm uses `disruption_risk` as the tie-breaker, executing low-risk controls before high-risk ones.

### 6. Simulation Execution
**Component**: `simulator/run_mock.py`

The pipeline terminates by passing the generated `plan.json` to the mock executor.
- This script does not apply system state changes. 
- It simulates execution by iterating through the ordered plan, evaluating if an incompatible state occurs (e.g., executing both sides of a hardcoded conflict pair, such as `firewalld_loopback_traffic_restricted` and `firewalld_loopback_traffic_trusted`). 
- On a conflict, it safely aborts and simulates a state corruption crash (`[CRASH] Health Check Failed: Conflict Detected!`). On success, it outputs `[SUCCESS] Plan executed safely.`

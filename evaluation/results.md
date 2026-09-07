# Evaluation Results

## Experiment Objective
The objective of this prototype experiment is to evaluate the impact of three distinct plan-ordering strategies on a curated set of compliance controls. The experiment aims to determine if a dependency-aware heuristic reduces simulated state corruption compared to baseline ordering methods.

## Control/Strategy Definitions
The planner engine generated three remediation plans based on the following strategies:
1. **Random**: A baseline strategy that shuffles the curated control set using a fixed seed.
2. **Severity-Only**: A naive baseline strategy that prioritizes controls purely by their security severity (`high` -> `medium` -> `low`), ignoring dependencies and potential operational conflicts.
3. **Dependency-Aware**: A proposed heuristic that respects `depends_on` directed edges, resolves declared conflicts by safely dropping one of the conflicting controls (and its descendants), and tie-breaks independent controls by favoring lower `disruption_risk`.

## Experimental Setup
The execution of the generated plans was simulated using a lightweight mock executor (`simulator/run_mock.py`). 
- The simulator does not apply real system state changes. 
- It evaluates the execution sequence sequentially.
- If the simulator encounters execution of both elements of a known incompatible pair (`firewalld_loopback_traffic_restricted` and `firewalld_loopback_traffic_trusted`), it immediately terminates with a simulated state corruption crash.
- The control definitions, dependencies, and conflict relationships are manually curated for the prototype within the `control_definitions.yaml` contract. The final relationships were selected from a candidate matrix generated deterministically from mechanically extracted resource touches.

## Results
The mock executor was run against the three generated plan outputs (`plans/random.json`, `plans/severity.json`, `plans/dependency_aware.json`). The outcome of each simulation run is documented below.

### Comparison Table

| Strategy             | Run Status | Result Message                                                             | Verification Status |
| :-----------------   | :--------- | :------------------------------------------------------------------------- | :------------------ |
| **Random**           | Failed     | `[CRASH] Health Check Failed: Conflict Detected! System state corrupted.`  | **VERIFIED**        |
| **Severity-Only**    | Failed     | `[CRASH] Health Check Failed: Conflict Detected! System state corrupted.`  | **VERIFIED**        |
| **Dependency-Aware** | Succeeded  | `[SUCCESS] Plan executed safely.`                                          | **VERIFIED**        |

*Note: Verification Status indicates whether the execution behavior was actually verified by the simulation run.*


### Baseline Strategies Performance

The baseline strategies (random and severity-only) treat the controls as a flat list of tasks without any additional context regarding dependencies or conflicts. Consequently, they blindly schedule all controls for execution, including mutually exclusive pairs like firewalld_loopback_traffic_restricted and firewalld_loopback_traffic_trusted. Pushing these conflicting states to the same service is exactly what triggered the state corruption crash during our simulation run. Thus, in the evaluated scenario, baseline strategies which represent naive automation will cause system corruption.

### Dependency-Aware Strategy Performance

The dependency-aware strategy, on the other hand, takes into account the dependencies and conflicts between controls, and uses this information to generate a plan that is safe to execute. It achieves this by modeling controls' interactions as a directed acyclic graph using `networkx` and applying a topological sort to extract a safe execution sequence. During this process, it resolves conflicts by dropping one of the conflicting controls (and its descendants) and tie-breaking independent controls by favoring lower `disruption_risk`. This approach prevents system corruption by ensuring that the generated plan does not contain any conflicting controls simultaneously. 

### Relation to the Research Hypothesis

The results of the simulation support the hypothesis that incorporating dependency and conflict information into automated remediation planning can reduce the risk of system state corruption. In the evaluated scenarios, the baseline strategies scheduled mutually exclusive configurations without accounting for their dependencies, leading to state corruption during execution. In contrast, the dependency-aware strategy successfully modeled the remediation workflow as a directed acyclic graph, applying a topological sort and a disruption-risk heuristic explicitly identifying and excluding conflicting actions before execution. This observed contrast provides evidence that accounting for dependencies and conflicts supports safer remediation decisions, though further evaluation is required to establish generalization.


### Limitations

The prototype's validation utilized a manually curated set of 8 controls tailored for an AlmaLinux 9 minimal, CIS Level 1 Server profile, rather than processing a full enterprise scan dynamically. Furthermore, the execution boundary was restricted to a deterministic Python mock simulator rather than a live environment. As a result, operational complexities such as OS-level execution latency, real-world Ansible failures, and VM snapshot rollbacks were strictly out of scope and remain unverified.


# Autonomous Compliance Remediation Planning Engine

A research prototype for AlmaLinux 9 that parses OpenSCAP compliance scan results, models remediation interactions using a dependency graph, and evaluates risk-aware execution strategies via simulation-based validation.

## Project Structure

This repository focuses strictly on compliance intelligence, planning, and simulation. Live hypervisor execution, VM snapshotting, and real system rollbacks are reserved for the full thesis phase and are excluded from this prototype boundary.

*   **Planner Track:** Parses OpenSCAP ARF/XCCDF XML results, mechanically extracts system touches from Ansible tasks, and constructs a Directed Acyclic Graph (DAG) to generate safe execution sequences.
*   **Simulation Track:** A lightweight deterministic mock executor (`simulator/run_mock.py`) that consumes the generated sequence and triggers a simulated state corruption crash upon encountering mutually exclusive constraints, verifying the planner's safety logic.

## Ordering Strategies

The planner generates execution plans (`plan.json`) based on three distinct strategies to support a comparative experiment:

1.  `random`: A baseline randomized sequence using an explicitly recorded random seed for reproducibility.
2.  `severity_only`: A naive baseline sequence ordered strictly by compliance severity (`high` -> `medium` -> `low`), ignoring dependencies and potential operational conflicts.
3.  `dependency_aware`: A proposed heuristic strategy that enforces topological ordering for dependencies, algorithmically resolves conflicts by dropping conflicting nodes, and uses disruption risk (`low` -> `medium` -> `high`) as a tie-breaker.

## Requirements

*   Python 3.10+

### Python Dependencies

The core logic uses a minimal toolchain:

```bash
pip install lxml networkx pytest pyyaml
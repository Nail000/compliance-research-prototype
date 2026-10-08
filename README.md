# Compliance Remediation Planning Engine (research prototype)

A research prototype for AlmaLinux 9 that parses OpenSCAP compliance scan results, models interactions between remediations as a dependency graph, and compares ordering strategies in a simulation.

**▶ Demo:** [Terminal demo (asciinema)](https://asciinema.org/a/IqsRsJF3czMA40am), a simulated firewall conflict handled by the planner
**📄 Docs:** [Architecture](architecture.md) · [Results and limitations](results.md)

## Scope

This repository covers compliance planning and simulation only. Live hypervisor execution, VM snapshotting and real system rollbacks are reserved for the full thesis phase and are excluded from this prototype.

- **Planner track:** Parses OpenSCAP ARF/XCCDF XML results, extracts the system resources each Ansible remediation touches, and builds a directed acyclic graph (DAG) to generate an execution sequence.
- **Simulation track:** A deterministic mock executor (`simulator/run_mock.py`) consumes the generated sequence and simulates a state-corruption crash when it hits mutually exclusive remediations. It exercises the planner's conflict handling on a hand-authored scenario.

## Ordering strategies

The planner writes an execution plan (`plan.json`) for each of three strategies, to support a comparative experiment:

1. `random`: baseline random sequence with an explicitly recorded seed for reproducibility.
2. `severity_only`: naive baseline ordered by compliance severity (`high` → `medium` → `low`), ignoring dependencies and conflicts.
3. `dependency_aware`: proposed heuristic. It enforces topological ordering for dependencies, resolves conflicts by dropping conflicting nodes and flags them for human review, and uses disruption risk (`low` → `medium` → `high`) as a tie-breaker.

## Usage

```bash
# 1. Generate plans from an OpenSCAP result file
python planner/generate_plan.py --yaml-path control_definitions.yaml --output-dir plans

# 2. Run the mock executor on a plan
python simulator/run_mock.py plans/dependency_aware.json

# 3. Run the tests
pytest
```

The pipeline uses a manually curated YAML file (`control_definitions.yaml`) mapping to 9 failed controls extracted from an OpenSCAP scan (fixture available at `tests/fixtures/real_scan_small.xml`).

## Results and limitations

Full details are in [results.md](results.md). In short:

- The simulation is **deterministic** and uses a **hand-authored conflict**, so results are identical on every run.
- It demonstrates the planner's logic on that scenario. It does **not** evaluate the planner on real systems.
- `dependency_aware` is a **heuristic**, with no formal guarantee.

## Future work (thesis phase)

- Live execution, snapshots and rollback on real systems.
- Formalizing the conflict model.

## Requirements

- Python 3.10+

```bash
pip install lxml networkx pytest pyyaml
```
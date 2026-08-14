# Autonomous Compliance Remediation Engine

A collaborative research prototype for AlmaLinux 9 that parses OpenSCAP compliance scan results, models remediation interactions using a dependency graph, and evaluates risk-aware execution strategies.

## Project Structure

This repository is split into two distinct, decoupled tracks:

*   **Planner Track (Student 1):** Parses OpenSCAP ARF/XCCDF XML results, extracts system touches from Ansible tasks, and uses a directed graph to generate safe execution sequences.
*   **Executor Track (Student 2):** Consumes the generated sequence, handles VirtualBox snapshots, executes tasks on the target VM, and triggers automated rollbacks if health checks fail.

## Ordering Strategies

The planner generates execution plans (`plan.json`) based on three distinct strategies to support a comparative experiment:

1.  `random`: A baseline randomized sequence using a fixed seed.
2.  `severity_only`: A baseline sequence ordered strictly by compliance severity, ignoring system disruption.
3.  `dependency_aware`: A proposed heuristic strategy that enforces topological ordering for dependencies and uses disruption risk as a tie-breaker.

## Requirements

*   Python 3.10+
*   Target VM: AlmaLinux 9 (Minimal, Headless) with `openscap-scanner`

### Python Dependencies

The core logic uses a minimal toolchain:

```bash
pip install lxml networkx pytest pyyaml
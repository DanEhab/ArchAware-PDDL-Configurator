# S0-D1: Pipeline Architecture Diagram

```mermaid
graph TD
    A[run_stage0.py] -->|Initializes| B[master_orchestrator.py]
    B -->|Spawns Threads| C[Thread Pool]
    C -->|Executes| D1[planner_runner.py<br>(LAMA)]
    C -->|Executes| D2[planner_runner.py<br>(DecStar)]
    C -->|Executes| D3[planner_runner.py<br>(BFWS)]
    C -->|Executes| D4[planner_runner.py<br>(Madagascar)]
    D1 --> E[Docker Containers<br>isolated environments]
    D2 --> E
    D3 --> E
    D4 --> E
    E -->|Telemetry| F[Thread-safe CSV Manager]
    F -->|Writes to| G[base_planner_execution_data.csv]
```

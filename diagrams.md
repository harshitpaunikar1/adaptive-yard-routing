# Adaptive Yard Routing Diagrams

Generated on 2026-04-26T04:29:37Z from README narrative plus project blueprint requirements.

## Yard routing decision flow

```mermaid
flowchart TD
    N1["Step 1\nMapped as-is yard flows with supervisors and drivers; defined SLAs and baseline me"]
    N2["Step 2\nConsolidated yard state into live map: docks, trailers, jockeys, queues; normalise"]
    N1 --> N2
    N3["Step 3\nBuilt decision engine to find nearest empty docks and assign moves using distance,"]
    N2 --> N3
    N4["Step 4\nDelivered guidance UIs for gate, control room, jockey handhelds with one-tap accep"]
    N3 --> N4
    N5["Step 5\nRan shadow pilots and replay tests on historical days; tuned thresholds; instrumen"]
    N4 --> N5
```

## Architecture diagram (gate → engine → jockey UI)

```mermaid
flowchart LR
    N1["Inputs\nLive yard-state entities such as docks, trailers, queues, and jockey availability"]
    N2["Decision Layer\nArchitecture diagram (gate → engine → jockey UI)"]
    N1 --> N2
    N3["User Surface\nAPI-facing integration surface described in the README"]
    N2 --> N3
    N4["Business Outcome\nSLA adherence"]
    N3 --> N4
```

## Evidence Gap Map

```mermaid
flowchart LR
    N1["Present\nREADME, diagrams.md, local SVG assets"]
    N2["Missing\nSource code, screenshots, raw datasets"]
    N1 --> N2
    N3["Next Task\nReplace inferred notes with checked-in artifacts"]
    N2 --> N3
```

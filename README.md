# Adaptive Yard Routing

> **Domain:** Logistics

## Overview

Yard dispatch and moves were coordinated manually, making every gate-in, docking, and relocation slower than necessary. Teams struggled to see which docks were free, where trailers were parked, and which jockey was closest and available. Radio calls and ad-hoc searches created uneven workloads, idle assets, and queueing at peak times. Without automation, dwell time kept creeping up, dock turns were unpredictable, and the cost of missed slots, detention, and demurrage grew. The goal: a system continuously finding empty docking spaces, guiding inbound trucks to nearest slots, recommending best-placed jockeys to execute moves, and removing manual bottlenecks end to end.

## Approach

- Mapped as-is yard flows with supervisors and drivers; defined SLAs and baseline metrics for dwell, move time, dock utilisation, first-response
- Consolidated yard state into live map: docks, trailers, jockeys, queues; normalised geofences and check-in events to maintain accuracy
- Built decision engine to find nearest empty docks and assign moves using distance, trailer compatibility, priorities, business rules
- Delivered guidance UIs for gate, control room, jockey handhelds with one-tap accept/decline, ETA updates, exception capture
- Ran shadow pilots and replay tests on historical days; tuned thresholds; instrumented alerts, audit logs, fallbacks for safe manual override
- Integrated with existing TMS/WMS and gate systems; shipped iteratively in 2-week sprints with training, playbooks, change management

## Skills & Technologies

- Process Mapping
- Operational Analytics
- Routing & Assignment Algorithms
- Geofencing
- Event-Driven Architecture
- API Integration
- Mobile UX Design
- SQL Data Modeling
- Operational Dashboards

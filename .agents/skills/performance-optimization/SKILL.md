---
name: performance-optimization
description: Design or change code for a concrete performance requirement or measured bottleneck in Django, PostgreSQL, or browser data handling. Use for optimization decisions and implementation, not routine edits or load-test execution alone.
---

# Performance optimization

KNJSC adaptation of Addy Osmani's performance workflow.
Use [AGENTS.md](../../../AGENTS.md) and the relevant ADR as the source of constraints.
This is the implementation skill; browser measurement and load testing are separate.

## Establish the problem

1. Identify the user operation, dataset, concurrency, and target environment.
2. Distinguish a measured bottleneck from a prospective scale requirement.
3. For existing code, read the execution path and establish a comparable baseline.
4. For a new design, state assumptions and plan a representative measurement.
5. Locate the time or resource cost before choosing an optimization.
6. Do not infer browser speed from server latency or database speed from index names.

## Choose the relevant layer

| Evidence or requirement | Investigate |
|---|---|
| Slow query | Query count, plan, rows visited, joins, sorting |
| Slow server with fast SQL | HTML generation, serialization, synchronous work |
| Lag while selecting or scrolling | DOM work, layout, paint, main-thread tasks |
| Memory grows while scrolling | Unbounded cache, DOM accumulation, retained objects |
| Slow under concurrent writes | Lock waits, worker queues, transaction duration |
| Large transfer | Row/column selection, repeated metadata, compression |

Read [data and grid decisions](references/data-and-grid.md) only for database,
large-grid, pagination, cache, or concurrent-edit optimization.

## Design the change

- State the bottleneck and the specific work the change removes or bounds.
- Preserve correctness, authorization, ordering, and failure behavior.
- Prefer a bounded change to replacing the whole stack.
- Compare alternatives using measured cost and implementation complexity.
- Account for write cost when adding indexes and invalidation when adding caches.
- Treat unavailable data and unloaded rows differently from empty values.
- Do not select a grid library, add a dependency, or change UX without scope authority.

## Implement and compare

- Change one meaningful bottleneck at a time where practical.
- Use relevant regression coverage for behavior affected by the optimization.
- Reuse measurements from web-perf or load testing rather than repeat collection.
- Compare the same dataset, user scope, operation, environment, and warm/cold state.
- Record both gains and regressions, including memory and payload where relevant.
- If results are noisy, report uncertainty and repeat only to resolve that uncertainty.
- Do not claim improvement from code shape alone.

## Avoid common detours

- JSON alone does not bound the number of DOM cells.
- More indexes, workers, connections, caches, or threads are not inherently faster.
- A small local dataset cannot validate the target capacity.
- Library benchmarks are not measurements of this application.
- Do not add a formula engine when the scope is data entry and editing.
- Do not optimize unrelated pages while investigating one CRM operation.

## Handoff

Report the decision, baseline and final evidence, correctness checks, and limits.
For a design-only task, report the proposed mechanism and unverified assumptions.
Do not present a target latency or payload budget as an achieved measurement.
Do not automatically invoke every performance skill or read every project document.

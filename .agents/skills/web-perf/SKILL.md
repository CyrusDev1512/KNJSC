---
name: web-perf
description: Measure and diagnose browser page loading, scrolling, selection, typing lag, rendering, and memory. Use for frontend performance evidence; excludes SQL-only optimization and API load testing.
---

# Browser performance evidence

KNJSC adaptation of Cloudflare's web-perf skill.
Follow [AGENTS.md](../../../AGENTS.md) for project scope and browser verification.
Use this skill to locate frontend costs, not to trigger a general website redesign.

## Establish the observation

1. Identify the page and the exact slow interaction.
2. Record viewport, browser, device conditions, data size, and applied filters.
3. Check which browser, network, and trace tools are actually available.
4. Use existing tools; do not invent APIs or install an MCP server automatically.
5. Separate read-only inspection from interactions that save or delete data.
6. Use authorized test data for any write-path measurement.

## Collect the smallest useful trace

- For page loading, inspect navigation and resource timings.
- For scrolling, selection, or typing, record that interaction, not only page reload.
- Inspect main-thread tasks, layout, paint, and scripting cost where tools expose them.
- Compare initial load with later updates and warm-cache behavior.
- Correlate visible pauses with requests and DOM replacements.
- Inspect actual response size and compression, not source-file size alone.
- Avoid unnecessary screenshots, repeated snapshots, and unrelated page audits.

Read [grid profiling](references/grid-profiling.md) only for spreadsheet-like
interaction, virtualization, or repeated-update investigation.

## Interpret evidence

| Observation | What it can establish |
|---|---|
| Server response time | Waiting for data, not rendering completion |
| Large DOM update | Work to investigate; not proof of a specific latency |
| Interaction trace | Where browser time was spent for that interaction |
| Source inspection | A possible costly path requiring measurement |
| Raw HTML bytes | Uncompressed document payload only |
| Screenshot | Visible state at capture time |

Distinguish findings, hypotheses, and measurements explicitly.
Do not report FPS, INP, long-task duration, or memory without actual instrumentation.
If citing current metric definitions, retrieve official web.dev or Chrome documentation.
An individual trace does not establish field-wide percentile metrics.

## Missing instrumentation

- Continue useful source and network inspection when tracing is unavailable.
- State which measurements remain unavailable and why.
- Do not equate a passing HTTP test with smooth browser interaction.
- Do not use an empty or logged-out page to claim the populated grid is fast.
- Do not reset data or create accounts just to make a trace possible.

## Findings and next action

- Rank measured bottlenecks by user impact and evidence strength.
- Identify the operation and source location involved when known.
- Recommend a focused experiment, not a generic checklist of optimizations.
- Use performance-optimization only when the task moves into design or code changes.
- Reuse collected evidence at final verification.
- Disclose limitations of the device, dataset, and duration used.

## Reporting boundary

Keep traces or screenshots local and avoid exposing customer values in reports.
No telemetry upload, configuration change, or new dependency is implied by this skill.
Report what was measured and what remains to test on representative hardware.

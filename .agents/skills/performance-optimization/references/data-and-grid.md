# Decisions for data-heavy grids

## PostgreSQL and Django

- Inspect existing indexes and an actual query plan before proposing another index.
- An index's existence does not prove it serves the predicate or ordering.
- Use query counts to find N+1; choose select_related/prefetch_related for the actual access.
- EXPLAIN ANALYZE executes the query. Start with read-only SELECT paths and do not run
  write statements against active data for diagnosis.
- Composite/partial/expression indexes depend on real filter and sort shapes.
  GIN on JSON is not a universal accelerator for every extracted-key expression.
- Measure write amplification and index maintenance, not only SELECT latency.

## Continuous view

- Separate backend block loading from DOM row/column virtualization.
- Maintain a bounded cache and stable record IDs; never use visual row numbers as write IDs.
- Preserve selection and pending edits independently of recycled DOM elements.
- Filtering, sorting, search, and export must cover the authorized result set,
  not just downloaded rows. Always include a stable tie-breaker in ordering.
- Keyset pagination suits sequential traversal; arbitrary jumps need a separate
  strategy. Do not promise direct row jumps from cursor pagination alone.
- Replacing page buttons with endless DOM appends eventually recreates the size problem.
- Abort or ignore stale responses after a changed filter; do not let old data overwrite
  a newer view. Use query identity and invalidate cached blocks on relevant changes.

## Writes and background work

- Changes to concurrency policy require explicit project agreement; first inspect the
  existing locking/version scheme. Bulk speed must not introduce silent lost updates.
- Preserve failure states, retry semantics, and undo validity under other users' edits.
- For import/export, read authorized rows server-side in bounded batches; use existing
  background facilities where needed. Do not export only the browser's cached rows.
- Prefer small updates or scoped invalidation over reloading the entire grid body.
  Choose polling/SSE/WebSocket from requirements and measurements, not fashion.

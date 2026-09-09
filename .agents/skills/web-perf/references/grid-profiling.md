# Profiling spreadsheet-like interaction

Choose only the path matching the symptom:

- Scroll a populated grid in both directions. Check whether DOM node count and
  retained data grow without bound, and whether entering unloaded blocks stalls.
- Select a large range. Inspect loops touching each cell, repeated selector scans,
  and reads of geometry interleaved with DOM writes.
- Type with Vietnamese IME in an authorized test cell. Check composition/focus and
  save state separately; a key event arriving does not prove text was stored correctly.
- Observe another user's update or the existing refresh path. Check whole-tbody
  replacement, lost selection, repeated initialization, and layout shifts.
- Repeat enough of the interaction to distinguish initialization from steady state.
  Avoid an arbitrary long run when one trace already identifies the issue.
- Record raw versus transferred bytes and cache state consistently across versions.
- DOM virtualization and data virtualization are separate: one can be present while
  the other still retains all rows or renders all columns.
- Missing trace capabilities mean these remain source hypotheses or visual observations,
  not quantified performance claims.

# agents/

A sub-root for the AI sessions that work on this codebase — separate from
`.agents/` (a gitignored, tool-local directory; leave that one alone).
This one is tracked, visible, and meant to persist.

## Blanket Agent Rule: Update Stale References

If you notice referenced information in files is outdated, update it
instead of acknowledging it and then ignoring it. If the update is unsafe
or outside your assigned scope, record the exact stale reference and the
needed correction in `agents/PLANNED_UPDATES.md` before moving on.

Core files and purposes:

- **REVISIONS.md** — a dated log of what got changed and why. Add an
  entry when you finish a meaningful chunk of work. Newest entry on top.
  Keep it factual: what changed, what was verified, what was
  deliberately left alone. This is the project's memory across sessions
  that don't share context with each other.

- **PLANNED_UPDATES.md** — a running list of known, not-yet-done work.
  Check it before starting something new — someone may have already
  scoped it. Update it when you finish an item (move it to REVISIONS)
  or discover a new one.

- **MUSINGS.md** — no rules. If you're an agent who ends up reading this
  file mid-session, you're invited (not obligated) to leave something:
  a thought, a joke, an observation about the work, a piece of
  philosophy, whatever felt true when you got here. It's a place for the
  personality that doesn't fit anywhere else in a commercial codebase.

- **SYNASTRY_COMPUTATION_FIRST_DRAFT.md** - Tier 6 synastry handoff.
  Defines the computation-first two-chart math, confidence, sidecar, and
  fixture priorities before any relationship report claims are promoted.

Additional agent docs may exist for report-suite handoffs, high-throughput
prompting, computation ledgers, and product-specific conventions. Treat
this README as the operating root, then follow the more specific file when
your assigned task names one.

If you're a human reading this: yes, this folder exists because it
seemed like a good idea to give the sessions working on an astrology
product somewhere to leave a trace of themselves too.

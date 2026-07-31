# Cleanup Register

This register classifies current repository hygiene findings by risk. It is a
working handoff document for future cleanup batches.

## Safe Cleanup

- Add pytest discovery exclusions so generated workspaces under `tmp/` are not
  collected as active tests.
- Keep legacy test import wrappers for renamed formula modules until tests are
  migrated to `formulas.standard.*`.
- Ignore local/generated output roots: `output/`, `outputs/`, `tmp/`,
  `audit_output/`, `runtime/`, caches, build folders, and frontend/mobile
  generated artifacts.
- Document rather than move root audit docs, `agents/`, `phase0/`, `archive/`,
  and `quarantine/`.
- Index empty or ambiguous directories such as `outputs/` before removing them.
- Remove untracked cache files only when they are provably generated and not
  part of a user handoff.

## Needs Verification

- Extracting report-specific context builders from `generate.py`.
- Moving product-local docs from runtime packages into `docs/`.
- Consolidating duplicate renderer wrappers in location services.
- Renaming product block files or directories.
- Changing `config.CONTENT_PACKS`, `REPORT_BLOCK_DIRS`, or template maps.
- Updating tests that still encode retired-product assumptions.
- Deciding whether untracked folders are source, experiments, vendored apps, or
  local generated workspaces.

## Requires Human Review

- Any astrology formula, score, ranking, threshold, timing, transit, ephemeris,
  or confidence-state change.
- Any selector or fallback behavior change.
- Any content library, report prose, template, visual rendering, public-facing
  copy, product positioning, or methodology change.
- Any removal of `archive/`, `quarantine/`, root audit docs, research packs, or
  untracked app subprojects.

## Current Notes

- `generate.py` is the main debt concentration, but it is also the active
  public integration surface. Split it only through import-compatible,
  output-equivalent steps.
- The retired Asteroid Portrait path should not be recreated to satisfy stale
  tests; tests should reflect the current README retirement note.
- `test_offline_location.py` depends on fake optional dependencies for stable
  offline tests. If it fails only when a real optional package is installed,
  fix the test harness rather than production ephemeris code.

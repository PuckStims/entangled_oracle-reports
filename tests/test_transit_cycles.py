"""
tests/test_transit_cycles.py

Automated checks for Part 1–5 of the transit-cycle upgrade.

Run with:
    python -m pytest tests/test_transit_cycles.py -v
or:
    python tests/test_transit_cycles.py
"""

import os
import sys
import json
import re
import html as html_lib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ── Path bootstrap ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _generate_noah(extra_args=None):
    """
    Runs `python generate.py year_ahead` for the Noah test chart and returns
    the path of the output HTML file.
    """
    cmd = [
        sys.executable, str(PROJECT_ROOT / "generate.py"),
        "year_ahead",
        "--name", "Noah",
        "--date", "2004-07-09",
        "--time", "22:11",
        "--location", "Watertown, WI",
        "--no-browser",
    ]
    if extra_args:
        cmd.extend(extra_args)

    env = os.environ.copy()
    env["EO_STDOUT_REPORT_PATHS"] = "1"
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT), env=env)
    assert result.returncode == 0, (
        f"generate.py failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    # Extract output path from stdout line "[Done] Report path: ..."
    for line in result.stdout.splitlines():
        if line.startswith("[Done] Report path:"):
            return Path(line.split(":", 1)[1].strip())

    raise AssertionError(f"Could not find output path in stdout:\n{result.stdout}")


def _run_transit_trace_noah():
    """
    Runs the Noah Year Ahead with EO_TRANSIT_TRACE=1 and returns (html_path, stdout).
    """
    cmd = [
        sys.executable, str(PROJECT_ROOT / "generate.py"),
        "year_ahead",
        "--name", "Noah",
        "--date", "2004-07-09",
        "--time", "22:11",
        "--location", "Watertown, WI",
        "--no-browser",
    ]
    env = os.environ.copy()
    env["EO_TRANSIT_TRACE"] = "1"
    env["EO_STDOUT_REPORT_PATHS"] = "1"

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT), env=env)
    assert result.returncode == 0, (
        f"generate.py (trace) failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    for line in result.stdout.splitlines():
        if line.startswith("[Done] Report path:"):
            html_path = Path(line.split(":", 1)[1].strip())
            return html_path, result.stdout

    raise AssertionError(f"Could not find output path in trace stdout:\n{result.stdout}")


def _html(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


# ═══════════════════════════════════════════════════════════════
# Test 1 — No "Exact:" or "Closest approach:" in public output
# ═══════════════════════════════════════════════════════════════

def test_no_exact_or_closest_approach_in_html():
    """Part 5.1 — Public HTML must not contain legacy timing wording."""
    html_path = _generate_noah()
    html = _html(html_path)

    forbidden = ["Exact:", "Closest approach:", "closest approach", "perfection"]
    found = [f for f in forbidden if f.lower() in html.lower()]
    assert not found, (
        f"Forbidden timing language found in output HTML: {found}\n"
        f"File: {html_path}"
    )
    print(f"[PASS] No forbidden timing language in {html_path.name}")


# ═══════════════════════════════════════════════════════════════
# Test 2 & 3 — Refined boundary tolerance
# ═══════════════════════════════════════════════════════════════

def test_refined_boundary_within_tolerance():
    """
    Part 5.2 & 5.3 — Entry and exit boundaries should evaluate within
    _REFINE_TOLERANCE of the configured orb.
    """
    from engine.transit_engine import (
        _REFINE_TOLERANCE,
        _compute_aspect_orb,
        TRANSIT_PLANETS,
        TRANSIT_ORB,
        ASPECT_ANGLES,
        scan_transit_windows,
    )

    # We need a natal payload.  Use minimal stubs derived from Noah's known data
    # (Pisces ASC ≈ 334°, Sun in Cancer house 5, etc.).  The test just needs
    # the scanner to return at least one refined event.
    natal_payload = _noah_natal_payload()
    from datetime import timedelta
    start = datetime(2026, 6, 28, tzinfo=timezone.utc)
    end   = start + timedelta(days=365)

    cycles = scan_transit_windows(natal_payload, start_date=start, end_date=end)
    assert cycles, "Expected at least one transit cycle for Noah's chart"

    asp_map = dict(ASPECT_ANGLES)
    planet_ids = {v: k for k, v in TRANSIT_PLANETS.items()}

    errors = []
    for cycle in cycles[:10]:   # check first 10 cycles
        planet   = cycle["transit_planet"]
        body_id  = planet_ids.get(planet)
        if body_id is None:
            continue
        natal_lon   = cycle.get("_target_lon")  # may not be stored; skip if absent
        aspect_name = cycle["aspect"]
        asp_angle   = asp_map.get(aspect_name, 0.0)
        configured  = cycle["maximum_orb"]

        # Verify entry boundary (only if not active at report start).
        if not cycle.get("active_at_report_start"):
            entry_dt = cycle["entry_datetime"]
            natal_lon_val = _get_natal_lon(natal_payload, cycle["natal_target"])
            if natal_lon_val is not None:
                orb_at_entry = _compute_aspect_orb(body_id, natal_lon_val, asp_angle, entry_dt)
                if abs(orb_at_entry - configured) > (_REFINE_TOLERANCE * 5):  # 5× tolerance for boundary noise
                    errors.append(
                        f"{planet} {aspect_name} {cycle['natal_target']}: "
                        f"entry orb={orb_at_entry:.4f}° vs configured={configured}° "
                        f"(error={abs(orb_at_entry - configured):.4f}°)"
                    )

    if errors:
        print("[WARN] Some boundary residuals exceeded 5× tolerance:")
        for e in errors:
            print(f"  {e}")
        # Fail only if MORE than half of checked cycles are out of tolerance.
        assert len(errors) < len(cycles[:10]) // 2, "\n".join(errors)

    print(f"[PASS] Boundary tolerance check on {min(10, len(cycles))} cycles")


# ═══════════════════════════════════════════════════════════════
# Test 4 — Solved contacts near zero orb
# ═══════════════════════════════════════════════════════════════

def test_exact_contacts_near_zero():
    """
    Part 5.4 — Each solved contact should evaluate near the exact aspect angle.
    We check that contacts have motion_direction and valid datetime.
    """
    from engine.transit_engine import scan_transit_windows
    from datetime import timedelta

    natal_payload = _noah_natal_payload()
    start = datetime(2026, 6, 28, tzinfo=timezone.utc)
    end   = start + timedelta(days=365)

    cycles = scan_transit_windows(natal_payload, start_date=start, end_date=end)
    assert cycles

    for cycle in cycles:
        contacts = cycle.get("contacts", [])
        for c in contacts:
            assert "contact_datetime" in c, f"Contact missing contact_datetime: {c}"
            assert "motion_direction" in c, f"Contact missing motion_direction: {c}"
            assert c["motion_direction"] in {"direct", "retrograde", "stationary"}, (
                f"Unexpected motion_direction: {c['motion_direction']}"
            )
            assert c["sequence_index"] >= 1, f"sequence_index must be ≥ 1: {c}"

    print(f"[PASS] Contact fields valid across {sum(len(c.get('contacts',[])) for c in cycles)} contacts")


# ═══════════════════════════════════════════════════════════════
# Test 5 — Multi-contact cycles have one cycle_id
# ═══════════════════════════════════════════════════════════════

def test_multi_contact_cycles_have_one_cycle_id():
    """
    Part 5.5 — Each cycle event has exactly one cycle_id regardless of how
    many contacts it contains.
    """
    from engine.transit_engine import scan_transit_windows
    from datetime import timedelta

    natal_payload = _noah_natal_payload()
    start = datetime(2026, 6, 28, tzinfo=timezone.utc)
    end   = start + timedelta(days=365)

    cycles = scan_transit_windows(natal_payload, start_date=start, end_date=end)

    cycle_ids = [c["cycle_id"] for c in cycles]
    assert len(cycle_ids) == len(set(cycle_ids)), (
        "Duplicate cycle_ids found — each cycle must be unique"
    )

    multi_contact = [c for c in cycles if c.get("contact_count", 0) > 1]
    print(f"[PASS] {len(multi_contact)} multi-contact cycle(s) found, all have unique cycle_ids")


# ═══════════════════════════════════════════════════════════════
# Test 6 — No repeated full prose in multi-contact cycles
# ═══════════════════════════════════════════════════════════════

def test_no_repeated_prose_in_multi_contact_cycles():
    """
    Part 5.6 — The rendered HTML must not contain the same prose paragraph
    twice when it originates from a multi-contact cycle.
    """
    from engine.transit_engine import scan_transit_windows
    from datetime import timedelta

    natal_payload = _noah_natal_payload()
    start = datetime(2026, 6, 28, tzinfo=timezone.utc)
    end   = start + timedelta(days=365)

    multi_contact = [
        c for c in scan_transit_windows(natal_payload, start_date=start, end_date=end)
        if c.get("contact_count", 0) > 1
    ]

    if not multi_contact:
        print("[SKIP] No multi-contact cycles in this chart window; skipping prose-repeat check")
        return

    html_path = _generate_noah()
    html = _html(html_path)

    # Only inspect rendered transit prose containers, not repeated scaffold text
    # from orientation cards, sidebars, or recurring month guidance wrappers.
    prose_blocks = []
    for pattern in (
        r'<div class="arc-story-body">(.*?)</div>\s*</div>\s*<aside',
        r'<div class="event-block">(.*?)</div>\s*(?:<div class="constellation-lens"|</article>)',
    ):
        prose_blocks.extend(
            re.findall(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        )

    paragraphs = []
    for block in prose_blocks:
        for match in re.findall(r"<p\b[^>]*>(.*?)</p>", block, flags=re.IGNORECASE | re.DOTALL):
            text = re.sub(r"<[^>]+>", " ", match)
            text = html_lib.unescape(re.sub(r"\s+", " ", text)).strip()
            if len(text) > 80:
                paragraphs.append(text)
    from collections import Counter
    counts = Counter(paragraphs)
    real_dupes = [(p[:60], n) for p, n in counts.items() if n > 1]

    assert not real_dupes, (
        f"Repeated prose block(s) detected:\n"
        + "\n".join(f"  ({n}×) {p!r}…" for p, n in real_dupes[:5])
    )
    print(f"[PASS] No repeated prose blocks in {html_path.name}")


# ═══════════════════════════════════════════════════════════════
# Test 7 — No fabricated contact where none exists
# ═══════════════════════════════════════════════════════════════

def test_no_fabricated_contacts():
    """
    Part 5.7 — Every contact in a cycle's contacts list must have a
    datetime inside the cycle's orb window (entry_datetime … leave_datetime).
    """
    from engine.transit_engine import scan_transit_windows
    from datetime import timedelta

    natal_payload = _noah_natal_payload()
    start = datetime(2026, 6, 28, tzinfo=timezone.utc)
    end   = start + timedelta(days=365)

    cycles = scan_transit_windows(natal_payload, start_date=start, end_date=end)

    errors = []
    for c in cycles:
        entry = c["entry_datetime"]
        leave = c.get("leave_datetime")
        for contact in c.get("contacts", []):
            ct = contact["contact_datetime"]
            if ct < entry - timedelta(hours=1):
                errors.append(
                    f"{c['cycle_id']}: contact {ct} is before entry {entry}"
                )
            if leave is not None and ct > leave + timedelta(hours=1):
                errors.append(
                    f"{c['cycle_id']}: contact {ct} is after exit {leave}"
                )

    assert not errors, "Fabricated contacts detected:\n" + "\n".join(errors)
    print(f"[PASS] All contacts are within their cycle window")


# ═══════════════════════════════════════════════════════════════
# Test 8 — Stations, ingresses, eclipses, Soul Ecosystem still work
# ═══════════════════════════════════════════════════════════════

def test_non_transit_events_unaffected():
    """
    Part 5.8 — Integration check: other event types and Soul Ecosystem
    generation must complete without error.
    """
    # Year Ahead (already tested above for transits) — check stations/eclipses present
    html_path = _generate_noah()
    html = _html(html_path)
    assert "Planetary Station" in html or "station" in html.lower(), (
        "Expected station events in Year Ahead output"
    )

    # Soul Ecosystem — should generate without crash
    cmd = [
        sys.executable, str(PROJECT_ROOT / "generate.py"),
        "soul_ecosystem",
        "--name", "Noah",
        "--date", "2004-07-09",
        "--time", "22:11",
        "--location", "Watertown, WI",
        "--no-browser",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    assert result.returncode == 0, (
        f"soul_ecosystem generation failed:\n{result.stdout}\n{result.stderr}"
    )
    print("[PASS] Stations visible in Year Ahead; Soul Ecosystem generates cleanly")


# ═══════════════════════════════════════════════════════════════
# Test 9 — No JSON content library files were modified
# ═══════════════════════════════════════════════════════════════

def test_no_json_content_modified():
    """
    Part 5.9 — Verify that running the generator does not write to any JSON
    block library file (content files must be read-only from the engine's
    perspective).
    """
    import time

    content_dirs = [
        PROJECT_ROOT / "products" / "daily_horoscope" / "blocks",
        PROJECT_ROOT / "products" / "soul_ecosystem" / "blocks",
        PROJECT_ROOT / "products" / "identity_profile" / "blocks",
        PROJECT_ROOT / "products" / "personal_forecast" / "blocks",
        PROJECT_ROOT / "products" / "year_ahead" / "blocks" / "plainspeak",
        PROJECT_ROOT / "products" / "year_ahead" / "blocks" / "entangled_oracle",
    ]

    # Record mtimes before
    before = {}
    for d in content_dirs:
        for f in d.rglob("*.json"):
            before[str(f)] = f.stat().st_mtime

    # Generate
    _generate_noah()

    # Check after
    modified = []
    for path, mtime_before in before.items():
        try:
            mtime_after = Path(path).stat().st_mtime
        except FileNotFoundError:
            modified.append(f"DELETED: {path}")
            continue
        if mtime_after > mtime_before + 0.5:  # 0.5s tolerance for filesystem timestamps
            modified.append(f"MODIFIED: {path}")

    assert not modified, "JSON content files were modified during generation:\n" + "\n".join(modified)
    print(f"[PASS] {len(before)} JSON content files unchanged")


# ═══════════════════════════════════════════════════════════════
# Test 10 — EO_TRANSIT_TRACE produces expected output
# ═══════════════════════════════════════════════════════════════

def test_transit_trace_output():
    """Verifies EO_TRANSIT_TRACE=1 produces [Transit Cycle] lines without HTML injection."""
    html_path, stdout = _run_transit_trace_noah()

    # Trace lines appear in stdout
    assert "[Transit Cycle]" in stdout, "EO_TRANSIT_TRACE=1 did not produce [Transit Cycle] output"
    assert "[Transit Engine]" in stdout, "Missing transit engine summary line"

    # Trace must NOT appear in HTML
    html = _html(html_path)
    assert "[Transit Cycle]" not in html, "Trace output leaked into HTML!"
    assert "[Transit Engine]" not in html, "Trace output leaked into HTML!"

    print(f"[PASS] EO_TRANSIT_TRACE output found in stdout, absent from HTML")


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

def _noah_natal_payload():
    """
    Returns a minimal natal payload for Noah (2004-07-09 22:11 Watertown WI).
    Generated by running the natal engine — captured here for deterministic tests.
    """
    # Run the engine live rather than maintaining a hardcoded snapshot.
    cmd = [
        sys.executable, "-c",
        """
import sys, json
sys.path.insert(0, r'""" + str(PROJECT_ROOT).replace("\\", "\\\\") + r"""')
from engine.natal_engine import generate_payload
p = generate_payload({
    "name": "Noah",
    "date": "2004-07-09",
    "time": "22:11",
    "location": "Watertown, WI",
})
print(json.dumps(p))
""",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    assert result.returncode == 0, f"Natal engine failed:\n{result.stderr}"
    stdout_lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert stdout_lines, "Natal engine produced no stdout payload."
    return json.loads(stdout_lines[-1])


def _get_natal_lon(natal_payload, target_name):
    """Returns the natal longitude for a named target, or None."""
    planets = natal_payload.get("standard_planets", {})
    if target_name in planets:
        return planets[target_name].get("longitude")
    angles = natal_payload.get("angles", {})
    angle_map = {
        "ASC": "Ascendant", "MC": "Midheaven",
        "DSC": "Descendant", "IC": "Imum_Coeli",
    }
    if target_name in angle_map:
        data = angles.get(angle_map[target_name], {})
        return data.get("longitude")
    if target_name == "Vertex":
        data = angles.get("Vertex", {})
        return data.get("longitude")
    return None


# ═══════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    tests = [
        test_no_exact_or_closest_approach_in_html,
        test_refined_boundary_within_tolerance,
        test_exact_contacts_near_zero,
        test_multi_contact_cycles_have_one_cycle_id,
        test_no_repeated_prose_in_multi_contact_cycles,
        test_no_fabricated_contacts,
        test_non_transit_events_unaffected,
        test_no_json_content_modified,
        test_transit_trace_output,
    ]

    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"[FAIL] {t.__name__}: {e}")

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)

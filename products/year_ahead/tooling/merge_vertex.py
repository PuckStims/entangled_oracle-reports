import json
import sys

SOURCE = r"C:\entangled_oracle\EO_Vertex_Transit_Blocks.json"
TARGET = r"C:\entangled_oracle\products\year_ahead\blocks\entangled_oracle\EO_standard_transit_blocks_working.json"

FLOWING = {"Conjunction", "Trine", "Sextile"}
CHALLENGING = {"Square", "Opposition"}
PLANETS = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Mars"]

with open(SOURCE, "r", encoding="utf-8") as f:
    source = json.load(f)

with open(TARGET, "r", encoding="utf-8") as f:
    raw = f.read()

# Detect line endings
crlf = "\r\n" in raw
target = json.loads(raw)

# Inject Vertex entries
for planet in PLANETS:
    flowing_vertex = source[planet]["flowing"]["Vertex"]
    challenging_vertex = source[planet]["challenging"]["Vertex"]
    for aspect in list(target[planet].keys()):
        if aspect == "fallback":
            continue
        if aspect in FLOWING:
            target[planet][aspect]["Vertex"] = flowing_vertex
        elif aspect in CHALLENGING:
            target[planet][aspect]["Vertex"] = challenging_vertex

# Re-serialize with same formatting
out = json.dumps(target, indent=2, ensure_ascii=False)

# Restore line endings if original used CRLF
if crlf:
    out = out.replace("\n", "\r\n")

# Preserve trailing newline if original had one
if raw.endswith("\n") or raw.endswith("\r\n"):
    if not out.endswith("\n"):
        out += "\r\n" if crlf else "\n"

with open(TARGET, "w", encoding="utf-8", newline="") as f:
    f.write(out)

print("Done. Vertex entries injected for all 6 planets x 5 aspect types.")

# Quick sanity check
with open(TARGET, "r", encoding="utf-8") as f:
    check = json.load(f)
for planet in PLANETS:
    for aspect in FLOWING | CHALLENGING:
        assert "Vertex" in check[planet][aspect], f"MISSING: {planet}.{aspect}.Vertex"
print("Validation passed: all 30 Vertex entries present (6 planets x 5 aspect types).")

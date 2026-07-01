import json

TARGET = r"C:\entangled_oracle\products\year_ahead\blocks\entangled_oracle\EO_Standard_Eclipse_Blocks.json"

# Vertex blocks from the source
VERTEX = {
    "Solar": {
        "Conjunction": {
            "Vertex": "Some arrivals announce themselves quietly and change everything anyway. A solar eclipse on your Vertex is one of those moments — what enters the field now carries the weight of a genuine threshold. A person, opportunity, institution, or circumstance may appear that reorients the current chapter in ways that only become clear with time. Eclipse contacts here tend to initiate rather than develop gradually. Notice what shows up in the weeks surrounding this date and treat it with the seriousness it is offering."
        },
        "Opposition": {
            "Vertex": "A solar eclipse opposing your Vertex activates the fated axis from the far side — through relationship, negotiation, or a situation that arrives carrying someone else’s momentum. What enters the field may feel like it belongs to another person’s story at first. It does not. The Vertex axis runs in both directions, and what comes through others still arrives for you. Stay clear about your own position as the contact unfolds. The most useful thing you can offer this moment is an honest read of where you actually stand."
        }
    },
    "Lunar": {
        "Conjunction": {
            "Vertex": "Lunar eclipses on the Vertex have a way of making the previously unacknowledged impossible to overlook. What arrives now may carry emotional weight, relational significance, or the quiet force of something that has been building toward this moment for longer than it appears. A person, realization, or circumstance surfaces and asks to be genuinely seen. Resist the urge to process it too quickly. What a contact like this brings tends to mean more the longer you are willing to sit with it."
        },
        "Opposition": {
            "Vertex": "Something arrives through the relational axis that is harder to receive than to deflect. A lunar eclipse opposing your Vertex can surface tension between what you need and what a person, institution, or circumstance is currently delivering — not as punishment, but as information. The Vertex does not reach out; it receives. What is being brought to you now, even under pressure, belongs to the current chapter. Let the friction be clarifying. What feels like a confrontation may turn out to be an honest introduction."
        }
    }
}

with open(TARGET, "r", encoding="utf-8") as f:
    raw = f.read()

crlf = "\r\n" in raw
target = json.loads(raw)

# Inject Conjunction and Opposition objects (each containing Vertex) into Solar and Lunar
for eclipse_type in ("Solar", "Lunar"):
    for aspect in ("Conjunction", "Opposition"):
        target[eclipse_type][aspect] = VERTEX[eclipse_type][aspect]

out = json.dumps(target, indent=2, ensure_ascii=False)

if crlf:
    out = out.replace("\n", "\r\n")

if raw.endswith("\n") or raw.endswith("\r\n"):
    if not out.endswith("\n"):
        out += "\r\n" if crlf else "\n"

with open(TARGET, "w", encoding="utf-8", newline="") as f:
    f.write(out)

print("Done. Vertex entries injected for Solar and Lunar x Conjunction and Opposition.")

# Validation
with open(TARGET, "r", encoding="utf-8") as f:
    check = json.load(f)

for eclipse in ("Solar", "Lunar"):
    for aspect in ("Conjunction", "Opposition"):
        assert "Vertex" in check[eclipse][aspect], f"MISSING: {eclipse}.{aspect}.Vertex"
        # Existing house keys must still be present
    for house in [str(i) for i in range(1, 13)]:
        assert house in check[eclipse], f"MISSING existing key: {eclipse}.{house}"

print("Validation passed: 4 Vertex entries present, all existing house keys intact.")
print("\nKey order in Solar:", list(check["Solar"].keys()))
print("Key order in Lunar:", list(check["Lunar"].keys()))

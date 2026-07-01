from pathlib import Path
import webbrowser

from constellation_mesh import build_mesh_data, render_mesh_svg

# Temporary mock proprietary index data for visual testing.
# Mimics the output shape of formulas/proprietary_indexes.py
computed_indexes = {
    "KVQ": {
        "score": 0.88, 
        "archetype": "Vindicated Oracle"
    },
    "RWI": {
        "score": 0.42, 
        "archetype": "The Storyteller"
    },
    "MKI": {
        "score": 0.94, 
        "archetype": "The Archivist"
    },
    "NGE": {
        "score": 0.65, 
        "archetype": "The Epic"
    },
    "DFIS": {
        "score": 0.76, 
        "archetype": "The Sovereign Queen"
    },
    "CATALYST": {
        "score": 0.35, 
        "archetype": "The Awakener"
    }
}

mesh_data = build_mesh_data(
    computed_indexes,
)

svg = render_mesh_svg(
    mesh_data,
    variant="medium",
    show_labels=True,
)

html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Constellation Mesh Preview</title>
    <style>
        body {{
            margin: 0;
            padding: 48px;
            background: #05050a; /* Darker backdrop to frame the mesh */
            font-family: Arial, sans-serif;
            color: #E7E9F1;
        }}

        main {{
            max-width: 800px;
            margin: auto;
            background: #0d0d1a; /* Matches the mesh SVG background */
            padding: 36px;
            border-radius: 14px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            border: 1px solid #25253a;
        }}

        h1 {{
            margin-top: 0;
            margin-bottom: 24px;
            font-size: 24px;
            text-align: center;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #C8CDE8;
        }}
        
        .svg-container {{
            display: flex;
            justify-content: center;
        }}
    </style>
</head>
<body>
    <main>
        <h1>Constellation Mesh — Visual Test</h1>
        <div class="svg-container">
            {svg}
        </div>
    </main>
</body>
</html>
"""

output_path = Path("constellation_mesh_preview.html").resolve()
output_path.write_text(html, encoding="utf-8")

print(f"Created preview: {output_path}")
webbrowser.open(output_path.as_uri())
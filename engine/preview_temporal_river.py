from pathlib import Path
import webbrowser

from temporal_river import build_temporal_river_data, render_temporal_river_svg


# Temporary mock forecast data for visual testing.
# Each score should generally be between 0.0 and 1.0.
months = [
    {"label": "Jun", "score": 0.35, "theme": "inner_life_rest"},
    {"label": "Jul", "score": 0.52, "theme": "career_visibility"},
    {"label": "Aug", "score": 0.44, "theme": "relationship_focus"},
    {"label": "Sep", "score": 0.61, "theme": "structural_growth"},
    {"label": "Oct", "score": 0.76, "theme": "transformation"},
    {"label": "Nov", "score": 0.94, "theme": "career_visibility"},
    {"label": "Dec", "score": 0.64, "theme": "inner_life_rest"},
    {"label": "Jan", "score": 0.49, "theme": "relationship_focus"},
    {"label": "Feb", "score": 0.82, "theme": "transformation"},
    {"label": "Mar", "score": 0.57, "theme": "structural_growth"},
    {"label": "Apr", "score": 0.42, "theme": "career_visibility"},
    {"label": "May", "score": 0.30, "theme": "inner_life_rest"},
]

events = [
    {"month_index": 5, "label": "Peak window"},
    {"month_index": 8, "label": "Turning point"},
]

river_data = build_temporal_river_data(
    months,
    palette_name="vibrant",
    events=events,
)

svg = render_temporal_river_svg(
    river_data,
    variant="wide",
    show_labels=True,
)

html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Temporal River Preview</title>
    <style>
        body {{
            margin: 0;
            padding: 48px;
            background: #f7f7f5;
            font-family: Arial, sans-serif;
        }}

        main {{
            max-width: 1200px;
            margin: auto;
            background: white;
            padding: 36px;
            border-radius: 14px;
            box-shadow: 0 8px 28px rgba(0, 0, 0, 0.10);
        }}

        h1 {{
            margin-top: 0;
            font-size: 24px;
        }}
    </style>
</head>
<body>
    <main>
        <h1>Temporal River — Visual Test</h1>
        {svg}
    </main>
</body>
</html>
"""

output_path = Path("temporal_river_preview.html").resolve()
output_path.write_text(html, encoding="utf-8")

print(f"Created preview: {output_path}")
webbrowser.open(output_path.as_uri())
import os

with open("C:/entangled_oracle/generate.py", "r", encoding="utf-8") as f:
    content = f.read()

# Target 1
target1 = """    payload = get_payload(birth_data)

    _log_verbose("[Formulas] Computing indexes...")"""
replacement1 = """    payload = get_payload(birth_data)

    LOCATION_SERVICES_TYPES = {
        "place_resonance",
        "place_resonance_search",
        "world_lines",
        "local_compass",
        "living_map",
    }
    
    if report_type in LOCATION_SERVICES_TYPES:
        dest = {"location": birth_data.get("destination") or birth_data.get("current_location") or birth_data["location"], "display_name": birth_data.get("destination") or birth_data.get("current_location") or birth_data["location"]}
        
        if report_type == "place_resonance":
            from products.location_services.place_resonance.renderer import build_place_resonance_html
            html = build_place_resonance_html(payload, dest)
        elif report_type == "place_resonance_search":
            from products.location_services.place_resonance_search.renderer import build_place_resonance_search_html
            html = build_place_resonance_search_html(payload)
        elif report_type == "world_lines":
            from products.location_services.world_lines_companion.renderer import build_world_lines_html
            html = build_world_lines_html(payload, dest)
        elif report_type == "local_compass":
            from products.location_services.local_compass.renderer import build_local_compass_html
            html = build_local_compass_html(payload, dest)
        elif report_type == "living_map":
            from products.location_services.living_map.renderer import build_living_map_html
            html = build_living_map_html(payload, dest)
        else:
            html = "<html><body>Not implemented</body></html>"
            
        if output_filename is None:
            output_filename = _default_output_filename(report_type, birth_data, datetime.now(timezone.utc))
            
        effective_dir = output_dir if output_dir else OUTPUT_DIR
        output_path = os.path.join(effective_dir, output_filename)
        os.makedirs(effective_dir, exist_ok=True)
        _atomic_write_text(output_path, html)
        print(f"[Done] Report saved: {os.path.basename(output_path)}")
        return output_path

    _log_verbose("[Formulas] Computing indexes...")"""

# Target 2
target2 = """    parser.add_argument("report_type",
        choices=["horoscope", "weekly_horoscope", "year_ahead", "personal_forecast", "soul_ecosystem", "identity_profile"],
        help="Type of report to generate"
    )"""
replacement2 = """    parser.add_argument("report_type",
        choices=["horoscope", "weekly_horoscope", "year_ahead", "personal_forecast", "soul_ecosystem", "identity_profile", "place_resonance", "place_resonance_search", "world_lines", "local_compass", "living_map"],
        help="Type of report to generate"
    )"""

# Target 3
target3 = """    parser.add_argument("--simple",   action="store_true",
                        help="Simple mode: DOB only, no birth time needed")
    parser.add_argument("--no-browser", action="store_true","""
replacement3 = """    parser.add_argument("--simple",   action="store_true",
                        help="Simple mode: DOB only, no birth time needed")
    parser.add_argument("--destination", required=False, help="Destination place name for location services")
    parser.add_argument("--no-browser", action="store_true","""

# Target 4
target4 = """    birth_data["current_location"] = args.current_location or args.location or ""

    output_filename = args.output_filename or args.output"""
replacement4 = """    birth_data["current_location"] = args.current_location or args.location or ""
    birth_data["destination"] = getattr(args, "destination", None)

    output_filename = args.output_filename or args.output"""

content = content.replace(target1, replacement1)
content = content.replace(target2, replacement2)
content = content.replace(target3, replacement3)
content = content.replace(target4, replacement4)

with open("C:/entangled_oracle/generate.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Done patching")

"""
engine/natal_engine.py — Entangled Oracle Natal Chart Engine

Uses:
- Swiss Ephemeris for planetary, asteroid, angle, and node positions
- Whole Sign houses for all house assignments
- Offline-first place resolution with optional Geopy fallback

Payload output is designed for the Entangled Oracle formula,
selector, and report-rendering layers.
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import swisseph as swe
from engine.offline_place_resolver import (
    AmbiguousLocationError,
    LocationResolutionError,
    UnresolvedLocationError,
    resolve_place,
    resolve_timezone,
)

from formulas.standard.confidence import (
    APPROXIMATE_BIRTH_TIME,
    EXACT_BIRTH_TIME,
    UNKNOWN_BIRTH_TIME,
)
from formulas.standard.methodology_profiles import get_active_methodology_metadata


class ChartCalculationError(ValueError):
    """Raised when a valid birth location/time cannot be turned into a chart
    (e.g. extreme polar latitudes where house-angle math is undefined)."""


# ── Paths and Swiss Ephemeris Setup ─────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPHE_PATH = os.path.join(PROJECT_ROOT, "ephemeris")

swe.set_ephe_path(EPHE_PATH)

# Ask Swiss Ephemeris for Swiss ephemeris data and planetary speed.
CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED


# ── Location Services ──────────────────────────────────────────

# ── Chart Bodies ───────────────────────────────────────────────

STANDARD_PLANETS = {
    swe.SUN: "Sun",
    swe.MOON: "Moon",
    swe.MERCURY: "Mercury",
    swe.VENUS: "Venus",
    swe.MARS: "Mars",
    swe.JUPITER: "Jupiter",
    swe.SATURN: "Saturn",
    swe.URANUS: "Uranus",
    swe.NEPTUNE: "Neptune",
    swe.PLUTO: "Pluto",
    swe.CHIRON: "Chiron",
}


# Swiss Ephemeris asteroid IDs use:
# 10000 + asteroid number
#
# Example:
# 212 Medea  -> 10212
# 1912 Anubis -> 11912

ASTEROID_DICTIONARY = {
    11009: "Sirene",
    11388: "Aphrodite",
    11862: "Apollo",

    10114: "Kassandra",
    13811: "Karma",
    16583: "Destinn",

    10057: "Mnemosyne",
    11198: "Atlantis",
    10251: "Sophia",

    10407: "Arachne",
    29521: "Chaos",
    79230: "Hermes",

    10024: "Themis",
    10027: "Euterpe",
    10030: "Urania",
    10033: "Polyhymnia",
    10034: "Circe",
    10042: "Isis",
    10056: "Melete",

    10080: "Sappho",
    10081: "Terpsichore",
    10093: "Minerva",
    10100: "Hekate",

    10212: "Medea",
    10259: "Aletheia",

    10389: "Industria",
    10390: "Alma",
    10638: "Moirai",

    11181: "Lilith_Asteroid",
    11912: "Anubis",

    14227: "Kaali",
    14580: "Child",
    21911: "Angel",
    65555: "DNA",
}


SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


# Store all major aspects found within 10 degrees.
# The formulas layer applies each formula's actual configured orb later.
ASPECTS = [
    ("Conjunction", 0),
    ("Sextile", 60),
    ("Quintile", 72),
    ("Square", 90),
    ("Trine", 120),
    ("Biquintile", 144),
    ("Opposition", 180),
]

ASPECT_SCAN_ORB = 10.0


# ── Position Helpers ───────────────────────────────────────────

def zodiac_position(longitude: float) -> dict:
    """Returns sign, degree, minute, decimal degree, and display formatting."""
    longitude = longitude % 360
    sign_index = int(longitude // 30)
    degree_decimal = longitude % 30

    return {
        "sign": SIGNS[sign_index],
        "degree": int(degree_decimal),
        "minute": int((degree_decimal % 1) * 60),
        "degree_decimal": round(degree_decimal, 4),
        "formatted": f"{degree_decimal:.2f}° {SIGNS[sign_index]}",
    }


def is_retrograde(speed: float) -> bool:
    """Returns True when a body's apparent longitudinal speed is retrograde."""
    return speed < 0


def angular_distance(longitude_a: float, longitude_b: float) -> float:
    """Shortest distance between two positions on the zodiac wheel."""
    difference = abs((longitude_a - longitude_b) % 360)
    return min(difference, 360 - difference)


def detect_aspect(longitude_a: float, longitude_b: float) -> dict | None:
    """
    Detects a major aspect inside the broad payload scan orb.

    Formula functions later decide whether an aspect is valid under
    their more specific configured orb rules.
    """
    distance = angular_distance(longitude_a, longitude_b)

    for aspect_name, aspect_angle in ASPECTS:
        orb = abs(distance - aspect_angle)

        if orb <= ASPECT_SCAN_ORB:
            return {
                "aspect": aspect_name,
                "orb": round(orb, 4),
                "angle": round(distance, 4),
            }

    return None


# ── Whole Sign Houses ──────────────────────────────────────────

def whole_sign_house(longitude: float, ascendant_longitude: float) -> int:
    """
    Returns the Whole Sign house number for a body.

    The sign containing the Ascendant is House 1.
    Every following zodiac sign is the next house.

    Example:
    Ascendant in Taurus:
    Taurus = House 1
    Gemini = House 2
    Cancer = House 3
    """
    body_sign_index = int((longitude % 360) // 30)
    ascendant_sign_index = int((ascendant_longitude % 360) // 30)

    return ((body_sign_index - ascendant_sign_index) % 12) + 1


def generate_whole_sign_houses(ascendant_longitude: float) -> dict:
    """
    Creates the twelve Whole Sign house cusps.

    In Whole Sign astrology, House 1 begins at 0° of the Ascendant sign,
    not at the Ascendant's exact degree.
    """
    ascendant_sign_index = int((ascendant_longitude % 360) // 30)
    houses = {}

    for index in range(12):
        sign_index = (ascendant_sign_index + index) % 12
        cusp_longitude = sign_index * 30.0

        houses[f"House_{index + 1}"] = {
            "longitude": round(cusp_longitude, 4),
            **zodiac_position(cusp_longitude),
        }

    return houses


# ── Data Builders ──────────────────────────────────────────────


def _is_cazimi(longitude: float, sun_longitude: float | None) -> bool:
    """Returns True when a body is within 1° of the Sun (cazimi)."""
    if sun_longitude is None:
        return False
    sep = abs((longitude - sun_longitude) % 360)
    if sep > 180:
        sep = 360 - sep
    return sep <= 1.0

def build_body_data(
    longitude: float,
    speed: float,
    ascendant_longitude: float,
    sun_longitude: float = None,
) -> dict:
    """Creates one standardized body record for the Entangled Oracle payload."""
    return {
        "longitude": round(longitude % 360, 4),
        "speed": round(speed, 4),
        "retrograde": is_retrograde(speed),
        "cazimi": _is_cazimi(longitude, sun_longitude),
        "house": whole_sign_house(longitude, ascendant_longitude),
        **zodiac_position(longitude),
    }


def build_angle_data(longitude: float) -> dict:
    """Creates a standardized angle record."""
    return {
        "longitude": round(longitude % 360, 4),
        **zodiac_position(longitude),
    }


def _resolve_location_online(location_name: str) -> dict:
    """Uses Nominatim only when the local packaged data has no match."""
    try:
        from geopy.geocoders import Nominatim
    except Exception as exc:
        raise UnresolvedLocationError(
            f"Could not resolve location \"{location_name}\" offline, and online lookup is unavailable."
        ) from exc

    try:
        geolocator = Nominatim(user_agent="entangled_oracle_engine", timeout=10)
        location_data = geolocator.geocode(location_name)
    except Exception as exc:
        raise UnresolvedLocationError(
            f"Could not resolve location \"{location_name}\" offline, and the online lookup failed. "
            "Please try a fuller city/state/country format."
        ) from exc

    if not location_data:
        raise UnresolvedLocationError(
            f"Could not resolve location \"{location_name}\". "
            "Please include a fuller city/state/country format."
        )

    latitude = round(float(location_data.latitude), 4)
    longitude = round(float(location_data.longitude), 4)

    return {
        "display_name": getattr(location_data, "address", None) or location_name,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": resolve_timezone(latitude, longitude),
        "source": "online_nominatim",
    }


def _resolve_location(location_name: str) -> dict:
    try:
        return resolve_place(location_name)
    except AmbiguousLocationError:
        raise
    except UnresolvedLocationError as offline_error:
        print("[Engine] Offline resolver had no unique match. Trying optional online fallback...")
        try:
            return _resolve_location_online(location_name)
        except LocationResolutionError:
            raise offline_error


def _is_nonexistent_local_time(naive_dt: datetime, timezone_name: str) -> bool:
    """
    Detects a "spring forward" DST-gap wall-clock time that never actually
    occurred in the given zone (e.g. 2:30 AM on the day a zone jumps from
    2:00 AM to 3:00 AM). zoneinfo silently resolves such times to a UTC
    offset rather than raising, so we round-trip through UTC and back —
    a gap time will not survive the round trip unchanged.
    """
    tz = ZoneInfo(timezone_name)
    aware = naive_dt.replace(tzinfo=tz)
    utc_dt = aware.astimezone(ZoneInfo("UTC"))
    round_tripped = utc_dt.astimezone(tz).replace(tzinfo=None)
    return round_tripped != naive_dt


# ── Main Chart Generator ───────────────────────────────────────

def generate_payload(birth_data: dict) -> dict:
    """
    Main Entangled Oracle natal chart entry point.

    Required birth_data keys:
        name
        date      YYYY-MM-DD
        location  city, state/country

    Optional:
        time      HH:MM or HH:MM:SS
        simple_mode

    Returns the complete normalized chart payload used by:
        - proprietary formula indexes
        - variable resolver
        - transit engine
        - report generators
    """

    location_name = birth_data.get("location")
    if not location_name:
        raise ValueError("Birth location is required.")
    date_string = birth_data.get("date")

    if not date_string:
        raise ValueError("Birth date is required in YYYY-MM-DD format.")

    time_string = birth_data.get("time")
    is_simple_mode = bool(birth_data.get("simple_mode") or not time_string)
    birth_time_state = UNKNOWN_BIRTH_TIME if is_simple_mode else EXACT_BIRTH_TIME
    methodology = get_active_methodology_metadata()

    # Simple mode intentionally uses noon as an approximate chart time.
    if is_simple_mode:
        time_string = "12:00:00"

    if len(time_string.split(":")) == 2:
        time_string += ":00"

    # ── Resolve Location ───────────────────────────────────────

    print("[Engine] Resolving birth location...")

    resolved_location = _resolve_location(location_name)
    latitude = resolved_location["latitude"]
    longitude = resolved_location["longitude"]
    timezone_name = resolved_location["timezone"]

    print(
        "[Engine] Location resolved: "
        f"{resolved_location['source']} lookup succeeded."
    )

    # ── Convert Local Birth Time to Julian Day ─────────────────

    naive_local_datetime = datetime.strptime(
        f"{date_string} {time_string}",
        "%Y-%m-%d %H:%M:%S",
    )

    if not is_simple_mode and _is_nonexistent_local_time(naive_local_datetime, timezone_name):
        print(
            "[Engine] Warning: Provided local birth time falls inside a DST "
            "spring-forward gap for the resolved timezone. "
            "Treating birth time as approximate rather than exact."
        )
        birth_time_state = APPROXIMATE_BIRTH_TIME

    local_datetime = naive_local_datetime.replace(tzinfo=ZoneInfo(timezone_name))

    utc_datetime = local_datetime.astimezone(ZoneInfo("UTC"))

    decimal_hour_utc = (
        utc_datetime.hour
        + (utc_datetime.minute / 60.0)
        + (utc_datetime.second / 3600.0)
    )

    julian_day = swe.julday(
        utc_datetime.year,
        utc_datetime.month,
        utc_datetime.day,
        decimal_hour_utc,
    )

    # ── Angles ─────────────────────────────────────────────────
    #
    # We retain Swiss Ephemeris's house calculation call solely
    # to obtain reliable astronomical angles:
    # Ascendant, Midheaven, Vertex, etc.
    #
    # We do NOT use Placidus cusps for house assignment.
    #
    # Placidus cusps are mathematically degenerate inside the polar
    # circles (roughly beyond +/-66.5 deg latitude) and swe.houses can
    # raise there. Since only ascmc (Ascendant/MC/Vertex) is used below,
    # retry with Porphyry — a simple trisection system with no polar
    # degeneracy — before giving up with a clear, catchable error.
    try:
        _cusps, ascmc = swe.houses(julian_day, latitude, longitude, b"P")
    except swe.Error:
        try:
            _cusps, ascmc = swe.houses(julian_day, latitude, longitude, b"O")
        except swe.Error as exc:
            raise ChartCalculationError(
                f"Could not calculate chart angles for this birth location "
                f"(latitude {latitude}°). Extreme polar latitudes can fall "
                f"outside what the house-angle calculation supports. "
                f"Original error: {exc}"
            ) from exc

    ascendant = ascmc[0]
    midheaven = ascmc[1]
    vertex = ascmc[3]

    descendant = (ascendant + 180) % 360
    imum_coeli = (midheaven + 180) % 360

    # ── Start Payload ──────────────────────────────────────────

    master_payload = {
        "simple_mode": is_simple_mode,
        "location": resolved_location["display_name"],
        "birth_location": resolved_location["display_name"],
        "user_profile": {
            "queried_location": location_name,
            "resolved_location": resolved_location["display_name"],
            "resolved_coordinates": {
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
            },
            "timezone": timezone_name,
            "local_datetime": local_datetime.isoformat(),
            "utc_datetime": utc_datetime.isoformat(),
            "julian_day": julian_day,
            "house_system": methodology["house_system"],
            "simple_mode": is_simple_mode,
            "birth_time_state": birth_time_state,
            "birth_time_confidence": birth_time_state,
            "methodology_id": methodology["id"],
            "methodology_label": methodology["label"],
            "zodiac": methodology["zodiac"],
            "methodology": methodology,
        },
        "angles": {
            "Ascendant": build_angle_data(ascendant),
            "Midheaven": build_angle_data(midheaven),
            "Descendant": build_angle_data(descendant),
            "Imum_Coeli": build_angle_data(imum_coeli),
            "Vertex": {
                **build_angle_data(vertex),
                "house": whole_sign_house(vertex, ascendant),
            },
        },
        "houses": generate_whole_sign_houses(ascendant),
        "standard_planets": {},
        "custom_asteroids": {},
        "aspects": [],
    }

    # ── Standard Planets ───────────────────────────────────────

    # Pre-compute Sun longitude for cazimi detection
    _sun_coords, _sun_flag = swe.calc_ut(julian_day, swe.SUN, CALC_FLAGS)
    _sun_longitude = float(_sun_coords[0] % 360)

    for body_id, body_name in STANDARD_PLANETS.items():
        coordinates, _flag = swe.calc_ut(
            julian_day,
            body_id,
            CALC_FLAGS,
        )

        body_longitude = coordinates[0]
        body_speed = coordinates[3]

        master_payload["standard_planets"][body_name] = build_body_data(
            body_longitude,
            body_speed,
            ascendant,
            sun_longitude=_sun_longitude,
        )

    # ── True North and South Nodes ─────────────────────────────

    north_node_coordinates, _flag = swe.calc_ut(
        julian_day,
        swe.TRUE_NODE,
        CALC_FLAGS,
    )

    north_node_longitude = north_node_coordinates[0]
    north_node_speed = north_node_coordinates[3]

    south_node_longitude = (north_node_longitude + 180) % 360

    master_payload["standard_planets"]["North_Node"] = build_body_data(
        north_node_longitude,
        north_node_speed,
        ascendant,
        sun_longitude=_sun_longitude,
    )

    master_payload["standard_planets"]["South_Node"] = build_body_data(
        south_node_longitude,
        north_node_speed,
        ascendant,
        sun_longitude=_sun_longitude,
    )

    # ── Black Moon Lilith: Mean Lunar Apogee ───────────────────

    bml_coordinates, _flag = swe.calc_ut(
        julian_day,
        swe.MEAN_APOG,
        CALC_FLAGS,
    )

    bml_longitude = bml_coordinates[0]
    bml_speed = bml_coordinates[3]

    master_payload["standard_planets"]["Lilith_BML"] = build_body_data(
        bml_longitude,
        bml_speed,
        ascendant,
        sun_longitude=_sun_longitude,
    )

    # ── Custom Asteroids ───────────────────────────────────────

    for body_id, asteroid_name in ASTEROID_DICTIONARY.items():
        try:
            coordinates, _flag = swe.calc_ut(
                julian_day,
                body_id,
                CALC_FLAGS,
            )

            asteroid_longitude = coordinates[0]
            asteroid_speed = coordinates[3]

            master_payload["custom_asteroids"][asteroid_name] = build_body_data(
                asteroid_longitude,
                asteroid_speed,
                ascendant,
                sun_longitude=_sun_longitude,
            )

        except Exception as error:
            # This is intentional graceful handling.
            # A missing asteroid ephemeris file should not crash the report.
            master_payload["custom_asteroids"][asteroid_name] = (
                f"Calculation failed: {error}"
            )


    # ── Declination Computation ──────────────────────────────────
    # Second ephemeris call per body for equatorial coordinates.
    # Pattern from engine/world_lines.py L92.

    for body_id, body_name in STANDARD_PLANETS.items():
        try:
            eq_coords, _eq_flag = swe.calc_ut(
                julian_day, body_id, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL,
            )
            master_payload["standard_planets"][body_name]["declination"] = round(float(eq_coords[1]), 4)
        except Exception:
            pass

    for body_id, asteroid_name in ASTEROID_DICTIONARY.items():
        body_data = master_payload["custom_asteroids"].get(asteroid_name)
        if not isinstance(body_data, dict):
            continue
        try:
            eq_coords, _eq_flag = swe.calc_ut(
                julian_day, body_id, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL,
            )
            body_data["declination"] = round(float(eq_coords[1]), 4)
        except Exception:
            pass

    for _node_id, _node_name in [(swe.TRUE_NODE, 'North_Node'), (swe.MEAN_APOG, 'Lilith_BML')]:
        try:
            eq_coords, _eq_flag = swe.calc_ut(
                julian_day, _node_id, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL,
            )
            if _node_name in master_payload["standard_planets"]:
                master_payload["standard_planets"][_node_name]["declination"] = round(float(eq_coords[1]), 4)
            if _node_name == 'North_Node':
                sn = master_payload["standard_planets"].get("South_Node")
                if isinstance(sn, dict):
                    sn["declination"] = round(-float(eq_coords[1]), 4)
        except Exception:
            pass

    # ── Natal Aspect Matrix ────────────────────────────────────
    #
    # Includes planets, nodes, Black Moon Lilith, asteroids, and the
    # independent chart angles used as aspect targets.
    #
    # Descendant and Imum_Coeli are derived from Ascendant and Midheaven, so
    # treating them as separate aspect targets would double-count every axis
    # contact. Vertex remains because it is an independent calculated point.

    all_bodies = {}

    all_bodies.update(master_payload["standard_planets"])

    all_bodies.update({
        name: data
        for name, data in master_payload["custom_asteroids"].items()
        if isinstance(data, dict)
    })

    all_bodies.update({
        name: data
        for name, data in master_payload["angles"].items()
        if name in {"Ascendant", "Midheaven", "Vertex"}
    })

    body_names = list(all_bodies.keys())

    for index_a in range(len(body_names)):
        for index_b in range(index_a + 1, len(body_names)):
            body_a_name = body_names[index_a]
            body_b_name = body_names[index_b]

            aspect = detect_aspect(
                all_bodies[body_a_name]["longitude"],
                all_bodies[body_b_name]["longitude"],
            )

            if aspect:
                master_payload["aspects"].append({
                    "body_1": body_a_name,
                    "body_2": body_b_name,
                    **aspect,
                })


    # ── Declination Aspects (Parallel / Contraparallel) ────────
    declination_aspects = []
    decl_body_names = [
        n for n in all_bodies
        if isinstance(all_bodies[n], dict) and 'declination' in all_bodies[n]
    ]
    for idx_a in range(len(decl_body_names)):
        for idx_b in range(idx_a + 1, len(decl_body_names)):
            name_a = decl_body_names[idx_a]
            name_b = decl_body_names[idx_b]
            dec_a = all_bodies[name_a]['declination']
            dec_b = all_bodies[name_b]['declination']
            if abs(dec_a - dec_b) <= 1.0:
                declination_aspects.append({
                    "body_1": name_a, "body_2": name_b,
                    "aspect": "Parallel",
                    "orb": round(abs(dec_a - dec_b), 4),
                    "character": "flowing",
                    "declination_aspect": True,
                })
            elif abs(dec_a + dec_b) <= 1.0:
                declination_aspects.append({
                    "body_1": name_a, "body_2": name_b,
                    "aspect": "Contraparallel",
                    "orb": round(abs(dec_a + dec_b), 4),
                    "character": "challenging",
                    "declination_aspect": True,
                })
    master_payload["declination_aspects"] = declination_aspects

    print(
        "[Engine] Chart complete: "
        f"{len(master_payload['standard_planets'])} standard bodies, "
        f"{len(master_payload['custom_asteroids'])} asteroid records, "
        f"{len(master_payload['aspects'])} major aspects."
    )

    return master_payload

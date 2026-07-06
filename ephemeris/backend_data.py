import os
import swisseph as swe
from geopy.geocoders import Nominatim
from datetime import datetime
from zoneinfo import ZoneInfo
from timezonefinder import TimezoneFinder
from copy import deepcopy
import json

# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPHE_PATH = os.path.join(PROJECT_ROOT, "ephemeris")
swe.set_ephe_path(EPHE_PATH)

FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

geolocator = Nominatim(user_agent="entangled_oracle_engine")
tf = TimezoneFinder()

SENSITIVE_USER_PROFILE_KEYS = {
    "name",
    "querent_name",
    "birth_date",
    "birth_time",
    "queried_location",
    "resolved_location",
    "generation_location",
    "timezone",
    "local_datetime",
    "utc_datetime",
}

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

# Swiss Ephemeris asteroid rule:
# asteroid catalog number + 10000
ASTEROID_DICTIONARY = {
    # Core EAS / Entangled Oracle bodies
    11009: "Sirene",       # 1009 Sirene
    11388: "Aphrodite",    # 1388 Aphrodite
    11862: "Apollo",       # 1862 Apollo
    10114: "Kassandra",    # 114 Kassandra
    13811: "Karma",        # 3811 Karma
    16583: "Destinn",      # 6583 Destinn
    10057: "Mnemosyne",    # 57 Mnemosyne
    11198: "Atlantis",     # 1198 Atlantis
    10251: "Sophia",       # 251 Sophia
    10407: "Arachne",      # 407 Arachne
    29521: "Chaos",        # 19521 Chaos
    79230: "Hermes",       # 69230 Hermes

    # Existing support bodies
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
    10259: "Aletheia",
    10389: "Industria",
    10390: "Alma",
    10638: "Moirai",
    11181: "Lilith",
    14227: "Kaali",
    14580: "Child",
    21911: "Angel",
    65555: "DNA",

    # Replacement bodies
    10151: "Abundantia",   # replaces Fortuna
    10677: "Felicitas",    # replaces Tyche, per your chosen file set
    10128: "Nemesis",      # replaces Medea
    11923: "Osiris",       # replaces Anubis
    11221: "Amor",         # replaces Eros
    10055: "Pandora",      # replaces Psyche
    11981: "Sympatia",     # replaces Union, verify locally
    10003: "Juno",
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

ASPECTS = {
    "Conjunction": (0, 6),
    "Sextile": (60, 4),
    "Square": (90, 5),
    "Trine": (120, 5),
    "Opposition": (180, 6),
}

# ============================================================
# HELPERS
# ============================================================

def zodiac_position(longitude):
    longitude = longitude % 360
    sign_index = int(longitude // 30)
    degree_decimal = longitude % 30

    return {
        "sign": SIGNS[sign_index],
        "degree": int(degree_decimal),
        "minute": int((degree_decimal % 1) * 60),
        "degree_decimal": round(degree_decimal, 4),
        "formatted": f"{degree_decimal:.2f}° {SIGNS[sign_index]}"
    }


def is_retrograde(speed):
    return speed < 0


def angle_difference(a, b):
    diff = abs((a - b) % 360)
    return min(diff, 360 - diff)


def detect_aspect(lon1, lon2):
    diff = angle_difference(lon1, lon2)

    for name, (angle, orb) in ASPECTS.items():
        if abs(diff - angle) <= orb:
            return {
                "aspect": name,
                "orb": round(abs(diff - angle), 4),
                "angle": round(diff, 4)
            }

    return None


def find_house(longitude, house_cusps):
    longitude = longitude % 360
    cusps = [c % 360 for c in house_cusps]

    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]

        if start < end:
            if start <= longitude < end:
                return i + 1
        else:
            if longitude >= start or longitude < end:
                return i + 1

    return None


def calculate_body(julian_day, body_id, house_cusps):
    coordinates, flag = swe.calc_ut(julian_day, body_id, FLAGS)

    longitude = coordinates[0]
    speed = coordinates[3]

    return {
        "longitude": round(longitude, 4),
        "speed": round(speed, 4),
        "retrograde": is_retrograde(speed),
        "house": find_house(longitude, house_cusps),
        **zodiac_position(longitude)
    }


# ============================================================
# MAIN PAYLOAD GENERATOR
# ============================================================

def generate_payload(birth_data: dict) -> dict:
    location_name = birth_data.get("location", "Greenwich, UK")
    date_str = birth_data.get("date")

    time_str = birth_data.get("time")
    if not time_str or birth_data.get("simple_mode"):
        time_str = "12:00:00"

    if len(time_str.split(":")) == 2:
        time_str += ":00"

    print("[Engine] Resolving birth location...")
    location_data = geolocator.geocode(location_name)

    if not location_data:
        raise ValueError(f"Could not resolve location '{location_name}'.")

    lat = location_data.latitude
    lon = location_data.longitude

    timezone_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"

    print("[Engine] Geolocation success: lookup succeeded.")

    local_dt = datetime.strptime(
        f"{date_str} {time_str}",
        "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=ZoneInfo(timezone_name))

    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

    decimal_hour_utc = (
        utc_dt.hour +
        utc_dt.minute / 60.0 +
        utc_dt.second / 3600.0
    )

    julian_day = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        decimal_hour_utc
    )

    house_cusps, ascmc = swe.houses(julian_day, lat, lon, b"P")

    ascendant = ascmc[0]
    midheaven = ascmc[1]
    descendant = (ascendant + 180) % 360
    imum_coeli = (midheaven + 180) % 360
    vertex_lon = ascmc[3]

    payload = {
        "user_profile": {
            "queried_location": location_name,
            "resolved_coordinates": {
                "latitude": round(lat, 4),
                "longitude": round(lon, 4)
            },
            "timezone": timezone_name,
            "local_datetime": local_dt.isoformat(),
            "utc_datetime": utc_dt.isoformat(),
            "julian_day": julian_day
        },
        "angles": {
            "Ascendant": {
                "longitude": round(ascendant, 4),
                **zodiac_position(ascendant)
            },
            "Midheaven": {
                "longitude": round(midheaven, 4),
                **zodiac_position(midheaven)
            },
            "Descendant": {
                "longitude": round(descendant, 4),
                **zodiac_position(descendant)
            },
            "Imum_Coeli": {
                "longitude": round(imum_coeli, 4),
                **zodiac_position(imum_coeli)
            },
            "Vertex": {
                "longitude": round(vertex_lon, 4),
                **zodiac_position(vertex_lon)
            }
        },
        "houses": {},
        "standard_planets": {},
        "custom_asteroids": {},
        "aspects": []
    }

    for i in range(12):
        cusp = house_cusps[i]
        payload["houses"][f"House_{i + 1}"] = {
            "longitude": round(cusp, 4),
            **zodiac_position(cusp)
        }

    for body_id, name in STANDARD_PLANETS.items():
        payload["standard_planets"][name] = calculate_body(
            julian_day,
            body_id,
            house_cusps
        )

    bml, flag = swe.calc_ut(julian_day, swe.MEAN_APOG, FLAGS)
    bml_lon = bml[0]

    payload["standard_planets"]["Lilith_BML"] = {
        "longitude": round(bml_lon, 4),
        "speed": round(bml[3], 4),
        "retrograde": is_retrograde(bml[3]),
        "house": find_house(bml_lon, house_cusps),
        **zodiac_position(bml_lon)
    }

    for body_id, name in ASTEROID_DICTIONARY.items():
        try:
            payload["custom_asteroids"][name] = calculate_body(
                julian_day,
                body_id,
                house_cusps
            )
        except Exception as e:
            payload["custom_asteroids"][name] = {
                "error": True,
                "message": str(e),
                "swe_id": body_id
            }

    all_bodies = {}

    all_bodies.update(payload["standard_planets"])

    all_bodies.update({
        name: data
        for name, data in payload["custom_asteroids"].items()
        if isinstance(data, dict) and not data.get("error")
    })

    all_bodies.update(payload["angles"])

    body_names = list(all_bodies.keys())

    for i in range(len(body_names)):
        for j in range(i + 1, len(body_names)):
            name1 = body_names[i]
            name2 = body_names[j]

            aspect = detect_aspect(
                all_bodies[name1]["longitude"],
                all_bodies[name2]["longitude"]
            )

            if aspect:
                payload["aspects"].append({
                    "body_1": name1,
                    "body_2": name2,
                    **aspect
                })

    return payload


# ============================================================
# DEBUG / TESTING HELPERS
# ============================================================

def test_asteroid_availability(julian_day):
    print("\n================ ASTEROID AVAILABILITY TEST ================")

    for swe_id, name in ASTEROID_DICTIONARY.items():
        try:
            coords, flag = swe.calc_ut(julian_day, swe_id, FLAGS)
            print(f"✅ {name:14} | SWE ID {swe_id:<6} | {coords[0]:9.4f}°")
        except Exception as e:
            print(f"❌ {name:14} | SWE ID {swe_id:<6} | {e}")


def _redact_user_profile(user_profile: dict) -> dict:
    redacted = {}
    for key, value in user_profile.items():
        if key == "resolved_coordinates" and isinstance(value, dict):
            redacted[key] = {
                "latitude": "[redacted]",
                "longitude": "[redacted]",
            }
            continue
        if key in SENSITIVE_USER_PROFILE_KEYS:
            redacted[key] = "[redacted]"
            continue
        redacted[key] = value
    return redacted


def _sanitize_payload_for_debug(payload: dict) -> dict:
    sanitized = deepcopy(payload)
    user_profile = sanitized.get("user_profile")
    if isinstance(user_profile, dict):
        sanitized["user_profile"] = _redact_user_profile(user_profile)
    return sanitized


def print_backend_chart_data(payload: dict, *, redact_user_profile: bool = True):
    payload_to_print = _sanitize_payload_for_debug(payload) if redact_user_profile else payload

    print("\n================ USER PROFILE ================")
    print(json.dumps(payload_to_print["user_profile"], indent=2))

    print("\n================ ANGLES ================")
    for name, data in payload_to_print["angles"].items():
        print(f"{name:12} | {data['formatted']:18} | {data['longitude']}")

    print("\n================ HOUSES ================")
    for name, data in payload_to_print["houses"].items():
        print(f"{name:8} | {data['formatted']:18} | {data['longitude']}")

    print("\n================ STANDARD PLANETS ================")
    for name, data in payload_to_print["standard_planets"].items():
        rx = "Rx" if data["retrograde"] else "Direct"
        print(
            f"{name:12} | {data['formatted']:18} | "
            f"House {data['house']:2} | {rx:6} | Speed {data['speed']}"
        )

    print("\n================ CUSTOM ASTEROIDS ================")
    for name, data in payload_to_print["custom_asteroids"].items():
        if data.get("error"):
            print(f"{name:14} | FAILED | {data['message']}")
            continue

        rx = "Rx" if data["retrograde"] else "Direct"
        print(
            f"{name:14} | {data['formatted']:18} | "
            f"House {data['house']:2} | {rx:6} | Speed {data['speed']}"
        )

    print("\n================ ASPECTS ================")
    for asp in payload_to_print["aspects"]:
        print(
            f"{asp['body_1']:14} {asp['aspect']:12} {asp['body_2']:14} "
            f"| Orb {asp['orb']:5} | Angle {asp['angle']}"
        )


def save_backend_payload(
    payload: dict,
    filename="backend_payload_debug.json",
    *,
    redact_user_profile: bool = True,
):
    payload_to_write = _sanitize_payload_for_debug(payload) if redact_user_profile else payload
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload_to_write, f, indent=2, ensure_ascii=False)

    label = "sanitized backend payload" if redact_user_profile else "backend payload"
    print(f"\nSaved {label} to: {filename}")


# ============================================================
# LOCAL TEST RUN
# ============================================================

if __name__ == "__main__":
    birth_data = {
        "date": "1992-03-21",
        "time": "08:12:00",
        "location": "Peoria, Illinois, USA",
        "simple_mode": False
    }

    payload = generate_payload(birth_data)

    test_asteroid_availability(payload["user_profile"]["julian_day"])
    print_backend_chart_data(payload)
    save_backend_payload(payload)

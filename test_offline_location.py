import importlib
import sys
import types
import unittest
from datetime import timezone


FAKE_CITIES = {
    "1": {
        "geonameid": 1,
        "name": "Peoria",
        "latitude": 40.6936,
        "longitude": -89.5890,
        "countrycode": "US",
        "admin1code": "IL",
        "population": 113150,
    },
    "2": {
        "geonameid": 2,
        "name": "Peoria",
        "latitude": 33.5806,
        "longitude": -112.2374,
        "countrycode": "US",
        "admin1code": "AZ",
        "population": 190985,
    },
    "3": {
        "geonameid": 3,
        "name": "St. Louis",
        "latitude": 38.6270,
        "longitude": -90.1994,
        "countrycode": "US",
        "admin1code": "MO",
        "population": 300576,
    },
    "4": {
        "geonameid": 4,
        "name": "Dublin",
        "latitude": 53.3498,
        "longitude": -6.2603,
        "countrycode": "IE",
        "admin1code": "",
        "population": 1173179,
    },
    "5": {
        "geonameid": 5,
        "name": "Dublin",
        "latitude": 40.0992,
        "longitude": -83.1141,
        "countrycode": "US",
        "admin1code": "OH",
        "population": 499328,
    },
    "6": {
        "geonameid": 6,
        "name": "Springfield",
        "latitude": 39.7817,
        "longitude": -89.6501,
        "countrycode": "US",
        "admin1code": "IL",
        "population": 114394,
    },
    "7": {
        "geonameid": 7,
        "name": "Springfield",
        "latitude": 37.2089,
        "longitude": -93.2923,
        "countrycode": "US",
        "admin1code": "MO",
        "population": 170188,
    },
    "8": {
        "geonameid": 8,
        "name": "Ballina",
        "latitude": 54.1143,
        "longitude": -9.1535,
        "countrycode": "IE",
        "admin1code": "MAYO",
        "population": 10610,
    },
}

FAKE_COUNTRIES = {
    "US": {"name": "United States", "iso3": "USA"},
    "IE": {"name": "Ireland", "iso3": "IRL"},
}

TIMEZONE_BY_COORDS = {
    (40.6936, -89.5890): "America/Chicago",
    (33.5806, -112.2374): "America/Phoenix",
    (38.6270, -90.1994): "America/Chicago",
    (53.3498, -6.2603): "Europe/Dublin",
    (40.0992, -83.1141): "America/New_York",
    (39.7817, -89.6501): "America/Chicago",
    (37.2089, -93.2923): "America/Chicago",
    (54.1143, -9.1535): "Europe/Dublin",
}


def ensure_module(module_name: str, installer) -> None:
    try:
        importlib.import_module(module_name)
    except Exception:
        installer()


def install_fake_geonamescache() -> None:
    module = types.ModuleType("geonamescache")

    class GeonamesCache:
        def get_cities(self):
            return FAKE_CITIES

        def get_countries(self):
            return FAKE_COUNTRIES

    module.GeonamesCache = GeonamesCache
    sys.modules["geonamescache"] = module


def install_fake_timezonefinder() -> None:
    module = types.ModuleType("timezonefinder")

    class TimezoneFinder:
        def timezone_at(self, *, lat, lng):
            return TIMEZONE_BY_COORDS.get((round(float(lat), 4), round(float(lng), 4)))

        def closest_timezone_at(self, *, lat, lng):
            return self.timezone_at(lat=lat, lng=lng)

    module.TimezoneFinder = TimezoneFinder
    sys.modules["timezonefinder"] = module


def install_fake_swisseph() -> None:
    module = types.ModuleType("swisseph")
    module.FLG_SWIEPH = 1
    module.FLG_SPEED = 2
    module.SUN = 0
    module.MOON = 1
    module.MERCURY = 2
    module.VENUS = 3
    module.MARS = 4
    module.JUPITER = 5
    module.SATURN = 6
    module.URANUS = 7
    module.NEPTUNE = 8
    module.PLUTO = 9
    module.CHIRON = 10
    module.TRUE_NODE = 11
    module.MEAN_APOG = 12

    def set_ephe_path(_path):
        return None

    def julday(year, month, day, decimal_hour):
        return float(year * 10000 + month * 100 + day) + decimal_hour / 24.0

    def houses(_julian_day, _lat, _lng, _system):
        return ([0.0] * 12, [15.0, 105.0, 0.0, 225.0])

    def calc_ut(_julian_day, body_id, _flags):
        longitude = (body_id * 17.5) % 360
        speed = -0.1 if body_id % 2 else 0.1
        return ([longitude, 0.0, 0.0, speed], 0)

    module.set_ephe_path = set_ephe_path
    module.julday = julday
    module.houses = houses
    module.calc_ut = calc_ut
    sys.modules["swisseph"] = module


def clear_engine_modules() -> None:
    for module_name in [
        "engine.offline_place_resolver",
        "engine.natal_engine",
    ]:
        sys.modules.pop(module_name, None)


class OfflineLocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_module("geonamescache", install_fake_geonamescache)
        ensure_module("timezonefinder", install_fake_timezonefinder)
        ensure_module("swisseph", install_fake_swisseph)
        clear_engine_modules()

    def setUp(self):
        clear_engine_modules()
        sys.modules.pop("geopy", None)
        sys.modules.pop("geopy.geocoders", None)

    def test_peoria_il_resolves_offline(self):
        resolver = importlib.import_module("engine.offline_place_resolver")
        result = resolver.resolve_place("Peoria, IL")
        self.assertEqual(result["display_name"], "Peoria, Illinois, United States")
        self.assertEqual(result["timezone"], "America/Chicago")
        self.assertEqual(result["source"], "offline_geonamescache")

    def test_st_louis_missouri_resolves_offline(self):
        resolver = importlib.import_module("engine.offline_place_resolver")
        result = resolver.resolve_place("St. Louis, Missouri")
        self.assertEqual(result["display_name"], "St. Louis, Missouri, United States")
        self.assertEqual(result["timezone"], "America/Chicago")

    def test_dublin_ireland_resolves_offline(self):
        resolver = importlib.import_module("engine.offline_place_resolver")
        result = resolver.resolve_place("Dublin, Ireland")
        self.assertEqual(result["display_name"], "Dublin, Ireland")
        self.assertEqual(result["timezone"], "Europe/Dublin")

    def test_springfield_is_ambiguous(self):
        resolver = importlib.import_module("engine.offline_place_resolver")
        with self.assertRaises(resolver.AmbiguousLocationError) as context:
            resolver.resolve_place("Springfield")
        self.assertIn('Could not uniquely resolve "Springfield".', str(context.exception))
        self.assertIn('"Springfield, Missouri, United States"', str(context.exception))

    def test_generate_payload_uses_offline_resolution_without_importing_geopy(self):
        self.assertNotIn("geopy", sys.modules)
        natal_engine = importlib.import_module("engine.natal_engine")
        natal_engine.ZoneInfo = lambda _name: timezone.utc
        payload = natal_engine.generate_payload(
            {
                "name": "Puck",
                "date": "1992-03-21",
                "time": "08:11",
                "location": "Peoria, IL",
            }
        )
        self.assertNotIn("geopy", sys.modules)
        self.assertEqual(payload["birth_location"], "Peoria, Illinois, United States")
        self.assertEqual(payload["location"], "Peoria, Illinois, United States")
        self.assertEqual(
            payload["user_profile"]["resolved_coordinates"],
            {"latitude": 40.6936, "longitude": -89.589},
        )
        self.assertEqual(payload["user_profile"]["timezone"], "America/Chicago")
        self.assertEqual(payload["user_profile"]["resolved_location"], "Peoria, Illinois, United States")


if __name__ == "__main__":
    unittest.main(verbosity=2)

import csv
import logging
import requests
from functools import lru_cache
from io import StringIO

CSV_URL = "https://raw.githubusercontent.com/lxndrblz/Airports/refs/heads/main/airports.csv"

@lru_cache(maxsize=1)
def load_global_iata_map() -> dict:
    mapping = {}
    try:
        response = requests.get(CSV_URL, timeout=10)
        response.raise_for_status()
        f = StringIO(response.text)
        reader = csv.DictReader(f)
        for row in reader:
            iata = row.get("code", "").strip()
            city = row.get("city", "").strip()
            name = row.get("name", "").strip()
            country = row.get("country", "").strip()
            if iata:
                if city:
                    mapping[iata.upper()] = city
                elif name:
                    mapping[iata.upper()] = name
                elif country:
                    mapping[iata.upper()] = country
    except Exception as e:
        logging.error(f"Failed to fetch IATA mapping: {e}")
    return mapping

def get_city_from_iata(iata_code: str) -> str:
    """
    Return the city, or if not available, the airport name, or if not available, the country for the given IATA code.
    Falls back to the original string if not found.
    """
    mapping = load_global_iata_map()
    return mapping.get(iata_code.strip().upper(), iata_code)

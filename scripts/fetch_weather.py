"""Fetch weather data using an API key and write a JSON payload for the static site.

This script supports local development via .env.local/.env files and CI execution via
environment variables (for example GitHub Actions secrets).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
import logging
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import requests


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs"

logging.basicConfig(level = os.getenv("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)

def load_env_file(path: Path) -> None:
    """Load KEY=VALUE pairs from a .env-style file into the environment."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch weather data and write a JSON file for the static site."
    )
    parser.add_argument(
        "--location",
        default=os.environ.get("WEATHER_LOCATION", "London"),
        help="Location query used by the weather API (default: WEATHER_LOCATION or London)",
    )
    parser.add_argument(
        "--lat",
        default=os.environ.get("WEATHER_LOCATION_LAT", "0"),
        help="Latitude for the weather API (default: WEATHER_LOCATION_LAT or 0)",
    )
    parser.add_argument(
        "--lon",
        default=os.environ.get("WEATHER_LOCATION_LON", "0"),
        help="Longitude for the weather API (default: WEATHER_LOCATION_LON or 0)",
    )
    parser.add_argument(
        "--bpf-collection",
        default=os.environ.get("WEATHER_LOCATION_BPF_COLLECTION"),
        help="Collection name for the BPF API (default: WEATHER_LOCATION_BPF_COLLECTION)",
    )
    parser.add_argument(
        "--bpf-location-id",
        default=os.environ.get("WEATHER_LOCATION_BPF_LOCATION_ID"),
        help="Location ID for the BPF API (default: WEATHER_LOCATION_BPF_LOCATION_ID)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output JSON directory (default: docs/)",
    )
    parser.add_argument(
        "--timeout",
        default=15,
        type=int,
        help="HTTP timeout in seconds (default: 15)",
    )
    return parser.parse_args()


def fetch_global_spot_daily(api_key: str, lat: float, lon: float) -> dict:
    api_base_url = "https://data.hub.api.metoffice.gov.uk/sitespecific/v0"
    url = f"{api_base_url}/point/daily"
    response = requests.get(
        url,
        params={
            "dataSource": "BD1",
            "includeLocationName": "true",
            "latitude": lat,
            "longitude": lon,
        },
        headers={"apikey": api_key},
    )
    response.raise_for_status()
    return response.json()


def get_global_spot_daily(api_key: str, lat: float, lon: float) -> dict:
    data = fetch_global_spot_daily(api_key, lat, lon)
    # Extract data, e.g. convert 'midday' to an actual timestamp
    # Example response at /example_payloads/global_spot_daily.geojson
    model_run_date = data["features"][0]["properties"]["modelRunDate"]
    logger.info(f"Global spot model run '{model_run_date}' retrieved with {len(data['features'][0]['properties']['timeSeries'])} time series entries")
    global_spot_daily_data = []

    for ts in data["features"][0]["properties"]["timeSeries"]:
        # Daytime parameters are excluded from the first timestep if the model run time is after midday
        if not "dayUpperBoundMaxFeelsLikeTemp" in ts or not "dayLowerBoundMaxFeelsLikeTemp" in ts:
            logger.info(f"Skipping global spot timestep {ts['time']} due to missing daytime parameters")
            continue
        base_dt = datetime.fromisoformat(ts["time"].replace("Z", "+00:00"))
        global_spot_daily_data.append(
            {
                "time": base_dt.isoformat(),
                "temperature_max": ts["dayUpperBoundMaxFeelsLikeTemp"],
                "temperature_min": ts["dayLowerBoundMaxFeelsLikeTemp"],
            }
        )
    d = {
        "model": "global_spot_daily",
        "modelRunDate": model_run_date,
        "timeSeries": global_spot_daily_data,
    }
    return d


def update_data_payload(api_key: str, lat: float, lon: float, output_dir: Path) -> None:
    global_spot_daily_data = get_global_spot_daily(api_key, lat, lon)

    d = {"global_spot_daily": global_spot_daily_data}
    out_path = output_dir / "global_spot_daily.geojson"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(d), encoding="utf-8")
    print(f"Wrote global spot daily JSON to {out_path}")


def get_bpf_percentiles(api_key: str, collection: str, location_id: str) -> dict:
    api_base_url = "https://data.hub.api.metoffice.gov.uk/mo-site-specific-blended-probabilistic-forecast/1.0.0"
    url = f"{api_base_url}/collections/{collection}/locations/{location_id}"
    response = requests.get(
        url,
        headers={"apikey": api_key},
    )
    response.raise_for_status()
    return response.json()


def update_bpf_data(
    api_key: str, collection: str, location_id: str, output_dir: Path
) -> None:
    data = get_bpf_percentiles(api_key, collection, location_id)
    out_path = output_dir / f"{collection}-point.geojson"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data), encoding="utf-8")
    print(f"Wrote BPF percentiles JSON to {out_path}")


def main() -> int:
    # Load local development env files if present, while allowing CI env vars to win.
    load_env_file(REPO_ROOT / ".env.local")
    load_env_file(REPO_ROOT / ".env")

    args = parse_args()
    spot_api_key = os.environ.get("WEATHER_API_KEY_SPOT", "").strip()
    if not spot_api_key:
        print(
            "Missing WEATHER_API_KEY_SPOT. Set it in your environment or .env.local (never commit secrets).",
            file=sys.stderr,
        )
        return 1
    bpf_api_key = os.environ.get("WEATHER_API_KEY_BPF", "").strip()
    if not bpf_api_key:
        print(
            "Missing WEATHER_API_KEY_BPF. Set it in your environment or .env.local (never commit secrets).",
            file=sys.stderr,
        )
        return 1
    try:
        # raw_weather = fetch_weather(args.api_base_url, api_key, args.location, args.timeout)
        # site_payload = build_site_payload(raw_weather, args.location)
        update_data_payload(
            spot_api_key, float(args.lat), float(args.lon), Path(args.output_dir)
        )
        # Hard-coded location id for now to minimise API calls - limited quota
        update_bpf_data(
            bpf_api_key,
            args.bpf_collection,
            args.bpf_location_id,
            Path(args.output_dir),
        )
    except Exception as exc:  # pragma: no cover - runtime safety path
        print(f"Failed to fetch weather data: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

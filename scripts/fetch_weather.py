"""Fetch weather data using an API key and write a JSON payload for the static site.

This script supports local development via .env.local/.env files and CI execution via
environment variables (for example GitHub Actions secrets).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "json"
# .invalid is a reserved TLD that never resolves publicly.
DEFAULT_API_BASE_URL = "https://weather-api.example.invalid/v1/current.json"


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
        "--api-base-url",
        default=os.environ.get("WEATHER_API_BASE_URL", DEFAULT_API_BASE_URL),
        help="Weather API endpoint base URL",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUTPUT),
        help="Output JSON file path (default: docs/json)",
    )
    parser.add_argument(
        "--timeout",
        default=15,
        type=int,
        help="HTTP timeout in seconds (default: 15)",
    )
    return parser.parse_args()


def fetch_weather(api_base_url: str, api_key: str, location: str, timeout: int) -> dict:
    params = urlencode({"key": api_key, "q": location})
    request_url = f"{api_base_url}?{params}"

    with urlopen(request_url, timeout=timeout) as response:  # nosec B310
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def build_site_payload(raw: dict, fallback_location: str) -> dict:
    location = raw.get("location", {}).get("name", fallback_location)
    current = raw.get("current", {})
    condition = current.get("condition", {}).get("text", "Unknown")
    temp_c = current.get("temp_c", "?")

    return {
        "siteMessage": f"Weather for {location}: {temp_c}C, {condition}",
        "weather": {
            "location": location,
            "temperatureC": temp_c,
            "condition": condition,
            "lastUpdated": current.get("last_updated", ""),
        },
    }


def main() -> int:
    # Load local development env files if present, while allowing CI env vars to win.
    load_env_file(REPO_ROOT / ".env.local")
    load_env_file(REPO_ROOT / ".env")

    args = parse_args()
    api_key = os.environ.get("WEATHER_API_KEY", "").strip()
    if not api_key:
        print(
            "Missing WEATHER_API_KEY. Set it in your environment or .env.local (never commit secrets).",
            file=sys.stderr,
        )
        return 1

    if "example.invalid" in args.api_base_url:
        print(
            "WEATHER_API_BASE_URL is still using the placeholder domain. "
            "Set a real API endpoint in .env.local or environment variables.",
            file=sys.stderr,
        )
        return 1

    try:
        raw_weather = fetch_weather(args.api_base_url, api_key, args.location, args.timeout)
        site_payload = build_site_payload(raw_weather, args.location)
    except Exception as exc:  # pragma: no cover - runtime safety path
        print(f"Failed to fetch weather data: {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(site_payload, indent=2), encoding="utf-8")
    print(f"Wrote weather JSON to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
from geopy.distance import geodesic
import json
from pathlib import Path


def find_nearest_point(lat: float, lon: float, feature_path: Path) -> str:
    """
    Find the nearest point in a GeoJSON file to the given latitude and longitude.

    Args:
        lat (float): Latitude of the point to find.
        lon (float): Longitude of the point to find.
        feature_path (Path): Path to the GeoJSON file containing features.

    Returns:
        str: The name of the nearest feature.
    """

    with open(feature_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nearest_feature = None
    min_distance = float("inf")

    for feature in data["features"]:
        feature_coords = feature["geometry"]["coordinates"]
        feature_lat, feature_lon = feature_coords[1], feature_coords[0]
        distance = geodesic((lat, lon), (feature_lat, feature_lon)).kilometers

        if distance < min_distance:
            min_distance = distance
            nearest_feature = feature

    return nearest_feature["id"] if nearest_feature else None


if __name__ == "__main__":
    lat = 0.0
    lon = 0.0
    global_location_id = find_nearest_point(
        lat,
        lon,
        Path(
            "example_payloads/probabilistic/improver-percentiles-spot-global-locations.geojson"
        ),
    )
    print(f"Nearest global location ID: {global_location_id}")
    uk_location_id = find_nearest_point(
        lat,
        lon,
        Path(
            "example_payloads/probabilistic/improver-percentiles-spot-uk-locations.geojson"
        ),
    )
    print(f"Nearest UK location ID: {uk_location_id}")

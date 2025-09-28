import requests
import json
import pandas as pd
from typing import Sequence, Dict, Any


def get_data(file_path: str, max_coordinates: int = 100) -> str:
    """
    Read latitude and longitude data from a CSV file and format it for the API request.

    Args:
        file_path (str): Path to the CSV file containing latitude and longitude data.
        max_coordinates (int, optional): Maximum number of coordinates to consider. Defaults to 100.

    Returns:
        str: Formatted coordinates string for the API request.
    """
    try:
        # Read the CSV file and extract latitude and longitude columns
        df = pd.read_csv(file_path)
        df = df[["lat", "lng"]]

        # Convert DataFrame to a list of tuples and format as "lat,lng"
        coordinates = list(df.itertuples(index=False, name=None))
        coordinates = [f"{c[0]},{c[1]}" for c in coordinates][:max_coordinates]

        # Join the formatted coordinates with a semicolon
        return ";".join(coordinates)
    except FileNotFoundError:
        raise FileNotFoundError("CSV file not found.")
    except Exception as e:
        raise Exception(f"An error occurred while processing the data: {e}")


def get_matrix(
    coordinates: str,
    annotations: Sequence[str] = ("distance", "duration"),
    base_url: str = "http://router.project-osrm.org",
    profile: str = "driving",
    timeout: int = 60,
) -> Dict[str, Any]:
    """Fetch OSRM table (matrix) with selected annotations (distance, duration).

    Parameters
    ----------
    coordinates : str
        String like 'lon,lat;lon,lat;...' (OSRM expects lon,lat order).
    annotations : Sequence[str], default ("distance", "duration")
        Which matrices to request. Supported: distance, duration.
    base_url : str
        OSRM server base URL (allow overriding to self-hosted instance).
    profile : str
        Routing profile: driving, driving-hgv, foot, bicycle.
    timeout : int
        Request timeout in seconds.

    Returns
    -------
    dict
        Raw JSON dict from OSRM containing requested matrices.
    """
    annot = ",".join(annotations)
    url = f"{base_url.rstrip('/')}/table/v1/{profile}/{coordinates}?annotations={annot}"
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "vrp-matrix-generator/1.0"})
        response.raise_for_status()
        data = response.json()
        # Basic validation
        if "code" in data and data["code"] != "Ok":
            raise RuntimeError(f"OSRM returned code={data['code']} message={data.get('message')}")
        return data
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"API request failed: {e}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from the API.")
    except Exception as e:
        raise Exception(f"An error occurred while fetching the matrix: {e}")


def parse_coordinates(df: pd.DataFrame) -> str:
    """
    Parse latitude and longitude data from a DataFrame and format it for the API request.

    Args:
        df (pd.DataFrame): DataFrame containing 'lat' and 'lng' columns.

    Returns:
        str: Formatted coordinates string for the API request.
    """
    # Extract latitude and longitude columns from the DataFrame
    coordinates = df[["lat", "lng"]]

    # Convert DataFrame to a list of tuples and format as "lng,lat"
    coordinates = list(coordinates.itertuples(index=False, name=None))
    coordinates = [f"{c[1]},{c[0]}" for c in coordinates]

    # Join the formatted coordinates with a semicolon
    return ";".join(coordinates)


if __name__ == "__main__":
    try:
        # Specify the path to the CSV file containing latitude and longitude data
        csv_file_path = "data/places.csv"

        # Get the coordinates data and fetch the distance matrix
        coordinates_data = get_data(csv_file_path)
        distance_matrix = get_matrix(coordinates_data)

        # Print the distance matrix
        print(distance_matrix)
    except Exception as e:
        print(f"Error: {e}")

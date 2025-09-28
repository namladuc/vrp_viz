import math
import random
from typing import Tuple
import requests


def calculate_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Khoảng cách Haversine (km) giữa 2 toạ độ."""
    R = 6371
    lat1_rad, lng1_rad = math.radians(lat1), math.radians(lng1)
    lat2_rad, lng2_rad = math.radians(lat2), math.radians(lng2)
    dlat, dlng = lat2_rad - lat1_rad, lng2_rad - lng1_rad
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def generate_random_coordinates(
    center_lat: float, center_lng: float, radius_km: float
) -> Tuple[float, float]:
    """Sinh toạ độ ngẫu nhiên trong bán kính (km) quanh điểm trung tâm."""
    radius_deg = radius_km / 111.32
    angle = random.uniform(0, 2 * math.pi)
    distance = radius_deg * math.sqrt(random.uniform(0, 1))
    return center_lat + distance * math.cos(angle), center_lng + distance * math.sin(
        angle
    )


def get_real_address_from_coordinates(lat: float, lng: float) -> dict:
    """Reverse geocode qua Nominatim, có fallback khi lỗi."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "addressdetails": 1,
            "accept-language": "vi,en",
        }
        headers = {"User-Agent": "VRP_Data_Generator/1.0 (Educational Purpose)"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            addr = data.get("address", {})
            display_name = data.get("display_name", "")
            house_number = addr.get("house_number", "")
            street = addr.get("road", addr.get("street", ""))
            suburb = addr.get("suburb", addr.get("neighbourhood", ""))
            city = addr.get("city", addr.get("town", addr.get("village", "")))
            state = addr.get("state", "")
            country = addr.get("country", "")
            parts = [p for p in [house_number, street] if p]
            full_address = " ".join(parts) if parts else display_name.split(",")[0]
            return {
                "full_address": full_address or f"Toạ độ {lat:.6f}, {lng:.6f}",
                "street": street or "N/A",
                "suburb": suburb or "N/A",
                "lat": lat,
                "lng": lng,
                "city": city or "N/A",
                "state": state or "N/A",
                "country": country or "N/A",
                "display_name": display_name,
            }
    except Exception as e:
        print(f"Reverse geocode lỗi: {e}")
    return {
        "full_address": f"Toạ độ {lat:.6f}, {lng:.6f}",
        "street": "N/A",
        "suburb": "N/A",
        "lat": lat,
        "lng": lng,
        "city": "N/A",
        "state": "N/A",
        "country": "N/A",
        "display_name": f"Coordinates: {lat:.6f}, {lng:.6f}",
    }


def generate_customer_with_real_address(
    lat: float, lng: float, min_packages: int, max_packages: int
) -> dict:
    """Sinh thông tin khách với địa chỉ thực tế và số gói."""
    customer_names = [
        "Nguyễn Văn An",
        "Trần Thị Bình",
        "Lê Hoài Nam",
        "Phạm Thị Cúc",
        "Hoàng Văn Đức",
        "Vũ Thị Hoa",
        "Đặng Văn Kiên",
        "Bùi Thị Lan",
        "Ngô Văn Minh",
        "Đinh Thị Nga",
        "Tạ Văn Phong",
        "Cao Thị Quỳnh",
        "Dương Văn Sơn",
        "Lý Thị Tâm",
        "Phan Văn Út",
    ]
    info = get_real_address_from_coordinates(lat, lng)
    return {
        "name": random.choice(customer_names),
        "address": info["full_address"],
        "street": info["street"],
        "suburb": info["suburb"],
        "lat": lat,
        "lng": lng,
        "city": info["city"],
        "state": info["state"],
        "country": info["country"],
        "display_name": info["display_name"],
        "packages": random.randint(min_packages, max_packages),
    }

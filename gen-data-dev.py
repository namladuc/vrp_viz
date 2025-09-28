import time
from typing import List

import pandas as pd
import numpy as np

from vrp_viz.map_viz.gen_data import (
    generate_random_coordinates,
    generate_customer_with_real_address,
    get_real_address_from_coordinates,
    calculate_distance_km
)
from vrp_viz.map_viz.api_osmr import get_matrix, parse_coordinates

if __name__ == "__main__":
    
    # Cấu hình kho hàng và tham số
    warehouse_info = {
        'name': 'Điểm dịch vụ SPX Hà Nội - Đống Đa 5',
        'address': '530 Láng, P. Láng Hạ',
        'lat': 21.011257,
        'lng': 105.810770,
        'ward': 'Phường Đống Đa',
        'post_office': 'Bưu cục shopee',
    }

    N_CUSTOMERS = 5   # số KH cần tạo
    RADIUS_KM = 2       # bán kính tìm kiếm (km)
    MIN_PACKAGES = 1    # min gói/khách
    MAX_PACKAGES = 5    # max gói/khách
    
    print('Kho hàng:')
    print(f"- Tên: {warehouse_info['name']}")
    print(f"- Địa chỉ: {warehouse_info['address']}")
    print(f"- Toạ độ: {warehouse_info['lat']}, {warehouse_info['lng']}")
    print('\nTham số:')
    print(f"- Số khách hàng: {N_CUSTOMERS}")
    print(f"- Bán kính: {RADIUS_KM} km")
    print(f"- Gói/khách: {MIN_PACKAGES}-{MAX_PACKAGES}")
    
    # Tạo danh sách khách hàng ngẫu nhiên
    customers: List[dict] = []
    warehouse_lat = warehouse_info['lat']
    warehouse_lng = warehouse_info['lng']

    print(f"Tạo {N_CUSTOMERS} khách trong bán kính {RADIUS_KM} km...")
    for i in range(N_CUSTOMERS):
        # Sinh toạ độ và thông tin khách
        lat, lng = generate_random_coordinates(warehouse_lat, warehouse_lng, RADIUS_KM)
        info = generate_customer_with_real_address(lat, lng, MIN_PACKAGES, MAX_PACKAGES)
        info['customer_id'] = f"KH_{i+1:03d}"
        # Khoảng cách Haversine tạm thời
        info['distance_from_warehouse_km'] = round(calculate_distance_km(warehouse_lat, warehouse_lng, lat, lng), 2)
        customers.append(info)
        print(f"{i+1:03d}/{N_CUSTOMERS}: {info['address'][:60]}")
        time.sleep(0.5)  # tránh spam API

    customers_df = pd.DataFrame(customers)
    print(f"\n✓ Đã tạo {len(customers_df)} khách hàng.")
    customers_df[['customer_id','name','address','city','packages','distance_from_warehouse_km']].head(10)

    print("Lấy địa chỉ thực tế cho kho...")
    warehouse_address_info = get_real_address_from_coordinates(warehouse_info['lat'], warehouse_info['lng'])

    warehouse_df = pd.DataFrame({
        'customer_id': ['WAREHOUSE'],
        'name': [warehouse_info['name']],
        'address': [warehouse_info.get('address', warehouse_address_info['full_address'])],
        'street': [warehouse_address_info['street']],
        'suburb': [warehouse_address_info['suburb']],
        'lat': [warehouse_info['lat']],
        'lng': [warehouse_info['lng']],
        'city': [warehouse_address_info['city']],
        'state': [warehouse_address_info['state']],
        'country': [warehouse_address_info['country']],
        'display_name': [warehouse_address_info['display_name']],
        'packages': [0],
        'distance_from_warehouse_km': [0.0],
    })

    all_locations_df = pd.concat([warehouse_df, customers_df], ignore_index=True)
    print("Tổng hợp xong. Tổng điểm:", len(all_locations_df))

    # Thống kê cơ bản
    total_packages = int(customers_df['packages'].sum())
    avg_packages = float(customers_df['packages'].mean())
    max_distance = float(customers_df['distance_from_warehouse_km'].max())
    avg_distance = float(customers_df['distance_from_warehouse_km'].mean())

    print("Tổng gói hàng:", total_packages)
    print("TB gói/khách:", f"{avg_packages:.1f}")
    print("Xa nhất (km):", f"{max_distance:.2f}")
    print("TB khoảng cách (km):", f"{avg_distance:.2f}")
    
    print("Gọi OSRM /table để lấy ma trận khoảng cách...")

    try:
        coordinates = parse_coordinates(all_locations_df)
        response = get_matrix(coordinates)
        if 'distances' in response:
            distance_matrix = np.array(response['distances'])
            distance_matrix_km = distance_matrix / 1000.0
            distances_df = pd.DataFrame(
                distance_matrix_km,
                index=all_locations_df['customer_id'],
                columns=all_locations_df['customer_id'],
            )
            print("✓ Đã nhận ma trận khoảng cách:", distance_matrix.shape)
            print(distance_matrix_km[:5, :5].round(2))
        else:
            print("Phản hồi thiếu 'distances':", list(response.keys()))
            raise RuntimeError("OSRM trả về dữ liệu không hợp lệ")
    except Exception as e:
        print("OSRM lỗi -> tạo ma trận Haversine giả lập.", e)
        n = len(all_locations_df)
        distance_matrix_km = np.zeros((n, n))
        for i in range(n):
            lat_i, lng_i = all_locations_df.iloc[i]['lat'], all_locations_df.iloc[i]['lng']
            for j in range(i + 1, n):
                lat_j, lng_j = all_locations_df.iloc[j]['lat'], all_locations_df.iloc[j]['lng']
                d = calculate_distance_km(lat_i, lng_i, lat_j, lng_j)
                distance_matrix_km[i, j] = distance_matrix_km[j, i] = d
        distances_df = pd.DataFrame(
            distance_matrix_km,
            index=all_locations_df['customer_id'],
            columns=all_locations_df['customer_id'],
        )
        print("✓ Đã tạo ma trận Haversine giả lập.")
    
    print("=== KẾT QUẢ TẠO DỮ LIỆU VRP ===")
    print("1) Kho hàng:")
    print(f"   ID: {all_locations_df.iloc[0]['customer_id']}")
    print(f"   Tên: {all_locations_df.iloc[0]['name']}")
    print(f"   ĐC: {all_locations_df.iloc[0]['address']}")
    print(f"   Toạ độ: ({all_locations_df.iloc[0]['lat']:.6f}, {all_locations_df.iloc[0]['lng']:.6f})")

    print("\n2) Khách hàng:")
    print(f"   Số lượng: {len(customers_df)} | Tổng gói: {total_packages} | Bán kính: {RADIUS_KM} km")

    print("\n3) Ma trận khoảng cách:")
    print(f"   Kích thước: {distances_df.shape[0]}x{distances_df.shape[1]}")
    print(f"   Gần nhất (>0): {distances_df.values[distances_df.values>0].min():.2f} km")
    print(f"   Xa nhất: {distances_df.values.max():.2f} km")
    print(f"   Trung bình: {distances_df.values[distances_df.values>0].mean():.2f} km")

    print("\n4) Top 5 gần kho nhất (theo Haversine):")
    for _, c in customers_df.nsmallest(5, 'distance_from_warehouse_km').iterrows():
        print(f"   - {c['customer_id']}: {c['name']} - {c['distance_from_warehouse_km']:.2f} km")

    print("\n5) Top 5 xa kho nhất (theo Haversine):")
    for _, c in customers_df.nlargest(5, 'distance_from_warehouse_km').iterrows():
        print(f"   - {c['customer_id']}: {c['name']} - {c['distance_from_warehouse_km']:.2f} km")
        
    # Lưu dữ liệu
    locations_file = f"data/map-viz/vrp_locations_dev.csv"
    all_locations_df.to_csv(locations_file, index=False, encoding='utf-8-sig')
    print("Lưu locations:", locations_file)

    distance_file = f"data/map-viz/vrp_distances_dev.csv"
    distances_df.to_csv(distance_file, encoding='utf-8-sig')
    print("Lưu distances:", distance_file)

    customers_file = f"data/map-viz/vrp_customers_dev.csv"
    customers_df.to_csv(customers_file, index=False, encoding='utf-8-sig')
    print("Lưu customers:", customers_file)

    summary_df = pd.DataFrame({
        'timestamp': ['2025-09-28 12:00:00'],  # Cố định để dễ so sánh
        'warehouse_name': [warehouse_info['name']],
        'warehouse_lat': [warehouse_info['lat']],
        'warehouse_lng': [warehouse_info['lng']],
        'n_customers': [N_CUSTOMERS],
        'radius_km': [RADIUS_KM],
        'total_packages': [total_packages],
        'avg_distance_km': [avg_distance],
        'max_distance_km': [max_distance],
        'locations_file': [locations_file],
        'distance_file': [distance_file],
    })
    summary_file = f"data/map-viz/vrp_summary_dev.csv"
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    print("Lưu summary:", summary_file)

    print("\n=== HOÀN THÀNH ===")
import requests
import folium

# 출발지 및 도착지 좌표 (경도, 위도)
start = (126.776167, 37.232688)
end = (126.774400, 37.247704)

# 출발지 
# 37.239555, 126.773549

# 경유지1
# 37.242583, 126.774213

# 경유지2
# 37.246189, 126.773422

# 목적지
# 37.240285, 126.774347

start = (126.773549, 37.239555)
via1 = (126.774213, 37.242583)
via2 = (126.773422, 37.246189)
end = (126.774347, 37.240285)


# OSRM 서버에서 경로 요청
url = f"http://localhost:5000/route/v1/driving/{start[0]},{start[1]};{via1[0]},{via1[1]};{via2[0]},{via2[1]};{end[0]},{end[1]}?overview=full&geometries=geojson"
response = requests.get(url)
data = response.json()

# 경로 정보 추출
geometry = data["routes"][0]["geometry"]
distance = data["routes"][0]["distance"]  # meters
duration = data["routes"][0]["duration"]  # seconds

# folium 지도 초기화
m = folium.Map(location=[(start[1] + end[1]) / 2, (start[0] + end[0]) / 2], zoom_start=15)

# 경로 라인 추가
folium.GeoJson(geometry, name="route").add_to(m)

# 시작/끝 마커 추가
folium.Marker(location=[start[1], start[0]], tooltip="출발지", icon=folium.Icon(color="green")).add_to(m)
folium.Marker(location=[end[1], end[0]], tooltip="도착지", icon=folium.Icon(color="red")).add_to(m)

# 거리/시간 정보 출력
popup_text = f"총 거리: {distance:.1f} m<br>예상 시간: {duration:.1f} 초"
folium.Popup(popup_text).add_to(m)

# 지도 저장 및 표시
m.save("osrm_route_map.html")
print("✅ 지도 파일 생성 완료: osrm_route_map.html")

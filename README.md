# shp_to_osm
KATRI shp 데이터를 OSRM network데이터 변환 가능 여부 판단

## shp to osm.pbf
shp_to_osm.py 실행
데이터 생성됨

## docker
docker composer로 osrm-extract를 실행
rp를 위한 데이터가 생성됨

docker composer로 osrm-routed를 실행

## display 
display_route.py를 실행
rp 경로를 지도에 표시해주는 html생성해줌

import geopandas as gpd
from lxml import etree
from shapely.geometry import Point, LineString
from lxml.etree import ElementTree
import argparse
import os
import subprocess

# 매핑 테이블 정의
NODE_TYPE_MAP = {
    1: "flat_intersection",
    2: "grade_separated_intersection",
    3: "tunnel_terminal",
    4: "bridge_terminal",
    5: "under_or_overpass_terminal",
    7: "lane_change",
    8: "tollgate_terminal",
    9: "toll_station",
    10: "roundabout",
    99: "unknown"
}

ROAD_RANK_MAP = {
    1: "motorway",
    2: "trunk",
    3: "primary",
    4: "secondary",
    5: "tertiary",
    6: "residential",
    7: "residential",
    8: "residential",
    9: "road"
}

ROAD_TYPE_MAP = {
    1: "normal",
    2: "tunnel",
    3: "bridge",
    4: "underpass",
    5: "overpass"
}

LINK_TYPE_MAP = {
    1: "intersection_path",
    2: "toll_highpass",
    3: "toll_non_highpass",
    4: "bus_only",
    5: "reversible",
    6: "main_lane",
    7: "rest_area_entry",
    8: "rest_area_internal",
    9: "rest_area_exit",
    10: "nap_area_entry",
    11: "nap_area_internal",
    12: "nap_area_exit",
    13: "intersection_entry",
    14: "intersection_exit",
    99: "other"
}


def convert_shp_to_osm(node_path: str, link_path: str, output_path: str = "network.osm"):
    nodes_gdf = gpd.read_file(node_path).to_crs(epsg=4326)
    links_gdf = gpd.read_file(link_path).to_crs(epsg=4326)

    osm_root = etree.Element("osm", version="0.6", generator="shp2osm")
    node_id_map = {}
    osm_id = -1

    # Convert Nodes
    for _, row in nodes_gdf.iterrows():
        geom: Point = row.geometry
        if not isinstance(geom, Point):
            continue

        lat, lon = geom.y, geom.x
        string_id = str(row["ID"])

        node_elem = etree.Element("node", id=str(osm_id), visible="true",
                                  lat=str(lat), lon=str(lon))
        node_elem.append(etree.Element("tag", k="ref", v=string_id))
        node_elem.append(etree.Element("tag", k="node_type", v=str(row["NodeType"])))
        node_elem.append(etree.Element("tag", k="admin_code", v=str(row["AdminCode"])))
        node_elem.append(etree.Element("tag", k="its_node_id", v=str(row["ITSNodeID"])))
        osm_root.append(node_elem)

        node_id_map[string_id] = osm_id
        osm_id -= 1

    # Convert Links (Ways)
    way_id = 1
    for _, row in links_gdf.iterrows():
        geom: LineString = row.geometry
        if not isinstance(geom, LineString):
            continue

        from_id = node_id_map.get(str(row["FromNodeID"]))
        to_id = node_id_map.get(str(row["ToNodeID"]))
        if from_id is None or to_id is None:
            continue

        way_elem = etree.Element("way", id=str(way_id), visible="true")
        coords = list(geom.coords)

        # 구성 노드 추가
        way_elem.append(etree.Element("nd", ref=str(from_id)))
        for coord in coords[1:-1]:
            lon, lat = coord[:2]
            node_elem = etree.Element("node", id=str(osm_id), visible="true",
                                      lat=str(lat), lon=str(lon))
            osm_root.append(node_elem)
            way_elem.append(etree.Element("nd", ref=str(osm_id)))
            osm_id -= 1
        way_elem.append(etree.Element("nd", ref=str(to_id)))

        # 태그 매핑
        tag_map = {
            "ref": str(row["ID"]),
            "highway": {
                1: "motorway",
                2: "trunk",
                3: "primary",
                4: "secondary",
                5: "tertiary",
                6: "residential",
                7: "residential",
                8: "residential",
                9: "primary"
            }.get(int(row["RoadRank"]), "primary"),
            "road_type": str(row["RoadType"]),
            "link_type": str(row["LinkType"]),
            "length": str(row["Length"]),
            "lanes": str(row["LaneNo"]),
            "admin_code": str(row["AdminCode"]),
            "its_link_id": str(row["ITSLinkID"]),
            "r_link_id": str(row["R_LinkID"]),
            "l_link_id": str(row["L_LinkID"])
        }

        for k, v in tag_map.items():
            if v and v != "nan":
                way_elem.append(etree.Element("tag", k=k, v=v))

        osm_root.append(way_elem)
        way_id += 1

    tree = ElementTree(osm_root)
    tree.write(output_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    print(f"✅ OSM 파일 생성 완료: {output_path}")

    # 항상 pbf 생성
    pbf_path = os.path.splitext(output_path)[0] + ".pbf"
    try:
        subprocess.run(["osmium", "cat", output_path, "-o", pbf_path], check=True)
        print(f"✅ PBF 파일 생성 완료: {pbf_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ PBF 변환 실패: {e}")

def main():
    parser = argparse.ArgumentParser(description="SHP to OSM 변환 스크립트")
    parser.add_argument("--node", default='shps/A1_NODE.shp', help="노드 SHP 파일 경로 (예: A1_NODE.shp)")
    parser.add_argument("--link", default='shps/A2_LINK.shp', help="링크 SHP 파일 경로 (예: A2_LINK.shp)")
    parser.add_argument("--output", default="data/network.osm", help="출력 OSM 파일 경로")

    args = parser.parse_args()

    if not os.path.exists(args.node):
        print(f"❌ 노드 파일 없음: {args.node}")
        return
    if not os.path.exists(args.link):
        print(f"❌ 링크 파일 없음: {args.link}")
        return

    convert_shp_to_osm(args.node, args.link, args.output)

if __name__ == "__main__":
    main()

"""Pre- and post-event shortest path routing, detour analysis, and settlement access classification."""

import math
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx
from shapely.geometry import shape, Point
import pyproj

from track_b.schemas import GridSpec, SettlementAccessResult, SettlementAccessStatus, RoutingScenario
from track_b.geo.road_graph import build_scenario_graph


def snap_point_to_graph(
    pt_lon: float,
    pt_lat: float,
    node_coords_utm: Dict[str, Tuple[float, float]],
    transformer_to_utm: pyproj.Transformer,
    max_snap_dist_m: float = 1000.0
) -> Tuple[Optional[str], float]:
    """Snap a WGS84 point to the nearest road network node in metric space."""
    px, py = transformer_to_utm.transform(pt_lon, pt_lat)
    best_node = None
    min_dist = float("inf")

    for nid, (nx_val, ny_val) in node_coords_utm.items():
        d = math.hypot(px - nx_val, py - ny_val)
        if d < min_dist:
            min_dist = d
            best_node = nid

    if min_dist <= max_snap_dist_m:
        return best_node, round(min_dist, 1)
    return None, round(min_dist, 1)


def analyze_settlement_accessibility(
    settlements_geojson: Dict[str, Any],
    hospitals_geojson: Dict[str, Any],
    G_base: nx.Graph,
    node_coords_utm: Dict[str, Tuple[float, float]],
    grid: GridSpec,
    scenario: str = "precautionary",
    max_snap_dist_m: float = 1500.0
) -> Dict[str, Any]:
    """Perform before/after network routing to assess cut-off settlements."""
    transformer_to_utm = pyproj.Transformer.from_crs("EPSG:4326", grid.crs, always_xy=True)
    G_post = build_scenario_graph(G_base, scenario=scenario)

    # 1. Snap hospitals
    hospital_nodes: Dict[str, Dict[str, Any]] = {}
    for h_feat in hospitals_geojson.get("features", []):
        h_geom = shape(h_feat.get("geometry"))
        h_props = h_feat.get("properties", {})
        h_id = str(h_props.get("@id") or h_props.get("id"))
        h_name = h_props.get("name", "Hospital")
        
        nid, dist = snap_point_to_graph(h_geom.x, h_geom.y, node_coords_utm, transformer_to_utm, max_snap_dist_m)
        if nid:
            hospital_nodes[h_id] = {
                "name": h_name,
                "node_id": nid,
                "snap_distance_m": dist,
                "coords": [h_geom.x, h_geom.y]
            }

    # 2. Identify towns
    town_nodes: Dict[str, Dict[str, Any]] = {}
    for s_feat in settlements_geojson.get("features", []):
        s_props = s_feat.get("properties", {})
        p_type = s_props.get("place", "village")
        if p_type in ("town", "city"):
            s_geom = shape(s_feat.get("geometry"))
            s_id = str(s_props.get("@id") or s_props.get("id"))
            nid, dist = snap_point_to_graph(s_geom.x, s_geom.y, node_coords_utm, transformer_to_utm, max_snap_dist_m)
            if nid:
                town_nodes[s_id] = {
                    "name": s_props.get("name", "Town"),
                    "node_id": nid,
                    "snap_distance_m": dist,
                    "coords": [s_geom.x, s_geom.y]
                }

    settlement_results: List[Dict[str, Any]] = []
    status_counts: Dict[str, int] = {
        "access_retained": 0,
        "rerouted": 0,
        "access_lost_to_baseline_destination": 0,
        "newly_cut_off": 0,
        "already_disconnected": 0,
        "unsnapped": 0,
        "destination_missing": 0,
        "boundary_uncertain": 0
    }

    # 3. Analyze each settlement
    for s_feat in settlements_geojson.get("features", []):
        s_geom = shape(s_feat.get("geometry"))
        s_props = s_feat.get("properties", {})
        s_id = str(s_props.get("@id") or s_props.get("id"))
        s_name = s_props.get("name", f"Settlement_{s_id}")
        place_type = s_props.get("place", "village")

        s_node, s_dist = snap_point_to_graph(s_geom.x, s_geom.y, node_coords_utm, transformer_to_utm, max_snap_dist_m)

        if not s_node:
            status_counts["unsnapped"] += 1
            settlement_results.append({
                "settlement_id": s_id,
                "name": s_name,
                "place_type": place_type,
                "coordinates": [s_geom.x, s_geom.y],
                "snapped": False,
                "snap_distance_m": s_dist,
                "status_overall": SettlementAccessStatus.UNSNAPPED.value,
                "status_hospital": SettlementAccessStatus.UNSNAPPED.value,
                "status_town": SettlementAccessStatus.UNSNAPPED.value,
            })
            continue

        # Baseline shortest path to hospitals
        best_hosp_id = None
        base_hosp_dist = float("inf")
        for hid, hdata in hospital_nodes.items():
            hnid = hdata["node_id"]
            if nx.has_path(G_base, s_node, hnid):
                d = nx.shortest_path_length(G_base, s_node, hnid, weight="length")
                if d < base_hosp_dist:
                    base_hosp_dist = d
                    best_hosp_id = hid

        # Post shortest path to hospitals
        post_hosp_dist = float("inf")
        post_hosp_reachable = False
        if best_hosp_id and nx.has_path(G_post, s_node, hospital_nodes[best_hosp_id]["node_id"]):
            post_hosp_dist = nx.shortest_path_length(G_post, s_node, hospital_nodes[best_hosp_id]["node_id"], weight="length")
            post_hosp_reachable = True
        else:
            # Check if any alternate hospital reachable
            for hid, hdata in hospital_nodes.items():
                hnid = hdata["node_id"]
                if nx.has_path(G_post, s_node, hnid):
                    d = nx.shortest_path_length(G_post, s_node, hnid, weight="length")
                    if d < post_hosp_dist:
                        post_hosp_dist = d
                        post_hosp_reachable = True

        # Classify hospital status
        if not hospital_nodes:
            h_status = SettlementAccessStatus.DESTINATION_MISSING
        elif base_hosp_dist == float("inf"):
            h_status = SettlementAccessStatus.ALREADY_DISCONNECTED
        elif not post_hosp_reachable:
            h_status = SettlementAccessStatus.NEWLY_CUT_OFF
        elif post_hosp_dist > base_hosp_dist * 1.1:
            h_status = SettlementAccessStatus.REROUTED
        else:
            h_status = SettlementAccessStatus.ACCESS_RETAINED

        # Baseline shortest path to towns
        best_town_id = None
        base_town_dist = float("inf")
        for tid, tdata in town_nodes.items():
            tnid = tdata["node_id"]
            if nx.has_path(G_base, s_node, tnid):
                d = nx.shortest_path_length(G_base, s_node, tnid, weight="length")
                if d < base_town_dist:
                    base_town_dist = d
                    best_town_id = tid

        post_town_dist = float("inf")
        post_town_reachable = False
        if best_town_id and nx.has_path(G_post, s_node, town_nodes[best_town_id]["node_id"]):
            post_town_dist = nx.shortest_path_length(G_post, s_node, town_nodes[best_town_id]["node_id"], weight="length")
            post_town_reachable = True
        else:
            for tid, tdata in town_nodes.items():
                tnid = tdata["node_id"]
                if nx.has_path(G_post, s_node, tnid):
                    d = nx.shortest_path_length(G_post, s_node, tnid, weight="length")
                    if d < post_town_dist:
                        post_town_dist = d
                        post_town_reachable = True

        if not town_nodes:
            t_status = SettlementAccessStatus.DESTINATION_MISSING
        elif base_town_dist == float("inf"):
            t_status = SettlementAccessStatus.ALREADY_DISCONNECTED
        elif not post_town_reachable:
            t_status = SettlementAccessStatus.NEWLY_CUT_OFF
        elif post_town_dist > base_town_dist * 1.1:
            t_status = SettlementAccessStatus.REROUTED
        else:
            t_status = SettlementAccessStatus.ACCESS_RETAINED

        # Overall status prioritization
        if h_status == SettlementAccessStatus.NEWLY_CUT_OFF or t_status == SettlementAccessStatus.NEWLY_CUT_OFF:
            overall_status = SettlementAccessStatus.NEWLY_CUT_OFF
        elif h_status == SettlementAccessStatus.REROUTED or t_status == SettlementAccessStatus.REROUTED:
            overall_status = SettlementAccessStatus.REROUTED
        elif h_status == SettlementAccessStatus.ACCESS_RETAINED and t_status == SettlementAccessStatus.ACCESS_RETAINED:
            overall_status = SettlementAccessStatus.ACCESS_RETAINED
        else:
            overall_status = h_status

        status_counts[overall_status.value] = status_counts.get(overall_status.value, 0) + 1

        settlement_results.append({
            "settlement_id": s_id,
            "name": s_name,
            "place_type": place_type,
            "coordinates": [s_geom.x, s_geom.y],
            "snapped": True,
            "snap_distance_m": s_dist,
            "status_overall": overall_status.value,
            "status_hospital": h_status.value,
            "status_town": t_status.value,
            "baseline_hospital_dist_km": round(base_hosp_dist / 1000.0, 2) if base_hosp_dist < float("inf") else None,
            "post_hospital_dist_km": round(post_hosp_dist / 1000.0, 2) if post_hosp_dist < float("inf") else None,
            "baseline_town_dist_km": round(base_town_dist / 1000.0, 2) if base_town_dist < float("inf") else None,
            "post_town_dist_km": round(post_town_dist / 1000.0, 2) if post_town_dist < float("inf") else None
        })

    return {
        "scenario": scenario,
        "summary": status_counts,
        "settlements": settlement_results
    }

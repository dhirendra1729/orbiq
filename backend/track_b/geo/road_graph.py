"""Historical road network graph builder with endpoint tolerance and multi-component preservation."""

from typing import Any, Dict, List, Optional, Tuple
import networkx as nx
from shapely.geometry import shape, Point, LineString
import pyproj

from track_b.schemas import GridSpec


def build_road_graph(
    roads_exposure_geojson: Dict[str, Any],
    grid: GridSpec,
    vertex_tolerance_m: float = 3.0
) -> Tuple[nx.Graph, Dict[str, Tuple[float, float]]]:
    """Construct a metric networkx graph from road GeoJSON.

    Preserves ALL connected components, sets metric edge lengths, and stores
    exposure and scenario blocking flags on edges.
    """
    transformer_to_utm = pyproj.Transformer.from_crs("EPSG:4326", grid.crs, always_xy=True)
    G = nx.Graph()

    # Spatial index for endpoint snapping
    nodes_spatial: List[Tuple[float, float, str]] = []  # (x, y, node_id)
    node_id_counter = 0

    def get_or_create_node(pt_utm: Tuple[float, float]) -> str:
        nonlocal node_id_counter
        px, py = pt_utm
        # Find existing node within vertex_tolerance_m
        for ex, ey, nid in nodes_spatial:
            if (px - ex)**2 + (py - ey)**2 <= vertex_tolerance_m**2:
                return nid
        
        nid = f"n_{node_id_counter}"
        node_id_counter += 1
        nodes_spatial.append((px, py, nid))
        G.add_node(nid, x=px, y=py)
        return nid

    node_coords: Dict[str, Tuple[float, float]] = {}

    for feat in roads_exposure_geojson.get("features", []):
        geom = shape(feat.get("geometry"))
        props = feat.get("properties", {})
        way_id = str(props.get("id"))

        if geom.geom_type == "LineString":
            lines = [geom]
        elif geom.geom_type == "MultiLineString":
            lines = list(geom.geoms)
        else:
            continue

        for l_idx, line in enumerate(lines):
            coords = list(line.coords)
            if len(coords) < 2:
                continue

            # Convert coords to UTM
            utm_coords = [transformer_to_utm.transform(c[0], c[1]) for c in coords]
            u = get_or_create_node(utm_coords[0])
            v = get_or_create_node(utm_coords[-1])

            # Edge metric length
            seg_line = LineString(utm_coords)
            edge_len_m = float(round(seg_line.length, 2))

            node_coords[u] = utm_coords[0]
            node_coords[v] = utm_coords[-1]

            edge_key = f"{way_id}_{l_idx}"
            G.add_edge(
                u, v,
                key=edge_key,
                way_id=way_id,
                length=edge_len_m,
                highway=props.get("highway", "unclassified"),
                name=props.get("name", ""),
                is_bridge=props.get("is_bridge", False),
                water_overlap_m=props.get("water_overlap_m", 0.0),
                debris_overlap_m=props.get("debris_overlap_m", 0.0),
                blocked_optimistic=props.get("blocked_optimistic", False),
                blocked_precautionary=props.get("blocked_precautionary", False),
                coords_wgs84=coords
            )

    return G, node_coords


def build_scenario_graph(
    G_base: nx.Graph,
    scenario: str = "precautionary"
) -> nx.Graph:
    """Create a post-event graph by filtering blocked edges under the specified policy."""
    G_post = G_base.copy()
    edges_to_remove = []

    for u, v, data in G_post.edges(data=True):
        if scenario == "optimistic" and data.get("blocked_optimistic", False):
            edges_to_remove.append((u, v))
        elif scenario == "precautionary" and data.get("blocked_precautionary", False):
            edges_to_remove.append((u, v))

    for u, v in edges_to_remove:
        G_post.remove_edge(u, v)

    return G_post

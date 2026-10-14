"use client";

import React, { useEffect, useState, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  ZoomControl,
  CircleMarker,
  Popup,
  useMap,
  useMapEvents
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { Layers, Eye, EyeOff, Navigation, Sparkles } from "lucide-react";

interface DamageMapProps {
  runId: string | null;
  aoiGeojson?: any;
  inundationData?: any;
  debrisData?: any;
  buildingsData?: any;
  roadsData?: any;
  settlementsData?: any[];
  downstreamCorridorData?: any;
  onFeatureSelect?: (type: string, feature: any) => void;
  onMapClickForDownstream?: (lat: number, lon: number) => void;
}

// Map helper to auto-fit bounds
function FitBoundsHelper({ aoi }: { aoi?: any }) {
  const map = useMap();
  useEffect(() => {
    if (!aoi) return;
    try {
      const geoLayer = L.geoJSON(aoi);
      const bounds = geoLayer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [30, 30] });
      }
    } catch (e) {
      console.warn("Could not fit bounds:", e);
    }
  }, [aoi, map]);
  return null;
}

// Map click listener for downstream tracing
function MapClickHandler({ onMapClick }: { onMapClick?: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(e) {
      if (onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    }
  });
  return null;
}

export default function DamageMap({
  runId,
  aoiGeojson,
  inundationData,
  debrisData,
  buildingsData,
  roadsData,
  settlementsData,
  downstreamCorridorData,
  onFeatureSelect,
  onMapClickForDownstream
}: DamageMapProps) {
  const [showInundation, setShowInundation] = useState(true);
  const [showDebris, setShowDebris] = useState(true);
  const [showBuildings, setShowBuildings] = useState(true);
  const [showRoads, setShowRoads] = useState(true);
  const [showSettlements, setShowSettlements] = useState(true);
  const [showDownstream, setShowDownstream] = useState(true);

  // Basemap options: public keyless providers
  const [basemap, setBasemap] = useState<"osm" | "satellite">("osm");

  const basemapUrls = {
    osm: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    satellite: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
  };

  return (
    <div className="relative w-full h-full min-h-[500px] rounded-lg overflow-hidden border border-slate-700 bg-slate-950">
      <MapContainer
        center={[28.0, 85.2]}
        zoom={11}
        zoomControl={false}
        className="w-full h-full z-0"
      >
        <ZoomControl position="topright" />
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap'
          url={basemapUrls[basemap]}
        />
        <FitBoundsHelper aoi={aoiGeojson} />
        <MapClickHandler onMapClick={onMapClickForDownstream} />

        {/* AOI Boundary Layer */}
        {aoiGeojson && (
          <GeoJSON
            key="aoi_boundary"
            data={aoiGeojson}
            style={{
              color: "#38bdf8",
              weight: 2,
              dashArray: "4, 4",
              fillColor: "transparent"
            }}
          />
        )}

        {/* Water Inundation (Observed) */}
        {showInundation && inundationData && (
          <GeoJSON
            key={`water_${runId}`}
            data={inundationData}
            style={{
              color: "#0284c7",
              weight: 1.5,
              fillColor: "#38bdf8",
              fillOpacity: 0.65
            }}
            onEachFeature={(feat, layer) => {
              layer.on("click", () => onFeatureSelect && onFeatureSelect("water", feat));
            }}
          />
        )}

        {/* Candidate Debris (Observed/Derived) */}
        {showDebris && debrisData && (
          <GeoJSON
            key={`debris_${runId}`}
            data={debrisData}
            style={{
              color: "#d97706",
              weight: 1.5,
              fillColor: "#f59e0b",
              fillOpacity: 0.55
            }}
            onEachFeature={(feat, layer) => {
              layer.on("click", () => onFeatureSelect && onFeatureSelect("debris", feat));
            }}
          />
        )}

        {/* Exposed Roads (Estimated) */}
        {showRoads && roadsData && (
          <GeoJSON
            key={`roads_${runId}`}
            data={roadsData}
            style={(feat) => {
              const isFlooded = feat?.properties?.water_overlap_m > 0 || feat?.properties?.debris_overlap_m > 0;
              return {
                color: isFlooded ? "#ef4444" : "#94a3b8",
                weight: isFlooded ? 3.5 : 1.5,
                dashArray: isFlooded ? "6, 4" : undefined,
                opacity: 0.9
              };
            }}
            onEachFeature={(feat, layer) => {
              layer.on("click", () => onFeatureSelect && onFeatureSelect("road", feat));
            }}
          />
        )}

        {/* Exposed Buildings (Estimated) */}
        {showBuildings && buildingsData && (
          <GeoJSON
            key={`bldg_${runId}`}
            data={buildingsData}
            style={(feat) => {
              const expClass = feat?.properties?.exposure_class;
              const isExposed = expClass && expClass !== "no_mapped_overlap";
              return {
                color: isExposed ? "#dc2626" : "#64748b",
                weight: 1,
                fillColor: isExposed ? "#f87171" : "#475569",
                fillOpacity: isExposed ? 0.8 : 0.2
              };
            }}
            onEachFeature={(feat, layer) => {
              layer.on("click", () => onFeatureSelect && onFeatureSelect("building", feat));
            }}
          />
        )}

        {/* Downstream Corridor Bonus (Simulated) */}
        {showDownstream && downstreamCorridorData && (
          <GeoJSON
            key={`downstream_${runId}`}
            data={downstreamCorridorData}
            style={(feat) => {
              if (feat?.properties?.type === "dem_derived_drainage_path") {
                return { color: "#a855f7", weight: 3.5, opacity: 0.9 };
              }
              return { color: "#9333ea", weight: 1, dashArray: "3, 3", fillColor: "#c084fc", fillOpacity: 0.2 };
            }}
          />
        )}

        {/* Settlement Access Status Markers (Estimated) */}
        {showSettlements && settlementsData && settlementsData.map((s, idx) => {
          const isCutOff = s.status_overall === "newly_cut_off";
          const isRerouted = s.status_overall === "rerouted";
          const markerColor = isCutOff ? "#ef4444" : isRerouted ? "#eab308" : "#22c55e";

          return (
            <CircleMarker
              key={`settlement_${s.settlement_id || idx}`}
              center={[s.coordinates[1], s.coordinates[0]]}
              radius={isCutOff ? 7 : 5}
              pathOptions={{
                color: "#ffffff",
                weight: 1.5,
                fillColor: markerColor,
                fillOpacity: 0.95
              }}
              eventHandlers={{
                click: () => onFeatureSelect && onFeatureSelect("settlement", s)
              }}
            >
              <Popup>
                <div className="text-xs">
                  <strong>{s.name}</strong> ({s.place_type})<br />
                  Status: <span className="font-semibold">{s.status_overall}</span><br />
                  Hospital dist: {s.post_hospital_dist_km ? `${s.post_hospital_dist_km} km` : "Cut off"}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Layer Control Bar */}
      <div className="absolute top-3 left-3 z-[1000] bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-lg p-2.5 shadow-xl text-xs space-y-1.5 text-slate-200">
        <div className="flex items-center gap-1.5 font-semibold text-slate-100 pb-1 border-b border-slate-700">
          <Layers className="w-3.5 h-3.5 text-sky-400" />
          <span>Track B Map Layers</span>
        </div>
        <div className="space-y-1 pt-1">
          <label className="flex items-center gap-2 cursor-pointer hover:text-white">
            <input type="checkbox" checked={showInundation} onChange={(e) => setShowInundation(e.target.checked)} className="rounded bg-slate-800 text-sky-500" />
            <span className="w-2.5 h-2.5 rounded-sm bg-sky-400 inline-block"></span>
            <span>Flood Inundation (SAR)</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:text-white">
            <input type="checkbox" checked={showDebris} onChange={(e) => setShowDebris(e.target.checked)} className="rounded bg-slate-800 text-amber-500" />
            <span className="w-2.5 h-2.5 rounded-sm bg-amber-500 inline-block"></span>
            <span>Candidate Debris (S2)</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:text-white">
            <input type="checkbox" checked={showRoads} onChange={(e) => setShowRoads(e.target.checked)} className="rounded bg-slate-800 text-red-500" />
            <span className="w-2.5 h-0.5 bg-red-500 inline-block"></span>
            <span>Roads & Bridges</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:text-white">
            <input type="checkbox" checked={showBuildings} onChange={(e) => setShowBuildings(e.target.checked)} className="rounded bg-slate-800 text-red-400" />
            <span className="w-2.5 h-2.5 rounded-sm bg-red-400 inline-block"></span>
            <span>Exposed Buildings</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:text-white">
            <input type="checkbox" checked={showSettlements} onChange={(e) => setShowSettlements(e.target.checked)} className="rounded bg-slate-800 text-emerald-400" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span>
            <span>Settlement Access</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:text-white">
            <input type="checkbox" checked={showDownstream} onChange={(e) => setShowDownstream(e.target.checked)} className="rounded bg-slate-800 text-purple-400" />
            <span className="w-2.5 h-1 bg-purple-500 inline-block"></span>
            <span>Downstream Path (DEM)</span>
          </label>
        </div>
      </div>

      {/* Legend & Instructions */}
      <div className="absolute bottom-3 left-3 z-[1000] bg-slate-900/80 backdrop-blur-sm border border-slate-800 rounded px-2.5 py-1.5 text-[11px] text-slate-300">
        <span className="text-purple-300 font-medium">Tip:</span> Click anywhere on map to calculate DEM downstream drainage path.
      </div>
    </div>
  );
}

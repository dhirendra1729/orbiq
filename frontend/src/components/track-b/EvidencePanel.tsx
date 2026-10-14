"use client";

import React from "react";
import { Info, MapPin, Building, Activity, ShieldCheck, X } from "lucide-react";

interface EvidencePanelProps {
  selectedFeature: { type: string; data: any } | null;
  onClose: () => void;
}

export default function EvidencePanel({ selectedFeature, onClose }: EvidencePanelProps) {
  if (!selectedFeature) return null;

  const { type, data } = selectedFeature;
  const props = data.properties || data;

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-3.5 space-y-2.5 text-xs text-slate-200 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
        <div className="flex items-center gap-1.5 font-semibold text-slate-100">
          <Info className="w-3.5 h-3.5 text-sky-400" />
          <span>Feature Evidence Inspector: {type.toUpperCase()}</span>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-0.5 rounded hover:bg-slate-800"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="space-y-1.5 font-mono text-[11px]">
        {type === "building" && (
          <>
            <div className="flex justify-between">
              <span className="text-slate-400">Building ID:</span>
              <span className="text-slate-200">{props.id || "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Name / Amenity:</span>
              <span className="text-slate-200">{props.name || props.amenity || "Unnamed structure"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Exposure Class:</span>
              <span className={`font-semibold ${props.exposure_class !== "no_mapped_overlap" ? "text-red-400" : "text-emerald-400"}`}>
                {props.exposure_class}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Footprint Area:</span>
              <span className="text-slate-200">{props.footprint_area_m2} m²</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Water Overlap:</span>
              <span className="text-sky-300">{props.water_overlap_m2} m² ({Math.round(props.overlap_fraction * 100)}%)</span>
            </div>
          </>
        )}

        {type === "road" && (
          <>
            <div className="flex justify-between">
              <span className="text-slate-400">Road Way ID:</span>
              <span className="text-slate-200">{props.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Highway Class:</span>
              <span className="text-slate-200">{props.highway} {props.is_bridge ? "(Bridge)" : ""}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Segment Length:</span>
              <span className="text-slate-200">{props.length_m} m</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Flooded Length:</span>
              <span className="text-red-400 font-semibold">{props.water_overlap_m} m</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Status:</span>
              <span className={props.exposure_status === "exposed" ? "text-red-400" : "text-emerald-400"}>
                {props.exposure_status}
              </span>
            </div>
          </>
        )}

        {type === "settlement" && (
          <>
            <div className="flex justify-between">
              <span className="text-slate-400">Settlement Name:</span>
              <span className="font-sans font-semibold text-slate-100">{props.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Place Type:</span>
              <span className="text-slate-200">{props.place_type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Access Status:</span>
              <span className={`font-semibold ${props.status_overall === "newly_cut_off" ? "text-red-400" : "text-emerald-400"}`}>
                {props.status_overall}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Hospital Post Dist:</span>
              <span className="text-slate-200">{props.post_hospital_dist_km ? `${props.post_hospital_dist_km} km` : "Cut off"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Baseline Distance:</span>
              <span className="text-slate-200">{props.baseline_hospital_dist_km ? `${props.baseline_hospital_dist_km} km` : "N/A"}</span>
            </div>
          </>
        )}

        {type === "water" && (
          <>
            <div className="flex justify-between">
              <span className="text-slate-400">Hazard Class:</span>
              <span className="text-sky-300 font-semibold">New Flood Inundation</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Polygon Area:</span>
              <span className="text-slate-200">{props.area_m2} m² ({Math.round(props.area_m2 / 10000) / 100} ha)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Evidence Sensor:</span>
              <span className="text-slate-300">Sentinel-1 SAR IW (VV)</span>
            </div>
          </>
        )}

        {type === "debris" && (
          <>
            <div className="flex justify-between">
              <span className="text-slate-400">Hazard Class:</span>
              <span className="text-amber-300 font-semibold">Candidate Debris / Sediment</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Evidence Sensor:</span>
              <span className="text-slate-300">Sentinel-2 L2A (ΔNDVI + SWIR)</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

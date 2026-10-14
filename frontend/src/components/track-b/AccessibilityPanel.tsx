"use client";

import React, { useState } from "react";
import { AlertTriangle, CheckCircle, Navigation, ShieldAlert, Route } from "lucide-react";

interface AccessibilityPanelProps {
  settlements: any[];
  scenario?: string;
  onSelectSettlement?: (settlement: any) => void;
}

export default function AccessibilityPanel({
  settlements = [],
  scenario = "precautionary",
  onSelectSettlement
}: AccessibilityPanelProps) {
  const [filter, setFilter] = useState<string>("all");

  const filtered = settlements.filter((s) => {
    if (filter === "all") return true;
    return s.status_overall === filter;
  });

  const cutOffCount = settlements.filter((s) => s.status_overall === "newly_cut_off").length;
  const reroutedCount = settlements.filter((s) => s.status_overall === "rerouted").length;
  const retainedCount = settlements.filter((s) => s.status_overall === "access_retained").length;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3 text-slate-200">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
          <Navigation className="w-4 h-4 text-emerald-400" />
          <span>Settlement Access Intelligence</span>
        </h3>
        <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
          Policy: {scenario}
        </span>
      </div>

      {/* Summary KPI Badges */}
      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <div
          onClick={() => setFilter(filter === "newly_cut_off" ? "all" : "newly_cut_off")}
          className={`cursor-pointer p-2 rounded border transition ${
            filter === "newly_cut_off" ? "bg-red-950/80 border-red-700" : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
          }`}
        >
          <div className="text-red-400 font-bold text-lg">{cutOffCount}</div>
          <div className="text-[10px] text-slate-400">Newly Cut Off</div>
        </div>
        <div
          onClick={() => setFilter(filter === "rerouted" ? "all" : "rerouted")}
          className={`cursor-pointer p-2 rounded border transition ${
            filter === "rerouted" ? "bg-amber-950/80 border-amber-700" : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
          }`}
        >
          <div className="text-amber-400 font-bold text-lg">{reroutedCount}</div>
          <div className="text-[10px] text-slate-400">Rerouted / Detour</div>
        </div>
        <div
          onClick={() => setFilter(filter === "access_retained" ? "all" : "access_retained")}
          className={`cursor-pointer p-2 rounded border transition ${
            filter === "access_retained" ? "bg-emerald-950/80 border-emerald-700" : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
          }`}
        >
          <div className="text-emerald-400 font-bold text-lg">{retainedCount}</div>
          <div className="text-[10px] text-slate-400">Access Retained</div>
        </div>
      </div>

      {/* Settlements Table */}
      <div className="max-h-60 overflow-y-auto border border-slate-800 rounded">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-slate-950/80 sticky top-0 border-b border-slate-800 text-[11px] text-slate-400">
            <tr>
              <th className="p-2">Settlement</th>
              <th className="p-2">Type</th>
              <th className="p-2">Hospital Route</th>
              <th className="p-2 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={4} className="p-3 text-center text-slate-500 italic">
                  No settlements match the selected filter.
                </td>
              </tr>
            ) : (
              filtered.map((s, idx) => {
                const isCutOff = s.status_overall === "newly_cut_off";
                const isRerouted = s.status_overall === "rerouted";
                return (
                  <tr
                    key={s.settlement_id || idx}
                    onClick={() => onSelectSettlement && onSelectSettlement(s)}
                    className="hover:bg-slate-800/50 cursor-pointer transition"
                  >
                    <td className="p-2 font-sans font-medium text-slate-200">{s.name}</td>
                    <td className="p-2 text-slate-400">{s.place_type}</td>
                    <td className="p-2 text-slate-300">
                      {isCutOff ? (
                        <span className="text-red-400">Impassable</span>
                      ) : s.post_hospital_dist_km ? (
                        <span>
                          {s.post_hospital_dist_km} km{" "}
                          {s.baseline_hospital_dist_km && s.post_hospital_dist_km > s.baseline_hospital_dist_km && (
                            <span className="text-amber-400 text-[10px]">
                              (+{(s.post_hospital_dist_km - s.baseline_hospital_dist_km).toFixed(1)} km)
                            </span>
                          )}
                        </span>
                      ) : (
                        "N/A"
                      )}
                    </td>
                    <td className="p-2 text-right">
                      {isCutOff ? (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-red-950/80 text-red-300 border border-red-800">
                          Cut Off
                        </span>
                      ) : isRerouted ? (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-amber-950/80 text-amber-300 border border-amber-800">
                          Rerouted
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-emerald-950/80 text-emerald-300 border border-emerald-800">
                          Retained
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

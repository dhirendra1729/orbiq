"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import {
  Satellite,
  ShieldAlert,
  Bot,
  Layers,
  Sparkles,
  RefreshCw,
  FileText,
  AlertCircle,
  Clock,
  CheckCircle2,
  Navigation
} from "lucide-react";

import AreaDateForm, { TRISHULI_CASE_STUDY } from "./AreaDateForm";
import AccessibilityPanel from "./AccessibilityPanel";
import CopilotPanel from "./CopilotPanel";
import ComparisonPanel from "./ComparisonPanel";
import ReportDownloads from "./ReportDownloads";
import EvidencePanel from "./EvidencePanel";
import { cn } from "@/components/ui/cn";

// Dynamic import for Leaflet map to ensure client-only rendering
const DamageMap = dynamic(() => import("./DamageMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[500px] flex items-center justify-center bg-slate-950 border border-slate-800 rounded-lg text-slate-500 text-xs">
      Loading Leaflet satellite damage view...
    </div>
  )
});

interface TrackBStudioProps {
  embedded?: boolean;
  onSwitchMode?: (mode: string) => void;
}

export default function TrackBStudio({ embedded = false, onSwitchMode }: TrackBStudioProps) {
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<"copilot" | "access" | "validation">("copilot");

  // Layers data
  const [inundationData, setInundationData] = useState<any>(null);
  const [debrisData, setDebrisData] = useState<any>(null);
  const [buildingsData, setBuildingsData] = useState<any>(null);
  const [roadsData, setRoadsData] = useState<any>(null);
  const [settlementsData, setSettlementsData] = useState<any[]>([]);
  const [downstreamData, setDownstreamData] = useState<any>(null);
  const [selectedFeature, setSelectedFeature] = useState<{ type: string; data: any } | null>(null);

  // Automatically load the latest completed case study run on mount so data is immediately visible
  useEffect(() => {
    const loadInitialCaseStudy = async () => {
      try {
        const res = await fetch("/api/track-b/runs/run_20261014_165946_2a3de6");
        if (res.ok) {
          const data = await res.json();
          if (data && (data.status === "completed" || data.status === "reporting")) {
            setCurrentRunId(data.run_id);
            setRunStatus(data);
            fetchLayers(data.run_id);
          }
        }
      } catch (err) {
        console.warn("Could not load initial case study run:", err);
      }
    };
    loadInitialCaseStudy();
  }, []);

  // Poll run status
  useEffect(() => {
    if (!currentRunId || !isRunning) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/track-b/runs/${currentRunId}`);
        if (!res.ok) return;
        const data = await res.json();
        setRunStatus(data);

        if (data.status === "completed" || data.status === "failed") {
          setIsRunning(false);
          // Load generated layer artifacts
          fetchLayers(data.run_id);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [currentRunId, isRunning]);

  const fetchLayers = async (runId: string) => {
    try {
      // Inundation GeoJSON
      const rWater = await fetch(`/api/track-b/runs/${runId}/exports/s1_inundation.geojson`);
      if (rWater.ok) setInundationData(await rWater.json());

      // Debris GeoJSON
      const rDebris = await fetch(`/api/track-b/runs/${runId}/exports/s2_candidate_debris.geojson`);
      if (rDebris.ok) setDebrisData(await rDebris.json());

      // Buildings GeoJSON
      const rBldg = await fetch(`/api/track-b/runs/${runId}/exports/buildings_exposure.geojson`);
      if (rBldg.ok) setBuildingsData(await rBldg.json());

      // Roads GeoJSON
      const rRoad = await fetch(`/api/track-b/runs/${runId}/exports/roads_exposure.geojson`);
      if (rRoad.ok) setRoadsData(await rRoad.json());

      // Settlement Access JSON
      const rAcc = await fetch(`/api/track-b/runs/${runId}/exports/settlement_access.json`);
      if (rAcc.ok) {
        const acc = await rAcc.json();
        setSettlementsData(acc.settlements || []);
      }
    } catch (e) {
      console.warn("Could not load all layers:", e);
    }
  };

  const handleStartAnalysis = async (formData: any) => {
    setIsRunning(true);
    setRunStatus(null);
    setInundationData(null);
    setDebrisData(null);
    setBuildingsData(null);
    setRoadsData(null);
    setSettlementsData([]);
    setDownstreamData(null);

    try {
      const res = await fetch("/api/track-b/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      if (!res.ok) {
        const err = await res.json();
        alert(`Failed to start run: ${err.detail || "Server error"}`);
        setIsRunning(false);
        return;
      }
      const data = await res.json();
      setCurrentRunId(data.run_id);
      setRunStatus(data);
    } catch (e: any) {
      alert(`Error starting analysis: ${e.message || e}`);
      setIsRunning(false);
    }
  };

  const handleMapClickForDownstream = async (lat: number, lon: number) => {
    if (!currentRunId) {
      alert("Execute an analysis run first before tracing downstream flow paths.");
      return;
    }

    try {
      const res = await fetch(`/api/track-b/runs/${currentRunId}/downstream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          point: [lon, lat],
          buffer_m: 800.0
        })
      });
      if (res.ok) {
        const data = await res.json();
        setDownstreamData(data);
      }
    } catch (e) {
      console.warn("Downstream flow tracing error:", e);
    }
  };

  return (
    <div
      className={cn(
        "bg-slate-950 text-slate-100 flex flex-col font-sans",
        embedded ? "h-full overflow-y-auto fs-scroll" : "min-h-screen"
      )}
    >
      {/* Top Header - only rendered when viewing standalone /track-b */}
      {!embedded && (
        <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 py-3 flex items-center justify-between sticky top-0 z-50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-sky-950 border border-sky-800 text-sky-400">
              <Satellite className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-slate-100 tracking-wide">
                  Orbiq Track B
                </h1>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-sky-950 text-sky-300 border border-sky-800">
                  Satellite Damage & Access Intelligence
                </span>
              </div>
              <div className="text-xs text-slate-400">
                Multimodal AI Hackathon 2026 • Post-Event Earth Observation & Graph Access Studio
              </div>
            </div>
          </div>

          {/* Status Pills & Switcher */}
          <div className="flex items-center gap-2 text-xs">
            {runStatus && (
              <div className="flex items-center gap-2 px-3 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300 font-mono text-[11px]">
                <span className="text-slate-500">Run:</span>
                <span className="text-sky-300 font-semibold">{runStatus.run_id}</span>
                <span className="text-slate-600">|</span>
                <span className="text-slate-400">Stage:</span>
                <span className="text-amber-300 font-medium">{runStatus.current_stage}</span>
              </div>
            )}
            {onSwitchMode ? (
              <button
                type="button"
                onClick={() => onSwitchMode("studio")}
                className="text-xs px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              >
                Dam Solver
              </button>
            ) : (
              <a
                href="/?view=studio"
                className="text-xs px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              >
                Dam Studio
              </a>
            )}
          </div>
        </header>
      )}

      {/* Educational Disclaimer Banner */}
      <div className="bg-amber-950/40 border-b border-amber-900/60 px-6 py-2 text-[11px] text-amber-300 flex flex-wrap items-center justify-between gap-2 shrink-0">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-amber-400" />
          <span>
            <strong>EDUCATIONAL PROTOTYPE:</strong> Post-event assessment system adhering strictly to pre-event OSM and same-track SAR baselines. Does not prove structural bridge destruction or provide minutes-ahead evacuation warnings.
          </span>
        </div>
        {embedded && runStatus && (
          <div className="flex items-center gap-2 px-2.5 py-0.5 rounded bg-slate-900/90 border border-slate-800 text-slate-300 font-mono text-[11px] shrink-0">
            <span className="text-slate-500">Active Run:</span>
            <span className="text-sky-300 font-semibold">{runStatus.run_id}</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400">Stage:</span>
            <span className="text-amber-300 font-medium">{runStatus.current_stage}</span>
          </div>
        )}
      </div>

      {/* Main Workspace Layout */}
      <div className="flex-1 p-4 grid grid-cols-12 gap-4 max-w-[1700px] w-full mx-auto">
        {/* Left Column: Configuration & Exports (3 cols) */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          <AreaDateForm onSubmit={handleStartAnalysis} isRunning={isRunning} />
          {runStatus && (
            <ReportDownloads runId={runStatus.run_id} />
          )}
        </div>

        {/* Center: Interactive Damage Map (6 cols) */}
        <div className="col-span-12 lg:col-span-6 flex flex-col space-y-3">
          <div className="flex-1 relative min-h-[500px]">
            <DamageMap
              runId={currentRunId}
              aoiGeojson={runStatus?.request?.aoi || TRISHULI_CASE_STUDY.aoi}
              inundationData={inundationData}
              debrisData={debrisData}
              buildingsData={buildingsData}
              roadsData={roadsData}
              settlementsData={settlementsData}
              downstreamCorridorData={downstreamData}
              onFeatureSelect={(type, data) => setSelectedFeature({ type, data })}
              onMapClickForDownstream={handleMapClickForDownstream}
            />
            {selectedFeature && (
              <div className="absolute top-3 right-3 w-80 z-[1000]">
                <EvidencePanel
                  selectedFeature={selectedFeature}
                  onClose={() => setSelectedFeature(null)}
                />
              </div>
            )}
          </div>
        </div>

        {/* Right Column: AI Copilot, Accessibility & Validation Tabs (3 cols) */}
        <div className="col-span-12 lg:col-span-3 space-y-3">
          {/* Tab Navigation */}
          <div className="flex border-b border-slate-800 text-xs font-medium">
            <button
              onClick={() => setActiveTab("copilot")}
              className={`flex-1 py-2 text-center border-b-2 transition ${
                activeTab === "copilot"
                  ? "border-sky-500 text-sky-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              AI Copilot
            </button>
            <button
              onClick={() => setActiveTab("access")}
              className={`flex-1 py-2 text-center border-b-2 transition ${
                activeTab === "access"
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Cut-off Access
            </button>
            <button
              onClick={() => setActiveTab("validation")}
              className={`flex-1 py-2 text-center border-b-2 transition ${
                activeTab === "validation"
                  ? "border-purple-500 text-purple-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              EMSR927
            </button>
          </div>

          {/* Active Tab Panel */}
          {activeTab === "copilot" && (
            <CopilotPanel runId={currentRunId} scenario="precautionary" />
          )}

          {activeTab === "access" && (
            <AccessibilityPanel
              settlements={settlementsData}
              scenario="precautionary"
              onSelectSettlement={(s) => setSelectedFeature({ type: "settlement", data: s })}
            />
          )}

          {activeTab === "validation" && (
            <ComparisonPanel
              runId={currentRunId}
              freezeHash={runStatus?.freeze_hash}
              isFrozen={runStatus?.prediction_frozen}
            />
          )}
        </div>
      </div>
    </div>
  );
}

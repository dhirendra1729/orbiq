"use client";

import React, { useState } from "react";
import { Play, Sparkles, Sliders, Calendar, MapPin, Globe } from "lucide-react";

interface AreaDateFormProps {
  onSubmit: (formData: any) => void;
  isRunning: boolean;
}

// Trishuli River, Nepal case study preset polygon
export const TRISHULI_CASE_STUDY = {
  name: "Trishuli Basin, Nepal (August 2026)",
  event_date: "2026-08-26",
  event_timezone: "Asia/Kathmandu",
  aoi: {
    type: "Polygon",
    coordinates: [
      [
        [85.12, 27.92],
        [85.28, 27.92],
        [85.28, 28.08],
        [85.12, 28.08],
        [85.12, 27.92]
      ]
    ]
  }
};

export default function AreaDateForm({ onSubmit, isRunning }: AreaDateFormProps) {
  const [eventDate, setEventDate] = useState("2026-08-26");
  const [eventTimezone, setEventTimezone] = useState("Asia/Kathmandu");
  const [resolution, setResolution] = useState(20);
  const [scenario, setScenario] = useState("precautionary");
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Default to Trishuli case study coordinates
  const [coordinatesJson, setCoordinatesJson] = useState(
    JSON.stringify(TRISHULI_CASE_STUDY.aoi.coordinates, null, 2)
  );

  const handleApplyPreset = () => {
    setEventDate(TRISHULI_CASE_STUDY.event_date);
    setEventTimezone(TRISHULI_CASE_STUDY.event_timezone);
    setCoordinatesJson(JSON.stringify(TRISHULI_CASE_STUDY.aoi.coordinates, null, 2));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const parsedCoords = JSON.parse(coordinatesJson);
      onSubmit({
        aoi: {
          type: "Polygon",
          coordinates: parsedCoords
        },
        event_date: eventDate,
        event_timezone: eventTimezone,
        analysis_resolution_m: Number(resolution),
        routing_mode: "motor_vehicle",
        routing_scenario: scenario
      });
    } catch (err) {
      alert("Invalid JSON in coordinates field. Please provide a valid coordinate array.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-4 text-slate-200">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
          <MapPin className="w-4 h-4 text-sky-400" />
          <span>Analysis Configuration</span>
        </h2>
        <button
          type="button"
          onClick={handleApplyPreset}
          className="text-xs flex items-center gap-1 text-sky-400 hover:text-sky-300 font-medium px-2 py-0.5 rounded bg-sky-950/60 border border-sky-800/60"
        >
          <Sparkles className="w-3 h-3" />
          <span>Load Trishuli Preset</span>
        </button>
      </div>

      <div className="space-y-3">
        {/* Date and Timezone */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1 flex items-center gap-1">
              <Calendar className="w-3 h-3 text-slate-500" /> Event Date
            </label>
            <input
              type="date"
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1 flex items-center gap-1">
              <Globe className="w-3 h-3 text-slate-500" /> Timezone
            </label>
            <select
              value={eventTimezone}
              onChange={(e) => setEventTimezone(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            >
              <option value="Asia/Kathmandu">Asia/Kathmandu (Nepal)</option>
              <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
              <option value="UTC">UTC</option>
            </select>
          </div>
        </div>

        {/* AOI Coordinates */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            AOI Polygon Coordinates (WGS84 [lon, lat])
          </label>
          <textarea
            rows={4}
            value={coordinatesJson}
            onChange={(e) => setCoordinatesJson(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-xs font-mono text-slate-300 focus:outline-none focus:border-sky-500"
            required
          />
        </div>

        {/* Advanced Settings Toggle */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1"
          >
            <Sliders className="w-3 h-3" />
            <span>{showAdvanced ? "Hide Advanced Settings" : "Show Advanced Settings"}</span>
          </button>
        </div>

        {showAdvanced && (
          <div className="p-3 bg-slate-950/70 border border-slate-800 rounded space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Analysis Grid Resolution:</span>
              <select
                value={resolution}
                onChange={(e) => setResolution(Number(e.target.value))}
                className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
              >
                <option value={20}>20m (Standard)</option>
                <option value={10}>10m (High Res)</option>
                <option value={30}>30m (Fast Preview)</option>
              </select>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Access Policy Scenario:</span>
              <select
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
              >
                <option value="precautionary">Precautionary (Conservative)</option>
                <option value="optimistic">Optimistic (Open bridges)</option>
              </select>
            </div>
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={isRunning}
        className="w-full py-2 px-4 rounded bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 disabled:text-slate-500 font-medium text-xs text-white flex items-center justify-center gap-2 transition"
      >
        <Play className="w-3.5 h-3.5 fill-current" />
        <span>{isRunning ? "Running Satellite Analysis..." : "Execute Analysis Run"}</span>
      </button>
    </form>
  );
}

"use client";

import React, { useState } from "react";
import { ShieldCheck, CheckSquare, AlertTriangle, ExternalLink, RefreshCw } from "lucide-react";

interface ComparisonPanelProps {
  runId: string | null;
  freezeHash?: string | null;
  isFrozen?: boolean;
}

export default function ComparisonPanel({ runId, freezeHash, isFrozen }: ComparisonPanelProps) {
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunValidation = async () => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/track-b/runs/${runId}/validation/emsr927`, {
        method: "POST"
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Validation comparison failed");
      }
      setComparison(data);
    } catch (err: any) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3 text-slate-200">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-sky-400" />
          <span>Independent Reference Comparison (EMSR927)</span>
        </h3>
        <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-sky-950 text-sky-300 border border-sky-800">
          STRICTLY CHECKING-ONLY
        </span>
      </div>

      {/* Freeze Invariant State */}
      <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-xs space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Prediction Freeze State:</span>
          <span className={`font-mono text-[11px] font-semibold ${isFrozen ? "text-emerald-400" : "text-amber-400"}`}>
            {isFrozen ? "FROZEN_FOR_CHECKING" : "UNFROZEN"}
          </span>
        </div>
        {freezeHash && (
          <div className="text-[10px] text-slate-500 font-mono truncate">
            Freeze Digest: {freezeHash}
          </div>
        )}
      </div>

      {/* Trigger Validation Button */}
      <button
        type="button"
        onClick={handleRunValidation}
        disabled={!runId || !isFrozen || loading}
        className="w-full py-1.5 px-3 rounded bg-sky-700 hover:bg-sky-600 disabled:bg-slate-800 disabled:text-slate-600 text-xs font-medium text-white flex items-center justify-center gap-2 transition"
      >
        <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        <span>{loading ? "Comparing with EMSR927..." : "Evaluate Against EMSR927 Reference"}</span>
      </button>

      {error && (
        <div className="p-2.5 rounded bg-red-950/60 border border-red-800 text-xs text-red-300 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Display */}
      {comparison && comparison.metrics && (
        <div className="space-y-3 pt-2">
          <div className="grid grid-cols-4 gap-2 text-center">
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <div className="text-sky-400 font-bold text-base">{comparison.metrics.iou}</div>
              <div className="text-[10px] text-slate-400">IoU (Jaccard)</div>
            </div>
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <div className="text-emerald-400 font-bold text-base">{comparison.metrics.f1_score}</div>
              <div className="text-[10px] text-slate-400">F1 / Dice</div>
            </div>
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <div className="text-amber-400 font-bold text-base">{comparison.metrics.precision}</div>
              <div className="text-[10px] text-slate-400">Precision</div>
            </div>
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <div className="text-purple-400 font-bold text-base">{comparison.metrics.recall}</div>
              <div className="text-[10px] text-slate-400">Recall</div>
            </div>
          </div>

          <div className="p-2 rounded bg-slate-950/80 border border-slate-800 text-[11px] space-y-1">
            <div className="font-semibold text-slate-300">Discrepancy Analysis:</div>
            <ul className="list-disc pl-4 space-y-0.5 text-slate-400">
              {comparison.discrepancy_analysis?.map((item: string, i: number) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="text-[10px] text-slate-500 italic pt-1 border-t border-slate-800">
            {comparison.attribution}
          </div>
        </div>
      )}
    </div>
  );
}

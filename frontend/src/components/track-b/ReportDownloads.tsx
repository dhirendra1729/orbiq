"use client";

import React from "react";
import { Download, FileText, Map, ShieldCheck, FileSpreadsheet } from "lucide-react";

interface ReportDownloadsProps {
  runId: string | null;
}

export default function ReportDownloads({ runId }: ReportDownloadsProps) {
  if (!runId) return null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3 text-slate-200">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
          <Download className="w-4 h-4 text-sky-400" />
          <span>Deliverables & Exportable Artifacts</span>
        </h3>
        <span className="text-[10px] text-slate-400 font-mono">Run: {runId}</span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        {/* English Situation Report */}
        <a
          href={`/api/track-b/runs/${runId}/report?language=en`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 p-2 rounded bg-slate-950 border border-slate-800 hover:border-sky-500 hover:text-sky-300 transition"
        >
          <FileText className="w-4 h-4 text-sky-400 shrink-0" />
          <div>
            <div className="font-medium">Situation Report (EN)</div>
            <div className="text-[10px] text-slate-500">1-Page HTML / PDF Print</div>
          </div>
        </a>

        {/* Nepali Situation Report */}
        <a
          href={`/api/track-b/runs/${runId}/report?language=ne`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 p-2 rounded bg-slate-950 border border-slate-800 hover:border-sky-500 hover:text-sky-300 transition"
        >
          <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
          <div>
            <div className="font-medium">प्रतिवेदन (नेपाली)</div>
            <div className="text-[10px] text-slate-500">1-Page Nepali Report</div>
          </div>
        </a>

        {/* Fused Hazard GeoJSON */}
        <a
          href={`/api/track-b/runs/${runId}/exports/fused_hazard.geojson`}
          download
          className="flex items-center gap-2 p-2 rounded bg-slate-950 border border-slate-800 hover:border-sky-500 hover:text-sky-300 transition"
        >
          <Map className="w-4 h-4 text-amber-400 shrink-0" />
          <div>
            <div className="font-medium">Hazard Envelope</div>
            <div className="text-[10px] text-slate-500">Water + Debris GeoJSON</div>
          </div>
        </a>

        {/* Settlement Access Analysis */}
        <a
          href={`/api/track-b/runs/${runId}/exports/settlement_access.json`}
          download
          className="flex items-center gap-2 p-2 rounded bg-slate-950 border border-slate-800 hover:border-sky-500 hover:text-sky-300 transition"
        >
          <FileSpreadsheet className="w-4 h-4 text-purple-400 shrink-0" />
          <div>
            <div className="font-medium">Settlement Access JSON</div>
            <div className="text-[10px] text-slate-500">Detour & Cut-Off Metrics</div>
          </div>
        </a>

        {/* Fact Store JSON */}
        <a
          href={`/api/track-b/runs/${runId}/exports/facts.json`}
          download
          className="flex items-center gap-2 p-2 rounded bg-slate-950 border border-slate-800 hover:border-sky-500 hover:text-sky-300 transition"
        >
          <ShieldCheck className="w-4 h-4 text-sky-400 shrink-0" />
          <div>
            <div className="font-medium">Fact Store JSON</div>
            <div className="text-[10px] text-slate-500">Verified Evidence Facts</div>
          </div>
        </a>

        {/* Cryptographic Freeze Manifest */}
        <a
          href={`/api/track-b/runs/${runId}/manifest`}
          download
          className="flex items-center gap-2 p-2 rounded bg-slate-950 border border-slate-800 hover:border-sky-500 hover:text-sky-300 transition"
        >
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <div>
            <div className="font-medium">Freeze Manifest</div>
            <div className="text-[10px] text-slate-500">Locked SHA256 Hashes</div>
          </div>
        </a>
      </div>
    </div>
  );
}

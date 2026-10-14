"use client";

import { useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import {
  Waves,
  Map as MapIcon,
  FlaskConical,
  ClipboardCheck,
  Satellite,
  Globe2,
  Menu,
  X,
  Circle,
} from "lucide-react";

import DamBreakStudio from "@/components/DamBreakStudio";
import VerificationView from "@/components/views/VerificationView";
import DeliverablesView from "@/components/views/DeliverablesView";
import { Segmented, Skeleton, type SegmentedOption } from "@/components/ui";
import { cn } from "@/components/ui/cn";
import { BASEMAP_IDS, BASEMAPS, type BasemapId } from "@/lib/basemaps";

// The map pulls in Leaflet, georaster and the image-decoding path. Keep it out
// of the initial bundle so the studio renders without waiting on any of it.
const InundationMapView = dynamic(
  () => import("@/components/views/InundationMapView"),
  {
    ssr: false,
    loading: () => (
      <div className="h-full w-full flex items-center justify-center">
        <div className="w-full max-w-md space-y-3">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-[420px] w-full" />
        </div>
      </div>
    ),
  },
);

const TrackBStudio = dynamic(
  () => import("@/components/track-b/TrackBStudio"),
  {
    ssr: false,
    loading: () => (
      <div className="h-full w-full flex items-center justify-center bg-slate-950 text-slate-400">
        <div className="space-y-3 text-center">
          <Skeleton className="h-8 w-48 mx-auto" />
          <p className="text-2xs text-content-subtle">Loading Orbiq Satellite Damage Studio...</p>
        </div>
      </div>
    ),
  },
);

type ViewId = "satellite" | "studio" | "map" | "verification" | "deliverables";

interface NavItem {
  id: ViewId;
  label: string;
  short: string;
  icon: typeof Waves;
  /** Rendered in the rail to explain what the view is for. */
  blurb: string;
}

const NAV: NavItem[] = [
  {
    id: "studio",
    label: "Breach Studio",
    short: "Studio",
    icon: Waves,
    blurb: "Configure a dam-break scenario and run the 2D solver",
  },
  {
    id: "map",
    label: "Inundation Map",
    short: "Map",
    icon: MapIcon,
    blurb: "Downstream flood extent, depth and land cover",
  },
  {
    id: "verification",
    label: "Verification",
    short: "Verify",
    icon: FlaskConical,
    blurb: "Solver results against closed-form and historical records",
  },
  {
    id: "deliverables",
    label: "Deliverables",
    short: "Deliverables",
    icon: ClipboardCheck,
    blurb: "Traceability against problem statement SIH26161",
  },
];

const BASEMAP_OPTIONS: SegmentedOption<BasemapId>[] = BASEMAP_IDS.map((id) => ({
  value: id,
  label: BASEMAPS[id].label,
}));

const VIEW_IDS: ViewId[] = ["satellite", ...NAV.map((n) => n.id)];

/**
 * Reads `?view=` off the address bar. Done through `window.location` rather
 * than `useSearchParams` because the latter opts the whole page out of static
 * prerendering unless it is wrapped in a Suspense boundary — which would cost
 * more than the parameter is worth. The page is already a client component, so
 * this runs only in the browser and never during the prerender pass.
 */
function viewFromLocation(): ViewId | null {
  if (typeof window === "undefined") return null;
  const requested = new URLSearchParams(window.location.search).get("view");
  return VIEW_IDS.includes(requested as ViewId) ? (requested as ViewId) : null;
}

/** Polls the backend so the shell can say plainly whether it is connected. */
function useBackendHealth() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;

    const ping = async () => {
      try {
        const res = await fetch("/api/health", { cache: "no-store" });
        if (!cancelled) setOnline(res.ok);
      } catch {
        if (!cancelled) setOnline(false);
      }
    };

    ping();
    const timer = setInterval(ping, 15000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  return online;
}

export default function Home() {
  const [view, setView] = useState<ViewId>("satellite");
  const [basemap, setBasemap] = useState<BasemapId>("satellite");
  const [railOpen, setRailOpen] = useState(false);
  const backendOnline = useBackendHealth();

  const active =
    view === "satellite"
      ? {
          id: "satellite" as ViewId,
          label: "Satellite Studio",
          short: "Satellite",
          icon: Satellite,
          blurb:
            "Post-event SAR and optical disaster extent, debris detection and road graph accessibility",
        }
      : NAV.find((n) => n.id === view) ?? NAV[0];

  // Adopt ?view= once, after mount, so a view can be linked to directly.
  useEffect(() => {
    const requested = viewFromLocation();
    if (requested) setView(requested);
  }, []);

  const selectView = useCallback((id: ViewId) => {
    setView(id);
    setRailOpen(false);

    // Keep the address bar in step, so the current view can be copied out of
    // it or reloaded. replaceState rather than pushState: switching tabs is not
    // navigation, and pushing an entry per tab would make the back button walk
    // backwards through views the user has already left.
    const url = new URL(window.location.href);
    url.searchParams.set("view", id);
    window.history.replaceState(null, "", url.toString());
  }, []);

  return (
    <div className="h-dvh w-full flex flex-col overflow-hidden bg-surface-base">
      <a
        href="#workspace"
        className="sr-only focus:not-sr-only focus:absolute focus:z-[100] focus:top-2 focus:left-2 focus:px-4 focus:py-2 focus:bg-brand focus:text-surface-base focus:rounded"
      >
        Skip to workspace
      </a>

      {/* ------------------------------------------------------------------ */}
      {/* Header                                                              */}
      {/* ------------------------------------------------------------------ */}
      <header className="shrink-0 h-14 px-4 sm:px-5 flex items-center justify-between gap-3 border-b border-edge bg-surface-sunken/90 backdrop-blur z-40">
        <div className="flex items-center gap-3 min-w-0">
          {view !== "satellite" && (
            <button
              type="button"
              onClick={() => setRailOpen((v) => !v)}
              aria-expanded={railOpen}
              aria-controls="primary-navigation"
              aria-label={railOpen ? "Close navigation" : "Open navigation"}
              className="lg:hidden h-10 w-10 -ml-1.5 flex items-center justify-center rounded text-content-muted hover:text-content hover:bg-white/5"
            >
              {railOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          )}

          <div className="flex items-center gap-2.5 min-w-0">
            <div className="h-8 w-8 shrink-0 rounded bg-sky-950/80 border border-sky-800/60 flex items-center justify-center text-sky-400 shadow-sm">
              <Satellite className="w-4 h-4" aria-hidden />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-bold text-content tracking-tight leading-none">
                  Orbiq
                </h1>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800/80">
                  {view === "satellite" ? "Satellite Studio" : "Dam Solver"}
                </span>
              </div>
              <p className="text-2xs text-content-subtle leading-none mt-1 truncate">
                {view === "satellite"
                  ? "Multimodal Earth Observation & Graph Access Intelligence"
                  : "Dam-Break Hydrodynamics · 2D Shallow-Water Solver"}
              </p>
            </div>
          </div>
        </div>

        {/* Center Mode Switcher */}
        <div className="flex items-center bg-surface-base/80 border border-edge rounded-lg p-0.5 shadow-sm">
          <button
            type="button"
            onClick={() => selectView("satellite")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all duration-fast",
              view === "satellite"
                ? "bg-sky-600 text-white shadow-sm"
                : "text-content-muted hover:text-content hover:bg-white/5"
            )}
          >
            <Satellite className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">🛰️ Satellite Damage Studio</span>
            <span className="sm:hidden">🛰️ Satellite</span>
          </button>
          <button
            type="button"
            onClick={() => selectView("studio")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all duration-fast",
              view !== "satellite"
                ? "bg-brand text-surface-base shadow-sm font-bold"
                : "text-content-muted hover:text-content hover:bg-white/5"
            )}
          >
            <Waves className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">🌊 2D Dam Solver</span>
            <span className="sm:hidden">🌊 Dam Solver</span>
          </button>
        </div>

        {/* Right Status & Controls */}
        <div className="flex items-center gap-3 shrink-0">
          {view !== "satellite" && (
            <div className="hidden sm:block">
              <Segmented
                label="Base map"
                options={BASEMAP_OPTIONS}
                value={basemap}
                onChange={setBasemap}
              />
            </div>
          )}

          <div
            className="flex items-center gap-1.5 pl-3 border-l border-edge"
            role="status"
            aria-live="polite"
          >
            <Circle
              className={cn(
                "w-2 h-2",
                backendOnline === null && "fill-content-faint text-content-faint",
                backendOnline === true && "fill-success text-success",
                backendOnline === false && "fill-danger text-danger",
              )}
              aria-hidden
            />
            <span className="text-2xs font-medium text-content-subtle whitespace-nowrap">
              {backendOnline === null
                ? "Checking…"
                : backendOnline
                  ? "Engine online"
                  : "Engine offline"}
            </span>
          </div>
        </div>
      </header>

      <div className="flex-1 flex min-h-0 relative">
        {/* ---------------------------------------------------------------- */}
        {/* Navigation rail (only shown when in Dam Solver modes)            */}
        {/* ---------------------------------------------------------------- */}
        {view !== "satellite" && (
          <nav
            id="primary-navigation"
            aria-label="Workspace"
            className={cn(
              "absolute inset-y-0 left-0 z-30 w-64 shrink-0 flex-col border-r border-edge",
              "bg-surface-sunken/95 backdrop-blur lg:static lg:flex lg:bg-surface-sunken/60",
              "transition-transform duration lg:transition-none",
              railOpen ? "flex translate-x-0" : "hidden -translate-x-full lg:flex lg:translate-x-0",
            )}
          >
            <div className="p-3 pb-1 border-b border-edge/60">
              <button
                type="button"
                onClick={() => selectView("satellite")}
                className="w-full flex items-center justify-center gap-2 rounded px-3 py-2 text-xs font-semibold text-sky-300 bg-sky-950/60 border border-sky-800/80 hover:bg-sky-900/50 transition-colors shadow-sm"
              >
                <Satellite className="w-3.5 h-3.5" />
                <span>← Back to Satellite Studio</span>
              </button>
            </div>

            <ul className="flex-1 overflow-y-auto fs-scroll p-3 space-y-1">
              {NAV.map((item) => {
                const Icon = item.icon;
                const isActive = item.id === view;
                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => selectView(item.id)}
                      aria-current={isActive ? "page" : undefined}
                      className={cn(
                        "w-full flex items-start gap-3 rounded px-3 py-3 text-left min-h-11",
                        "transition-colors duration-fast",
                        isActive
                          ? "bg-brand-wash text-brand border border-brand/25"
                          : "text-content-muted border border-transparent hover:bg-white/5 hover:text-content",
                      )}
                    >
                      <Icon className="w-4 h-4 mt-0.5 shrink-0" aria-hidden />
                      <span className="min-w-0">
                        <span className="block text-sm font-semibold leading-tight">
                          {item.label}
                        </span>
                        <span
                          className={cn(
                            "block text-2xs leading-snug mt-1",
                            isActive ? "text-brand/70" : "text-content-faint",
                          )}
                        >
                          {item.blurb}
                        </span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>

            <div className="shrink-0 p-3 border-t border-edge">
              <p className="text-2xs text-content-faint leading-relaxed">
                Bhuragaon reach, Brahmaputra
                <br />
                Raster extent 26.25–26.53° N, 92.00–92.55° E
              </p>
            </div>
          </nav>
        )}

        {railOpen && view !== "satellite" && (
          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setRailOpen(false)}
            className="absolute inset-0 z-20 bg-black/50 lg:hidden"
          />
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Workspace                                                         */}
        {/* ---------------------------------------------------------------- */}
        <main
          id="workspace"
          className="flex-1 min-w-0 min-h-0 flex flex-col overflow-hidden"
        >
          {/* Compact view switcher for narrow screens, where the rail is hidden. */}
          {view !== "satellite" && (
            <div className="lg:hidden shrink-0 border-b border-edge bg-surface-sunken/60 px-2 overflow-x-auto fs-scroll">
              <div className="flex items-center gap-1 min-w-max">
                {NAV.map((item) => {
                  const isActive = item.id === view;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => selectView(item.id)}
                      aria-current={isActive ? "page" : undefined}
                      className={cn(
                        "h-11 px-3 text-xs font-medium whitespace-nowrap border-b-2 transition-colors duration-fast",
                        isActive
                          ? "border-brand text-brand"
                          : "border-transparent text-content-subtle hover:text-content",
                      )}
                    >
                      {item.short}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <div className="flex-1 min-h-0 overflow-hidden" key={view}>
            {view === "satellite" && (
              <TrackBStudio
                embedded={true}
                onSwitchMode={(mode) => selectView(mode as ViewId)}
              />
            )}
            {view === "studio" && <DamBreakStudio />}
            {view === "map" && <InundationMapView basemap={basemap} />}
            {view === "verification" && <VerificationView />}
            {view === "deliverables" && <DeliverablesView />}
          </div>
        </main>
      </div>

      {/* Screen-reader summary of the current view, so route changes are announced. */}
      <p className="sr-only" aria-live="polite">
        {active.label} view. {active.blurb}
      </p>
    </div>
  );
}

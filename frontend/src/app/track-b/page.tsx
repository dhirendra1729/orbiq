import type { Metadata } from "next";
import TrackBStudio from "@/components/track-b/TrackBStudio";

export const metadata: Metadata = {
  title: "Orbiq Track B: Satellite Damage & Access Intelligence",
  description: "Educational post-event flood damage mapping from space, same-track SAR change detection, historical OpenStreetMap infrastructure exposure, and cut-off settlement routing."
};

export default function TrackBPage() {
  return <TrackBStudio />;
}

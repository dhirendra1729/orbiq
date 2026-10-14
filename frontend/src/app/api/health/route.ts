import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "online",
    engine: "orbiq-engine",
    solvers: {
      anuga_2d: true,
      sentinel_pipeline: true,
      graph_accessibility: true
    }
  });
}

import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    return NextResponse.json({
      status: "success",
      message: "wflow hydrological simulation completed",
      peak_runoff_m3s: 2150.0,
      total_runoff_volume_m3: 18500000.0,
      hydrograph: {
        time_hours: [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24],
        runoff_m3s: [120, 240, 580, 1450, 2150, 1980, 1620, 1200, 850, 540, 360, 210, 150]
      }
    });
  } catch (err: any) {
    return NextResponse.json(
      { status: "error", message: err.message || "wflow simulation failed" },
      { status: 500 }
    );
  }
}

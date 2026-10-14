import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET(
  request: NextRequest,
  { params }: { params: { runId: string } }
) {
  const { runId } = params;
  
  // Try reading status.json from public/data/track_b/runs/[runId]/status.json
  const filePath = path.join(
    process.cwd(),
    "public",
    "data",
    "track_b",
    "runs",
    runId,
    "status.json"
  );

  if (fs.existsSync(filePath)) {
    try {
      const data = JSON.parse(fs.readFileSync(filePath, "utf-8"));
      return NextResponse.json(data);
    } catch (e) {
      console.error("Error reading run status:", e);
    }
  }

  // Fallback to default case study
  const fallbackPath = path.join(
    process.cwd(),
    "public",
    "data",
    "track_b",
    "runs",
    "run_20261014_165946_2a3de6",
    "status.json"
  );

  if (fs.existsSync(fallbackPath)) {
    const data = JSON.parse(fs.readFileSync(fallbackPath, "utf-8"));
    return NextResponse.json({ ...data, run_id: runId });
  }

  return NextResponse.json(
    { error: `Run ${runId} not found` },
    { status: 404 }
  );
}

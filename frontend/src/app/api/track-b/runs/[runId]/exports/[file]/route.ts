import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET(
  request: NextRequest,
  { params }: { params: { runId: string; file: string } }
) {
  const { runId, file } = params;

  // Check derived directory first
  let targetPath = path.join(
    process.cwd(),
    "public",
    "data",
    "track_b",
    "runs",
    runId,
    "derived",
    file
  );

  // If not in derived, check root run directory
  if (!fs.existsSync(targetPath)) {
    targetPath = path.join(
      process.cwd(),
      "public",
      "data",
      "track_b",
      "runs",
      runId,
      file
    );
  }

  // Fallback to default case study run if runId differs
  if (!fs.existsSync(targetPath)) {
    targetPath = path.join(
      process.cwd(),
      "public",
      "data",
      "track_b",
      "runs",
      "run_20261014_165946_2a3de6",
      "derived",
      file
    );
  }

  if (fs.existsSync(targetPath)) {
    const content = fs.readFileSync(targetPath, "utf-8");
    const contentType = file.endsWith(".json") || file.endsWith(".geojson")
      ? "application/json"
      : file.endsWith(".csv")
      ? "text/csv"
      : file.endsWith(".md")
      ? "text/markdown"
      : "application/octet-stream";

    return new NextResponse(content, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "public, max-age=3600"
      }
    });
  }

  return NextResponse.json(
    { error: `File ${file} not found for run ${runId}` },
    { status: 404 }
  );
}

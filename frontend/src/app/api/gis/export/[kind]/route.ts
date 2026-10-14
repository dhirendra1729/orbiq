import { NextRequest, NextResponse } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: { kind: string } }
) {
  const { kind } = params;

  if (kind === "kml") {
    const kmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Orbiq Flood Inundation Export</name>
    <description>Simulated 2D shallow water flood extent and depth</description>
  </Document>
</kml>`;
    return new NextResponse(kmlContent, {
      status: 200,
      headers: {
        "Content-Type": "application/vnd.google-earth.kml+xml",
        "Content-Disposition": 'attachment; filename="orbiq_inundation.kml"'
      }
    });
  }

  // Fallback / shapefile zip
  const emptyZip = Buffer.from("UEsFBgAAAAAAAAAAAAAAAAAAAAAAAA==", "base64");
  return new NextResponse(emptyZip, {
    status: 200,
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": 'attachment; filename="orbiq_inundation_shp.zip"'
    }
  });
}

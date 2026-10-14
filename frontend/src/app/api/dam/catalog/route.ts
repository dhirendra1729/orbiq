import { NextResponse } from "next/server";

export async function GET() {
  const presets = [
    {
      id: "machchhu-ii",
      name: "Machchhu-II Dam (Morbi Failure 1979)",
      state: "Gujarat",
      river: "Machhu",
      basin: "Rivers draining into Gulf of Kachchh",
      latitude: 22.7667,
      longitude: 70.8667,
      dam_height_m: 25.0,
      crest_length_m: 5125.0,
      reservoir_volume_mcm: 100.55,
      normal_pool_level_m: 22.0,
      historical_event: "Catastrophic overtopping failure on 11 Aug 1979 after extreme monsoon rainfall (over 20 inches in 24h). Inundated Morbi town downstream.",
      failure_mode: "overtopping",
      default_model: "froehlich",
      downstream_villages: ["Morbi City", "Lilapar", "Mahendranagar", "Jambu"]
    },
    {
      id: "teesta-iii",
      name: "Teesta-III Dam (Chungthang GLOF 2023)",
      state: "Sikkim",
      river: "Teesta",
      basin: "Brahmaputra",
      latitude: 27.5975,
      longitude: 88.6503,
      dam_height_m: 60.0,
      crest_length_m: 200.0,
      reservoir_volume_mcm: 18.4,
      normal_pool_level_m: 55.0,
      historical_event: "South Lhonak Glacial Lake Outburst Flood (GLOF) on 3-4 Oct 2023 released >50 MCM water + sediment, breaching dam within 10 minutes.",
      failure_mode: "overtopping",
      default_model: "froehlich",
      downstream_villages: ["Chungthang", "Mangan", "Singtam", "Rangpo"]
    },
    {
      id: "rishi-ganga",
      name: "Rishi Ganga Hydro Project (Chamoli Rock-Ice Avalanche 2021)",
      state: "Uttarakhand",
      river: "Rishiganga",
      basin: "Ganga",
      latitude: 30.5528,
      longitude: 79.7214,
      dam_height_m: 20.0,
      crest_length_m: 65.0,
      reservoir_volume_mcm: 1.2,
      normal_pool_level_m: 18.0,
      historical_event: "Ronti peak rock-ice avalanche on 7 Feb 2021 generated hyperconcentrated debris flow completely destroying the 13.2 MW barrage.",
      failure_mode: "sudden",
      default_model: "ritter",
      downstream_villages: ["Raini", "Tapovan", "Joshimath"]
    }
  ];

  return NextResponse.json(presets);
}

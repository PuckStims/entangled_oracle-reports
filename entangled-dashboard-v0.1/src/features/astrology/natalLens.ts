import placeholder from "../../data/astrology/profile.placeholder.json";
import { fetchCurrentField, fetchNatalChart, natalChartToLens, type AstrologyProfile } from "./astrologyApi";
import type { NatalLensResult } from "./astroTypes";
import type { ReadingPacket } from "../synthesis/readingPacket";

export function getScaffoldNatalLens(note?: string): NatalLensResult {
  return {
    status: "not_wired",
    adapterName: "natalLens.placeholder",
    note:
      note ??
      (typeof placeholder.note === "string"
        ? placeholder.note
        : "Wire this adapter to a private .local.json profile or existing natal engine."),
    routes: []
  };
}

export function getNatalLensForPacket(_packet?: ReadingPacket): NatalLensResult {
  return getScaffoldNatalLens();
}

export async function fetchNatalLensForPacket(
  profile?: AstrologyProfile,
  _packet?: ReadingPacket
): Promise<NatalLensResult> {
  if (!profile) {
    return getScaffoldNatalLens("Add a local astrology profile in Settings to call the existing natal engine.");
  }

  try {
    const [chart, field] = await Promise.all([fetchNatalChart(profile), fetchCurrentField(profile)]);
    return natalChartToLens(chart, field, profile.displayName);
  } catch (error) {
    return {
      status: "error",
      adapterName: "entangled-astrology-api.natal-chart",
      note: error instanceof Error ? error.message : "The astrology API did not return a natal lens.",
      routes: []
    };
  }
}

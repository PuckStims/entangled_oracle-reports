import placeholder from "../../data/astrology/live-astro.placeholder.json";
import { currentFieldToLiveAstroContext, fetchCurrentField, type AstrologyProfile } from "./astrologyApi";
import type { LiveAstroContext } from "./astroTypes";

export function getScaffoldLiveAstroContext(note?: string): LiveAstroContext {
  return {
    status: "not_wired",
    generatedAt: new Date().toISOString(),
    adapterName: "liveAstroEngine.placeholder",
    note:
      note ??
      (typeof placeholder.note === "string"
        ? placeholder.note
        : "Wire this function to your existing astrology engine.")
  };
}

export function getLiveAstroContext(): LiveAstroContext {
  return getScaffoldLiveAstroContext();
}

export async function fetchLiveAstroContext(profile?: AstrologyProfile): Promise<LiveAstroContext> {
  if (!profile) {
    return getScaffoldLiveAstroContext("Add a local astrology profile in Settings to call the existing engine.");
  }

  try {
    return currentFieldToLiveAstroContext(await fetchCurrentField(profile));
  } catch (error) {
    return {
      status: "error",
      generatedAt: new Date().toISOString(),
      adapterName: "entangled-astrology-api.current-field",
      note: error instanceof Error ? error.message : "The astrology API did not return current-field context."
    };
  }
}

export function getAstrologyReadiness(context = getLiveAstroContext()): {
  label: string;
  ready: boolean;
  detail: string;
} {
  if (context.status === "available") {
    return {
      label: "Live sky online",
      ready: true,
      detail: "The astrology adapter is returning structured context."
    };
  }

  return {
    label: "Live sky scaffolded",
    ready: false,
    detail: context.note ?? "The adapter exists, but no live astrology source is connected."
  };
}

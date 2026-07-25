import type { LiveAstroContext, NatalLensResult } from "./astroTypes";

export type BirthTimeConfidence = "EXACT_RECORD" | "EXACT_RECALLED" | "APPROXIMATE" | "UNKNOWN";

export type AstrologyProfile = {
  id: string;
  displayName: string;
  localDate: string;
  localTime?: string | null;
  timeZoneId: string;
  locationName: string;
  birthTimeConfidence: BirthTimeConfidence;
};

export type CalculatedEvent = {
  id: string;
  technique: string;
  movingBody?: string | null;
  natalTarget: string;
  aspect?: string | null;
  orbDegrees?: number | null;
  phase: string;
  title?: string | null;
  lifeAreas?: string[];
};

export type CurrentField = {
  calculatedAt: string;
  events: CalculatedEvent[];
  patterns: Array<{ id: string; title: string; summary: string; role: string; stage: string; eventIds: string[] }>;
  provenance?: { warnings?: string[]; calculationModules?: string[] };
};

export type NatalChart = {
  calculatedAt: string;
  placements: Array<{ body: string; sign: string; degree: number; house?: number | null; retrograde?: boolean }>;
  aspects: Array<{ pointA: string; aspect: string; pointB: string; orbDegrees: number }>;
  provenance?: { warnings?: string[]; calculationModules?: string[] };
};

export const ASTROLOGY_PROFILE_STORAGE_KEY = "entangled-dashboard.astrologyProfile.v1";

export const DEFAULT_ASTROLOGY_PROFILE: AstrologyProfile = {
  id: "personal-dashboard-default",
  displayName: "Personal Dashboard",
  localDate: "1992-03-21",
  localTime: "08:11",
  timeZoneId: "America/Chicago",
  locationName: "Peoria, IL",
  birthTimeConfidence: "EXACT_RECALLED"
};

export function getAstrologyApiBaseUrl(): string {
  return (import.meta.env.VITE_ASTROLOGY_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
}

export function loadSavedAstrologyProfile(): AstrologyProfile | undefined {
  try {
    const raw = localStorage.getItem(ASTROLOGY_PROFILE_STORAGE_KEY);
    if (!raw) return undefined;
    const profile = JSON.parse(raw) as AstrologyProfile;
    return profile.displayName && profile.localDate && profile.locationName ? profile : undefined;
  } catch {
    return undefined;
  }
}

export function loadAstrologyProfile(): AstrologyProfile {
  return loadSavedAstrologyProfile() ?? DEFAULT_ASTROLOGY_PROFILE;
}

export function saveAstrologyProfile(profile: AstrologyProfile) {
  localStorage.setItem(ASTROLOGY_PROFILE_STORAGE_KEY, JSON.stringify(profile));
  window.dispatchEvent(new Event("entangled-dashboard:astrology-profile"));
}

export function clearAstrologyProfile() {
  localStorage.removeItem(ASTROLOGY_PROFILE_STORAGE_KEY);
  window.dispatchEvent(new Event("entangled-dashboard:astrology-profile"));
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${getAstrologyApiBaseUrl()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }

  return (await response.json()) as T;
}

export async function fetchEngineHealth(): Promise<{ status: string; checkedAt: string; message?: string | null }> {
  const response = await fetch(`${getAstrologyApiBaseUrl()}/v1/health`);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return (await response.json()) as { status: string; checkedAt: string; message?: string | null };
}

export async function fetchCurrentField(profile: AstrologyProfile): Promise<CurrentField> {
  return postJson<CurrentField>("/v1/fields/current", {
    profile,
    moment: new Date().toISOString(),
    window: "today"
  });
}

export async function fetchNatalChart(profile: AstrologyProfile): Promise<NatalChart> {
  return postJson<NatalChart>("/v1/charts/natal", { profile });
}

function aspectFromEvent(event: CalculatedEvent) {
  return {
    planetA: event.movingBody || event.technique,
    aspect: event.aspect || event.phase,
    planetB: event.natalTarget,
    orb: event.orbDegrees ?? undefined
  };
}

export function currentFieldToLiveAstroContext(field: CurrentField): LiveAstroContext {
  const events = field.events ?? [];
  const retrogrades = events
    .filter((event) => event.title?.toLowerCase().includes("retrograde"))
    .map((event) => event.movingBody || event.title || event.id);

  return {
    status: "available",
    generatedAt: field.calculatedAt,
    adapterName: "entangled-astrology-api.current-field",
    note: field.patterns[0]?.summary ?? "Current field loaded from the Entangled Oracle astrology API.",
    majorAspects: events.slice(0, 8).map(aspectFromEvent),
    retrogrades,
    dominantModality: field.patterns[0]?.stage,
    dominantElement: field.patterns[0]?.role
  };
}

export function natalChartToLens(chart: NatalChart, field?: CurrentField, displayName?: string): NatalLensResult {
  const placementRoutes = chart.placements.slice(0, 8).map((placement) => ({
    id: `placement-${placement.body.toLowerCase().replace(/\s+/g, "-")}`,
    label: `${placement.body} in ${placement.sign}${placement.house ? `, house ${placement.house}` : ""}`,
    keywords: [placement.body, placement.sign, placement.house ? `house_${placement.house}` : ""].filter(Boolean),
    routing: "Natal placement supplied by the Entangled Oracle astrology API.",
    activatedBy: [placement.body]
  }));

  const eventRoutes =
    field?.patterns.slice(0, 3).map((pattern) => ({
      id: `field-${pattern.id}`,
      label: pattern.title,
      keywords: [pattern.role, pattern.stage],
      routing: pattern.summary,
      activatedBy: pattern.eventIds
    })) ?? [];

  return {
    status: "available",
    adapterName: "entangled-astrology-api.natal-chart",
    displayName,
    note: "Natal lens loaded from calculated placements and current-field patterns.",
    routes: [...eventRoutes, ...placementRoutes]
  };
}

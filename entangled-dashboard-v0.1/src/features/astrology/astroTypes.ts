export type AdapterStatus = "available" | "not_wired" | "error";

export type PlanetPosition = {
  planet: string;
  sign: string;
  degree?: number;
  retrograde?: boolean;
};

export type CurrentAspect = {
  planetA: string;
  aspect: string;
  planetB: string;
  orb?: number;
};

export type LiveAstroContext = {
  status: AdapterStatus;
  generatedAt: string;
  adapterName: string;
  note?: string;
  sunSign?: string;
  moonSign?: string;
  moonPhase?: string;
  planetPositions?: PlanetPosition[];
  retrogrades?: string[];
  majorAspects?: CurrentAspect[];
  dominantElement?: string;
  dominantModality?: string;
};

export type NatalLensRoute = {
  id: string;
  label: string;
  keywords: string[];
  routing: string;
  activatedBy: string[];
};

export type NatalLensResult = {
  status: AdapterStatus;
  adapterName: string;
  note?: string;
  displayName?: string;
  routes: NatalLensRoute[];
};

import type { LiveAstroContext, NatalLensResult } from "../astrology/astroTypes";
import type { LlmSynthesis } from "../llm/llmTypes";

export type Modality = "tarot" | "runes";

export type ReadingMode =
  | "standard"
  | "moon"
  | "retrograde"
  | "relationship"
  | "shadow"
  | "creative"
  | "custom";

export type SourceName =
  | "tarot-json"
  | "rune-json"
  | "live-astrology"
  | "natal-lens"
  | "openrouter";

export type SymbolEntry = {
  id: string;
  name: string;
  glyph?: string;
  modality: Modality;
  keywords: string[];
  meaning?: string;
  caution?: string;
  prompts?: string[];
  position?: string;
  reversed?: boolean;
  source: SourceName;
};

export type ReadingPosition = {
  id: string;
  label: string;
  meaning: string;
};

export type RuneCastGeometry = {
  matName: string;
  points: Array<{
    runeId: string;
    x: number;
    y: number;
    region: string;
    nearestRuneId?: string;
  }>;
  notes: string[];
};

export type ReadingLayout = {
  spreadName?: string;
  positions?: ReadingPosition[];
  runeCastGeometry?: RuneCastGeometry;
};

export type StaticInterpretation = {
  keywords: string[];
  meanings: string[];
  cautions: string[];
  prompts: string[];
};

export type LocalSynthesis = {
  title: string;
  summary: string;
  strands: string[];
  practicalVersion: string;
  mythicVersion: string;
  sourceNotes: string[];
};

export type SourceTrace = {
  usedTarotJson: boolean;
  usedRuneJson: boolean;
  usedLiveAstrology: boolean;
  usedNatalLens: boolean;
  usedOpenRouter: boolean;
  missing: SourceName[];
};

export type ReadingPacket = {
  id: string;
  createdAt: string;
  modality: Modality;
  readingMode: ReadingMode;
  userQuestion?: string;
  symbols: SymbolEntry[];
  layout?: ReadingLayout;
  staticInterpretation: StaticInterpretation;
  liveAstrology?: LiveAstroContext;
  natalLens?: NatalLensResult;
  localSynthesis?: LocalSynthesis;
  llmSynthesis?: LlmSynthesis;
  sourceTrace: SourceTrace;
};

export function createEmptyStaticInterpretation(): StaticInterpretation {
  return {
    keywords: [],
    meanings: [],
    cautions: [],
    prompts: []
  };
}

export function makePacketId(prefix: Modality): string {
  const random = Math.random().toString(36).slice(2, 9);
  return `${prefix}-${Date.now().toString(36)}-${random}`;
}

export function collectStaticInterpretation(symbols: SymbolEntry[]): StaticInterpretation {
  return {
    keywords: [...new Set(symbols.flatMap((symbol) => symbol.keywords))],
    meanings: symbols.map((symbol) => symbol.meaning).filter(Boolean) as string[],
    cautions: symbols.map((symbol) => symbol.caution).filter(Boolean) as string[],
    prompts: [...new Set(symbols.flatMap((symbol) => symbol.prompts ?? []))]
  };
}

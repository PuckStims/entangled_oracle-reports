export type RuneDatum = {
  id: string;
  index?: number;
  name: string;
  glyph?: string;
  aett?: string;
  domain?: string;
  processStage?: string;
  coreAction?: string;
  keywords?: string[];
  meanings?: string[];
  cautions?: string[];
  prompts?: string[];
  essence?: string;
  gloss?: string;
  upright?: string;
  reversed?: string | null;
  hasReverse?: boolean;
  isModernAddition?: boolean;
};

export type RuneReadingMode = "single" | "three-rune" | "freehand-cast";

export type RuneReadingOptions = {
  mode: RuneReadingMode;
  userQuestion?: string;
  entropyHash?: string;
  includeWyrd?: boolean;
  liveAstrology?: import("../astrology/astroTypes").LiveAstroContext;
  natalLens?: import("../astrology/astroTypes").NatalLensResult;
};

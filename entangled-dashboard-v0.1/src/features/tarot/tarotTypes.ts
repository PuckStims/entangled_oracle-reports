export type TarotCardDatum = {
  id: string;
  index?: number;
  name: string;
  shortName?: string;
  arcana?: string;
  kind?: string;
  suit?: string;
  number?: string | number;
  rank?: string;
  keywords?: string[];
  meanings?: string[];
  reversedMeanings?: string[];
  cautions?: string[];
  prompts?: string[];
  essence?: string;
  compositionNote?: string;
};

export type TarotSpreadId = string;

export type TarotSpread = {
  id: TarotSpreadId;
  label: string;
  subtitle?: string;
  cardCount: number;
  positionLabels: string[];
  positionPrompts?: string[];
};

export type TarotReadingOptions = {
  spreadId: TarotSpreadId;
  userQuestion?: string;
  allowReversals: boolean;
  entropyHash?: string;
  liveAstrology?: import("../astrology/astroTypes").LiveAstroContext;
  natalLens?: import("../astrology/astroTypes").NatalLensResult;
};

import type { ReadingPacket } from "../synthesis/readingPacket";

export type AbstractVisualModel = {
  rings: number;
  spokes: number;
  intensity: number;
  hue: number;
};

export function buildAbstractVisualModel(packet?: ReadingPacket): AbstractVisualModel {
  const symbolCount = packet?.symbols.length ?? 0;
  const missingCount = packet?.sourceTrace.missing.length ?? 5;
  const idSeed = packet?.id.split("").reduce((sum, char) => sum + char.charCodeAt(0), 0) ?? 180;

  return {
    rings: Math.max(3, Math.min(9, symbolCount + 3)),
    spokes: Math.max(6, Math.min(24, symbolCount * 3 || 9)),
    intensity: Math.max(0.25, 1 - missingCount * 0.12),
    hue: idSeed % 360
  };
}

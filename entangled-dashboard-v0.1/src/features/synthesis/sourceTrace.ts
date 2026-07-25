import type { ReadingPacket, SourceTrace } from "./readingPacket";

export function getMissingSourceLabel(source: SourceTrace["missing"][number]): string {
  const labels: Record<SourceTrace["missing"][number], string> = {
    "tarot-json": "Tarot JSON",
    "rune-json": "Rune JSON",
    "live-astrology": "Live astrology engine",
    "natal-lens": "Natal/profile lens",
    openrouter: "OpenRouter"
  };
  return labels[source];
}

export function summarizeSourceTrace(packet?: ReadingPacket): string[] {
  if (!packet) {
    return ["No reading packet is active."];
  }

  const present = [
    packet.sourceTrace.usedTarotJson && "Tarot JSON",
    packet.sourceTrace.usedRuneJson && "Rune JSON",
    packet.sourceTrace.usedLiveAstrology && "Live astrology",
    packet.sourceTrace.usedNatalLens && "Natal/profile lens",
    packet.sourceTrace.usedOpenRouter && "OpenRouter"
  ].filter(Boolean) as string[];

  const missing = packet.sourceTrace.missing.map(getMissingSourceLabel);

  return [
    present.length ? `Active sources: ${present.join(", ")}.` : "No source datasets are wired yet.",
    missing.length ? `Waiting on: ${missing.join(", ")}.` : "All declared sources are present."
  ];
}

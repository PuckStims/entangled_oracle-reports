import type { ReadingPacket } from "../synthesis/readingPacket";
import { getMissingSourceLabel } from "../synthesis/sourceTrace";

export type SpeculationRuleResult = {
  ifLine: string;
  thenLine: string;
  source: string;
};

export function buildSpeculationMatrix(packet?: ReadingPacket): SpeculationRuleResult[] {
  if (!packet) {
    return [
      {
        ifLine: "IF no reading packet is active",
        thenLine: "THEN create a tarot or rune packet before remixing it",
        source: "UI state"
      }
    ];
  }

  const results: SpeculationRuleResult[] = [];

  if (packet.symbols.length) {
    packet.symbols.slice(0, 6).forEach((symbol) => {
      results.push({
        ifLine: `IF ${symbol.name} appears${symbol.position ? ` in ${symbol.position}` : ""}`,
        thenLine: "THEN consult its static JSON meaning before any synthesis layer",
        source: symbol.source
      });
    });
  } else {
    results.push({
      ifLine: "IF the packet contains no symbols",
      thenLine: "THEN the tarot/rune dataset adapter is still waiting for your existing files",
      source: "ReadingPacket"
    });
  }

  packet.sourceTrace.missing.forEach((source) => {
    results.push({
      ifLine: `IF ${getMissingSourceLabel(source)} is missing`,
      thenLine: "THEN keep that layer out of interpretation and show the local scaffold honestly",
      source: "SourceTrace"
    });
  });

  return results;
}

import type { ReadingPacket } from "../synthesis/readingPacket";

export function getWordfallTerms(packet?: ReadingPacket): string[] {
  if (!packet) return [];

  const symbolTerms = packet.symbols.flatMap((symbol) => [
    symbol.name,
    ...(symbol.keywords ?? []),
    symbol.position ?? ""
  ]);

  const astroTerms =
    packet.liveAstrology?.status === "available"
      ? [
          packet.liveAstrology.sunSign,
          packet.liveAstrology.moonSign,
          packet.liveAstrology.moonPhase,
          ...(packet.liveAstrology.retrogrades ?? []),
          packet.liveAstrology.dominantElement,
          packet.liveAstrology.dominantModality
        ]
      : [];

  const natalTerms =
    packet.natalLens?.status === "available"
      ? packet.natalLens.routes.flatMap((route) => [route.label, ...route.keywords])
      : [];

  return [...new Set([...symbolTerms, ...astroTerms, ...natalTerms].filter(Boolean) as string[])];
}

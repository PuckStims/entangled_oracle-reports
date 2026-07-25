import { getLiveAstroContext } from "../astrology/liveAstroEngine";
import { deriveModalityHash, generateEntropyHash, HashCursor, validateAndNormalizeHash } from "../entropy/entropySource";
import { getNatalLensForPacket } from "../astrology/natalLens";
import { buildLocalSynthesis } from "../synthesis/localSynthesis";
import {
  collectStaticInterpretation,
  createEmptyStaticInterpretation,
  makePacketId,
  type ReadingPacket,
  type ReadingPosition,
  type SymbolEntry
} from "../synthesis/readingPacket";
import { loadTarotCatalog } from "./tarotCatalog";
import type { TarotCardDatum, TarotReadingOptions, TarotSpread, TarotSpreadId } from "./tarotTypes";

const tarotCatalogSource = loadTarotCatalog();
const tarotCatalog = tarotCatalogSource.cards;

export const tarotSpreads: TarotSpread[] = [
  {
    id: "single",
    label: "Single Card",
    cardCount: 1,
    positionLabels: ["Card 1"]
  },
  {
    id: "three-card",
    label: "Three Card",
    cardCount: 3,
    positionLabels: ["Card 1", "Card 2", "Card 3"]
  },
  {
    id: "celtic-cross",
    label: "Celtic Cross",
    cardCount: 10,
    positionLabels: Array.from({ length: 10 }, (_, index) => `Celtic Cross ${index + 1}`)
  }
];

const availableTarotSpreads = tarotCatalogSource.spreads.length ? tarotCatalogSource.spreads : tarotSpreads;

export function getTarotCatalogStatus() {
  return {
    count: tarotCatalog.length,
    ready: tarotCatalog.length >= 78 && !tarotCatalogSource.placeholder,
    source: tarotCatalogSource.source,
    note:
      tarotCatalog.length === 0
        ? "Tarot adapter is scaffolded. Wire your existing 78-card JSON in tarotEngine.ts."
        : `Tarot adapter loaded ${tarotCatalog.length} cards from ${tarotCatalogSource.source}.`
  };
}

export function getTarotSpread(spreadId: TarotSpreadId): TarotSpread {
  return availableTarotSpreads.find((spread) => spread.id === spreadId) ?? availableTarotSpreads[0];
}

export function getTarotSpreads(): TarotSpread[] {
  return availableTarotSpreads;
}

function selectIndexWithoutCollision(startIndex: number, alreadyDrawn: Set<number>, tableSize: number): number {
  if (!alreadyDrawn.has(startIndex)) return startIndex;
  for (let offset = 1; offset <= tableSize; offset += 1) {
    const candidate = (startIndex + offset) % tableSize;
    if (!alreadyDrawn.has(candidate)) return candidate;
  }
  throw new Error("Tarot deck exhausted.");
}

function toSymbolEntry(card: TarotCardDatum, position: ReadingPosition, reversed: boolean): SymbolEntry {
  const meaning = reversed ? card.reversedMeanings?.join(" ") || card.cautions?.join(" ") : card.meanings?.join(" ");
  const prompts = card.prompts ?? (card.compositionNote ? [card.compositionNote] : []);
  return {
    id: card.id,
    name: card.name,
    modality: "tarot",
    keywords: card.keywords ?? [],
    meaning: meaning || card.essence,
    caution: reversed ? undefined : card.cautions?.join(" "),
    prompts,
    position: position.label,
    reversed,
    source: "tarot-json"
  };
}

export async function createTarotReading(options: TarotReadingOptions): Promise<ReadingPacket> {
  const spread = getTarotSpread(options.spreadId);
  const liveAstrology = options.liveAstrology ?? getLiveAstroContext();
  const seedHash = validateAndNormalizeHash(options.entropyHash ?? (await generateEntropyHash(`tarot:${spread.id}`)));
  const derivedHash = await deriveModalityHash(seedHash, `tarot:${spread.id}`);
  const cursor = new HashCursor(derivedHash);
  const deckByIndex = new Map(tarotCatalog.map((card, fallbackIndex) => [card.index ?? fallbackIndex, card]));
  const drawnIndices = new Set<number>();
  const positions: ReadingPosition[] = spread.positionLabels.map((label, index) => ({
    id: `${spread.id}-${index + 1}`,
    label,
    meaning: spread.positionPrompts?.[index] ?? "Position prompt supplied by the spread adapter."
  }));

  const symbols = positions.flatMap((position) => {
    if (!tarotCatalog.length) return [];
    const rawCardValue = cursor.read(4);
    const selectedIndex = selectIndexWithoutCollision(rawCardValue % 78, drawnIndices, 78);
    drawnIndices.add(selectedIndex);
    const orientationRawValue = cursor.read(1);
    const reversed = options.allowReversals && orientationRawValue % 2 !== 0;
    const card = deckByIndex.get(selectedIndex);
    return card ? [toSymbolEntry(card, position, reversed)] : [];
  });

  const packet: ReadingPacket = {
    id: makePacketId("tarot"),
    createdAt: new Date().toISOString(),
    modality: "tarot",
    readingMode: "standard",
    userQuestion: options.userQuestion?.trim() || undefined,
    symbols,
    layout: {
      spreadName: `${spread.label} / ${derivedHash.slice(0, 8)}`,
      positions
    },
    staticInterpretation: symbols.length ? collectStaticInterpretation(symbols) : createEmptyStaticInterpretation(),
    liveAstrology,
    natalLens: options.natalLens,
    sourceTrace: {
      usedTarotJson: symbols.length > 0,
      usedRuneJson: false,
      usedLiveAstrology: liveAstrology.status === "available",
      usedNatalLens: options.natalLens?.status === "available",
      usedOpenRouter: false,
      missing: [
        ...(symbols.length ? [] : (["tarot-json"] as const)),
        ...(liveAstrology.status === "available" ? [] : (["live-astrology"] as const)),
        ...(options.natalLens?.status === "available" ? [] : (["natal-lens"] as const)),
        "openrouter"
      ]
    }
  };

  packet.natalLens = options.natalLens ?? getNatalLensForPacket(packet);
  packet.localSynthesis = buildLocalSynthesis(packet);
  return packet;
}

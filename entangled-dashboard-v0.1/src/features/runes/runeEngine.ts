import { getLiveAstroContext } from "../astrology/liveAstroEngine";
import { deriveModalityHash, generateEntropyHash, HashCursor, validateAndNormalizeHash } from "../entropy/entropySource";
import { getNatalLensForPacket } from "../astrology/natalLens";
import { buildLocalSynthesis } from "../synthesis/localSynthesis";
import {
  collectStaticInterpretation,
  createEmptyStaticInterpretation,
  makePacketId,
  type ReadingPacket,
  type RuneCastGeometry,
  type SymbolEntry
} from "../synthesis/readingPacket";
import { loadRuneCatalog } from "./runeCatalog";
import type { RuneDatum, RuneReadingMode, RuneReadingOptions } from "./runeTypes";

const runeCatalogSource = loadRuneCatalog();
const runeCatalog = runeCatalogSource.runes;

export function getRuneCatalogStatus() {
  return {
    count: runeCatalog.length,
    ready: runeCatalog.length >= 24 && !runeCatalogSource.placeholder,
    source: runeCatalogSource.source,
    note:
      runeCatalog.length === 0
        ? "Rune adapter is scaffolded. Wire your existing Elder Futhark JSON in runeEngine.ts."
        : `Rune adapter loaded ${runeCatalog.length} runes from ${runeCatalogSource.source}.`
  };
}

function runeCountForMode(mode: RuneReadingMode): number {
  if (mode === "single") return 1;
  if (mode === "three-rune") return 3;
  return Math.min(9, runeCatalog.length);
}

function activeRuneTable(includeWyrd = false): RuneDatum[] {
  return includeWyrd ? runeCatalog : runeCatalog.filter((rune) => !rune.isModernAddition && rune.id !== "rune_wyrd");
}

function selectRunes(cursor: HashCursor, count: number, includeWyrd = false): RuneDatum[] {
  const table = activeRuneTable(includeWyrd);
  const drawn = new Set<number>();
  return Array.from({ length: Math.min(count, table.length) }).flatMap(() => {
    if (!table.length) return [];
    let tableIndex = cursor.read(2) % table.length;
    while (drawn.has(tableIndex)) tableIndex = (tableIndex + 1) % table.length;
    drawn.add(tableIndex);
    return [table[tableIndex]];
  });
}

function toSymbolEntry(rune: RuneDatum, index: number, isReversed: boolean): SymbolEntry {
  const effectiveReversed = Boolean(isReversed && rune.hasReverse);
  const meaning = effectiveReversed ? rune.reversed ?? rune.upright : rune.upright;
  const prompts = rune.prompts ?? [rune.essence, rune.coreAction].filter((item): item is string => Boolean(item));
  return {
    id: rune.id,
    name: rune.name,
    glyph: rune.glyph,
    modality: "runes",
    keywords: rune.keywords ?? [],
    meaning: meaning ?? rune.meanings?.join(" ") ?? rune.gloss,
    caution: effectiveReversed ? undefined : rune.cautions?.join(" "),
    prompts,
    position: `Rune ${index + 1}`,
    reversed: effectiveReversed,
    source: "rune-json"
  };
}

type GeneratedPoint = {
  stoneIndex: number;
  x: number;
  y: number;
  isUpright: boolean;
  zone: string;
};

function assignZone(x: number, y: number): string {
  const dx = x - 50;
  const dy = y - 50;
  const distance = Math.sqrt(dx * dx + dy * dy);
  if (distance <= 18.8) return "MIDGARD";
  if (distance <= 42.05) {
    if (dx >= 0 && dy <= 0) return "ASGARD";
    if (dx >= 0 && dy > 0) return "SWARTALFHEIM";
    if (dx < 0 && dy > 0) return "HELHEIM";
    return "LIGHTALFHEIM";
  }
  const absDx = Math.abs(dx);
  const absDy = Math.abs(dy);
  if (absDy >= absDx && dy < 0) return "MUSPELHEIM";
  if (absDy >= absDx && dy > 0) return "NIFELHEIM";
  if (absDx > absDy && dx > 0) return "VANAHEIM";
  return "JOTUNHEIM";
}

function generatePoints(cursor: HashCursor): GeneratedPoint[] {
  const stoneCount = 3 + (cursor.read(2) % 6);
  const points: GeneratedPoint[] = [];

  for (let index = 0; index < stoneCount; index += 1) {
    let x = (cursor.read(2) / 255) * 100;
    let y = (cursor.read(2) / 255) * 100;
    const isUpright = cursor.read(1) % 2 === 0;
    let collisionDetected = true;
    let escapeCounter = 0;

    while (collisionDetected && escapeCounter < 20) {
      collisionDetected = false;
      for (const existing of points) {
        if (Math.sqrt((x - existing.x) ** 2 + (y - existing.y) ** 2) < 5) {
          x = (x + 5) % 100;
          collisionDetected = true;
          escapeCounter += 1;
          break;
        }
      }
    }

    points.push({ stoneIndex: index, x, y, isUpright, zone: assignZone(x, y) });
  }

  return points;
}

function resolvePointRunes(cursor: HashCursor, points: GeneratedPoint[], includeWyrd = false): SymbolEntry[] {
  const table = activeRuneTable(includeWyrd);
  const drawn = new Set<number>();
  return points.flatMap((point) => {
    if (!table.length) return [];
    let tableIndex = cursor.read(2) % table.length;
    while (drawn.has(tableIndex)) tableIndex = (tableIndex + 1) % table.length;
    drawn.add(tableIndex);
    const rune = table[tableIndex];
    const symbol = toSymbolEntry(rune, point.stoneIndex, !point.isUpright);
    return [{ ...symbol, position: `${point.zone} / Stone ${point.stoneIndex + 1}` }];
  });
}

function buildGeometry(symbols: SymbolEntry[], points: GeneratedPoint[] | undefined, mode: RuneReadingMode): RuneCastGeometry | undefined {
  if (mode !== "freehand-cast") return undefined;

  return {
    matName: "Nine Worlds freehand field",
    points: symbols.map((symbol, index) => ({
      runeId: symbol.id,
      x: points?.[index] ? points[index].x / 100 : 0.5,
      y: points?.[index] ? points[index].y / 100 : 0.5,
      region: points?.[index]?.zone ?? `Region ${index + 1}`
    })),
    notes: ["Geometry generated with the dashboard TypeScript port of the EntangledOracle PareidoliaProtocol point field."]
  };
}

export async function createRuneReading(options: RuneReadingOptions): Promise<ReadingPacket> {
  const liveAstrology = options.liveAstrology ?? getLiveAstroContext();
  const seedHash = validateAndNormalizeHash(options.entropyHash ?? (await generateEntropyHash(`runes:${options.mode}`)));
  const derivedHash = await deriveModalityHash(
    seedHash,
    options.mode === "freehand-cast" ? "pareidolia" : `runes:${options.mode}`
  );
  const cursor = new HashCursor(derivedHash);
  const points = options.mode === "freehand-cast" ? generatePoints(cursor) : undefined;
  const symbols = points
    ? resolvePointRunes(cursor, points, options.includeWyrd)
    : selectRunes(cursor, runeCountForMode(options.mode), options.includeWyrd).map((rune, index) =>
        toSymbolEntry(rune, index, cursor.read(1) % 2 !== 0)
      );
  const geometry = buildGeometry(symbols, points, options.mode);

  const packet: ReadingPacket = {
    id: makePacketId("runes"),
    createdAt: new Date().toISOString(),
    modality: "runes",
    readingMode: "standard",
    userQuestion: options.userQuestion?.trim() || undefined,
    symbols,
    layout: {
      spreadName: `${options.mode} / ${derivedHash.slice(0, 8)}`,
      runeCastGeometry: geometry
    },
    staticInterpretation: symbols.length ? collectStaticInterpretation(symbols) : createEmptyStaticInterpretation(),
    liveAstrology,
    natalLens: options.natalLens,
    sourceTrace: {
      usedTarotJson: false,
      usedRuneJson: symbols.length > 0,
      usedLiveAstrology: liveAstrology.status === "available",
      usedNatalLens: options.natalLens?.status === "available",
      usedOpenRouter: false,
      missing: [
        ...(symbols.length ? [] : (["rune-json"] as const)),
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

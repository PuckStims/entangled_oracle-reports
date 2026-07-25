import type { TarotCardDatum, TarotSpread } from "./tarotTypes";

type JsonModuleMap = Record<string, unknown>;

const tarotModules = import.meta.glob("../../data/tarot/*.json", {
  eager: true,
  import: "default"
}) as JsonModuleMap;

type CatalogResult = { cards: TarotCardDatum[]; spreads: TarotSpread[]; source: string; placeholder: boolean };

function toCards(value: unknown): TarotCardDatum[] {
  if (Array.isArray(value)) return value as TarotCardDatum[];
  if (value && typeof value === "object" && Array.isArray((value as { cards?: unknown }).cards)) {
    return (value as { cards: TarotCardDatum[] }).cards;
  }
  return [];
}

function toSpreads(value: unknown): TarotSpread[] {
  const spreads = value && typeof value === "object" ? (value as { spreads?: unknown }).spreads : undefined;
  if (!Array.isArray(spreads)) return [];
  return spreads.map((spread) => {
    const item = spread as {
      id: string;
      title?: string;
      label?: string;
      subtitle?: string;
      positions?: Array<{ label: string; prompt?: string }>;
      positionLabels?: string[];
    };
    const positionLabels = item.positionLabels ?? item.positions?.map((position) => position.label) ?? [];
    return {
      id: item.id,
      label: item.label ?? item.title ?? item.id,
      subtitle: item.subtitle,
      cardCount: positionLabels.length,
      positionLabels,
      positionPrompts: item.positions?.map((position) => position.prompt ?? "")
    };
  });
}

export function loadTarotCatalog(): CatalogResult {
  const entries = Object.entries(tarotModules)
    .map(([path, value]) => ({
      path,
      cards: toCards(value),
      spreads: toSpreads(value),
      placeholder: path.includes(".placeholder.")
    }))
    .filter((entry) => entry.cards.length > 0 || entry.spreads.length > 0);

  const selected =
    entries.find((entry) => entry.path.includes(".local.")) ??
    entries.find((entry) => !entry.placeholder) ??
    entries[0];

  return {
    cards: selected?.cards ?? [],
    spreads: selected?.spreads ?? [],
    source: selected?.path ?? "src/data/tarot/*.json",
    placeholder: selected?.placeholder ?? true
  };
}

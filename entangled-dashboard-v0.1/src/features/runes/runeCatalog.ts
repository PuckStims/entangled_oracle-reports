import type { RuneDatum } from "./runeTypes";

type JsonModuleMap = Record<string, unknown>;

const runeModules = import.meta.glob("../../data/runes/*.json", {
  eager: true,
  import: "default"
}) as JsonModuleMap;

function toRunes(value: unknown): RuneDatum[] {
  if (Array.isArray(value)) return value as RuneDatum[];
  if (value && typeof value === "object" && Array.isArray((value as { runes?: unknown }).runes)) {
    return (value as { runes: RuneDatum[] }).runes;
  }
  return [];
}

export function loadRuneCatalog(): { runes: RuneDatum[]; source: string; placeholder: boolean } {
  const entries = Object.entries(runeModules)
    .map(([path, value]) => ({
      path,
      runes: toRunes(value),
      placeholder: path.includes(".placeholder.")
    }))
    .filter((entry) => entry.runes.length > 0);

  const selected =
    entries.find((entry) => entry.path.includes(".local.")) ??
    entries.find((entry) => !entry.placeholder) ??
    entries[0];

  return {
    runes: selected?.runes ?? [],
    source: selected?.path ?? "src/data/runes/*.json",
    placeholder: selected?.placeholder ?? true
  };
}

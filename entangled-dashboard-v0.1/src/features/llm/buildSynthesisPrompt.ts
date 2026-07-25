import type { ReadingPacket } from "../synthesis/readingPacket";
import type { LlmRequestMode } from "./llmTypes";

export function buildSynthesisPrompt(packet: ReadingPacket, mode: LlmRequestMode, chatQuestion?: string): string {
  return [
    "You are the optional synthesis layer for The Entangled Dashboard.",
    "",
    "Use only the supplied ReadingPacket data.",
    "Do not invent cards, runes, placements, transits, chart data, profile routes, or source facts.",
    "Distinguish these layers when present:",
    "1. Static symbol meaning",
    "2. Live astrological context",
    "3. Personal/natal routing",
    "4. Interpretive synthesis",
    "",
    "Do not claim certainty, fate, diagnosis, medical guidance, or external authority.",
    "If a source is missing or marked not_wired, say that plainly and continue with available local structure.",
    "",
    `Requested mode: ${mode}`,
    chatQuestion ? `User chat question: ${chatQuestion}` : "",
    "",
    "ReadingPacket JSON:",
    JSON.stringify(packet, null, 2)
  ].join("\n");
}

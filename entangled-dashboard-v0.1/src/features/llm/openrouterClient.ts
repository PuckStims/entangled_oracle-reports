import type { ReadingPacket } from "../synthesis/readingPacket";
import { buildSynthesisPrompt } from "./buildSynthesisPrompt";
import type { LlmRequestMode, LlmSynthesis } from "./llmTypes";

type OpenRouterProxyResponse = {
  status: LlmSynthesis["status"];
  model?: string;
  content?: string;
  errorMessage?: string;
};

function classifyStatus(status: number, text: string): LlmSynthesis["status"] {
  const normalized = text.toLowerCase();
  if (status === 402 || status === 429 || normalized.includes("quota") || normalized.includes("rate limit")) {
    return "quota_reached";
  }
  return "error";
}

export async function requestOpenRouterSynthesis(
  packet: ReadingPacket,
  mode: LlmRequestMode,
  chatQuestion?: string
): Promise<LlmSynthesis> {
  const proxyUrl = import.meta.env.VITE_OPENROUTER_PROXY_URL as string | undefined;

  if (!proxyUrl) {
    return {
      status: "disabled",
      promptVersion: "openrouter-v0.1",
      errorMessage: "No OpenRouter proxy URL configured."
    };
  }

  const prompt = buildSynthesisPrompt(packet, mode, chatQuestion);

  try {
    const response = await fetch(proxyUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ prompt, packetId: packet.id, mode })
    });

    const text = await response.text();
    let parsed: OpenRouterProxyResponse | undefined;
    try {
      parsed = JSON.parse(text) as OpenRouterProxyResponse;
    } catch {
      parsed = undefined;
    }

    if (!response.ok) {
      return {
        status: classifyStatus(response.status, text),
        promptVersion: "openrouter-v0.1",
        generatedAt: new Date().toISOString(),
        errorMessage: parsed?.errorMessage ?? text
      };
    }

    return {
      status: parsed?.status ?? "available",
      model: parsed?.model,
      content: parsed?.content,
      errorMessage: parsed?.errorMessage,
      generatedAt: new Date().toISOString(),
      promptVersion: "openrouter-v0.1"
    };
  } catch (error) {
    return {
      status: "error",
      promptVersion: "openrouter-v0.1",
      generatedAt: new Date().toISOString(),
      errorMessage: error instanceof Error ? error.message : "Unknown OpenRouter proxy error."
    };
  }
}

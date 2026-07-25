export type LlmStatus = "disabled" | "available" | "quota_reached" | "error";

export type LlmSynthesis = {
  status: LlmStatus;
  model?: string;
  generatedAt?: string;
  content?: string;
  errorMessage?: string;
  promptVersion: string;
};

export type LlmRequestMode = "mythic" | "practical" | "source_trace" | "chat";

# Reading Packet

`ReadingPacket` is the central object in the app.

```ts
type ReadingPacket = {
  id: string;
  createdAt: string;
  modality: "tarot" | "runes";
  readingMode: "standard" | "moon" | "retrograde" | "relationship" | "shadow" | "creative" | "custom";
  userQuestion?: string;
  symbols: SymbolEntry[];
  layout?: ReadingLayout;
  staticInterpretation: StaticInterpretation;
  liveAstrology?: LiveAstroContext;
  natalLens?: NatalLensResult;
  localSynthesis?: LocalSynthesis;
  llmSynthesis?: LlmSynthesis;
  sourceTrace: SourceTrace;
};
```

The packet is deliberately plain JSON so it can be saved, copied, diffed, exported, and sent to an LLM without hidden runtime state.

import { useState } from "react";
import { Bot, Braces, WandSparkles } from "lucide-react";
import LlmStatusBadge from "../llm/LlmStatusBadge";
import OracleChat from "../llm/OracleChat";
import { requestOpenRouterSynthesis } from "../llm/openrouterClient";
import type { LlmRequestMode, LlmStatus, LlmSynthesis } from "../llm/llmTypes";
import type { ReadingPacket, SourceName } from "./readingPacket";
import { summarizeSourceTrace } from "./sourceTrace";

type SynthesisPageProps = {
  currentPacket?: ReadingPacket;
  onUpdatePacket: (packet: ReadingPacket) => void;
};

export default function SynthesisPage({ currentPacket, onUpdatePacket }: SynthesisPageProps) {
  const [llmStatus, setLlmStatus] = useState<LlmStatus>(currentPacket?.llmSynthesis?.status ?? "disabled");
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const local = currentPacket?.localSynthesis;

  function applyLlmResult(result: LlmSynthesis) {
    setLlmStatus(result.status);
    if (!currentPacket) return;

    const missingSources: SourceName[] =
      result.status === "available"
        ? currentPacket.sourceTrace.missing.filter((source) => source !== "openrouter")
        : Array.from(new Set<SourceName>([...currentPacket.sourceTrace.missing, "openrouter"]));

    onUpdatePacket({
      ...currentPacket,
      llmSynthesis: result,
      sourceTrace: {
        ...currentPacket.sourceTrace,
        usedOpenRouter: result.status === "available",
        missing: missingSources
      }
    });
  }

  async function handleSynthesize(mode: LlmRequestMode) {
    if (!currentPacket) return;
    setIsSynthesizing(true);
    const result = await requestOpenRouterSynthesis(currentPacket, mode);
    applyLlmResult(result);
    setIsSynthesizing(false);
  }

  return (
    <main className="page-grid">
      <section className="section-panel section-panel--wide">
        <div className="section-kicker">
          <WandSparkles size={16} />
          Synthesis Layer
        </div>
        <h1>Synthesis</h1>
        <p>
          Local synthesis is always available. OpenRouter can add a richer mask when configured,
          but the dashboard remains usable when it is disabled, exhausted, or unreachable.
        </p>
        <LlmStatusBadge status={llmStatus} />
      </section>

      <section className="data-card">
        <div className="card-title-row">
          <Braces />
          <h2>Reading Packet</h2>
        </div>
        {currentPacket ? (
          <dl className="detail-list">
            <div>
              <dt>ID</dt>
              <dd>{currentPacket.id}</dd>
            </div>
            <div>
              <dt>Modality</dt>
              <dd>{currentPacket.modality}</dd>
            </div>
            <div>
              <dt>Symbols</dt>
              <dd>{currentPacket.symbols.length}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{new Date(currentPacket.createdAt).toLocaleString()}</dd>
            </div>
          </dl>
        ) : (
          <p>No active packet. Create one from Tarot or Runes.</p>
        )}
      </section>

      <section className="data-card">
        <div className="card-title-row">
          <Bot />
          <h2>OpenRouter Actions</h2>
        </div>
        <div className="button-row">
          <button
            className="secondary-action"
            type="button"
            disabled={!currentPacket || isSynthesizing}
            onClick={() => handleSynthesize("mythic")}
          >
            Mythic version
          </button>
          <button
            className="secondary-action"
            type="button"
            disabled={!currentPacket || isSynthesizing}
            onClick={() => handleSynthesize("practical")}
          >
            Practical version
          </button>
          <button
            className="secondary-action"
            type="button"
            disabled={!currentPacket || isSynthesizing}
            onClick={() => handleSynthesize("source_trace")}
          >
            Source trace
          </button>
        </div>
        <p className="microcopy">
          {isSynthesizing ? "Contacting optional synthesis layer..." : "No LLM call is required for the app to work."}
        </p>
      </section>

      <section className="section-panel">
        <h2>Local Synthesis</h2>
        {local ? (
          <>
            <h3>{local.title}</h3>
            <p>{local.summary}</p>
            <ul className="clean-list">
              {local.strands.map((strand) => (
                <li key={strand}>{strand}</li>
              ))}
            </ul>
          </>
        ) : (
          <p>No local synthesis yet.</p>
        )}
      </section>

      <section className="section-panel">
        <h2>Source Trace</h2>
        <ul className="clean-list">
          {summarizeSourceTrace(currentPacket).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      {currentPacket?.llmSynthesis?.content && (
        <section className="section-panel section-panel--wide">
          <h2>OpenRouter Synthesis</h2>
          <p className="llm-output">{currentPacket.llmSynthesis.content}</p>
        </section>
      )}

      <OracleChat packet={currentPacket} onLlmResult={applyLlmResult} />
    </main>
  );
}

import { useState } from "react";
import { MessageCircle, Send } from "lucide-react";
import type { ReadingPacket } from "../synthesis/readingPacket";
import { requestOpenRouterSynthesis } from "./openrouterClient";
import type { LlmSynthesis } from "./llmTypes";

type OracleChatProps = {
  packet?: ReadingPacket;
  onLlmResult: (result: LlmSynthesis) => void;
};

export default function OracleChat({ packet, onLlmResult }: OracleChatProps) {
  const [question, setQuestion] = useState("");
  const [isSending, setIsSending] = useState(false);

  async function handleAsk() {
    if (!packet || !question.trim()) return;
    setIsSending(true);
    const result = await requestOpenRouterSynthesis(packet, "chat", question);
    onLlmResult(result);
    setIsSending(false);
  }

  return (
    <section className="data-card">
      <div className="card-title-row">
        <MessageCircle />
        <h2>Oracle Chat</h2>
      </div>
      <p>
        Chat is optional and packet-bound. It cannot add cards, runes, placements, or astrology
        that were not already supplied.
      </p>
      <label className="field-label">
        Ask about the active packet
        <textarea
          value={question}
          disabled={!packet || isSending}
          onChange={(event) => setQuestion(event.target.value)}
        />
      </label>
      <button className="secondary-action" type="button" disabled={!packet || isSending} onClick={handleAsk}>
        <Send size={16} />
        {isSending ? "Asking..." : "Ask OpenRouter"}
      </button>
    </section>
  );
}

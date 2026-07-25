import { CalendarClock, Database, Moon, Radio } from "lucide-react";
import LlmStatusBadge from "../../features/llm/LlmStatusBadge";
import type { LlmStatus } from "../../features/llm/llmTypes";
import type { LiveAstroContext } from "../../features/astrology/astroTypes";
import type { ReadingPacket } from "../../features/synthesis/readingPacket";

type StatusBarProps = {
  liveAstrology: LiveAstroContext;
  currentPacket?: ReadingPacket;
  llmStatus: LlmStatus;
};

export default function StatusBar({ liveAstrology, currentPacket, llmStatus }: StatusBarProps) {
  return (
    <aside className="status-bar" aria-label="Console status">
      <span>
        <CalendarClock size={15} />
        {new Date().toLocaleDateString(undefined, {
          weekday: "short",
          month: "short",
          day: "numeric"
        })}
      </span>
      <span>
        <Moon size={15} />
        {liveAstrology.status === "available" ? "Live sky online" : "Sky adapter scaffolded"}
      </span>
      <span>
        <Database size={15} />
        {currentPacket ? `${currentPacket.modality} packet active` : "No packet active"}
      </span>
      <span>
        <Radio size={15} />
        Local synthesis ready
      </span>
      <LlmStatusBadge status={llmStatus} />
    </aside>
  );
}

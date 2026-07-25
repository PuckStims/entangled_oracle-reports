import { Bot, CircleOff, SignalHigh, TriangleAlert } from "lucide-react";
import type { LlmStatus } from "./llmTypes";

type LlmStatusBadgeProps = {
  status: LlmStatus;
};

const statusCopy: Record<LlmStatus, { label: string; className: string; icon: typeof Bot }> = {
  disabled: {
    label: "AI mask offline",
    className: "status-pill status-pill--muted",
    icon: CircleOff
  },
  available: {
    label: "OpenRouter available",
    className: "status-pill status-pill--good",
    icon: SignalHigh
  },
  quota_reached: {
    label: "Quota reached, local synthesis active",
    className: "status-pill status-pill--warn",
    icon: TriangleAlert
  },
  error: {
    label: "LLM error, local synthesis active",
    className: "status-pill status-pill--warn",
    icon: TriangleAlert
  }
};

export default function LlmStatusBadge({ status }: LlmStatusBadgeProps) {
  const copy = statusCopy[status];
  const Icon = copy.icon;

  return (
    <span className={copy.className}>
      <Icon size={14} />
      {copy.label}
    </span>
  );
}

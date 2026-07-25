import type { ReactNode } from "react";
import type { LiveAstroContext } from "../../features/astrology/astroTypes";
import type { LlmStatus } from "../../features/llm/llmTypes";
import type { ReadingPacket } from "../../features/synthesis/readingPacket";
import type { AppRouteId } from "../routes";
import StatusBar from "./StatusBar";
import TopNav from "./TopNav";

type DashboardShellProps = {
  activeRoute: AppRouteId;
  onRouteChange: (route: AppRouteId) => void;
  liveAstrology: LiveAstroContext;
  currentPacket?: ReadingPacket;
  llmStatus: LlmStatus;
  children: ReactNode;
};

export default function DashboardShell({
  activeRoute,
  onRouteChange,
  liveAstrology,
  currentPacket,
  llmStatus,
  children
}: DashboardShellProps) {
  return (
    <div className="dashboard-shell">
      <header className="app-header">
        <div>
          <p className="brand-kicker">The Entangled Dashboard</p>
          <h1>Cyber-pagan symbolic console</h1>
        </div>
        <TopNav activeRoute={activeRoute} onRouteChange={onRouteChange} />
      </header>
      <StatusBar liveAstrology={liveAstrology} currentPacket={currentPacket} llmStatus={llmStatus} />
      {children}
    </div>
  );
}

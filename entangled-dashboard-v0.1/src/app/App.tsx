import { useEffect, useMemo, useState } from "react";
import ArchivePage from "../features/archive/ArchivePage";
import { saveReading } from "../features/archive/readingStorage";
import { loadAstrologyProfile, type AstrologyProfile } from "../features/astrology/astrologyApi";
import AstrologyPage from "../features/astrology/AstrologyPage";
import { fetchLiveAstroContext, getLiveAstroContext } from "../features/astrology/liveAstroEngine";
import { fetchNatalLensForPacket, getNatalLensForPacket } from "../features/astrology/natalLens";
import type { LiveAstroContext, NatalLensResult } from "../features/astrology/astroTypes";
import ExperimentalPage from "../features/experimental/ExperimentalPage";
import type { LlmStatus } from "../features/llm/llmTypes";
import RunesPage from "../features/runes/RunesPage";
import SettingsPage from "../features/settings/SettingsPage";
import SynthesisPage from "../features/synthesis/SynthesisPage";
import type { ReadingPacket } from "../features/synthesis/readingPacket";
import TarotPage from "../features/tarot/TarotPage";
import DashboardHome from "./DashboardHome";
import DashboardShell from "./layout/DashboardShell";
import type { AppRouteId } from "./routes";

export default function App() {
  const [activeRoute, setActiveRoute] = useState<AppRouteId>("dashboard");
  const [currentPacket, setCurrentPacket] = useState<ReadingPacket | undefined>();
  const [astroProfile, setAstroProfile] = useState<AstrologyProfile>(() => loadAstrologyProfile());
  const [liveAstrology, setLiveAstrology] = useState<LiveAstroContext>(() => getLiveAstroContext());
  const [natalLens, setNatalLens] = useState<NatalLensResult>(() => getNatalLensForPacket());
  const llmStatus: LlmStatus = currentPacket?.llmSynthesis?.status ?? "disabled";
  const packetLens = useMemo(() => natalLens, [natalLens]);

  useEffect(() => {
    function syncProfile() {
      setAstroProfile(loadAstrologyProfile());
    }

    window.addEventListener("storage", syncProfile);
    window.addEventListener("entangled-dashboard:astrology-profile", syncProfile);
    return () => {
      window.removeEventListener("storage", syncProfile);
      window.removeEventListener("entangled-dashboard:astrology-profile", syncProfile);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function refreshAstrology() {
      const [liveContext, lens] = await Promise.all([
        fetchLiveAstroContext(astroProfile),
        fetchNatalLensForPacket(astroProfile, currentPacket)
      ]);
      if (!cancelled) {
        setLiveAstrology(liveContext);
        setNatalLens(lens);
      }
    }

    void refreshAstrology();
    return () => {
      cancelled = true;
    };
  }, [astroProfile, currentPacket?.id]);

  function handleCreatePacket(packet: ReadingPacket) {
    setCurrentPacket(packet);
  }

  function handleUpdatePacket(packet: ReadingPacket) {
    setCurrentPacket(packet);
  }

  function handleSavePacket() {
    if (currentPacket) saveReading(currentPacket);
  }

  return (
    <DashboardShell
      activeRoute={activeRoute}
      onRouteChange={setActiveRoute}
      liveAstrology={liveAstrology}
      currentPacket={currentPacket}
      llmStatus={llmStatus}
    >
      {activeRoute === "dashboard" && (
        <DashboardHome
          currentPacket={currentPacket}
          liveAstrology={liveAstrology}
          natalLens={packetLens}
          onRouteChange={setActiveRoute}
          onSavePacket={handleSavePacket}
        />
      )}
      {activeRoute === "tarot" && (
        <TarotPage
          currentPacket={currentPacket}
          liveAstrology={liveAstrology}
          natalLens={packetLens}
          onCreatePacket={handleCreatePacket}
        />
      )}
      {activeRoute === "runes" && (
        <RunesPage
          currentPacket={currentPacket}
          liveAstrology={liveAstrology}
          natalLens={packetLens}
          onCreatePacket={handleCreatePacket}
        />
      )}
      {activeRoute === "astrology" && <AstrologyPage liveAstrology={liveAstrology} natalLens={packetLens} />}
      {activeRoute === "synthesis" && (
        <SynthesisPage currentPacket={currentPacket} onUpdatePacket={handleUpdatePacket} />
      )}
      {activeRoute === "experimental" && <ExperimentalPage currentPacket={currentPacket} />}
      {activeRoute === "archive" && <ArchivePage currentPacket={currentPacket} onLoadPacket={setCurrentPacket} />}
      {activeRoute === "settings" && <SettingsPage />}
    </DashboardShell>
  );
}

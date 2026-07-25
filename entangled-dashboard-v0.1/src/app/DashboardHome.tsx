import { Archive, Bot, Gem, Moon, Save, Sparkles, WandSparkles } from "lucide-react";
import { getAstrologyReadiness } from "../features/astrology/liveAstroEngine";
import type { LiveAstroContext, NatalLensResult } from "../features/astrology/astroTypes";
import { getRuneCatalogStatus } from "../features/runes/runeEngine";
import { getTarotCatalogStatus } from "../features/tarot/tarotEngine";
import type { ReadingPacket } from "../features/synthesis/readingPacket";
import type { AppRouteId } from "./routes";

type DashboardHomeProps = {
  currentPacket?: ReadingPacket;
  liveAstrology: LiveAstroContext;
  natalLens: NatalLensResult;
  onRouteChange: (route: AppRouteId) => void;
  onSavePacket: () => void;
};

export default function DashboardHome({
  currentPacket,
  liveAstrology,
  natalLens,
  onRouteChange,
  onSavePacket
}: DashboardHomeProps) {
  const tarotStatus = getTarotCatalogStatus();
  const runeStatus = getRuneCatalogStatus();
  const astroStatus = getAstrologyReadiness(liveAstrology);

  return (
    <main className="page-grid">
      <section className="hero-panel section-panel--wide">
        <div className="hero-panel__content">
          <p className="section-kicker">
            <Sparkles size={16} />
            Standard cards. Standard stones. Living sky. Optional machine oracle.
          </p>
          <h1>The Entangled Dashboard</h1>
          <p>
            A localhost symbolic console where tarot, runes, astrology, optional synthesis, and
            experimental interfaces share one packet architecture.
          </p>
          <div className="button-row">
            <button className="primary-action" type="button" onClick={() => onRouteChange("tarot")}>
              <WandSparkles size={18} />
              Tarot
            </button>
            <button className="primary-action" type="button" onClick={() => onRouteChange("runes")}>
              <Gem size={18} />
              Runes
            </button>
            <button className="secondary-action" type="button" onClick={() => onRouteChange("experimental")}>
              <Sparkles size={16} />
              Experimental
            </button>
          </div>
        </div>
      </section>

      <section className="data-card">
        <div className="card-title-row">
          <WandSparkles />
          <h2>Tarot JSON</h2>
        </div>
        <p className={tarotStatus.ready ? "status-good" : "status-muted"}>{tarotStatus.note}</p>
        <strong>{tarotStatus.count} / 78</strong>
      </section>

      <section className="data-card">
        <div className="card-title-row">
          <Gem />
          <h2>Rune JSON</h2>
        </div>
        <p className={runeStatus.ready ? "status-good" : "status-muted"}>{runeStatus.note}</p>
        <strong>{runeStatus.count} / 24</strong>
      </section>

      <section className="data-card">
        <div className="card-title-row">
          <Moon />
          <h2>Sky Lens</h2>
        </div>
        <p className={astroStatus.ready ? "status-good" : "status-muted"}>{astroStatus.detail}</p>
        <strong>{liveAstrology.status}</strong>
      </section>

      <section className="data-card">
        <div className="card-title-row">
          <Bot />
          <h2>OpenRouter</h2>
        </div>
        <p>Optional. The app runs without it and shifts to local synthesis.</p>
        <strong>{currentPacket?.llmSynthesis?.status ?? "disabled"}</strong>
      </section>

      <section className="section-panel">
        <h2>Active Packet</h2>
        {currentPacket ? (
          <>
            <dl className="detail-list">
              <div>
                <dt>Modality</dt>
                <dd>{currentPacket.modality}</dd>
              </div>
              <div>
                <dt>Symbols</dt>
                <dd>{currentPacket.symbols.length}</dd>
              </div>
              <div>
                <dt>Profile lens</dt>
                <dd>{natalLens.status}</dd>
              </div>
            </dl>
            <div className="button-row">
              <button className="secondary-action" type="button" onClick={() => onRouteChange("synthesis")}>
                <Bot size={16} />
                Open Synthesis
              </button>
              <button className="secondary-action" type="button" onClick={onSavePacket}>
                <Save size={16} />
                Save
              </button>
            </div>
          </>
        ) : (
          <p>No active packet yet. Start with Tarot or Runes.</p>
        )}
      </section>

      <section className="section-panel">
        <h2>Routes</h2>
        <div className="route-stack">
          <button type="button" onClick={() => onRouteChange("astrology")}>
            <Moon size={16} />
            Astrology adapters
          </button>
          <button type="button" onClick={() => onRouteChange("archive")}>
            <Archive size={16} />
            Archive packets
          </button>
          <button type="button" onClick={() => onRouteChange("settings")}>
            <Sparkles size={16} />
            Wiring settings
          </button>
        </div>
      </section>
    </main>
  );
}

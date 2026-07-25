import { useMemo, useState } from "react";
import { Shuffle, WandSparkles } from "lucide-react";
import type { LiveAstroContext, NatalLensResult } from "../astrology/astroTypes";
import type { ReadingPacket } from "../synthesis/readingPacket";
import { createTarotReading, getTarotCatalogStatus, getTarotSpreads } from "./tarotEngine";
import type { TarotSpreadId } from "./tarotTypes";
import TarotCardView from "./TarotCardView";
import TarotSpreadSelector from "./TarotSpreadSelector";

type TarotPageProps = {
  currentPacket?: ReadingPacket;
  liveAstrology: LiveAstroContext;
  natalLens: NatalLensResult;
  onCreatePacket: (packet: ReadingPacket) => void;
};

export default function TarotPage({ currentPacket, liveAstrology, natalLens, onCreatePacket }: TarotPageProps) {
  const [spreadId, setSpreadId] = useState<TarotSpreadId>("single");
  const [allowReversals, setAllowReversals] = useState(true);
  const [isLocking, setIsLocking] = useState(false);
  const [question, setQuestion] = useState("");
  const status = useMemo(() => getTarotCatalogStatus(), []);
  const spreads = useMemo(() => getTarotSpreads(), []);
  const tarotPacket = currentPacket?.modality === "tarot" ? currentPacket : undefined;
  const selectedSpreadId = spreads.some((spread) => spread.id === spreadId) ? spreadId : spreads[0]?.id ?? spreadId;

  async function handlePull() {
    setIsLocking(true);
    try {
      onCreatePacket(
        await createTarotReading({
        spreadId: selectedSpreadId,
        allowReversals,
        userQuestion: question,
        liveAstrology,
        natalLens
        })
      );
    } finally {
      setIsLocking(false);
    }
  }

  return (
    <main className="page-grid">
      <section className="section-panel section-panel--wide">
        <div className="section-kicker">
          <WandSparkles size={16} />
          Standard Practice
        </div>
        <h1>Tarot</h1>
        <p>
          The card practice is scaffolded around your existing 78-card JSON. Until that dataset is
          wired, this tab shows the spread controls and packet path without inventing card meanings.
        </p>
      </section>

      <section className="control-panel">
        <h2>Reading Setup</h2>
        <TarotSpreadSelector selected={selectedSpreadId} onChange={setSpreadId} />
        <label className="field-label">
          Question or focus
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} />
        </label>
        <label className="toggle-row">
          <input
            type="checkbox"
            checked={allowReversals}
            onChange={(event) => setAllowReversals(event.target.checked)}
          />
          Reversals allowed
        </label>
        <button className="primary-action" type="button" onClick={handlePull} disabled={isLocking}>
          <Shuffle size={18} />
          {isLocking ? "Locking Entropy" : "Create Tarot Packet"}
        </button>
      </section>

      <section className="data-card">
        <h2>Catalog Status</h2>
        <p className={status.ready ? "status-good" : "status-muted"}>{status.note}</p>
        <dl className="detail-list">
          <div>
            <dt>Loaded cards</dt>
            <dd>{status.count}</dd>
          </div>
          <div>
            <dt>Expected</dt>
            <dd>78</dd>
          </div>
          <div>
            <dt>Sky source</dt>
            <dd>{liveAstrology.status === "available" ? liveAstrology.adapterName : "waiting"}</dd>
          </div>
        </dl>
      </section>

      <section className="section-panel section-panel--wide">
        <h2>Current Tarot Packet</h2>
        {tarotPacket?.symbols.length ? (
          <div className="symbol-grid">
            {tarotPacket.symbols.map((symbol) => (
              <TarotCardView key={`${symbol.id}-${symbol.position}`} symbol={symbol} />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>No tarot symbols are present yet. Wire the existing dataset, then create a packet.</p>
          </div>
        )}
      </section>
    </main>
  );
}

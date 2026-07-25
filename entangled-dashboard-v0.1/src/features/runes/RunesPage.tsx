import { useMemo, useState } from "react";
import { Gem, Shuffle } from "lucide-react";
import type { LiveAstroContext, NatalLensResult } from "../astrology/astroTypes";
import type { ReadingPacket } from "../synthesis/readingPacket";
import FreehandRuneCast from "./FreehandRuneCast";
import RuneDraw from "./RuneDraw";
import { createRuneReading, getRuneCatalogStatus } from "./runeEngine";
import type { RuneReadingMode } from "./runeTypes";

type RunesPageProps = {
  currentPacket?: ReadingPacket;
  liveAstrology: LiveAstroContext;
  natalLens: NatalLensResult;
  onCreatePacket: (packet: ReadingPacket) => void;
};

export default function RunesPage({ currentPacket, liveAstrology, natalLens, onCreatePacket }: RunesPageProps) {
  const [mode, setMode] = useState<RuneReadingMode>("single");
  const [includeWyrd, setIncludeWyrd] = useState(false);
  const [isLocking, setIsLocking] = useState(false);
  const [question, setQuestion] = useState("");
  const status = useMemo(() => getRuneCatalogStatus(), []);
  const runePacket = currentPacket?.modality === "runes" ? currentPacket : undefined;

  async function handleCast() {
    setIsLocking(true);
    try {
      onCreatePacket(
        await createRuneReading({
          mode,
          userQuestion: question,
          includeWyrd,
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
          <Gem size={16} />
          Standard Practice
        </div>
        <h1>Runes</h1>
        <p>
          The rune practice is scaffolded around your existing Elder Futhark JSON and freehand cast
          system. This tab keeps stones normal and leaves experimental remixing elsewhere.
        </p>
      </section>

      <section className="control-panel">
        <h2>Reading Setup</h2>
        <div className="segmented-control" aria-label="Rune reading mode">
          {[
            ["single", "Single Rune"],
            ["three-rune", "Three Rune"],
            ["freehand-cast", "Freehand Cast"]
          ].map(([id, label]) => (
            <button
              key={id}
              className={mode === id ? "is-active" : ""}
              type="button"
              onClick={() => setMode(id as RuneReadingMode)}
            >
              {label}
            </button>
          ))}
        </div>
        <label className="field-label">
          Question or focus
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} />
        </label>
        <label className="toggle-row">
          <input
            type="checkbox"
            checked={includeWyrd}
            onChange={(event) => setIncludeWyrd(event.target.checked)}
          />
          Include Wyrd
        </label>
        <button className="primary-action" type="button" onClick={handleCast} disabled={isLocking}>
          <Shuffle size={18} />
          {isLocking ? "Locking Entropy" : "Create Rune Packet"}
        </button>
      </section>

      <section className="data-card">
        <h2>Catalog Status</h2>
        <p className={status.ready ? "status-good" : "status-muted"}>{status.note}</p>
        <dl className="detail-list">
          <div>
            <dt>Loaded runes</dt>
            <dd>{status.count}</dd>
          </div>
          <div>
            <dt>Expected</dt>
            <dd>24 + optional Wyrd</dd>
          </div>
          <div>
            <dt>Sky source</dt>
            <dd>{liveAstrology.status === "available" ? liveAstrology.adapterName : "waiting"}</dd>
          </div>
        </dl>
      </section>

      <FreehandRuneCast packet={runePacket} />

      <section className="section-panel section-panel--wide">
        <h2>Current Rune Packet</h2>
        {runePacket?.symbols.length ? (
          <div className="symbol-grid">
            {runePacket.symbols.map((symbol) => (
              <RuneDraw key={`${symbol.id}-${symbol.position}`} symbol={symbol} />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>No rune symbols are present yet. Wire the existing dataset, then create a packet.</p>
          </div>
        )}
      </section>
    </main>
  );
}

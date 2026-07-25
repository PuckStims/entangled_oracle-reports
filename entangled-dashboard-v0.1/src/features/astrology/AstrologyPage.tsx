import { CircleDashed, LockKeyhole, Orbit } from "lucide-react";
import type { LiveAstroContext, NatalLensResult } from "./astroTypes";

type AstrologyPageProps = {
  liveAstrology: LiveAstroContext;
  natalLens: NatalLensResult;
};

export default function AstrologyPage({ liveAstrology, natalLens }: AstrologyPageProps) {
  return (
    <main className="page-grid">
      <section className="section-panel section-panel--wide">
        <div className="section-kicker">
          <Orbit size={16} />
          Sky Adapter
        </div>
        <h1>Astrology Layer</h1>
        <p>
          This wing reads from the existing Entangled Astrology API when a local profile is saved.
          If that service is offline or no profile exists, the dashboard keeps the adapter boundary
          visible instead of inventing signs, phases, aspects, or natal routing.
        </p>
      </section>

      <section className="data-card">
        <div className="card-title-row">
          <CircleDashed />
          <h2>Live Sky Context</h2>
        </div>
        <dl className="detail-list">
          <div>
            <dt>Status</dt>
            <dd>{liveAstrology.status}</dd>
          </div>
          <div>
            <dt>Adapter</dt>
            <dd>{liveAstrology.adapterName}</dd>
          </div>
          <div>
            <dt>Generated</dt>
            <dd>{new Date(liveAstrology.generatedAt).toLocaleString()}</dd>
          </div>
          <div>
            <dt>Note</dt>
            <dd>{liveAstrology.note}</dd>
          </div>
          <div>
            <dt>Major aspects</dt>
            <dd>{liveAstrology.majorAspects?.length ?? 0}</dd>
          </div>
        </dl>
      </section>

      <section className="data-card">
        <div className="card-title-row">
          <LockKeyhole />
          <h2>Personal Natal Lens</h2>
        </div>
        <dl className="detail-list">
          <div>
            <dt>Status</dt>
            <dd>{natalLens.status}</dd>
          </div>
          <div>
            <dt>Adapter</dt>
            <dd>{natalLens.adapterName}</dd>
          </div>
          <div>
            <dt>Routes</dt>
            <dd>{natalLens.routes.length}</dd>
          </div>
          <div>
            <dt>Note</dt>
            <dd>{natalLens.note}</dd>
          </div>
        </dl>
      </section>

      <section className="data-card">
        <h2>Current Field</h2>
        {liveAstrology.majorAspects?.length ? (
          <ul className="clean-list">
            {liveAstrology.majorAspects.map((aspect) => (
              <li key={`${aspect.planetA}-${aspect.aspect}-${aspect.planetB}`}>
                <strong>{aspect.planetA}</strong> {aspect.aspect} {aspect.planetB}
                {aspect.orb !== undefined ? ` (${aspect.orb.toFixed(2)} deg)` : ""}
              </li>
            ))}
          </ul>
        ) : (
          <p className="status-muted">No current-field events are available yet.</p>
        )}
      </section>

      <section className="data-card">
        <h2>Natal Routes</h2>
        {natalLens.routes.length ? (
          <div className="route-stack">
            {natalLens.routes.slice(0, 12).map((route) => (
              <article className="matrix-rule" key={route.id}>
                <span>{route.keywords.join(" / ")}</span>
                <p>
                  <strong>{route.label}</strong>
                </p>
                <p>{route.routing}</p>
              </article>
            ))}
          </div>
        ) : (
          <p className="status-muted">No natal routes are available yet.</p>
        )}
      </section>
    </main>
  );
}

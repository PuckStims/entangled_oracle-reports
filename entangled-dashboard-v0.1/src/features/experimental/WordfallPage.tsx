import { useMemo, useState } from "react";
import { Pause, Play } from "lucide-react";
import type { ReadingPacket } from "../synthesis/readingPacket";
import { getWordfallTerms } from "./wordfallEngine";

type WordfallPageProps = {
  packet?: ReadingPacket;
};

export default function WordfallPage({ packet }: WordfallPageProps) {
  const terms = useMemo(() => getWordfallTerms(packet), [packet]);
  const [frozen, setFrozen] = useState<string[]>([]);
  const [running, setRunning] = useState(true);

  function toggleTerm(term: string) {
    setFrozen((current) => (current.includes(term) ? current.filter((item) => item !== term) : [...current, term]));
  }

  return (
    <section className="section-panel section-panel--wide">
      <div className="card-title-row">
        {running ? <Play /> : <Pause />}
        <h2>Wordfall</h2>
      </div>
      <p>
        A packet-fed word stream. It does not interpret; it only lets available terms fall across
        the console for selection.
      </p>
      <button className="secondary-action" type="button" onClick={() => setRunning((value) => !value)}>
        {running ? "Freeze stream" : "Resume stream"}
      </button>
      {terms.length ? (
        <div className={running ? "wordfall is-running" : "wordfall"}>
          {terms.map((term, index) => (
            <button
              type="button"
              key={`${term}-${index}`}
              className={frozen.includes(term) ? "wordfall__term is-frozen" : "wordfall__term"}
              style={{ animationDelay: `${index * 0.35}s` }}
              onClick={() => toggleTerm(term)}
            >
              {term}
            </button>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <p>Wordfall is waiting for packet terms from wired tarot, rune, astrology, or profile data.</p>
        </div>
      )}
      {frozen.length > 0 && (
        <div className="frozen-words">
          <strong>Frozen words</strong>
          <p>{frozen.join(" / ")}</p>
        </div>
      )}
    </section>
  );
}

import { useState } from "react";
import { Sparkles } from "lucide-react";
import type { ReadingPacket } from "../synthesis/readingPacket";
import AbstractReadoutPage from "./AbstractReadoutPage";
import SpeculationMatrixPage from "./SpeculationMatrixPage";
import WordfallPage from "./WordfallPage";

type ExperimentalPageProps = {
  currentPacket?: ReadingPacket;
};

type ExperimentalTab = "wordfall" | "abstract" | "matrix";

export default function ExperimentalPage({ currentPacket }: ExperimentalPageProps) {
  const [tab, setTab] = useState<ExperimentalTab>("wordfall");

  return (
    <main className="page-grid">
      <section className="section-panel section-panel--wide">
        <div className="section-kicker">
          <Sparkles size={16} />
          Experimental Interfaces
        </div>
        <h1>Experimental</h1>
        <p>
          These surfaces remix completed reading packets. They are optional dream interfaces, not a
          replacement for standard tarot or rune practice.
        </p>
        <div className="segmented-control">
          <button className={tab === "wordfall" ? "is-active" : ""} type="button" onClick={() => setTab("wordfall")}>
            Wordfall
          </button>
          <button className={tab === "abstract" ? "is-active" : ""} type="button" onClick={() => setTab("abstract")}>
            Abstract
          </button>
          <button className={tab === "matrix" ? "is-active" : ""} type="button" onClick={() => setTab("matrix")}>
            Matrix
          </button>
        </div>
      </section>

      {tab === "wordfall" && <WordfallPage packet={currentPacket} />}
      {tab === "abstract" && <AbstractReadoutPage packet={currentPacket} />}
      {tab === "matrix" && <SpeculationMatrixPage packet={currentPacket} />}
    </main>
  );
}

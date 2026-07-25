import { GitBranch } from "lucide-react";
import type { ReadingPacket } from "../synthesis/readingPacket";
import { buildSpeculationMatrix } from "./speculationRules";

type SpeculationMatrixPageProps = {
  packet?: ReadingPacket;
};

export default function SpeculationMatrixPage({ packet }: SpeculationMatrixPageProps) {
  const rules = buildSpeculationMatrix(packet);

  return (
    <section className="section-panel section-panel--wide">
      <div className="card-title-row">
        <GitBranch />
        <h2>Speculation Matrix</h2>
      </div>
      <div className="matrix-list">
        {rules.map((rule, index) => (
          <article key={`${rule.ifLine}-${index}`} className="matrix-rule">
            <span>{rule.source}</span>
            <p>{rule.ifLine}</p>
            <strong>{rule.thenLine}</strong>
          </article>
        ))}
      </div>
    </section>
  );
}

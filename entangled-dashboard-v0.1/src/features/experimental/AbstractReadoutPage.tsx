import type { CSSProperties } from "react";
import type { ReadingPacket } from "../synthesis/readingPacket";
import { buildAbstractVisualModel } from "./abstractVisualEngine";

type AbstractReadoutPageProps = {
  packet?: ReadingPacket;
};

export default function AbstractReadoutPage({ packet }: AbstractReadoutPageProps) {
  const model = buildAbstractVisualModel(packet);
  const rings = Array.from({ length: model.rings });
  const spokes = Array.from({ length: model.spokes });

  return (
    <section className="section-panel section-panel--wide">
      <h2>Abstract Readout</h2>
      <p>No interpretation supplied. Notice what your mind tries to name.</p>
      <div
        className="abstract-readout"
        style={{
          "--readout-hue": String(model.hue),
          "--readout-intensity": String(model.intensity)
        } as CSSProperties}
        aria-label="Abstract packet readout"
      >
        {rings.map((_, index) => (
          <span key={`ring-${index}`} className="abstract-readout__ring" />
        ))}
        {spokes.map((_, index) => (
          <span
            key={`spoke-${index}`}
            className="abstract-readout__spoke"
            style={{ transform: `rotate(${(360 / spokes.length) * index}deg)` }}
          />
        ))}
      </div>
    </section>
  );
}

import RuneCastMat from "./RuneCastMat";
import type { ReadingPacket } from "../synthesis/readingPacket";

type FreehandRuneCastProps = {
  packet?: ReadingPacket;
};

export default function FreehandRuneCast({ packet }: FreehandRuneCastProps) {
  return (
    <section className="data-card">
      <h2>Freehand Cast Scaffold</h2>
      <RuneCastMat packet={packet} />
      <p>
        This surface is reserved for spatial placement, regions, proximity, and clustering notes.
        The repo does not create rune placement logic; it waits for your existing procedural cast.
      </p>
    </section>
  );
}

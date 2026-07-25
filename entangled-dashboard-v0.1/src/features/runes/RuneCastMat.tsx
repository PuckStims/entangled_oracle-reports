import type { ReadingPacket } from "../synthesis/readingPacket";

type RuneCastMatProps = {
  packet?: ReadingPacket;
};

export default function RuneCastMat({ packet }: RuneCastMatProps) {
  const points = packet?.layout?.runeCastGeometry?.points ?? [];

  return (
    <div className="cast-mat" aria-label="Rune cast mat">
      <div className="cast-mat__grid" />
      {points.map((point) => (
        <span
          key={point.runeId}
          className="cast-mat__point"
          style={{ left: `${point.x * 100}%`, top: `${point.y * 100}%` }}
        >
          {point.runeId}
        </span>
      ))}
      {!points.length && (
        <p className="cast-mat__empty">Freehand geometry adapter waiting for your existing cast system.</p>
      )}
    </div>
  );
}

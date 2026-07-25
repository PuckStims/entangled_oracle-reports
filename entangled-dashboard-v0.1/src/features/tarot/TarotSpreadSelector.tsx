import type { TarotSpreadId } from "./tarotTypes";
import { getTarotSpreads } from "./tarotEngine";

type TarotSpreadSelectorProps = {
  selected: TarotSpreadId;
  onChange: (spread: TarotSpreadId) => void;
};

export default function TarotSpreadSelector({ selected, onChange }: TarotSpreadSelectorProps) {
  return (
    <div className="segmented-control" aria-label="Tarot spread">
      {getTarotSpreads().map((spread) => (
        <button
          key={spread.id}
          className={selected === spread.id ? "is-active" : ""}
          type="button"
          onClick={() => onChange(spread.id)}
        >
          {spread.label}
        </button>
      ))}
    </div>
  );
}

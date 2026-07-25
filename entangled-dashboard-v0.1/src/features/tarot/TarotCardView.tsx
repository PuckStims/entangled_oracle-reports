import type { SymbolEntry } from "../synthesis/readingPacket";

type TarotCardViewProps = {
  symbol: SymbolEntry;
};

export default function TarotCardView({ symbol }: TarotCardViewProps) {
  return (
    <article className="symbol-card">
      <div>
        <span className="symbol-card__position">{symbol.position}</span>
        <h3>{symbol.name}</h3>
      </div>
      {symbol.reversed && <span className="status-pill status-pill--warn">Reversed</span>}
      <p>{symbol.meaning || "Meaning field is ready for your tarot JSON."}</p>
      <div className="keyword-row">
        {symbol.keywords.length ? (
          symbol.keywords.map((keyword) => <span key={keyword}>{keyword}</span>)
        ) : (
          <span>No keywords wired</span>
        )}
      </div>
    </article>
  );
}

import type { SymbolEntry } from "../synthesis/readingPacket";

type RuneDrawProps = {
  symbol: SymbolEntry;
};

export default function RuneDraw({ symbol }: RuneDrawProps) {
  return (
    <article className="symbol-card symbol-card--rune">
      <div className="rune-glyph">{symbol.glyph ?? "?"}</div>
      <div>
        <span className="symbol-card__position">{symbol.position}</span>
        <h3>{symbol.name}</h3>
        <p>{symbol.meaning || "Meaning field is ready for your rune JSON."}</p>
      </div>
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

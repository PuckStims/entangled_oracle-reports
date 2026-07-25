import { Settings } from "lucide-react";
import AstroProfileSettings from "./AstroProfileSettings";
import OpenRouterSettings from "./OpenRouterSettings";

export default function SettingsPage() {
  return (
    <main className="page-grid">
      <section className="section-panel section-panel--wide">
        <div className="section-kicker">
          <Settings size={16} />
          Console Wiring
        </div>
        <h1>Settings</h1>
        <p>
          This page keeps integration points visible: symbolic datasets, private profile routing,
          optional OpenRouter, and future engine wiring.
        </p>
      </section>
      <OpenRouterSettings />
      <AstroProfileSettings />
      <section className="data-card">
        <h2>Dataset Wiring</h2>
        <ul className="clean-list">
          <li>
            Tarot adapter: <code>src/features/tarot/tarotEngine.ts</code>
          </li>
          <li>
            Rune adapter: <code>src/features/runes/runeEngine.ts</code>
          </li>
          <li>
            Live astrology adapter: <code>src/features/astrology/liveAstroEngine.ts</code>
          </li>
          <li>
            Reading packet contract: <code>src/features/synthesis/readingPacket.ts</code>
          </li>
        </ul>
      </section>
    </main>
  );
}

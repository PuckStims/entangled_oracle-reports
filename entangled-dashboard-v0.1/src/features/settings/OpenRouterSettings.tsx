import { Bot, KeyRound, Server } from "lucide-react";

export default function OpenRouterSettings() {
  return (
    <section className="data-card">
      <div className="card-title-row">
        <Bot />
        <h2>OpenRouter</h2>
      </div>
      <p>
        OpenRouter is optional. The frontend calls a local proxy URL from
        <code> VITE_OPENROUTER_PROXY_URL</code>, and the proxy reads
        <code> OPENROUTER_API_KEY</code> from <code>.env</code>.
      </p>
      <dl className="detail-list">
        <div>
          <dt>Proxy command</dt>
          <dd>
            <code>npm run dev:api</code>
          </dd>
        </div>
        <div>
          <dt>Full local command</dt>
          <dd>
            <code>npm run dev:all</code>
          </dd>
        </div>
        <div>
          <dt>Fallback</dt>
          <dd>Local synthesis remains active when the proxy is offline.</dd>
        </div>
      </dl>
      <div className="integration-row">
        <KeyRound size={16} />
        <span>Keep API keys out of source control.</span>
      </div>
      <div className="integration-row">
        <Server size={16} />
        <span>The proxy prevents browser-side key exposure.</span>
      </div>
    </section>
  );
}

# The Entangled Dashboard

Standard cards. Standard stones. Living sky. Optional machine oracle. Experimental dream interfaces. One dashboard.

The Entangled Dashboard is a localhost-first cyber-pagan symbolic console where tarot, runes, live astrology context, optional OpenRouter synthesis, and experimental visual interfaces coexist without making AI or canned fortune-cookie output the center of the experience.

## What v0.1 Includes

- React + Vite + TypeScript localhost app.
- Standard tarot tab scaffolded for your existing 78-card JSON.
- Standard Elder Futhark tab scaffolded for your existing 24-rune JSON.
- Shared `ReadingPacket` architecture for tarot, runes, astrology, synthesis, archive, and experimental views.
- Live astrology adapter scaffold, ready to wire to your existing engine or a trusted ephemeris source.
- Optional profile lens adapter, ready for a gitignored `.local.json` profile or existing natal engine.
- Local synthesis that works without any LLM.
- Optional OpenRouter synthesis through a local proxy or browser key.
- Graceful LLM disabled/quota/error states.
- Archive using browser `localStorage`.
- Experimental Wordfall, Abstract Readout, and Speculation Matrix surfaces.

## Quick Start

```bash
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://127.0.0.1:5173`.

## Optional OpenRouter Proxy

Copy `.env.example` to `.env` and add an OpenRouter key.

```bash
npm run dev:api
```

In a second terminal:

```bash
npm run dev
```

Or run both:

```bash
npm run dev:all
```

The app still works when OpenRouter is disabled, quota is gone, or the proxy is not running. In those states it displays local synthesis and keeps the ritual console usable.

## Symbolic Data Policy

This scaffold intentionally does not create tarot meanings, rune meanings, live astrology data, or natal/profile data. Those datasets already exist outside this repo and should be wired through the adapters in `src/features`.

## Core Mantra

JSON is the source. Astrology is the lens. LLM is the synthesizer. UI is the ritual.

## Repo Map

```text
src/features/tarot          Standard tarot engine and UI
src/features/runes          Elder Futhark draw/cast engine and UI
src/features/astrology      Local live-sky context and natal/profile lens
src/features/synthesis      ReadingPacket, source trace, local synthesis
src/features/llm            OpenRouter client, prompt builder, chat-style synthesis
src/features/experimental   Wordfall, abstract readout, speculation matrix
src/features/archive        localStorage reading archive
src/features/settings       OpenRouter and profile settings
server/openrouter-proxy.ts  Optional local OpenRouter proxy
docs/                       Product and architecture notes
```

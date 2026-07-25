import {
  Archive,
  Bot,
  Home,
  Moon,
  Orbit,
  Sparkles,
  SquareStack,
  WandSparkles
} from "lucide-react";

export type AppRouteId =
  | "dashboard"
  | "tarot"
  | "runes"
  | "astrology"
  | "synthesis"
  | "experimental"
  | "archive"
  | "settings";

export type AppRoute = {
  id: AppRouteId;
  label: string;
  poeticLabel: string;
  icon: typeof Home;
  description: string;
};

export const appRoutes: AppRoute[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    poeticLabel: "Altar",
    icon: Home,
    description: "Current console state, quick actions, and source readiness."
  },
  {
    id: "tarot",
    label: "Tarot",
    poeticLabel: "Cards",
    icon: WandSparkles,
    description: "Standard tarot practice using your existing 78-card JSON."
  },
  {
    id: "runes",
    label: "Runes",
    poeticLabel: "Stones",
    icon: SquareStack,
    description: "Standard Elder Futhark practice using your existing rune data."
  },
  {
    id: "astrology",
    label: "Astrology",
    poeticLabel: "Sky",
    icon: Moon,
    description: "Live sky and personal lens adapters waiting for real engine wiring."
  },
  {
    id: "synthesis",
    label: "Synthesis",
    poeticLabel: "Synthesis",
    icon: Bot,
    description: "Local synthesis plus optional OpenRouter mask."
  },
  {
    id: "experimental",
    label: "Experimental",
    poeticLabel: "Matrix",
    icon: Sparkles,
    description: "Wordfall, abstract readout, and speculation matrix remixes."
  },
  {
    id: "archive",
    label: "Archive",
    poeticLabel: "Archive",
    icon: Archive,
    description: "Saved reading packets and source trace review."
  },
  {
    id: "settings",
    label: "Settings",
    poeticLabel: "Settings",
    icon: Orbit,
    description: "Integration notes, LLM settings, and local profile guidance."
  }
];

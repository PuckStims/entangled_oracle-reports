import { appRoutes, type AppRouteId } from "../routes";

type TopNavProps = {
  activeRoute: AppRouteId;
  onRouteChange: (route: AppRouteId) => void;
};

export default function TopNav({ activeRoute, onRouteChange }: TopNavProps) {
  return (
    <nav className="top-nav" aria-label="Primary">
      {appRoutes.map((route) => {
        const Icon = route.icon;
        return (
          <button
            key={route.id}
            type="button"
            className={activeRoute === route.id ? "top-nav__item is-active" : "top-nav__item"}
            onClick={() => onRouteChange(route.id)}
            title={route.description}
          >
            <Icon size={17} />
            <span>{route.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

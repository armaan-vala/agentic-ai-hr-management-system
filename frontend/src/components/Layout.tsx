import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/auth/AuthProvider";

interface NavItem {
  to: string;
  label: string;
  icon: string;
  adminOnly?: boolean;
}

const NAV: NavItem[] = [
  { to: "/dashboard", label: "Home", icon: "🏠" },
  { to: "/chat", label: "Assistant", icon: "💬" },
  { to: "/leaves", label: "Leave", icon: "🌴" },
  { to: "/announcements", label: "Announcements", icon: "📣" },
  { to: "/policies", label: "Policies", icon: "📚" },
  { to: "/employees", label: "Employees", icon: "👥", adminOnly: true },
  { to: "/console", label: "Agent Console", icon: "🤖", adminOnly: true },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

export default function Layout() {
  const { me, signOut } = useAuth();
  const isAdmin = me?.role === "admin";
  const items = NAV.filter((n) => !n.adminOnly || isAdmin);

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 border-r border-border bg-surface flex flex-col">
        <div className="flex items-center gap-2 px-5 h-16 border-b border-border">
          <div className="h-8 w-8 rounded-lg bg-brand flex items-center justify-center font-bold text-black">
            T
          </div>
          <span className="font-bold">TalentOS</span>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {items.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition ${
                  isActive
                    ? "bg-brand-50 text-brand-900"
                    : "text-foreground hover:bg-brand-50"
                }`
              }
            >
              <span>{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-border">
          <div className="px-3 py-2 mb-1">
            <p className="text-sm font-medium truncate">{me?.full_name || me?.email}</p>
            <p className="text-xs text-muted capitalize">{me?.role}</p>
          </div>
          <button
            onClick={signOut}
            className="w-full text-left px-3 py-2 rounded-xl text-sm text-muted hover:bg-brand-50"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 min-w-0 bg-background">
        <Outlet />
      </main>
    </div>
  );
}

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="h-16 border-b border-border flex items-center px-8 bg-surface">
      <div>
        <h1 className="font-semibold">{title}</h1>
        {subtitle && <p className="text-xs text-muted">{subtitle}</p>}
      </div>
    </div>
  );
}

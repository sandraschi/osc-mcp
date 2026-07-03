import { cn } from "@/common/utils";
import {
  Activity,
  Bot,
  Boxes,
  ChevronLeft,
  ChevronRight,
  Cpu,
  HelpCircle,
  LayoutDashboard,
  Map,
  Monitor,
  Music,
  Radio,
  ScrollText,
  Server,
  Settings,
  User,
  Wrench,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();

  const navItems = [
    { path: "/", label: "Overview", icon: LayoutDashboard },
    { path: "/apps", label: "Apps Hub", icon: Server },
    { path: "/status", label: "Status", icon: Activity },
    { path: "/control", label: "Signal Center", icon: Activity },
    { path: "/visualizer", label: "Spectrum", icon: Map },
    { path: "/tools", label: "Tools Hub", icon: Wrench },
    { path: "/chat", label: "Chat Orchestrator", icon: Bot },
    { path: "/help", label: "Help", icon: HelpCircle },
    { path: "/logs", label: "Logs", icon: ScrollText },
  ];

  const targetItems = [
    { label: "Ableton Live", icon: Music, path: "/ableton" },
    { label: "TouchDesigner", icon: Monitor, path: "/touchdesigner" },
    { label: "VRChat", icon: User, path: "/vrchat" },
    { label: "Max/MSP", icon: Radio, path: "/maxmsp" },
    { label: "SuperCollider", icon: Cpu, path: "/supercollider" },
    { label: "VCV Rack", icon: Boxes, path: "/vcvrack" },
  ];

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-slate-800 bg-slate-950/50 backdrop-blur-xl transition-all duration-300 ease-in-out",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex h-16 items-center border-b border-slate-800 px-4">
        <div className="flex items-center gap-2 font-semibold text-slate-100">
          <Activity className="h-6 w-6 text-blue-500" />
          {!collapsed && (
            <span className="animate-in fade-in duration-300">OSC-MCP</span>
          )}
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white",
                isActive ? "bg-slate-800 text-white" : "text-slate-400",
                collapsed ? "justify-center" : "justify-start",
              )}
            >
              <item.icon
                className={cn(
                  "h-5 w-5",
                  !collapsed && "mr-3",
                  isActive && "text-blue-400",
                )}
              />
              {!collapsed && <span>{item.label}</span>}

              {/* Tooltip for collapsed mode */}
              {collapsed && (
                <div className="absolute left-full ml-2 hidden rounded bg-slate-800 px-2 py-1 text-xs text-white group-hover:block z-50 whitespace-nowrap">
                  {item.label}
                </div>
              )}
            </Link>
          );
        })}

        <div className="space-y-1 px-2 pt-4">
          <h2 className="mb-2 px-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Targets
          </h2>
          {targetItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-emerald-500/10 text-emerald-500"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white",
                  collapsed ? "justify-center" : "justify-start",
                )}
              >
                <item.icon
                  className={cn(
                    "h-5 w-5",
                    !collapsed && "mr-3",
                    isActive && "text-emerald-400",
                  )}
                />
                {!collapsed && <span>{item.label}</span>}
                {collapsed && (
                  <div className="absolute left-full ml-2 hidden rounded bg-slate-800 px-2 py-1 text-xs text-white group-hover:block z-50 whitespace-nowrap">
                    {item.label}
                  </div>
                )}
              </Link>
            );
          })}
        </div>

        <div className="space-y-1 px-2 pt-4">
          <Link
            to="/settings"
            className={cn(
              "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white",
              location.pathname === "/settings"
                ? "bg-slate-800 text-white"
                : "text-slate-400",
              collapsed ? "justify-center" : "justify-start",
            )}
          >
            <Settings
              className={cn(
                "h-5 w-5",
                !collapsed && "mr-3",
                location.pathname === "/settings" && "text-blue-400",
              )}
            />
            {!collapsed && <span>Settings</span>}
            {collapsed && (
              <div className="absolute left-full ml-2 hidden rounded bg-slate-800 px-2 py-1 text-xs text-white group-hover:block z-50 whitespace-nowrap">
                Settings
              </div>
            )}
          </Link>
        </div>
      </nav>

      <div className="border-t border-slate-800 p-2">
        <button
          onClick={onToggle}
          className="flex w-full items-center justify-center rounded-md p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <div className="flex items-center w-full">
              <ChevronLeft className="h-5 w-5 mr-3" />
              <span>Collapse</span>
            </div>
          )}
        </button>
      </div>
    </aside>
  );
}

import {
  Activity,
  Beaker,
  Box,
  Cpu,
  Gamepad2,
  GitMerge,
  Guitar,
  Monitor,
  Music,
  Radio,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "../lib/api";

type Health = { status: string; server: string; version: string };
type Stats = {
  targets: Record<string, { status: string; port: number }>;
  messages_sent: number;
  uptime_seconds: number;
  backend_port: number;
};

const TARGET_ICONS: Record<string, React.ElementType> = {
  ableton: Music,
  touchdesigner: Monitor,
  vrchat: Gamepad2,
  maxmsp: Radio,
  supercollider: Beaker,
  vcvrack: Guitar,
};

const BACKOFF_INTERVALS = [1, 2, 4, 8, 16];

export function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    let attempt = 0;

    const fetchHealth = async () => {
      try {
        const [h, s] = await Promise.all([
          fetch(`${API_BASE}/api/v1/health`).then((r) => r.json()),
          fetch(`${API_BASE}/api/v1/stats`).then((r) => r.json()),
        ]);
        if (!cancelled) {
          setHealth(h);
          setStats(s);
          setBackendOk(true);
          setErr(null);
        }
      } catch (e) {
        if (!cancelled) {
          setErr(e instanceof Error ? e.message : String(e));
          setBackendOk(false);
          const delay =
            BACKOFF_INTERVALS[Math.min(attempt, BACKOFF_INTERVALS.length - 1)] *
            1000;
          attempt++;
          setTimeout(fetchHealth, delay);
        }
      }
    };

    fetchHealth();
    return () => {
      cancelled = true;
    };
  }, []);

  const targetCount = stats ? Object.keys(stats.targets).length : 0;
  const onlineTargets = stats
    ? Object.values(stats.targets).filter(
        (t) => t.status === "online" || t.status === "unknown",
      ).length
    : 0;
  const uptime = stats ? `${Math.floor(stats.uptime_seconds / 60)}m` : "--";
  const messages = stats?.messages_sent ?? 0;

  return (
    <div className="space-y-6" data-testid="dashboard">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 blur-[100px] rounded-full" />
        <div className="relative z-10">
          <div className="flex items-center gap-2 text-blue-400 text-xs font-medium uppercase tracking-wider mb-3">
            <Radio size={14} /> Open Sound Control
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            OSC-MCP Orchestrator
          </h1>
          <p className="text-slate-400 max-w-xl text-sm leading-relaxed">
            Universal OSC bridge with MCP tools, real-time routing, and
            multi-target orchestration. Route messages between AI agents and any
            OSC-capable target — DAWs, VJ software, game engines, and modular
            synthesizers — through a single backend on port 10767.
          </p>
          <div className="flex gap-4 mt-4 text-xs text-slate-500">
            <span>{health?.version ?? "--"}</span>
            <span>•</span>
            <span>{targetCount} targets</span>
            <span>•</span>
            <span
              className={
                health?.status === "ok" ? "text-emerald-400" : "text-red-400"
              }
            >
              {health?.status === "ok" ? "Connected" : "Offline"}
            </span>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card
          data-testid="kpi-targets"
          className="border-slate-800 bg-slate-950/50"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Available Targets
            </CardTitle>
            <Radio className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {onlineTargets}/{targetCount}
            </div>
            <p className="text-xs text-slate-400">OSC endpoints configured</p>
          </CardContent>
        </Card>

        <Card
          data-testid="kpi-messages"
          className="border-slate-800 bg-slate-950/50"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Messages Sent
            </CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {messages.toLocaleString()}
            </div>
            <p className="text-xs text-slate-400">Since last reset</p>
          </CardContent>
        </Card>

        <Card
          data-testid="kpi-uptime"
          className="border-slate-800 bg-slate-950/50"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Uptime
            </CardTitle>
            <Cpu className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{uptime}</div>
            <p className="text-xs text-slate-400">Backend runtime</p>
          </CardContent>
        </Card>

        <Card
          data-testid="kpi-backend"
          className="border-slate-800 bg-slate-950/50"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Backend
            </CardTitle>
            <GitMerge className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {health?.status === "ok" ? "Connected" : "Offline"}
            </div>
            <p className="text-xs text-slate-400">
              Port {stats?.backend_port ?? 10767}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Backend Status Dot */}
      <div data-testid="backend-dot" className="flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${backendOk === null ? "bg-gray-500" : backendOk ? "bg-green-500" : "bg-red-500"} animate-pulse`}
        />
        <span className="text-xs text-slate-400">
          {backendOk === null
            ? "Connecting..."
            : backendOk
              ? "Connected"
              : "Offline"}
        </span>
      </div>

      {/* Target Grid */}
      {stats && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white text-sm">OSC Targets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(stats.targets).map(([name, target]) => {
                const Icon = TARGET_ICONS[name] || Box;
                const isOnline =
                  target.status === "online" || target.status === "unknown";
                return (
                  <div
                    key={name}
                    className="flex items-center gap-3 p-3 rounded-lg border border-slate-800 bg-slate-900/30"
                  >
                    <Icon className="h-5 w-5 text-slate-400 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-white capitalize">
                        {name}
                      </p>
                      <p className="text-xs text-slate-500">:{target.port}</p>
                    </div>
                    <span
                      className={`h-2 w-2 rounded-full shrink-0 ${isOnline ? "bg-emerald-500" : "bg-red-500"}`}
                    />
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {err && (
        <Card className="border-red-800/50 bg-red-950/20">
          <CardContent className="p-4 text-xs text-red-400">
            API: {err} — start backend on port 10767 via{" "}
            <code className="text-red-300">
              uv run python -m oscmcp --http --port 10767
            </code>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

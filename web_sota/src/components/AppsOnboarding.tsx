import { CheckCircle2, Circle, Download, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "../lib/api";

interface AppOnboardingInfo {
  key: string;
  display_name: string;
  installed: boolean;
  installed_path: string | null;
  running: boolean;
  process_pid: number | null;
  default_osc_port: number | null;
  license: string;
  platform: string;
  download_url: string;
  testable_here: boolean;
  notes: string;
}

interface OnboardingResponse {
  apps: AppOnboardingInfo[];
  installed_count: number;
  total_count: number;
}

const LICENSE_LABEL: Record<string, string> = {
  free: "Free",
  "commercial-trial": "Trial",
  commercial: "Commercial",
  hardware: "Hardware",
};

export function AppsOnboarding() {
  const [data, setData] = useState<OnboardingResponse | null>(null);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/api/v1/onboarding/apps`)
      .then((r) => r.json())
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch(() => {
        // Dashboard already shows backend-offline state elsewhere
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!data) return null;

  return (
    <Card
      className="border-slate-800 bg-slate-950/50 backdrop-blur-xl"
      data-testid="apps-onboarding"
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white text-base">
            Connected apps — {data.installed_count}/{data.total_count} installed
            on this machine
          </CardTitle>
          <button
            type="button"
            className="text-xs text-slate-400 hover:text-slate-200"
            onClick={() => setCollapsed((c) => !c)}
          >
            {collapsed ? "Show" : "Hide"}
          </button>
        </div>
      </CardHeader>
      {!collapsed && (
        <CardContent className="space-y-2">
          {data.apps.map((app) => (
            <div
              key={app.key}
              data-testid={`onboarding-app-${app.key}`}
              className="flex items-start gap-2 text-sm border-b border-slate-800/60 pb-2 last:border-0 last:pb-0"
            >
              {app.installed ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <Circle className="h-4 w-4 text-slate-600 shrink-0 mt-0.5" />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={
                      app.installed
                        ? "text-slate-300 font-medium"
                        : "text-slate-100 font-medium"
                    }
                  >
                    {app.display_name}
                  </span>
                  <span className="text-[10px] uppercase tracking-wide rounded-full border border-slate-700 px-1.5 py-0.5 text-slate-400">
                    {LICENSE_LABEL[app.license] ?? app.license}
                  </span>
                  {app.installed && app.running && (
                    <span className="text-[10px] uppercase tracking-wide rounded-full border border-emerald-800 bg-emerald-950/40 px-1.5 py-0.5 text-emerald-400">
                      Running
                    </span>
                  )}
                  {!app.testable_here && (
                    <span className="text-[10px] uppercase tracking-wide rounded-full border border-amber-800 bg-amber-950/30 px-1.5 py-0.5 text-amber-400">
                      Not available on this OS
                    </span>
                  )}
                </div>
                {!app.installed && (
                  <p className="text-xs text-slate-500 mt-0.5">{app.notes}</p>
                )}
                {app.installed && app.installed_path && (
                  <p className="text-xs text-slate-600 font-mono mt-0.5 truncate">
                    {app.installed_path}
                  </p>
                )}
              </div>
              {!app.installed && app.testable_here && (
                <a
                  href={app.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 shrink-0"
                >
                  <Download className="h-3 w-3" /> Get it
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          ))}
          <p className="text-xs text-slate-500 pt-2">
            See{" "}
            <a
              href="https://github.com/sandraschi/osc-mcp/blob/main/docs/ONBOARDING.md"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300"
            >
              docs/ONBOARDING.md
            </a>{" "}
            for per-app OSC-enablement steps — most of these apps don't have OSC
            turned on by default.
          </p>
        </CardContent>
      )}
    </Card>
  );
}

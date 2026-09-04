import { ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "../lib/api";

export function ApiDocsPage() {
  const backendUrl = API_BASE;
  return (
    <div className="space-y-6" data-testid="api-docs-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">API Documentation</h1>
          <p className="text-sm text-slate-400 mt-1">
            FastAPI auto-generated docs for the OSC-MCP REST API
          </p>
        </div>
        <a
          href={`${backendUrl}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300"
        >
          <ExternalLink className="h-4 w-4" /> Open in browser
        </a>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-sm text-slate-200">Health</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-400 space-y-1">
            <code className="block text-emerald-400">GET /api/v1/health</code>
            <code className="block text-emerald-400">
              GET /api/v1/diagnostics
            </code>
            <code className="block text-emerald-400">
              GET /api/v1/capabilities
            </code>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-sm text-slate-200">Tools</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-400 space-y-1">
            <code className="block text-blue-400">GET /api/v1/tools/</code>
            <code className="block text-amber-400">
              POST /api/v1/tools/call
            </code>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-sm text-slate-200">Discovery</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-400 space-y-1">
            <code className="block text-purple-400">GET /api/v1/skills/</code>
            <code className="block text-purple-400">
              {"GET /api/v1/skills/{name}"}
            </code>
            <code className="block text-purple-400">
              GET /api/v1/llm/discover
            </code>
          </CardContent>
        </Card>
      </div>
      <div
        className="rounded-lg border border-slate-800 bg-slate-950/30 overflow-hidden"
        style={{ height: "70vh" }}
      >
        <iframe
          src={`${backendUrl}/docs`}
          className="w-full h-full border-0"
          title="Swagger UI"
          style={{ filter: "invert(0.9) hue-rotate(180deg)" }}
          onError={(e) => {
            (e.target as HTMLElement).style.display = "none";
          }}
        />
      </div>
    </div>
  );
}

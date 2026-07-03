import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Activity, ExternalLink, Search, Server } from "lucide-react";
import { useEffect, useState } from "react";

interface AppRegistryInfo {
  name: string;
  port: number;
  description: string;
  status: "running" | "stopped" | "unknown";
}

export function Apps() {
  const [apps, setApps] = useState<AppRegistryInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    fetchApps();
  }, []);

  const fetchApps = async () => {
    setLoading(true);
    try {
      // Fleet Discovery endpoint from mcp-central-docs
      const response = await fetch("http://localhost:10794/api/registry");
      if (response.ok) {
        const data = await response.json();
        const formattedApps = Object.entries(
          data as Record<string, { port: number; description?: string }>,
        ).map(([name, info]) => ({
          name,
          port: info.port,
          description: info.description || `MCP Server Webapp for ${name}`,
          status: "unknown" as const,
        }));
        setApps(formattedApps);
      } else {
        throw new Error("Failed to fetch fleet registry");
      }
    } catch (error) {
      console.error("Error fetching registry:", error);
      // Fallback mock data
      setApps([
        {
          name: "osc-mcp",
          port: 10766,
          description: "OSC and signal routing hub",
          status: "running",
        },
        {
          name: "virtualization-mcp",
          port: 10700,
          description: "VM operations",
          status: "unknown",
        },
        {
          name: "meta-mcp",
          port: 10719,
          description: "Meta fleet operations",
          status: "running",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filteredApps = apps.filter(
    (app) =>
      app.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.description.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Apps Hub
          </h1>
          <p className="text-slate-400">Fleet Discovery & Control</p>
        </div>
        <Badge
          variant="outline"
          className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
        >
          <Server className="w-3 h-3 mr-2 inline" />
          Fleet Connected
        </Badge>
      </div>

      <div className="flex items-center space-x-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search webapps..."
            className="pl-9 bg-slate-900 border-slate-800 text-white placeholder:text-slate-400"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2 text-slate-400">
            <Activity className="h-5 w-5 animate-pulse" />
            <span>Discovering fleet...</span>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredApps.map((app) => (
            <Card
              key={app.name}
              className="border-slate-800 bg-slate-950/50 hover:bg-slate-900/80 transition-colors group"
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-lg font-semibold text-white flex items-center">
                    <Server className="w-5 h-5 mr-2 text-blue-500" />
                    {app.name}
                  </CardTitle>
                  <a
                    href={`http://localhost:${app.port}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-500 hover:text-white transition-colors"
                    aria-label={`Open ${app.name} in new tab`}
                    title={`Open ${app.name}`}
                  >
                    <ExternalLink className="h-4 w-4" aria-hidden="true" />
                  </a>
                </div>
                <CardDescription className="text-slate-400 line-clamp-2">
                  {app.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between mt-2">
                  <Badge
                    variant="secondary"
                    className="bg-slate-800 text-slate-300"
                  >
                    Port: {app.port}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!loading && filteredApps.length === 0 && (
        <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-slate-800 rounded-lg bg-slate-950/20">
          <Server className="h-10 w-10 text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-300">No apps found</h3>
          <p className="text-sm text-slate-500">
            Try adjusting your search query or ensure the Fleet Registry is
            available.
          </p>
        </div>
      )}
    </div>
  );
}

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Activity, Server, ShieldCheck, Wifi } from "lucide-react";

export function Status() {
  return (
    <div className="flex flex-col space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          System Status
        </h2>
        <p className="text-slate-400">
          Target availability and connection health
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-300">
              Backend Connection
            </CardTitle>
            <ShieldCheck className="h-4 w-4 ml-auto text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">Connected</div>
            <p className="text-xs text-slate-500 mt-1">Active</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-300">
              Active Targets
            </CardTitle>
            <Activity className="h-4 w-4 ml-auto text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">2</div>
            <p className="text-xs text-slate-500 mt-1">Available to route</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-300">
              OSC Traffic
            </CardTitle>
            <Wifi className="h-4 w-4 ml-auto text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">45 msgs/s</div>
            <p className="text-xs text-slate-500 mt-1">Tx/Rx combined</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-300">
              Fleet Discovery
            </CardTitle>
            <Server className="h-4 w-4 ml-auto text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">Online</div>
            <p className="text-xs text-slate-500 mt-1">Port 10794 responding</p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Target Endpoints</CardTitle>
          <CardDescription className="text-slate-400">
            Known mapping of OSC receivers
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { name: "Ableton Live", port: 9000, status: "available" },
            { name: "VCV Rack", port: 10001, status: "available" },
            { name: "TouchDesigner", port: 9002, status: "unavailable" },
            { name: "VRChat", port: 9003, status: "unavailable" },
          ].map((t) => (
            <div
              key={t.name}
              className="flex items-center justify-between p-3 bg-slate-900/50 rounded-md border border-slate-800"
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-2 h-2 rounded-full ${t.status === "available" ? "bg-emerald-500" : "bg-slate-600"}`}
                ></div>
                <span className="text-sm font-medium text-slate-300">
                  {t.name}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs font-mono text-slate-500">
                  Port {t.port}
                </span>
                <Badge
                  variant="outline"
                  className={
                    t.status === "available"
                      ? "border-emerald-500/30 text-emerald-400"
                      : "border-slate-700 text-slate-500"
                  }
                >
                  {t.status}
                </Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

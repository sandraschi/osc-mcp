import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Activity, Cpu, Terminal } from "lucide-react";
import { useState } from "react";

export function SuperCollider() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const callManager = async (
    action: string,
    kwargs: Record<string, unknown> = {},
  ) => {
    setLoading(true);
    setStatus({ status: "sending", message: `Executing ${action}...` });
    try {
      const response = await fetch("http://localhost:10767/api/v1/tools/call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "supercollider_manager",
          arguments: { action, ...kwargs },
        }),
      });
      const data = await response.json();

      let resultStatus = data;
      if (
        data &&
        data.content &&
        Array.isArray(data.content) &&
        data.content.length > 0
      ) {
        try {
          if (data.content[0].type === "text") {
            resultStatus = JSON.parse(data.content[0].text);
          }
        } catch {
          resultStatus = { status: "raw", message: data.content[0].text };
        }
      }

      setStatus(resultStatus);
    } catch (error) {
      console.error("Error calling SuperCollider manager:", error);
      setStatus({ status: "error", message: String(error) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">SuperCollider</h1>
          {status && (
            <Badge
              variant={
                status.status === "error"
                  ? "destructive"
                  : status.status === "success"
                    ? "default"
                    : "secondary"
              }
              className="font-mono text-xs"
            >
              {String(status.status)}
            </Badge>
          )}
        </div>
        <p className="text-muted-foreground italic text-sm">
          Algorithmic Composition & Audio Synthesis (Port 57110/57120)
        </p>
      </div>

      {status && (
        <Card className="bg-slate-950 border-slate-800">
          <CardHeader className="py-3">
            <CardTitle className="text-sm font-mono flex items-center gap-2 text-slate-400">
              <Terminal className="w-4 h-4" />
              Command Output
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap overflow-auto max-h-40">
              {JSON.stringify(status, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Synth Nodes</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12 Active</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Load</CardTitle>
            <Activity className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4.2%</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Fast Node Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 border rounded-lg bg-slate-500/5">
              <span className="font-mono text-sm">node [1000] - \sine</span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => callManager("free_node", { node_id: 1000 })}
                  disabled={loading}
                >
                  Free
                </Button>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg bg-slate-500/5">
              <span className="font-mono text-sm">node [1001] - \saw</span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => callManager("free_node", { node_id: 1001 })}
                  disabled={loading}
                >
                  Free
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Global Synth Params</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm font-mono">
                <span>amp</span>
                <span>0.25</span>
              </div>
              <Slider
                defaultValue={[25]}
                max={100}
                onValueCommit={(val) =>
                  callManager("set_node_parameter", {
                    node_id: 1000,
                    parameter: "amp",
                    value: val[0] / 100,
                  })
                }
              />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm font-mono">
                <span>freq</span>
                <span>440 Hz</span>
              </div>
              <Slider
                defaultValue={[440]}
                max={2000}
                min={20}
                onValueCommit={(val) =>
                  callManager("set_node_parameter", {
                    node_id: 1000,
                    parameter: "freq",
                    value: val[0],
                  })
                }
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

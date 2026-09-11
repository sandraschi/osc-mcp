import { Terminal } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";

export function SuperCollider() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [nodeId, setNodeId] = useState(1000);

  const callManager = async (
    operation: string,
    kwargs: Record<string, unknown> = {},
  ) => {
    setLoading(true);
    setStatus({ status: "sending", message: `Executing ${operation}...` });
    try {
      const response = await fetch("http://localhost:10767/api/v1/tools/call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "supercollider_manager",
          arguments: { operation, ...kwargs },
        }),
      });
      const data = await response.json();

      let resultStatus = data;
      if (
        data?.content &&
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

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Node Control</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-xs text-muted-foreground">
              scsynth has no default reply convention this tool queries, so
              there's no live node/CPU list to show -- enter the node ID of a
              synth you already booted (via sclang or a .scd script).
            </p>
            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold uppercase text-muted-foreground shrink-0">
                Node ID
              </label>
              <Input
                type="number"
                value={nodeId}
                onChange={(e) => setNodeId(Number(e.target.value))}
                className="font-mono"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => callManager("free_node", { node_id: nodeId })}
                disabled={loading}
              >
                Free
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Set Node Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-xs text-muted-foreground">
              Sends to node {nodeId} (set above).
            </p>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase text-muted-foreground">
                amp
              </label>
              <Slider
                defaultValue={[25]}
                max={100}
                onValueCommit={(val) =>
                  callManager("set_node_parameter", {
                    node_id: nodeId,
                    parameter: "amp",
                    value: val[0] / 100,
                  })
                }
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase text-muted-foreground">
                freq
              </label>
              <Slider
                defaultValue={[440]}
                max={2000}
                min={20}
                onValueCommit={(val) =>
                  callManager("set_node_parameter", {
                    node_id: nodeId,
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

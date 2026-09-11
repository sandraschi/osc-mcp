import { Terminal, Zap } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";

export function MaxMSP() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

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
          name: "maxmsp_manager",
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
      console.error("Error calling MaxMSP manager:", error);
      setStatus({ status: "error", message: String(error) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">
            Max/MSP & Pure Data
          </h1>
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
          Visual Programming & Patching Environment
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

      <Card>
        <CardHeader>
          <CardTitle>Global Messaging</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-xs text-muted-foreground">
            Max has no fixed OSC namespace or reply convention -- these messages
            send one-way. There is no live DSP/telemetry readout to show without
            a patch that scripts its own reply.
          </p>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="secondary"
              className="font-mono"
              onClick={() => callManager("send_bang", { receiver: "global" })}
              disabled={loading}
            >
              <Zap className="mr-2 h-4 w-4" /> bang
            </Button>
            <Button
              variant="secondary"
              className="font-mono"
              onClick={() => callManager("reset_state", { component: "all" })}
              disabled={loading}
            >
              reset
            </Button>
          </div>
          <div className="space-y-2 pt-4 border-t">
            <label className="text-xs font-semibold uppercase text-muted-foreground">
              Global Float
            </label>
            <div className="flex items-center gap-4">
              <Slider
                defaultValue={[0]}
                max={100}
                className="flex-1"
                onValueCommit={(val) =>
                  callManager("set_float", {
                    receiver: "global",
                    value: val[0] / 100,
                  })
                }
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

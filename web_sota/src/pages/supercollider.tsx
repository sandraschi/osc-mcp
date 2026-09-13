import {
  Activity,
  ExternalLink,
  Layers,
  RefreshCw,
  Sliders,
  Terminal,
} from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { API_BASE } from "@/lib/api";

interface ServerStatus {
  status: string;
  num_ugens?: number;
  num_synths?: number;
  num_groups?: number;
  num_synthdefs?: number;
  avg_cpu_percent?: number;
  peak_cpu_percent?: number;
  nominal_sample_rate?: number;
  actual_sample_rate?: number;
  message?: string;
}

export function SuperCollider() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [nodeId, setNodeId] = useState(1000);
  const [groupId, setGroupId] = useState(100);
  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);

  const callManager = async (
    operation: string,
    kwargs: Record<string, unknown> = {},
  ) => {
    setLoading(true);
    setStatus({ status: "sending", message: `Executing ${operation}...` });
    try {
      const response = await fetch(`${API_BASE}/api/v1/tools/call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "supercollider_manager",
          arguments: { operation, ...kwargs },
        }),
      });
      const data = await response.json();

      // The real /api/v1/tools/call response nests the actual tool result one
      // level deeper than this parsing used to check (data.result.content /
      // data.result.structured_content, not data.content) - this made the
      // Command Output panel show the raw double-wrapped envelope instead of
      // the clean result, and left this page unable to read num_synths etc.
      // out of a "status" call at all (confirmed live against a real scsynth).
      let resultStatus = data;
      if (data?.result?.structured_content) {
        resultStatus = data.result.structured_content;
      } else if (
        data?.result?.content &&
        Array.isArray(data.result.content) &&
        data.result.content.length > 0
      ) {
        try {
          if (data.result.content[0].type === "text") {
            resultStatus = JSON.parse(data.result.content[0].text);
          }
        } catch {
          resultStatus = {
            status: "raw",
            message: data.result.content[0].text,
          };
        }
      }

      setStatus(resultStatus);
      return resultStatus;
    } catch (error) {
      console.error("Error calling SuperCollider manager:", error);
      const errResult = { status: "error", message: String(error) };
      setStatus(errResult);
      return errResult;
    } finally {
      setLoading(false);
    }
  };

  const refreshServerStatus = async () => {
    setStatusLoading(true);
    const result = await callManager("status");
    setServerStatus(result as ServerStatus);
    setStatusLoading(false);
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
          Controlled via scsynth's native OSC protocol — port 57110
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

      <Tabs defaultValue="synth" className="space-y-4">
        <TabsList className="bg-slate-900/50 border border-slate-800">
          <TabsTrigger
            value="synth"
            className="data-[state=active]:bg-slate-800"
          >
            <Sliders className="w-4 h-4 mr-2" />
            Synth Control
          </TabsTrigger>
          <TabsTrigger
            value="groups"
            className="data-[state=active]:bg-slate-800"
          >
            <Layers className="w-4 h-4 mr-2" />
            Groups
          </TabsTrigger>
          <TabsTrigger
            value="status"
            className="data-[state=active]:bg-slate-800"
          >
            <Activity className="w-4 h-4 mr-2" />
            Server Status
          </TabsTrigger>
          <TabsTrigger
            value="setup"
            className="data-[state=active]:bg-slate-800"
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Setup
          </TabsTrigger>
        </TabsList>

        {/* SYNTH CONTROL */}
        <TabsContent value="synth" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Node Control</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-xs text-muted-foreground">
                Enter the node ID of a synth you already booted (via sclang or a
                .scd script) — <code>def_name</code> must already be a loaded
                SynthDef; this tool can't compile one for you.
              </p>
              <div className="flex items-center gap-2">
                <Label className="text-xs font-semibold uppercase text-muted-foreground shrink-0">
                  Node ID
                </Label>
                <Input
                  type="number"
                  value={nodeId}
                  onChange={(e) => setNodeId(Number(e.target.value))}
                  className="font-mono w-32"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => callManager("free_node", { node_id: nodeId })}
                  disabled={loading}
                >
                  Free Node
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Set Node Controls</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-xs text-muted-foreground">
                Sends <code>/n_set</code> to node {nodeId} — only works if that
                SynthDef actually exposes controls named "amp"/"freq".
              </p>
              <div className="space-y-2">
                <Label className="text-xs font-semibold uppercase text-muted-foreground">
                  amp
                </Label>
                <Slider
                  defaultValue={[25]}
                  max={100}
                  onValueCommit={(val) =>
                    callManager("set_control", {
                      node_id: nodeId,
                      control_name: "amp",
                      value: val[0] / 100,
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-semibold uppercase text-muted-foreground">
                  freq
                </Label>
                <Slider
                  defaultValue={[440]}
                  max={2000}
                  min={20}
                  onValueCommit={(val) =>
                    callManager("set_control", {
                      node_id: nodeId,
                      control_name: "freq",
                      value: val[0],
                    })
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* GROUPS */}
        <TabsContent value="groups" className="space-y-4">
          <Card className="border-slate-800 bg-slate-950/30">
            <CardContent className="pt-4 text-xs text-slate-500">
              Groups and synth nodes share one ID space in scsynth — a group is
              just a node that can contain other nodes. <code>/g_freeAll</code>{" "}
              frees everything inside a group but leaves the (now empty) group
              itself in place.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="h-4 w-4" />
                Group Control
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2">
                <Label className="text-xs font-semibold uppercase text-muted-foreground shrink-0">
                  Group ID
                </Label>
                <Input
                  type="number"
                  value={groupId}
                  onChange={(e) => setGroupId(Number(e.target.value))}
                  className="font-mono w-32"
                />
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={() =>
                    callManager("create_group", { node_id: groupId })
                  }
                  disabled={loading}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  Create Group
                </Button>
                <Button
                  onClick={() =>
                    callManager("free_group", { node_id: groupId })
                  }
                  disabled={loading}
                  variant="destructive"
                >
                  Free All In Group
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SERVER STATUS */}
        <TabsContent value="status" className="space-y-4">
          <Card className="border-slate-800 bg-slate-950/30">
            <CardContent className="pt-4 text-xs text-slate-500">
              scsynth is the one app in this fleet whose OSC protocol is
              genuinely bidirectional — <code>/status</code> gets a real{" "}
              <code>/status.reply</code> back, not a fire-and-forget guess.
              Every number below is live, not fabricated.
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Live Server Status</CardTitle>
              <Button
                size="sm"
                variant="secondary"
                onClick={refreshServerStatus}
                disabled={statusLoading}
              >
                <RefreshCw
                  className={`w-4 h-4 mr-2 ${statusLoading ? "animate-spin" : ""}`}
                />
                Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {!serverStatus ? (
                <p className="text-sm text-slate-500 italic">
                  Click Refresh to query the real server status.
                </p>
              ) : serverStatus.status === "error" ? (
                <p className="text-sm text-red-400">{serverStatus.message}</p>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-xs text-slate-500 uppercase">
                      Synths
                    </div>
                    <div className="text-2xl font-bold">
                      {serverStatus.num_synths}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 uppercase">
                      Groups
                    </div>
                    <div className="text-2xl font-bold">
                      {serverStatus.num_groups}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 uppercase">
                      UGens
                    </div>
                    <div className="text-2xl font-bold">
                      {serverStatus.num_ugens}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 uppercase">
                      SynthDefs
                    </div>
                    <div className="text-2xl font-bold">
                      {serverStatus.num_synthdefs}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 uppercase">
                      Avg CPU
                    </div>
                    <div className="text-2xl font-bold">
                      {serverStatus.avg_cpu_percent?.toFixed(2)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 uppercase">
                      Peak CPU
                    </div>
                    <div className="text-2xl font-bold">
                      {serverStatus.peak_cpu_percent?.toFixed(2)}%
                    </div>
                  </div>
                  <div className="col-span-2">
                    <div className="text-xs text-slate-500 uppercase">
                      Sample Rate (nominal / actual)
                    </div>
                    <div className="text-lg font-mono">
                      {serverStatus.nominal_sample_rate?.toFixed(0)} Hz /{" "}
                      {serverStatus.actual_sample_rate?.toFixed(2)} Hz
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* SETUP */}
        <TabsContent value="setup" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Getting scsynth running</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-300">
              <p>
                SuperCollider is really two separate programs:{" "}
                <strong>sclang</strong> (the language you write code in) and{" "}
                <strong>scsynth</strong> (the audio server that actually answers
                OSC). Running the IDE alone does not start scsynth — every
                control on this page is a silent no-op until scsynth is actually
                listening.
              </p>
              <ol className="list-decimal list-inside space-y-2">
                <li>
                  Easiest: open the SuperCollider IDE and evaluate{" "}
                  <code>s.boot</code> (or just start the IDE — it boots the
                  default server automatically in most configurations).
                </li>
                <li>
                  Or run scsynth directly from a terminal — it refuses to start
                  without an explicit port: <code>scsynth.exe -u 57110</code>
                </li>
                <li>
                  Load at least one SynthDef via sclang before using{" "}
                  <strong>Synth Control</strong> above —{" "}
                  <code>create_synth</code> can trigger an already-loaded
                  SynthDef, it can't compile one.
                </li>
              </ol>
              <p className="text-slate-500">
                Port <strong>57110</strong> is scsynth's real convention (the
                default any <code>Server.default</code> in sclang binds to) —
                not <strong>57120</strong>, which is sclang's own separate
                default port, a very common mix-up.
              </p>
              <p className="text-slate-500">
                <code>/status</code> replies are suppressed if the server is in{" "}
                <code>/dumpOSC</code> mode — worth checking if Server Status
                keeps timing out.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

import { MessageSquare, Terminal, Zap } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";

export function VRChat() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [chatMessage, setChatMessage] = useState("");

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
          name: "vrchat_manager",
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
      console.error("Error calling VRChat manager:", error);
      setStatus({ status: "error", message: String(error) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">VRChat</h1>
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
          Social VR & Avatar Protocol (Port 9000)
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
            <CardTitle>Avatar Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm font-mono">
                <span>/avatar/parameters/Voice</span>
                <span>0.85</span>
              </div>
              <Slider
                defaultValue={[85]}
                max={100}
                onValueCommit={(val) =>
                  callManager("set_parameter", {
                    param_name: "Voice",
                    value: val[0] / 100,
                  })
                }
              />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm font-mono">
                <span>/avatar/parameters/Viseme</span>
                <span>4</span>
              </div>
              <Slider
                defaultValue={[4]}
                max={15}
                step={1}
                onValueCommit={(val) =>
                  callManager("set_parameter", {
                    param_name: "Viseme",
                    value: val[0],
                  })
                }
              />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm font-mono">
                <span>/avatar/parameters/Mood</span>
                <span>0.5</span>
              </div>
              <Slider
                defaultValue={[50]}
                max={100}
                onValueCommit={(val) =>
                  callManager("set_parameter", {
                    param_name: "Mood",
                    value: val[0] / 100,
                  })
                }
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Input Simulation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-xs text-muted-foreground">
              VRChat's real Input OSC surface only covers movement/camera/
              action buttons -- there's no OSC address for menu, sit, mute, or
              reset. Only what VRChat actually listens for is offered.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={() =>
                  callManager("input", { input_name: "Jump", value: 1 })
                }
                disabled={loading}
              >
                <Zap className="h-3 w-3" />
                Jump
              </Button>
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={() => callManager("afk_toggle", { enabled: true })}
                disabled={loading}
              >
                <Zap className="h-3 w-3" />
                AFK
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Chatbox</CardTitle>
          <MessageSquare className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            placeholder="Type a message to send to your VRChat chatbox..."
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            className="font-mono"
          />
          <Button
            className="w-full"
            onClick={() => callManager("send_chat", { message: chatMessage })}
            disabled={loading || !chatMessage}
          >
            Send to Chatbox
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

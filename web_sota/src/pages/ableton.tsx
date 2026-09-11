import {
  Circle,
  ExternalLink,
  Music,
  Play,
  Radio,
  Sliders,
  Square,
  Terminal,
  Volume2,
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

export function Ableton() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  // Ableton Live keeps no read-back channel through AbletonOSC's write-only
  // addresses this tool uses - there is no way to know how many tracks,
  // scenes, or clips actually exist in the user's live set. Every field
  // below is something the user types in, not something we discovered.
  const [trackIndex, setTrackIndex] = useState(0);
  const [clipSlot, setClipSlot] = useState(0);
  const [sceneId, setSceneId] = useState(0);
  const [lastBpm, setLastBpm] = useState<number | null>(null);
  const [lastVolume, setLastVolume] = useState<number | null>(null);
  const [lastPan, setLastPan] = useState<number | null>(null);

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
          name: "ableton_manager",
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
      console.error("Error calling Ableton manager:", error);
      setStatus({ status: "error", message: String(error) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">Ableton Live</h1>
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
          Controlled via the AbletonOSC remote script — port 11000
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

      <Tabs defaultValue="transport" className="space-y-4">
        <TabsList className="bg-slate-900/50 border border-slate-800">
          <TabsTrigger
            value="transport"
            className="data-[state=active]:bg-slate-800"
          >
            <Play className="w-4 h-4 mr-2" />
            Transport
          </TabsTrigger>
          <TabsTrigger
            value="mixer"
            className="data-[state=active]:bg-slate-800"
          >
            <Sliders className="w-4 h-4 mr-2" />
            Mixer
          </TabsTrigger>
          <TabsTrigger
            value="scenes"
            className="data-[state=active]:bg-slate-800"
          >
            <Radio className="w-4 h-4 mr-2" />
            Scenes &amp; Clips
          </TabsTrigger>
          <TabsTrigger
            value="setup"
            className="data-[state=active]:bg-slate-800"
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Setup
          </TabsTrigger>
        </TabsList>

        {/* TRANSPORT */}
        <TabsContent value="transport" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Transport Control</CardTitle>
            </CardHeader>
            <CardContent className="flex gap-4">
              <Button
                variant="outline"
                size="icon"
                className="h-12 w-12 text-emerald-500 border-emerald-500/20 bg-emerald-500/10 hover:bg-emerald-500/20"
                onClick={() => callManager("play")}
                disabled={loading}
              >
                <Play className="h-6 w-6 fill-current" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="h-12 w-12 text-slate-400 border-slate-500/20 bg-slate-500/10 hover:bg-slate-500/20"
                onClick={() => callManager("stop")}
                disabled={loading}
              >
                <Square className="h-6 w-6 fill-current" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="h-12 w-12 text-red-500 border-red-500/20 bg-red-500/10 hover:bg-red-500/20"
                onClick={() => callManager("trigger_record")}
                disabled={loading}
                title="Trigger session-mode record (/live/song/trigger_session_record)"
              >
                <Circle className="h-6 w-6 fill-current" />
              </Button>
              <Button
                variant="outline"
                onClick={() => callManager("stop_all_clips")}
                disabled={loading}
              >
                Stop All Clips
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tempo</CardTitle>
              <Music className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between mb-2">
                <div className="text-2xl font-bold">
                  {lastBpm !== null ? `${lastBpm.toFixed(1)} BPM` : "— BPM"}
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => callManager("tap_tempo")}
                  disabled={loading}
                >
                  Tap Tempo
                </Button>
              </div>
              <Slider
                defaultValue={[128]}
                max={200}
                min={60}
                step={1}
                onValueCommit={(val) => {
                  setLastBpm(val[0]);
                  callManager("set_tempo", { bpm: val[0] });
                }}
              />
              <p className="text-xs text-slate-500 mt-2">
                Shows the last value sent, not a live reading — AbletonOSC's
                write addresses don't report Live's actual current tempo back.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* MIXER */}
        <TabsContent value="mixer" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Volume2 className="h-4 w-4" />
                Track Mixer
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="track-index">Track index (0-based)</Label>
                <Input
                  id="track-index"
                  type="number"
                  min={0}
                  value={trackIndex}
                  onChange={(e) => setTrackIndex(Number(e.target.value))}
                  className="w-32"
                />
                <p className="text-xs text-slate-500">
                  There's no track list to pick from — AbletonOSC has no
                  read-back for this tool to discover your set's actual tracks.
                  Type the 0-based index of the track you want.
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Volume</span>
                  <span>
                    {lastVolume !== null ? lastVolume.toFixed(2) : "—"}
                  </span>
                </div>
                <Slider
                  defaultValue={[80]}
                  max={100}
                  onValueCommit={(val) => {
                    const volume = val[0] / 100;
                    setLastVolume(volume);
                    callManager("set_volume", {
                      track_index: trackIndex,
                      volume,
                    });
                  }}
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Pan</span>
                  <span>{lastPan !== null ? lastPan.toFixed(2) : "—"}</span>
                </div>
                <Slider
                  defaultValue={[50]}
                  max={100}
                  onValueCommit={(val) => {
                    const pan = (val[0] - 50) / 50;
                    setLastPan(pan);
                    callManager("set_pan", { track_index: trackIndex, pan });
                  }}
                />
              </div>

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() =>
                    callManager("set_mute", {
                      track_index: trackIndex,
                      mute: true,
                    })
                  }
                  disabled={loading}
                >
                  Mute
                </Button>
                <Button
                  variant="outline"
                  onClick={() =>
                    callManager("set_mute", {
                      track_index: trackIndex,
                      mute: false,
                    })
                  }
                  disabled={loading}
                >
                  Unmute
                </Button>
                <Button
                  variant="outline"
                  onClick={() =>
                    callManager("set_solo", {
                      track_index: trackIndex,
                      solo: true,
                    })
                  }
                  disabled={loading}
                >
                  Solo
                </Button>
                <Button
                  variant="outline"
                  onClick={() =>
                    callManager("set_solo", {
                      track_index: trackIndex,
                      solo: false,
                    })
                  }
                  disabled={loading}
                >
                  Unsolo
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SCENES & CLIPS */}
        <TabsContent value="scenes" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Scene Launch</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-end gap-3">
                <div className="space-y-1">
                  <Label htmlFor="scene-id">Scene index (0-based)</Label>
                  <Input
                    id="scene-id"
                    type="number"
                    min={0}
                    value={sceneId}
                    onChange={(e) => setSceneId(Number(e.target.value))}
                    className="w-32"
                  />
                </div>
                <Button
                  onClick={() =>
                    callManager("fire_scene", { scene_id: sceneId })
                  }
                  disabled={loading}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  Fire Scene
                </Button>
              </div>
              <p className="text-xs text-slate-500">
                Same caveat as the mixer — this tool can't discover how many
                scenes your live set actually has. Fire an index that doesn't
                exist and AbletonOSC will simply ignore it.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Clip Control</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-end gap-3 flex-wrap">
                <div className="space-y-1">
                  <Label htmlFor="clip-track">Track index</Label>
                  <Input
                    id="clip-track"
                    type="number"
                    min={0}
                    value={trackIndex}
                    onChange={(e) => setTrackIndex(Number(e.target.value))}
                    className="w-28"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="clip-slot">Clip slot</Label>
                  <Input
                    id="clip-slot"
                    type="number"
                    min={0}
                    value={clipSlot}
                    onChange={(e) => setClipSlot(Number(e.target.value))}
                    className="w-28"
                  />
                </div>
                <Button
                  onClick={() =>
                    callManager("play_clip", {
                      track_index: trackIndex,
                      clip_slot: clipSlot,
                    })
                  }
                  disabled={loading}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  <Play className="h-4 w-4 mr-2" />
                  Fire
                </Button>
                <Button
                  onClick={() =>
                    callManager("stop_clip", {
                      track_index: trackIndex,
                      clip_slot: clipSlot,
                    })
                  }
                  disabled={loading}
                  variant="destructive"
                >
                  <Square className="h-4 w-4 mr-2" />
                  Stop
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SETUP */}
        <TabsContent value="setup" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Ableton Live has no native OSC support</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-300">
              <p>
                Every control on this page depends on the third-party{" "}
                <a
                  href="https://github.com/ideoforms/AbletonOSC"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-1"
                >
                  AbletonOSC
                  <ExternalLink className="h-3 w-3" />
                </a>{" "}
                remote script. Without it, every button above sends a UDP packet
                into the void — no error, no response, nothing happens in Live.
              </p>
              <ol className="list-decimal list-inside space-y-2">
                <li>
                  Download AbletonOSC and copy its folder into Live's Remote
                  Scripts directory (the exact path depends on your OS and Live
                  version — see the project's own README).
                </li>
                <li>Restart Ableton Live.</li>
                <li>
                  Open Preferences → Link/Tempo/MIDI, and select{" "}
                  <strong>AbletonOSC</strong> as a Control Surface.
                </li>
              </ol>
              <p>
                Once selected, AbletonOSC listens on a fixed port —{" "}
                <strong>11000</strong> — which is why that's the default port
                here, unlike VCV Rack's OSCelot bridge, which has no fixed
                default at all.
              </p>
              <p className="text-slate-500">
                There's no in-Live settings toggle for this the way VRChat has
                Settings → OSC → Enabled — Ableton itself has zero OSC
                awareness. AbletonOSC <em>is</em> the entire OSC layer.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

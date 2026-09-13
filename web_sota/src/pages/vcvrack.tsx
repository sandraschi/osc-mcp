import {
  Activity,
  Database,
  Download,
  ExternalLink,
  MousePointerClick,
  Package,
  Sliders,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { API_BASE } from "@/lib/api";

interface Preset {
  name: string;
  description: string;
  modules: number;
  cables: number;
}

export function VCVRack() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [presetsLoading, setPresetsLoading] = useState(true);

  const [slotId, setSlotId] = useState(1);
  const [faderValue, setFaderValue] = useState(0.5);
  const [reaperTempo, setReaperTempo] = useState(120);

  useEffect(() => {
    const fetchPresets = async () => {
      try {
        const r = await fetch(`${API_BASE}/api/v1/vcv-presets/`);
        if (r.ok) {
          const data: { presets: Preset[] } = await r.json();
          setPresets(data.presets);
        }
      } catch {
        setPresets([]);
      } finally {
        setPresetsLoading(false);
      }
    };
    void fetchPresets();
  }, []);

  const callManager = async (
    operation: string,
    args: Record<string, any> = {},
  ) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/tools/call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "vcv_manager",
          arguments: { operation, ...args },
        }),
      });
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error("Error calling vcv_manager:", error);
      setStatus({ error: String(error) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            VCV Rack
          </h2>
          <p className="text-slate-400">Modular Synthesis Control Surface</p>
        </div>
        <Badge
          variant="outline"
          className="px-3 py-1 border-blue-500/20 text-blue-400 bg-blue-500/10"
        >
          <Database className="w-3 h-3 justify-center inline mr-2" />
          OSCelot port (no fixed default)
        </Badge>
      </div>

      <Tabs defaultValue="presets" className="space-y-4">
        <TabsList className="bg-slate-900/50 border border-slate-800">
          <TabsTrigger
            value="presets"
            className="data-[state=active]:bg-slate-800"
          >
            <Package className="w-4 h-4 mr-2" />
            Presets
          </TabsTrigger>
          <TabsTrigger
            value="parameters"
            className="data-[state=active]:bg-slate-800"
          >
            <Sliders className="w-4 h-4 mr-2" />
            Parameter Control
          </TabsTrigger>
          <TabsTrigger
            value="setup"
            className="data-[state=active]:bg-slate-800"
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Setup
          </TabsTrigger>
        </TabsList>

        {/* PRESETS */}
        <TabsContent value="presets" className="space-y-4">
          <Card className="border-slate-800 bg-slate-950/30">
            <CardContent className="pt-4 text-xs text-slate-500">
              VCV Rack has no OSC capability to build a patch remotely — no "add
              module" or "wire cable" address exists in OSCelot's real protocol.
              These are real, pre-generated <code>.vcv</code> files instead:
              download one and open it in Rack via File → Open.
            </CardContent>
          </Card>

          {presetsLoading ? (
            <p className="text-sm text-slate-500 italic">Loading presets…</p>
          ) : presets.length === 0 ? (
            <p className="text-sm text-slate-500 italic">
              No presets found — is the backend's `patches/` depot reachable?
            </p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {presets.map((p) => (
                <Card key={p.name} className="border-slate-800 bg-slate-950/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-white text-base font-mono">
                      {p.name}
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                      {p.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex items-center justify-between">
                    <div className="flex gap-2 text-xs text-slate-500">
                      <Badge variant="secondary" className="bg-slate-800">
                        {p.modules} modules
                      </Badge>
                      <Badge variant="secondary" className="bg-slate-800">
                        {p.cables} cables
                      </Badge>
                    </div>
                    <a
                      href={`${API_BASE}/api/v1/vcv-presets/${p.name}/download`}
                      download={`${p.name}.vcv`}
                    >
                      <Button
                        size="sm"
                        className="bg-emerald-600 hover:bg-emerald-700"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                    </a>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* PARAMETER CONTROL */}
        <TabsContent value="parameters" className="space-y-4">
          <Card className="border-slate-800 bg-slate-950/30">
            <CardContent className="pt-4 text-xs text-slate-500">
              OSCelot's real protocol only understands three message types on
              slots you've already mapped by hand in its own UI —{" "}
              <code>/fader</code>, <code>/encoder</code>, <code>/button</code>.
              There is no way to address a VCV module/parameter directly; the
              "slot Id" below is whatever number OSCelot assigned when you
              mapped that control, not a module ID.
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white text-lg flex items-center gap-2">
                <Sliders className="h-4 w-4" />
                Fader Slot
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="slot-id">OSCelot mapping slot Id</Label>
                <Input
                  id="slot-id"
                  type="number"
                  min={1}
                  value={slotId}
                  onChange={(e) => setSlotId(Number(e.target.value))}
                  className="w-32"
                />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-slate-300">
                  <span>Fader value</span>
                  <span>{faderValue.toFixed(3)}</span>
                </div>
                <Slider
                  value={[faderValue * 100]}
                  max={100}
                  onValueChange={(val) => setFaderValue(val[0] / 100)}
                  onValueCommit={(val) =>
                    callManager("set_parameter", {
                      module_id: slotId,
                      value: val[0] / 100,
                    })
                  }
                />
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white text-lg flex items-center gap-2">
                <MousePointerClick className="h-4 w-4" />
                Button Slot
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Button
                disabled={loading}
                onClick={() => callManager("trigger", { module_id: slotId })}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Zap className="w-4 h-4 mr-2" />
                Press slot {slotId}
              </Button>
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white text-lg">
                REAPER Tempo Sync
              </CardTitle>
              <CardDescription className="text-slate-400">
                Sends REAPER's tempo to a mapped fader slot, normalized against
                120 BPM = 1.0 — a crude convention, no better one is documented
                anywhere.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-end gap-3">
              <div className="space-y-1">
                <Label htmlFor="reaper-tempo">Tempo (BPM)</Label>
                <Input
                  id="reaper-tempo"
                  type="number"
                  min={20}
                  max={999}
                  value={reaperTempo}
                  onChange={(e) => setReaperTempo(Number(e.target.value))}
                  className="w-32"
                />
              </div>
              <Button
                disabled={loading}
                variant="outline"
                onClick={() =>
                  callManager("sync_reaper_tempo", {
                    module_id: slotId,
                    reaper_tempo: reaperTempo,
                  })
                }
              >
                Sync to slot {slotId}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SETUP */}
        <TabsContent value="setup" className="space-y-4">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white">
                VCV Rack has no native OSC support
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-300">
              <p>
                Every control on this page depends on the community{" "}
                <a
                  href="https://github.com/The-Modular-Mind/oscelot"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-1"
                >
                  OSCelot
                  <ExternalLink className="h-3 w-3" />
                </a>{" "}
                module, installed from the VCV Library (needs a free VCV
                account) and patched into your rack.
              </p>
              <ol className="list-decimal list-inside space-y-2">
                <li>
                  Search "OSCelot" in the VCV Library, click Add, then Rack's
                  own Library menu → "Update all".
                </li>
                <li>Drag OSCelot into your patch from the module browser.</li>
                <li>
                  <strong>Click the Send and Receive toggles</strong> — they
                  default OFF (status dots render orange). Until both are green,
                  every OSC message to OSCelot is silently dropped with no error
                  anywhere, including Rack's own log.
                </li>
                <li>
                  Map a parameter: click OSCelot's module-map button then the
                  target module (maps every exposed parameter at once), or
                  right-click a single knob/button in Rack and choose "OSCelot:
                  Map".
                </li>
              </ol>
              <p className="text-amber-400/90">
                Quirk worth knowing: the first message to a freshly-mapped slot
                only creates and types it (locks it to fader/encoder/ button) —
                it does not move the parameter yet. Send the same message a
                second time to actually apply the value.
              </p>
              <p className="text-slate-500">
                There is no fixed OSCelot port — it's whatever you configure in
                OSCelot's own UI, unlike AbletonOSC's fixed 11000.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white text-lg min-h-[1.5rem] flex items-center">
            <Activity className="w-4 h-4 mr-2 text-slate-400" />
            Command Output
          </CardTitle>
        </CardHeader>
        <CardContent>
          {status ? (
            <pre className="text-xs text-emerald-400 bg-black/60 p-4 rounded-md overflow-x-auto border border-white/5">
              {JSON.stringify(status, null, 2)}
            </pre>
          ) : (
            <p className="text-sm text-slate-500 italic">
              No commands executed yet.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

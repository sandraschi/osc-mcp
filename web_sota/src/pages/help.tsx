import { Card, CardContent } from "@/components/ui/card";
import {
  Activity,
  Beaker,
  Cpu,
  Gamepad2,
  Guitar,
  MessageCircle,
  Monitor,
  Music,
  Radio,
} from "lucide-react";
import { useState } from "react";

type Tab =
  | "overview"
  | "ableton"
  | "touchdesigner"
  | "vrchat"
  | "maxmsp"
  | "supercollider"
  | "vcvrack"
  | "control"
  | "chat";

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "overview", label: "Overview", icon: Activity },
  { id: "ableton", label: "Ableton Live", icon: Music },
  { id: "touchdesigner", label: "TouchDesigner", icon: Monitor },
  { id: "vrchat", label: "VRChat", icon: Gamepad2 },
  { id: "maxmsp", label: "Max/MSP", icon: Radio },
  { id: "supercollider", label: "SuperCollider", icon: Beaker },
  { id: "vcvrack", label: "VCV Rack", icon: Guitar },
  { id: "control", label: "Control", icon: Cpu },
  { id: "chat", label: "Chat", icon: MessageCircle },
];

const APP_CONTENT: Record<
  Tab,
  {
    title: string;
    desc: string;
    addr: string;
    port: number;
    notes: string[];
  } | null
> = {
  overview: null,
  ableton: {
    title: "Ableton Live",
    desc: "OSC bridge for Ableton Live — clip launch, scene control, volume/pan, transport, device parameters. Requires LiveOSC or a custom OSC device.",
    addr: "127.0.0.1",
    port: 11000,
    notes: [
      "Enable OSC remote control in Live's Preferences > Link, Tempo & MIDI",
      "Install LiveOSC if your Live version does not include native OSC out",
      "Use the ableton_manager MCP tool with actions like 'launch_clip', 'set_volume', 'start_playback'",
    ],
  },
  touchdesigner: {
    title: "TouchDesigner",
    desc: "OSC messaging for Derivative TouchDesigner — parameter modulation, channel swaps, DATs, TOPs. Ideal for real-time visual feedback loops.",
    addr: "127.0.0.1",
    port: 12000,
    notes: [
      "Create a DAT > OSC In CHOP in your TD network to receive",
      "Default listen port is 12000; configure in TD's OSC In CHOP",
      "Use touchdesigner_manager for parameter modulation and channel ops",
    ],
  },
  vrchat: {
    title: "VRChat",
    desc: "OSC control for VRChat avatars — avatar parameters, tracking, toggles, floats, ints, and bools. Full VRChat OSC API v1 support.",
    addr: "127.0.0.1",
    port: 9000,
    notes: [
      "Enable OSC in VRChat: Menu > Options > OSC > Enabled",
      "VRChat listens on 127.0.0.1:9000 by default",
      "Use vrchat_manager to set avatar parameters, trigger animations",
    ],
  },
  maxmsp: {
    title: "Max/MSP",
    desc: "OSC bridge for Cycling '74 Max/MSP — send from Max's udpreceive, route to any Max patch parameter.",
    addr: "127.0.0.1",
    port: 13000,
    notes: [
      "Use Max's [udpreceive 13000] object to receive messages",
      "Route with [route /ableton, /touchdesigner, etc.] for multi-target",
      "Use maxmsp_manager to send parameter updates and triggers",
    ],
  },
  supercollider: {
    title: "SuperCollider",
    desc: "OSC messaging for SuperCollider — interact with sclang, SynthDefs, NodeProxies, and patterns via OSC.",
    addr: "127.0.0.1",
    port: 57120,
    notes: [
      "SuperCollider's default language port is 57120",
      "Use OSCFunc in sclang to register responders for incoming messages",
      "Use supercollider_manager for synth control and pattern manipulation",
    ],
  },
  vcvrack: {
    title: "VCV Rack",
    desc: "OSC bridge for VCV Rack modular synth environment — module parameters, cable patching and CV/gate via MIDI CC.",
    addr: "127.0.0.1",
    port: 14000,
    notes: [
      "Install the OSC plugin from VCV Rack's Library",
      "Create an OSC Send module to transmit parameter changes",
      "Use vcvrack_manager for parameter automation and patch recall",
    ],
  },
  control: {
    title: "Control Surface",
    desc: "Central OSC control and monitoring — generic OSC send/receive, MIDI CC, system-wide parameter mapping.",
    addr: "127.0.0.1",
    port: 10767,
    notes: [
      "Use the Control page for manual OSC/MIDI message dispatch",
      "Monitor live OSC traffic in the Visualizer",
      "Configurable routing between any input and any output target",
    ],
  },
  chat: {
    title: "Chat Orchestrator",
    desc: "Natural language OSC automation — describe what you want in plain English and the MCP sampling engine plans and executes the OSC sequence.",
    addr: "127.0.0.1",
    port: 10767,
    notes: [
      "Example: 'fade volume to 0 over 3 seconds' generates an OSC workflow",
      "Multi-step workflows validated before execution",
      "Requires a sampling-capable MCP client (Claude Desktop, Cursor)",
    ],
  },
};

export function Help() {
  const [tab, setTab] = useState<Tab>("overview");
  const app = APP_CONTENT[tab];

  const tabBar = (
    <div className="flex gap-1 bg-slate-900/50 p-1 rounded-xl border border-slate-800 w-fit flex-wrap">
      {TABS.map((t) => {
        const Icon = t.icon;
        return (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-3 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${tab === t.id ? "bg-slate-800 text-white shadow-sm" : "text-slate-400 hover:text-white"}`}
          >
            <Icon size={14} /> {t.label}
          </button>
        );
      })}
    </div>
  );

  return (
    <div className="flex flex-col space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          System Guide
        </h2>
        <p className="text-slate-400">
          OSC-MCP reference — targets, addresses, ports, and usage
        </p>
      </div>

      {tabBar}

      {tab === "overview" ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card className="border-slate-800 bg-slate-950/50 col-span-full">
            <CardContent className="p-6">
              <h3 className="text-lg font-medium text-white mb-2">OSC-MCP</h3>
              <p className="text-slate-300 text-sm leading-relaxed">
                OSC-MCP is a universal OSC (Open Sound Control) bridge exposed
                as MCP tools and a web dashboard. It routes messages between MCP
                clients and any OSC-capable target: DAWs, VJ software, game
                engines, modular synthesizers, and research environments. Use
                the Chat Orchestrator for natural language automation or the
                individual app pages for per-target control.
              </p>
            </CardContent>
          </Card>
          {TABS.filter((t) => t.id !== "overview").map((t) => {
            const Icon = t.icon;
            const a = APP_CONTENT[t.id];
            return (
              <Card
                key={t.id}
                className="border-slate-800 bg-slate-950/50 cursor-pointer hover:border-slate-700 transition-colors"
                onClick={() => setTab(t.id)}
              >
                <CardContent className="p-5">
                  <div className="flex items-center gap-3 mb-2">
                    <Icon className="h-5 w-5 text-blue-400" />
                    <h3 className="font-medium text-white">
                      {a?.title || t.label}
                    </h3>
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-2">
                    {a?.desc || ""}
                  </p>
                  <div className="mt-2 text-xs text-slate-500">
                    {a?.addr}:{a?.port}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : app ? (
        <div className="space-y-4">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardContent className="p-6">
              <h3 className="text-lg font-medium text-white mb-1">
                {app.title}
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                {app.addr}:{app.port}
              </p>
              <p className="text-slate-300 text-sm leading-relaxed mb-4">
                {app.desc}
              </p>
              <h4 className="text-sm font-medium text-white mb-2">Notes</h4>
              <ul className="space-y-1.5">
                {app.notes.map((n, i) => (
                  <li key={i} className="text-xs text-slate-400 flex gap-2">
                    <span className="text-blue-400 shrink-0">•</span>
                    <span>{n}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
          <Card className="border-slate-800 bg-slate-950/50">
            <CardContent className="p-4">
              <p className="text-xs text-slate-500">
                Backend must be running on port 10767. Start with{" "}
                <code className="text-blue-400">
                  uv run python -m oscmcp --http --port 10767
                </code>
              </p>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}

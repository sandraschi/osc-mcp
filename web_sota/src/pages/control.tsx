import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Power, RefreshCw, Sliders, Radio, Link as LinkIcon, Trash2, Plus, AlertCircle, Play } from "lucide-react";

export function Control() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // OSCQuery State
  const [services, setServices] = useState<any[]>([]);
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [parameters, setParameters] = useState<any[]>([]);
  const [paramInputValues, setParamInputValues] = useState<Record<string, string>>({});

  // MIDI Bridge State
  const [midiPorts, setMidiPorts] = useState<{ inputs: string[]; outputs: string[] }>({ inputs: [], outputs: [] });
  const [midiBridgeStatus, setMidiBridgeStatus] = useState<any>(null);
  const [midiMappings, setMidiMappings] = useState<{ midi_to_osc: any[]; osc_to_midi: any[] }>({ midi_to_osc: [], osc_to_midi: [] });
  
  // MIDI Bridge Form State
  const [bridgeForm, setBridgeForm] = useState({
    oscHost: "127.0.0.1",
    oscPort: "8000",
    midiIn: "",
    midiOut: ""
  });
  
  // MIDI Mapping Form State
  const [mappingForm, setMappingForm] = useState({
    direction: "midi_to_osc",
    oscAddress: "/live/volume",
    midiType: "control_change",
    channel: "1",
    control: "1",
    minVal: "0.0",
    maxVal: "1.0"
  });

  // Reactive Triggers State
  const [triggers, setTriggers] = useState<any[]>([]);
  const [triggerForm, setTriggerForm] = useState({
    pattern: "/live/beat",
    tool: "send_osc_message",
    argsTemplate: '{\n  "host": "127.0.0.1",\n  "port": 9000,\n  "address": "/resolume/beat",\n  "values": ["$0"]\n}'
  });

  const callTool = async (name: string, args: Record<string, any> = {}) => {
    try {
      const response = await fetch("http://localhost:10767/api/v1/tools/call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, arguments: args }),
      });
      const data = await response.json();
      if (data.status === "error") {
        throw new Error(data.message || "Failed to execute tool");
      }
      return data;
    } catch (err: any) {
      console.error(`Error calling ${name}:`, err);
      throw err;
    }
  };

  // Fetch all initial data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch OSCQuery services
      const servicesRes = await callTool("oscquery_list_services");
      if (servicesRes && servicesRes.services) {
        setServices(servicesRes.services);
      }

      // Fetch MIDI Ports
      const portsRes = await callTool("get_midi_ports");
      if (portsRes && portsRes.status === "success") {
        setMidiPorts({ inputs: portsRes.inputs, outputs: portsRes.outputs });
        // Set default dropdown selections if ports found
        setBridgeForm(prev => ({
          ...prev,
          midiIn: prev.midiIn || portsRes.inputs[0] || "",
          midiOut: prev.midiOut || portsRes.outputs[0] || ""
        }));
      }

      // Fetch Active MIDI Mappings (fails gracefully if bridge not started)
      try {
        const mappingsRes = await callTool("get_midi_mappings");
        if (mappingsRes && mappingsRes.status === "success") {
          setMidiMappings({
            midi_to_osc: mappingsRes.midi_to_osc || [],
            osc_to_midi: mappingsRes.osc_to_midi || []
          });
          setMidiBridgeStatus({ active: true });
        } else {
          setMidiBridgeStatus({ active: false });
        }
      } catch {
        setMidiBridgeStatus({ active: false });
      }

      // Fetch Reactive Triggers
      const triggersRes = await callTool("get_reactive_triggers");
      if (triggersRes && triggersRes.triggers) {
        setTriggers(triggersRes.triggers);
      }

    } catch (err: any) {
      setError(err.message || "Failed to sync dashboard state");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Fetch parameters for selected OSCQuery service
  const handleSelectService = async (name: string) => {
    setSelectedService(name);
    setLoading(true);
    try {
      const res = await callTool("oscquery_get_parameters", { service_name: name });
      if (res && res.parameters) {
        setParameters(res.parameters);
      }
    } catch (err: any) {
      setError(`Failed to fetch parameters for ${name}: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Set Parameter via OSCQuery helper client
  const handleSetParameter = async (path: string, service: any) => {
    const rawVal = paramInputValues[path];
    if (rawVal === undefined || rawVal === "") return;

    setLoading(true);
    try {
      // We directly send the OSC message to target service host/port
      await callTool("send_osc_message", {
        host: service.host,
        port: service.osc_port,
        address: path,
        args: [isNaN(Number(rawVal)) ? rawVal : Number(rawVal)]
      });
      
      // Update local state value for reflection
      setParameters(prev =>
        prev.map(p => (p.path === path ? { ...p, value: rawVal } : p))
      );
      
      // Clear input
      setParamInputValues(prev => ({ ...prev, [path]: "" }));
    } catch (err: any) {
      setError(`Failed to send OSC parameter: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Start MIDI Bridge
  const handleStartBridge = async () => {
    setLoading(true);
    try {
      const res = await callTool("start_midi_bridge", {
        osc_host: bridgeForm.oscHost,
        osc_port: Number(bridgeForm.oscPort),
        midi_in: bridgeForm.midiIn || undefined,
        midi_out: bridgeForm.midiOut || undefined
      });
      if (res.status === "success") {
        setMidiBridgeStatus({ active: true, ...res });
        fetchData();
      }
    } catch (err: any) {
      setError(`Failed to start MIDI bridge: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Stop MIDI Bridge
  const handleStopBridge = async () => {
    setLoading(true);
    try {
      await callTool("stop_midi_bridge");
      setMidiBridgeStatus({ active: false });
      setMidiMappings({ midi_to_osc: [], osc_to_midi: [] });
    } catch (err: any) {
      setError(`Failed to stop MIDI bridge: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Add MIDI Mapping
  const handleAddMapping = async () => {
    setLoading(true);
    try {
      const res = await callTool("add_midi_mapping", {
        direction: mappingForm.direction,
        osc_address: mappingForm.oscAddress,
        midi_type: mappingForm.midiType,
        channel: Number(mappingForm.channel),
        control: Number(mappingForm.control),
        min_val: Number(mappingForm.minVal),
        max_val: Number(mappingForm.maxVal)
      });
      if (res.status === "success") {
        fetchData();
      }
    } catch (err: any) {
      setError(`Failed to add MIDI mapping: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Add Reactive Trigger
  const handleAddTrigger = async () => {
    setLoading(true);
    try {
      let resolvedJson;
      try {
        resolvedJson = JSON.parse(triggerForm.argsTemplate);
      } catch {
        throw new Error("Invalid JSON formatting in argument template");
      }

      const res = await callTool("register_reactive_trigger", {
        address_pattern: triggerForm.pattern,
        target_tool: triggerForm.tool,
        args_template: resolvedJson
      });
      if (res.status === "success") {
        fetchData();
      }
    } catch (err: any) {
      setError(`Failed to add trigger: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Remove Reactive Trigger
  const handleRemoveTrigger = async (pattern: string) => {
    setLoading(true);
    try {
      await callTool("remove_reactive_trigger", { address_pattern: pattern });
      fetchData();
    } catch (err: any) {
      setError(`Failed to remove trigger: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            OSC Control Center
          </h2>
          <p className="text-slate-400">
            Intelligent signal routing, MIDI loopback bridges, and dynamic parameter mapping
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={fetchData}
            disabled={loading}
            className="border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-slate-200"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${loading && "animate-spin"}`} />
            Sync Dashboard
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-red-500/20 bg-red-500/10 text-red-400">
          <CardContent className="flex items-center gap-3 p-4">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <p className="text-sm font-medium">{error}</p>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setError(null)}
              className="ml-auto hover:bg-red-500/20 text-red-400"
            >
              Dismiss
            </Button>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="oscquery" className="space-y-4">
        <TabsList className="bg-slate-900/50 border border-slate-800">
          <TabsTrigger value="oscquery" className="data-[state=active]:bg-slate-800">
            <Sliders className="w-4 h-4 mr-2" />
            OSCQuery Discovery
          </TabsTrigger>
          <TabsTrigger value="midibridge" className="data-[state=active]:bg-slate-800">
            <Radio className="w-4 h-4 mr-2" />
            MIDI Bridge
          </TabsTrigger>
          <TabsTrigger value="triggers" className="data-[state=active]:bg-slate-800">
            <LinkIcon className="w-4 h-4 mr-2" />
            Reactive Triggers
          </TabsTrigger>
        </TabsList>

        {/* OSCQUERY DISCOVERY CONTENT */}
        <TabsContent value="oscquery" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Services List */}
            <Card className="border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="text-white text-md">Discovered Devices</CardTitle>
                <CardDescription className="text-slate-400">OSCQuery nodes found via Zeroconf</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {services.length === 0 ? (
                  <p className="text-sm text-slate-500 italic p-4 text-center">Scanning for devices on network...</p>
                ) : (
                  services.map(s => (
                    <div
                      key={s.name}
                      onClick={() => handleSelectService(s.name)}
                      className={`flex flex-col p-3 rounded-md border cursor-pointer transition-colors ${
                        selectedService === s.name
                          ? "border-blue-500 bg-blue-500/10 text-white"
                          : "border-slate-800 bg-slate-900/20 text-slate-300 hover:bg-slate-900/50"
                      }`}
                    >
                      <span className="font-semibold">{s.name}</span>
                      <span className="text-xs text-slate-400 mt-1">Host: {s.host}:{s.osc_port}</span>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Parameters List */}
            <Card className="md:col-span-2 border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="text-white text-md">
                  {selectedService ? `Parameter Tree: ${selectedService}` : "Device Parameters"}
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Select a discovered device to inspect and manipulate parameter trees.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!selectedService ? (
                  <p className="text-sm text-slate-500 italic p-8 text-center">No device selected.</p>
                ) : parameters.length === 0 ? (
                  <p className="text-sm text-slate-500 italic p-8 text-center">No parameters exposed by this node.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-850 font-mono text-sm">
                      <thead>
                        <tr className="text-slate-400 text-left">
                          <th className="pb-3 pr-4">Path</th>
                          <th className="pb-3 px-4">Type</th>
                          <th className="pb-3 px-4">Value</th>
                          <th className="pb-3 pl-4">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-900 text-slate-300">
                        {parameters.map(p => (
                          <tr key={p.path} className="hover:bg-slate-900/20">
                            <td className="py-3 pr-4 font-semibold text-slate-200">{p.path}</td>
                            <td className="py-3 px-4">
                              <Badge className="bg-slate-800 text-slate-300 border-0">{p.type}</Badge>
                            </td>
                            <td className="py-3 px-4 text-emerald-400">{JSON.stringify(p.value) ?? "null"}</td>
                            <td className="py-3 pl-4">
                              <div className="flex gap-2">
                                <Input
                                  size={10}
                                  placeholder="Value..."
                                  value={paramInputValues[p.path] || ""}
                                  onChange={e =>
                                    setParamInputValues(prev => ({ ...prev, [p.path]: e.target.value }))
                                  }
                                  className="h-8 w-24 bg-slate-900 border-slate-800 text-xs text-white"
                                />
                                <Button
                                  size="sm"
                                  onClick={() =>
                                    handleSetParameter(
                                      p.path,
                                      services.find(s => s.name === selectedService)
                                    )
                                  }
                                  className="h-8 bg-blue-600 hover:bg-blue-700 text-white text-xs"
                                >
                                  Send
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* MIDI BRIDGE CONTENT */}
        <TabsContent value="midibridge" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Bridge Controller */}
            <Card className="border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="text-white text-md">Bridge Engine Connection</CardTitle>
                <CardDescription className="text-slate-400">Initialize virtual or physical MIDI port mapping</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-slate-300">Status</span>
                    {midiBridgeStatus?.active ? (
                      <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Running</Badge>
                    ) : (
                      <Badge className="bg-slate-800 text-slate-400 border-0">Inactive</Badge>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="oscHost" className="text-slate-400 text-xs">Target OSC Host</Label>
                  <Input
                    id="oscHost"
                    value={bridgeForm.oscHost}
                    onChange={e => setBridgeForm(prev => ({ ...prev, oscHost: e.target.value }))}
                    className="bg-slate-900 border-slate-800 text-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="oscPort" className="text-slate-400 text-xs">Target OSC Port</Label>
                  <Input
                    id="oscPort"
                    value={bridgeForm.oscPort}
                    onChange={e => setBridgeForm(prev => ({ ...prev, oscPort: e.target.value }))}
                    className="bg-slate-900 border-slate-800 text-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="midiIn" className="text-slate-400 text-xs">MIDI Input Interface</Label>
                  <select
                    id="midiIn"
                    value={bridgeForm.midiIn}
                    onChange={e => setBridgeForm(prev => ({ ...prev, midiIn: e.target.value }))}
                    className="w-full h-10 px-3 rounded-md bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none"
                  >
                    {midiPorts.inputs.length === 0 ? (
                      <option value="">No MIDI inputs detected</option>
                    ) : (
                      midiPorts.inputs.map(p => <option key={p} value={p}>{p}</option>)
                    )}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="midiOut" className="text-slate-400 text-xs">MIDI Output Interface</Label>
                  <select
                    id="midiOut"
                    value={bridgeForm.midiOut}
                    onChange={e => setBridgeForm(prev => ({ ...prev, midiOut: e.target.value }))}
                    className="w-full h-10 px-3 rounded-md bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none"
                  >
                    {midiPorts.outputs.length === 0 ? (
                      <option value="">No MIDI outputs detected</option>
                    ) : (
                      midiPorts.outputs.map(p => <option key={p} value={p}>{p}</option>)
                    )}
                  </select>
                </div>

                {midiBridgeStatus?.active ? (
                  <Button
                    onClick={handleStopBridge}
                    variant="destructive"
                    className="w-full"
                  >
                    <Power className="w-4 h-4 mr-2" /> Stop Loopback Bridge
                  </Button>
                ) : (
                  <Button
                    onClick={handleStartBridge}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    <Play className="w-4 h-4 mr-2" /> Start Loopback Bridge
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Mappings Setup */}
            <Card className="md:col-span-2 border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="text-white text-md">Mapping Configurator</CardTitle>
                <CardDescription className="text-slate-400">Map MIDI CC knobs and notes directly to OSC paths</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-md border border-slate-850 bg-slate-900/10">
                  <div className="space-y-2">
                    <Label className="text-slate-450 text-xs">Mapping Type</Label>
                    <select
                      value={mappingForm.direction}
                      onChange={e => setMappingForm(prev => ({ ...prev, direction: e.target.value }))}
                      className="w-full h-10 px-3 rounded bg-slate-900 border border-slate-800 text-sm text-slate-200"
                    >
                      <option value="midi_to_osc">MIDI CC {"->"} OSC Path</option>
                      <option value="osc_to_midi">OSC Path {"->"} MIDI CC/Note</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-slate-450 text-xs">OSC Path</Label>
                    <Input
                      value={mappingForm.oscAddress}
                      onChange={e => setMappingForm(prev => ({ ...prev, oscAddress: e.target.value }))}
                      className="bg-slate-900 border-slate-800 text-white"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-slate-450 text-xs">MIDI CC / Note</Label>
                    <Input
                      type="number"
                      value={mappingForm.control}
                      onChange={e => setMappingForm(prev => ({ ...prev, control: e.target.value }))}
                      className="bg-slate-900 border-slate-800 text-white"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-slate-450 text-xs">Channel (1-16)</Label>
                    <Input
                      type="number"
                      value={mappingForm.channel}
                      onChange={e => setMappingForm(prev => ({ ...prev, channel: e.target.value }))}
                      className="bg-slate-900 border-slate-800 text-white"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-slate-450 text-xs">Min Range</Label>
                    <Input
                      value={mappingForm.minVal}
                      onChange={e => setMappingForm(prev => ({ ...prev, minVal: e.target.value }))}
                      className="bg-slate-900 border-slate-800 text-white"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-slate-450 text-xs">Max Range</Label>
                    <Input
                      value={mappingForm.maxVal}
                      onChange={e => setMappingForm(prev => ({ ...prev, maxVal: e.target.value }))}
                      className="bg-slate-900 border-slate-800 text-white"
                    />
                  </div>

                  <Button
                    onClick={handleAddMapping}
                    disabled={!midiBridgeStatus?.active}
                    className="sm:col-span-3 bg-emerald-600 hover:bg-emerald-700 text-white mt-2"
                  >
                    <Plus className="w-4 h-4 mr-2" /> Add Mapping Rule
                  </Button>
                </div>

                <div className="space-y-4">
                  <h3 className="text-white text-sm font-semibold">Active Mappings List</h3>
                  <div className="overflow-x-auto max-h-60">
                    <table className="min-w-full divide-y divide-slate-850 font-mono text-xs">
                      <thead>
                        <tr className="text-slate-400 text-left">
                          <th className="pb-2">Direction</th>
                          <th className="pb-2 px-2">MIDI Msg</th>
                          <th className="pb-2 px-2">Ch / Control</th>
                          <th className="pb-2 px-2">OSC Address</th>
                          <th className="pb-2 pl-2">Range</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-900 text-slate-300">
                        {midiMappings.midi_to_osc.map((m, idx) => (
                          <tr key={`m2o-${idx}`}>
                            <td className="py-2 text-emerald-400">MIDI {"->"} OSC</td>
                            <td className="py-2 px-2">{m.midi_type}</td>
                            <td className="py-2 px-2">Ch: {m.channel} / CC: {m.control}</td>
                            <td className="py-2 px-2 font-semibold text-slate-200">{m.osc_address}</td>
                            <td className="py-2 pl-2">[{m.osc_range?.join(", ")}]</td>
                          </tr>
                        ))}
                        {midiMappings.osc_to_midi.map((m, idx) => (
                          <tr key={`o2m-${idx}`}>
                            <td className="py-2 text-blue-400">OSC {"->"} MIDI</td>
                            <td className="py-2 px-2">{m.midi_type}</td>
                            <td className="py-2 px-2">Ch: {m.channel} / CC: {m.control}</td>
                            <td className="py-2 px-2 font-semibold text-slate-200">{m.osc_address}</td>
                            <td className="py-2 pl-2">[{m.midi_range?.join(", ")}]</td>
                          </tr>
                        ))}
                        {midiMappings.midi_to_osc.length === 0 && midiMappings.osc_to_midi.length === 0 && (
                          <tr>
                            <td colSpan={5} className="py-4 text-slate-500 italic text-center">No active mappings configured.</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* REACTIVE TRIGGERS CONTENT */}
        <TabsContent value="triggers" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Create Trigger Form */}
            <Card className="border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="text-white text-md">Register Reactive Trigger</CardTitle>
                <CardDescription className="text-slate-400">Fire MCP tools dynamically upon incoming OSC matching rules</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="pattern" className="text-slate-400 text-xs">Incoming Address Pattern (Glob)</Label>
                  <Input
                    id="pattern"
                    value={triggerForm.pattern}
                    onChange={e => setTriggerForm(prev => ({ ...prev, pattern: e.target.value }))}
                    className="bg-slate-900 border-slate-800 text-white font-mono"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tool" className="text-slate-400 text-xs">Target MCP Tool to Call</Label>
                  <select
                    id="tool"
                    value={triggerForm.tool}
                    onChange={e => setTriggerForm(prev => ({ ...prev, tool: e.target.value }))}
                    className="w-full h-10 px-3 rounded bg-slate-900 border border-slate-800 text-sm text-white"
                  >
                    <option value="send_osc_message">send_osc_message</option>
                    <option value="execute_osc_workflow">execute_osc_workflow</option>
                    <option value="test_osc_echo">test_osc_echo</option>
                    <option value="trigger_vrchat_haptic_lfo">trigger_vrchat_haptic_lfo</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="argsTemplate" className="text-slate-400 text-xs">Arguments Template (JSON)</Label>
                  <textarea
                    id="argsTemplate"
                    rows={6}
                    value={triggerForm.argsTemplate}
                    onChange={e => setTriggerForm(prev => ({ ...prev, argsTemplate: e.target.value }))}
                    className="w-full p-3 rounded-md bg-slate-900 border border-slate-800 text-xs text-emerald-400 font-mono focus:outline-none focus:border-slate-700"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">
                    Use <code className="text-emerald-500">$0</code>, <code className="text-emerald-500">$1</code> to map incoming parameters.
                  </p>
                </div>

                <Button
                  onClick={handleAddTrigger}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <Plus className="w-4 h-4 mr-2" /> Add Rule
                </Button>
              </CardContent>
            </Card>

            {/* Triggers List */}
            <Card className="md:col-span-2 border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="text-white text-md">Active Trigger Rules</CardTitle>
                <CardDescription className="text-slate-400">Trigger-action bindings active on the OSC listener</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-850 font-mono text-sm">
                    <thead>
                      <tr className="text-slate-400 text-left">
                        <th className="pb-3 pr-4">OSC Glob Pattern</th>
                        <th className="pb-3 px-4">Action Tool</th>
                        <th className="pb-3 px-4">Arg Schema</th>
                        <th className="pb-3 pl-4 text-right">Delete</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-900 text-slate-300">
                      {triggers.map((t, idx) => (
                        <tr key={idx} className="hover:bg-slate-900/20">
                          <td className="py-3 pr-4 font-semibold text-slate-200">{t.pattern}</td>
                          <td className="py-3 px-4 text-emerald-400">{t.tool}</td>
                          <td className="py-3 px-4 max-w-xs overflow-hidden text-ellipsis">
                            <span className="text-xs text-slate-500">{JSON.stringify(t.template)}</span>
                          </td>
                          <td className="py-3 pl-4 text-right">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleRemoveTrigger(t.pattern)}
                              className="text-red-400 hover:text-red-500 hover:bg-red-500/10"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                      {triggers.length === 0 && (
                        <tr>
                          <td colSpan={4} className="py-8 text-slate-500 italic text-center">No reactive triggers configured.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

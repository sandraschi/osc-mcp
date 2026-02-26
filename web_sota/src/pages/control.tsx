import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Power,
    Play,
    Square,
    RefreshCw,
    Activity,
    Zap
} from "lucide-react";

// Mock Data for OSC/VCV Rack Control
interface ModuleStatus {
    id: string;
    name: string;
    type: 'vco' | 'vcf' | 'envelope' | 'lfo';
    status: 'online' | 'offline';
    cpu: number;
    latency: number;
    voltage: number;
    task: string;
}

const MODULES: ModuleStatus[] = [
    {
        id: 'vco-1',
        name: 'VCO-1 (Fundamental)',
        type: 'vco',
        status: 'online',
        cpu: 1.2,
        latency: 0.5,
        voltage: 5.0,
        task: 'Sine Wave - 440Hz'
    },
    {
        id: 'adsr-1',
        name: 'ADSR Envelope',
        type: 'envelope',
        status: 'online',
        cpu: 0.4,
        latency: 0.1,
        voltage: 0.0,
        task: 'A:10ms D:50ms S:0.5 R:100ms'
    },
    {
        id: 'lfo-1',
        name: 'LFO-1',
        type: 'lfo',
        status: 'online',
        cpu: 0.8,
        latency: 1.2,
        voltage: -2.5,
        task: 'Triangle - 0.5Hz'
    }
];

export function Control() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">OSC Control Center</h2>
                    <p className="text-slate-400">Direct VCV Rack parameter orchestration</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" className="border-slate-800 bg-slate-900/50 hover:bg-slate-800">
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Refresh
                    </Button>
                    <Button className="bg-emerald-600 hover:bg-emerald-700 text-white border-0">
                        <Power className="mr-2 h-4 w-4" />
                        Emergency Stop
                    </Button>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {MODULES.map((module) => (
                    <ModuleCard key={module.id} module={module} />
                ))}
            </div>

            <Tabs defaultValue="teleop" className="space-y-4">
                <TabsList className="bg-slate-900/50 border border-slate-800">
                    <TabsTrigger value="teleop" className="data-[state=active]:bg-slate-800">Signal Flow</TabsTrigger>
                    <TabsTrigger value="logs" className="data-[state=active]:bg-slate-800">OSC Logs</TabsTrigger>
                    <TabsTrigger value="config" className="data-[state=active]:bg-slate-800">Patch Config</TabsTrigger>
                </TabsList>
                <TabsContent value="teleop" className="space-y-4">
                    <OscPanel />
                </TabsContent>
                <TabsContent value="logs">
                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <CardTitle>System Events</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="font-mono text-sm text-slate-400 space-y-2">
                                <p>[10:42:15] <span className="text-emerald-500">INFO</span> OSC backend connected to VCV Rack</p>
                                <p>[10:41:22] <span className="text-yellow-500">WARN</span> UDP Jitter detected (1.5ms)</p>
                                <p>[10:40:05] <span className="text-blue-500">DEBUG</span> Mapping: /vco1/freq {"->"} Port 10767</p>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}

function ModuleCard({ module }: { module: ModuleStatus }) {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'online': return 'bg-emerald-500 text-emerald-500';
            case 'error': return 'bg-red-500 text-red-500';
            case 'offline': return 'bg-slate-500 text-slate-500';
            default: return 'bg-slate-500';
        }
    };

    return (
        <Card className="border-slate-800 bg-slate-950/50 backdrop-blur-sm transition-all hover:bg-slate-900/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-200">
                    {module.name}
                </CardTitle>
                <Badge variant="outline" className={`border-opacity-20 bg-opacity-10 capitalize ${getStatusColor(module.status)} border-current bg-current`}>
                    {module.status}
                </Badge>
            </CardHeader>
            <CardContent>
                <div className="grid gap-4 py-4">
                    <div className="flex items-center gap-4">
                        <div className="grid gap-1">
                            <p className="text-sm font-medium leading-none text-slate-400">CPU</p>
                            <div className="flex items-center gap-2">
                                <Activity className="h-4 w-4 text-slate-500" />
                                <span className="text-sm font-bold text-slate-200">{module.cpu}%</span>
                            </div>
                        </div>
                        <div className="grid gap-1">
                            <p className="text-sm font-medium leading-none text-slate-400">Latency</p>
                            <div className="flex items-center gap-2">
                                <RefreshCw className="h-4 w-4 text-slate-500" />
                                <span className="text-sm font-bold text-slate-200">{module.latency}ms</span>
                            </div>
                        </div>
                        <div className="grid gap-1">
                            <p className="text-sm font-medium leading-none text-slate-400">Voltage</p>
                            <div className="flex items-center gap-2">
                                <Zap className="h-4 w-4 text-slate-500" />
                                <span className="text-sm font-bold text-slate-200">{module.voltage}V</span>
                            </div>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs text-slate-400">
                            <span>Signal State</span>
                            <span className="text-slate-200">{module.task}</span>
                        </div>
                        <Progress value={module.cpu * 10} className="h-1 bg-slate-800" indicatorClassName={module.cpu > 5 ? "bg-red-500" : "bg-emerald-500"} />
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}


function OscPanel() {
    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            {/* Main Spectrum Feed */}
            <Card className="col-span-4 border-slate-800 bg-slate-950/50">
                <CardContent className="p-0 relative aspect-video bg-black/50 rounded-lg overflow-hidden flex items-center justify-center">
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
                        <Activity className="h-12 w-12 mb-4 opacity-50" />
                        <p>Waiting for Spectrum Signal...</p>
                    </div>
                    <div className="absolute top-2 left-2 px-2 py-1 bg-black/60 rounded text-xs text-emerald-500 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                        VCO MONITOR
                    </div>
                </CardContent>
            </Card>

            {/* Controls */}
            <Card className="col-span-3 border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
                        <Zap className="h-4 w-4 text-yellow-500" />
                        OSC Gating
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                        <Button variant="outline" className="h-24 w-full flex-col gap-2 border-slate-800 bg-slate-900/50 hover:bg-slate-800 hover:text-white">
                            <Play className="h-6 w-6 text-emerald-500" />
                            Open Gate
                        </Button>
                        <Button variant="outline" className="h-24 w-full flex-col gap-2 border-slate-800 bg-slate-900/50 hover:bg-slate-800 hover:text-white">
                            <Square className="h-6 w-6 text-red-500" />
                            Kill Signal
                        </Button>
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-medium text-slate-400">Trigger Mode</label>
                        <div className="grid grid-cols-3 gap-2">
                            <Button size="sm" variant="secondary" className="bg-slate-800 text-slate-300">Gate</Button>
                            <Button size="sm" variant="outline" className="border-slate-800 text-slate-400">Trigger</Button>
                            <Button size="sm" variant="outline" className="border-slate-800 text-slate-400">Loop</Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

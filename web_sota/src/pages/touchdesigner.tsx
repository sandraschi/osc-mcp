import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Layers, Monitor, Terminal } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function TouchDesigner() {
    const [status, setStatus] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(false);

    const callManager = async (action: string, kwargs: Record<string, unknown> = {}) => {
        setLoading(true);
        setStatus({ status: 'sending', message: `Executing ${action}...` });
        try {
            const response = await fetch('http://localhost:10767/api/v1/tools/call', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: 'touchdesigner_manager',
                    arguments: { action, ...kwargs }
                })
            });
            const data = await response.json();

            let resultStatus = data;
            if (data && data.content && Array.isArray(data.content) && data.content.length > 0) {
                try {
                    if (data.content[0].type === 'text') {
                        resultStatus = JSON.parse(data.content[0].text);
                    }
                } catch {
                    resultStatus = { status: 'raw', message: data.content[0].text };
                }
            }

            setStatus(resultStatus);
        } catch (error) {
            console.error('Error calling TouchDesigner manager:', error);
            setStatus({ status: 'error', message: String(error) });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                    <h1 className="text-3xl font-bold tracking-tight">TouchDesigner</h1>
                    {status && (
                        <Badge variant={status.status === 'error' ? 'destructive' : status.status === 'success' ? 'default' : 'secondary'} className="font-mono text-xs">
                            {String(status.status)}
                        </Badge>
                    )}
                </div>
                <p className="text-muted-foreground italic text-sm">
                    Generative Visuals & Interaction Engine (Port 9000)
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
                        <CardTitle className="text-sm font-medium">Render FPS</CardTitle>
                        <Monitor className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-emerald-500">59.94</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Active Ops</CardTitle>
                        <Layers className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">142</div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Global Overrides</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                                <label className="text-sm font-medium">Bypass Post-FX</label>
                                <p className="text-xs text-muted-foreground">Disable all screen-space effects</p>
                            </div>
                            <Switch
                                onCheckedChange={(checked) => callManager('set_parameter', { path: '/project1/postfx/bypass', value: checked ? 1 : 0 })}
                                disabled={loading}
                            />
                        </div>
                        <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                                <label className="text-sm font-medium">Freeze Simulation</label>
                                <p className="text-xs text-muted-foreground">Pause all solver calculations</p>
                            </div>
                            <Switch
                                onCheckedChange={(checked) => callManager('set_parameter', { path: '/project1/simulation/freeze', value: checked ? 1 : 0 })}
                                disabled={loading}
                            />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Instance Control</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Particle Density</span>
                                <span>45%</span>
                            </div>
                            <Slider
                                defaultValue={[45]} max={100}
                                onValueCommit={(val) => callManager('set_parameter', { path: '/project1/particles/density', value: val[0] / 100 })}
                            />
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Bloom Threshold</span>
                                <span>0.82</span>
                            </div>
                            <Slider
                                defaultValue={[82]} max={100}
                                onValueCommit={(val) => callManager('set_parameter', { path: '/project1/postfx/bloom_thresh', value: val[0] / 100 })}
                            />
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Parameter Mapping</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {['Brightness', 'Contrast', 'Saturation', 'Hue'].map((param) => (
                            <div key={param} className="space-y-2 border rounded-lg p-3 bg-slate-500/5">
                                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">{param}</div>
                                <Slider
                                    defaultValue={[50]} max={100}
                                    onValueCommit={(val) => callManager('control_parameter', {
                                        category: 'color',
                                        parameter: param.toLowerCase(),
                                        value: val[0] / 100
                                    })}
                                />
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

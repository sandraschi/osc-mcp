import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Play, Square, Circle, Music, Terminal } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function Ableton() {
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
                    name: 'ableton_manager',
                    arguments: { action, ...kwargs }
                })
            });
            const data = await response.json();

            let resultStatus = data;
            // Handle FastMCP specific return structures if needed
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
            console.error('Error calling Ableton manager:', error);
            setStatus({ status: 'error', message: String(error) });
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
                        <Badge variant={status.status === 'error' ? 'destructive' : status.status === 'success' ? 'default' : 'secondary'} className="font-mono text-xs">
                            {String(status.status)}
                        </Badge>
                    )}
                </div>
                <p className="text-muted-foreground italic text-sm">
                    Professional DAW Orchestration Layer (Port 11000)
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
                        <CardTitle className="text-sm font-medium">BPM</CardTitle>
                        <Music className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">128.0</div>
                        <Slider
                            defaultValue={[128]}
                            max={200} min={60} step={1}
                            className="mt-4"
                            onValueCommit={(val) => callManager('set_tempo', { value: val[0] })}
                        />
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Transport Control</CardTitle>
                    </CardHeader>
                    <CardContent className="flex gap-4">
                        <Button
                            variant="outline" size="icon"
                            className="h-12 w-12 text-emerald-500 border-emerald-500/20 bg-emerald-500/10 hover:bg-emerald-500/20"
                            onClick={() => callManager('play')}
                            disabled={loading}
                        >
                            <Play className="h-6 w-6 fill-current" />
                        </Button>
                        <Button
                            variant="outline" size="icon"
                            className="h-12 w-12 text-slate-400 border-slate-500/20 bg-slate-500/10 hover:bg-slate-500/20"
                            onClick={() => callManager('stop')}
                            disabled={loading}
                        >
                            <Square className="h-6 w-6 fill-current" />
                        </Button>
                        <Button
                            variant="outline" size="icon"
                            className="h-12 w-12 text-red-500 border-red-500/20 bg-red-500/10 hover:bg-red-500/20"
                            onClick={() => callManager('record')}
                            disabled={loading}
                        >
                            <Circle className="h-6 w-6 fill-current" />
                        </Button>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Master Bus</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Volume</span>
                                <span>-3.2 dB</span>
                            </div>
                            <Slider
                                defaultValue={[80]} max={100}
                                onValueCommit={(val) => callManager('set_volume', { track: 0, value: val[0] / 100 })}
                            />
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Pan</span>
                                <span>C</span>
                            </div>
                            <Slider
                                defaultValue={[50]} max={100}
                                onValueCommit={(val) => callManager('set_pan', { track: 0, value: (val[0] - 50) / 50 })}
                            />
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Scene Launch</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-4 gap-2">
                        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                            <Button
                                key={i} variant="secondary" className="justify-start font-mono text-xs"
                                onClick={() => callManager('launch_scene', { scene: i })}
                                disabled={loading}
                            >
                                Scene {i}
                            </Button>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Radio, Zap, Terminal } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function MaxMSP() {
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
                    name: 'maxmsp_manager',
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
            console.error('Error calling MaxMSP manager:', error);
            setStatus({ status: 'error', message: String(error) });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                    <h1 className="text-3xl font-bold tracking-tight">Max/MSP & Pure Data</h1>
                    {status && (
                        <Badge variant={status.status === 'error' ? 'destructive' : status.status === 'success' ? 'default' : 'secondary'} className="font-mono text-xs">
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

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">DSP Status</CardTitle>
                        <Radio className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">ON</div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Global Messaging</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-2">
                            <Button
                                variant="secondary" className="font-mono"
                                onClick={() => callManager('send_bang', { receiver: 'global' })}
                                disabled={loading}
                            >
                                <Zap className="mr-2 h-4 w-4" /> bang
                            </Button>
                            <Button
                                variant="secondary" className="font-mono"
                                onClick={() => callManager('reset_state', { component: 'all' })}
                                disabled={loading}
                            >
                                reset
                            </Button>
                        </div>
                        <div className="space-y-2 pt-4 border-t">
                            <label className="text-xs font-semibold uppercase text-muted-foreground">Global Float</label>
                            <div className="flex items-center gap-4">
                                <Slider
                                    defaultValue={[0]} max={100} className="flex-1"
                                    onValueCommit={(val) => callManager('set_float', { receiver: 'global', value: val[0] / 100 })}
                                />
                                <span className="font-mono text-sm">0.00</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Telemetry Stream</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[120px] w-full bg-slate-900/50 rounded flex items-end justify-between p-2 gap-1 border border-slate-800">
                            {[40, 60, 45, 90, 100, 80, 30, 45, 50, 70, 85, 40, 20, 60].map((h, i) => (
                                <div key={i} className="bg-emerald-500/40 w-full rounded-t-sm" style={{ height: `${h}%` } as React.CSSProperties}></div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

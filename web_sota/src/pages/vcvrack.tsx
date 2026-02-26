import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Play, Square, Settings, Database, Activity } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function VCVRack() {
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState<any>(null);

    const callManager = async (action: string, args: Record<string, any> = {}) => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:10767/api/v1/tools/call', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: 'vcv_manager',
                    arguments: { action, ...args }
                })
            });
            const data = await response.json();
            setStatus(data);
        } catch (error) {
            console.error('Error calling vcv_manager:', error);
            setStatus({ error: String(error) });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">VCV Rack</h2>
                    <p className="text-slate-400">Modular Synthesis Control Surface</p>
                </div>
                <Badge variant="outline" className="px-3 py-1 border-blue-500/20 text-blue-400 bg-blue-500/10">
                    <Database className="w-3 h-3 justify-center inline mr-2" />
                    Port 10001
                </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white text-lg">Transport Control</CardTitle>
                        <CardDescription className="text-slate-400">Global clock and sequencer transport</CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-wrap gap-3">
                        <Button
                            disabled={loading}
                            onClick={() => callManager('start_transport')}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white"
                        >
                            <Play className="w-4 h-4 mr-2" /> Play
                        </Button>
                        <Button
                            disabled={loading}
                            onClick={() => callManager('stop_transport')}
                            variant="destructive"
                        >
                            <Square className="w-4 h-4 mr-2" /> Stop
                        </Button>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white text-lg">Patch Orchestration</CardTitle>
                        <CardDescription className="text-slate-400">Automated patch configurations</CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-wrap gap-3">
                        <Button
                            disabled={loading}
                            onClick={() => callManager('setup_organ')}
                            variant="outline"
                            className="border-slate-700 hover:bg-slate-800"
                        >
                            <Settings className="w-4 h-4 mr-2" /> Setup Organ Patch
                        </Button>
                    </CardContent>
                </Card>

                <Card className="md:col-span-2 border-slate-800 bg-slate-950/50">
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
                            <p className="text-sm text-slate-500 italic">No commands executed yet.</p>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

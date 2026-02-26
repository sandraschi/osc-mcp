import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { User, MessageSquare, Zap, Terminal } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function VRChat() {
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
                    name: 'vrchat_manager',
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
                } catch (_e) {
                    resultStatus = { status: 'raw', message: data.content[0].text };
                }
            }

            setStatus(resultStatus);
        } catch (error) {
            console.error('Error calling VRChat manager:', error);
            setStatus({ status: 'error', message: String(error) });
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
                        <Badge variant={status.status === 'error' ? 'destructive' : status.status === 'success' ? 'default' : 'secondary'} className="font-mono text-xs">
                            {status.status}
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

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avatar Status</CardTitle>
                        <User className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-blue-500">Connected</div>
                    </CardContent>
                </Card>
            </div>

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
                                defaultValue={[85]} max={100}
                                onValueCommit={(val) => callManager('set_avatar_parameter', { parameter: 'Voice', value: val[0] / 100, type: 'float' })}
                            />
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm font-mono">
                                <span>/avatar/parameters/Viseme</span>
                                <span>4</span>
                            </div>
                            <Slider
                                defaultValue={[4]} max={15} step={1}
                                onValueCommit={(val) => callManager('set_avatar_parameter', { parameter: 'Viseme', value: val[0], type: 'int' })}
                            />
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm font-mono">
                                <span>/avatar/parameters/Mood</span>
                                <span>0.5</span>
                            </div>
                            <Slider
                                defaultValue={[50]} max={100}
                                onValueCommit={(val) => callManager('set_avatar_parameter', { parameter: 'Mood', value: val[0] / 100, type: 'float' })}
                            />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Input Simulation</CardTitle>
                    </CardHeader>
                    <CardContent className="grid grid-cols-3 gap-3">
                        {['Jump', 'Mute', 'Reset', 'Sit', 'AFK', 'Menu'].map((action) => (
                            <Button
                                key={action} variant="outline" className="flex items-center gap-2"
                                onClick={() => callManager('simulate_input', { button: action.toLowerCase(), state: 1 })}
                                disabled={loading}
                            >
                                <Zap className="h-3 w-3" />
                                {action}
                            </Button>
                        ))}
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>Chatbox Preview</CardTitle>
                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-md p-4 font-mono text-emerald-400">
                        "Synthesizing new audio patterns..."
                    </div>
                    <Button
                        className="w-full"
                        onClick={() => callManager('send_chatbox', { message: 'Synthesizing new audio patterns...', show_keyboard: false })}
                        disabled={loading}
                    >
                        Update Chatbox Text
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}

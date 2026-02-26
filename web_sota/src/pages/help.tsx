import { Card, CardContent } from "@/components/ui/card";

export function Help() {
    return (
        <div className="flex flex-col space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">System Guide</h2>
                <p className="text-slate-400">Documentation and operational support</p>
            </div>
            <Card className="border-slate-800 bg-slate-950/50">
                <CardContent className="p-6">
                    <h3 className="text-lg font-medium text-white mb-2">Webapp Usage</h3>
                    <p className="text-slate-300 text-sm mb-4">
                        The OSC-MCP web application allows you to orchestrate and route signals between various targets
                        such as Ableton Live, TouchDesigner, VRChat, Max/MSP, SuperCollider, and VCV Rack. Use the Chat
                        Orchestrator to write natural language automation commands, and the Tools Hub to execute raw
                        FastMCP tool calls directly against the backend.
                    </p>
                    <h3 className="text-lg font-medium text-white mb-2 mt-6">MCP Tools Reference</h3>
                    <p className="text-slate-400 text-sm italic">
                        Available tools are dynamically listed in the Tools Hub. You can use standard MCP prompts
                        to execute tasks such as `ableton_manager`, `vcv_manager`, or raw OSC/MIDI messaging.
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}

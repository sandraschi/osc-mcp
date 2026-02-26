import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send, Bot, User, Share, Plus, Settings2, Code, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

interface Message {
    role: "user" | "assistant" | "system";
    content: string;
    timestamp: Date;
    metadata?: any;
}

export function Chat() {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: "system",
            content: "Signal Orchestrator initialized. Connected to OSC targets: Ableton Live (9000), VCV Rack (10001).",
            timestamp: new Date()
        }
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [personality, setPersonality] = useState("Vitesse (Fast/Direct)");
    const endOfMessagesRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg: Message = { role: "user", content: input, timestamp: new Date() };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            // Note: This tries to connect to the specific semantic-router endpoints if they existed in OSC-MCP.
            // For now we mock the backend response, simulating the LLM orchestrator.
            // Real implementation would hit local Ollama/Gemini or an OSC-MCP specific route.
            setTimeout(() => {
                const assistantMsg: Message = {
                    role: "assistant",
                    content: "Command recognized. Executing patch changes in VCV Rack...",
                    timestamp: new Date(),
                    metadata: {
                        ops: [
                            { type: "OSC", path: "/param", value: "Sweep VCO-1", target: "VCV Rack" },
                            { type: "MIDI", path: "CC 74", value: "127", target: "External" }
                        ]
                    }
                };
                setMessages(prev => [...prev, assistantMsg]);
                setLoading(false);
            }, 1200);

        } catch (error) {
            setMessages(prev => [...prev, { role: "system", content: `Error: ${error}`, timestamp: new Date() }]);
            setLoading(false);
        }
    };

    const handleExport = () => {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(messages, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", `chat_export_${new Date().getTime()}.json`);
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    };

    return (
        <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        <Bot className="h-6 w-6 text-blue-500" />
                        Chat Orchestrator
                    </h2>
                    <p className="text-slate-400">Natural language patch and signal routing control</p>
                </div>
                <div className="flex items-center gap-2">
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline" className="border-slate-800 bg-slate-900 text-slate-300">
                                <Settings2 className="w-4 h-4 mr-2" />
                                {personality}
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="w-56 bg-slate-900 border-slate-800 text-slate-200">
                            <DropdownMenuItem onClick={() => setPersonality("Vitesse (Fast/Direct)")}>Vitesse (Fast/Direct)</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => setPersonality("Architect (Verbose/Planning)")}>Architect (Verbose/Planning)</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => setPersonality("Code-Only (Raw outputs)")}>Code-Only (Raw outputs)</DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>

                    <Button variant="outline" className="border-slate-800 bg-slate-900 text-slate-300" onClick={handleExport}>
                        <Share className="w-4 h-4 mr-2" />
                        Export
                    </Button>
                </div>
            </div>

            <Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden shadow-xl">
                <CardContent className="flex-1 overflow-y-auto p-4 space-y-6 flex flex-col pt-6">
                    {messages.map((msg, i) => (
                        <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                            <div className={`h-8 w-8 rounded-full flex items-center justify-center border shrink-0 ${msg.role === 'user' ? 'bg-indigo-900/20 border-indigo-800' :
                                    msg.role === 'system' ? 'bg-slate-800 border-slate-700' :
                                        'bg-blue-900/20 border-blue-800'
                                }`}>
                                {msg.role === 'user' ? <User className="h-4 w-4 text-indigo-400" /> :
                                    msg.role === 'system' ? <Code className="h-4 w-4 text-slate-400" /> :
                                        <Zap className="h-4 w-4 text-blue-400" />}
                            </div>

                            <div className={`flex flex-col space-y-1 max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                <div className="flex items-center gap-2 px-1">
                                    <span className={`text-xs font-medium ${msg.role === 'user' ? 'text-indigo-400' :
                                            msg.role === 'system' ? 'text-slate-400' :
                                                'text-blue-400'
                                        }`}>
                                        {msg.role === 'user' ? 'Operator' : msg.role === 'system' ? 'System' : 'Assistant'}
                                    </span>
                                    <span className="text-[10px] text-slate-600">
                                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                    </span>
                                </div>

                                <div className={`text-sm p-3 rounded-xl border ${msg.role === 'user' ? 'bg-indigo-950/30 border-indigo-900/50 text-indigo-100 rounded-tr-sm' :
                                        msg.role === 'system' ? 'bg-slate-900/50 border-slate-800 text-slate-300 font-mono text-xs rounded-tl-sm' :
                                            'bg-blue-950/10 border-blue-900/30 text-slate-200 rounded-tl-sm'
                                    }`}>
                                    <p className="whitespace-pre-wrap">{msg.content}</p>

                                    {msg.metadata?.ops && (
                                        <div className="mt-3 pt-3 border-t border-blue-900/30 space-y-1">
                                            <p className="text-xs font-semibold text-blue-400 mb-2">Executed Operations:</p>
                                            {msg.metadata.ops.map((op: any, j: number) => (
                                                <div key={j} className="flex items-center justify-between text-xs font-mono bg-black/40 p-2 rounded border border-blue-900/20">
                                                    <span className="text-emerald-400">{op.type}</span>
                                                    <span className="text-slate-300">{op.path}</span>
                                                    <span className="text-sky-300 border border-sky-900/50 px-1 rounded">{op.value}</span>
                                                    <span className="text-slate-500">{op.target}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex gap-3">
                            <div className="h-8 w-8 rounded-full bg-blue-900/20 flex items-center justify-center border border-blue-800 shrink-0">
                                <Bot className="h-4 w-4 text-blue-400 animate-pulse" />
                            </div>
                            <div className="flex items-center h-8 bg-blue-950/10 border border-blue-900/30 px-4 py-2 rounded-xl rounded-tl-sm">
                                <span className="flex space-x-1">
                                    <span className="h-1.5 w-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                                    <span className="h-1.5 w-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                                    <span className="h-1.5 w-1.5 bg-blue-500 rounded-full animate-bounce"></span>
                                </span>
                            </div>
                        </div>
                    )}
                    <div ref={endOfMessagesRef} />
                </CardContent>

                <div className="p-4 bg-slate-900/40 border-t border-slate-800">
                    <div className="flex gap-2">
                        <Button variant="outline" size="icon" className="shrink-0 border-slate-800 bg-slate-950 text-slate-400 hover:text-white">
                            <Plus className="h-4 w-4" />
                        </Button>
                        <Input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') handleSend(); }}
                            className="bg-slate-950 border-slate-700 text-white placeholder:text-slate-500 focus-visible:ring-blue-500 h-10"
                            placeholder="Type a command to orchestrate the grid... (e.g. 'Route Ableton track 1 to VCV VCO')"
                        />
                        <Button
                            onClick={handleSend}
                            disabled={!input.trim() || loading}
                            className="shrink-0 bg-blue-600 hover:bg-blue-700 text-white transition-all h-10 px-4"
                        >
                            <Send className="h-4 w-4 mr-2" />
                            Send
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    );
}

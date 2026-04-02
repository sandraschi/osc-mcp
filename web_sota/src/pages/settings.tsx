import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

export function Settings() {
    const [provider, setProvider] = useState("ollama");
    const [apiKey, setApiKey] = useState("");
    const [models, setModels] = useState<string[]>([]);
    const [selectedModel, setSelectedModel] = useState("");
    const [ollamaStatus, setOllamaStatus] = useState<"checking" | "online" | "offline">("checking");

    const checkOllama = useCallback(async () => {
        setOllamaStatus("checking");
        try {
            const res = await fetch("http://localhost:11434/api/tags");
            if (res.ok) {
                const data = await res.json();
                const modelNames = data.models.map((m: { name: string }) => m.name);
                setModels(modelNames);
                if (modelNames.length > 0) setSelectedModel(modelNames[0]);
                setOllamaStatus("online");
            } else {
                setOllamaStatus("offline");
                setModels([]);
            }
        } catch {
            setOllamaStatus("offline");
            setModels([]);
        }
    }, []);

    useEffect(() => {
        let isCancelled = false;

        const syncModels = async () => {
            if (provider === "ollama") {
                await checkOllama();
            } else {
                if (isCancelled) return;
                const mockModels = (provider === "anthropic") 
                    ? ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
                    : (provider === "gemini")
                    ? ["gemini-2.5-flash", "gemini-3-pro"]
                    : ["gpt-4o", "gpt-3.5-turbo"];
                
                setModels(mockModels);
                if (mockModels.length > 0) setSelectedModel(mockModels[0]);
            }
        };

        syncModels();

        return () => {
            isCancelled = true;
        };
    }, [provider, checkOllama]);

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Settings</h2>
                <p className="text-slate-400">Manage connections and preferences</p>
            </div>

            <div className="grid gap-6">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">LLM Provider Configuration</CardTitle>
                        <CardDescription className="text-slate-400">Configure the AI engine for orchestrations and workflow generations</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <Label className="text-slate-300">AI Provider</Label>
                            <select
                                className="bg-slate-900 border border-slate-800 text-slate-100 rounded-md p-2 outline-none"
                                value={provider}
                                onChange={(e) => setProvider(e.target.value)}
                                title="Select AI Provider"
                            >
                                <option value="ollama">Ollama (Local Inference)</option>
                                <option value="openai">OpenAI</option>
                                <option value="anthropic">Anthropic</option>
                                <option value="gemini">Google Gemini</option>
                            </select>
                        </div>

                        {provider !== "ollama" && (
                            <div className="grid gap-2">
                                <Label className="text-slate-300">API Key</Label>
                                <Input
                                    type="password"
                                    className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                                    placeholder="Enter your API Key"
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                />
                            </div>
                        )}

                        <div className="grid gap-2">
                            <Label className="text-slate-300 flex items-center justify-between">
                                Model Selection
                                {provider === "ollama" && (
                                    <Badge variant={ollamaStatus === "online" ? "default" : ollamaStatus === "checking" ? "secondary" : "destructive"}>
                                        {ollamaStatus === "online" ? "Ollama Online" : ollamaStatus === "checking" ? "Checking..." : "Ollama Offline"}
                                    </Badge>
                                )}
                            </Label>
                            <select
                                className="bg-slate-900 border border-slate-800 text-slate-100 rounded-md p-2 outline-none disabled:opacity-50"
                                value={selectedModel}
                                onChange={(e) => setSelectedModel(e.target.value)}
                                disabled={models.length === 0}
                                title="Select Model"
                            >
                                {models.length === 0 && <option value="">No models available</option>}
                                {models.map(m => (
                                    <option key={m} value={m}>{m}</option>
                                ))}
                            </select>
                        </div>

                        <Button variant="default" className="w-full mt-4 bg-blue-600 hover:bg-blue-500 text-white border-none">
                            Save LLM Settings
                        </Button>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">VCV Rack Bridge Configuration</CardTitle>
                        <CardDescription className="text-slate-400">Connection details for the OSC-mcp backend bridge</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <Label className="text-slate-300">Backend API URL</Label>
                            <Input
                                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                                defaultValue="http://localhost:10767"
                            />
                        </div>
                        <Button variant="outline" className="border-slate-800 text-slate-300 hover:bg-slate-800">
                            Test Connection
                        </Button>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">OSC Protocol Settings</CardTitle>
                        <CardDescription className="text-slate-400">UDP Port configuration for OSC communication</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <Label className="text-slate-300">OSC Receive Port (Inbound)</Label>
                            <Input
                                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                                defaultValue="11000"
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label className="text-slate-300">OSC Send Port (Outbound)</Label>
                            <Input
                                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                                defaultValue="11001"
                            />
                        </div>
                        <Button variant="outline" className="border-slate-800 text-slate-300 hover:bg-slate-800">
                            Apply Network Settings
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

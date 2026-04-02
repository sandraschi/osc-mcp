import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Terminal, Play, Search, Wrench } from 'lucide-react';

interface ToolParameter {
    name: string;
    type: string;
    description?: string;
    required: boolean;
}

interface ToolInfo {
    name: string;
    description: string;
    parameters: ToolParameter[];
}

export function Tools() {
    const [tools, setTools] = useState<ToolInfo[]>([]);
    const [selectedTool, setSelectedTool] = useState<ToolInfo | null>(null);
    const [args, setArgs] = useState<Record<string, any>>({});
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchTools();
    }, []);

    const fetchTools = async () => {
        try {
            const response = await fetch('http://localhost:10767/api/v1/tools/');
            const data = await response.json();
            setTools(data);
        } catch (error) {
            console.error('Error fetching tools:', error);
        }
    };

    const handleCallTool = async () => {
        if (!selectedTool) return;
        setLoading(true);
        try {
            const response = await fetch('http://localhost:10767/api/v1/tools/call', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: selectedTool.name,
                    arguments: args
                })
            });
            const data = await response.json();
            setResult(data);
        } catch (error) {
            setResult({ status: 'error', message: String(error) });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">MCP Tools Hub</h1>
                    <p className="text-muted-foreground">Industrial-grade tool discovery and execution</p>
                </div>
                <Badge variant="outline" className="px-3 py-1">
                    <Wrench className="w-3 h-3 mr-2" />
                    SOTA S3.0
                </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Tool List */}
                <Card className="md:col-span-1">
                    <CardHeader>
                        <CardTitle className="flex items-center">
                            <Search className="w-5 h-5 mr-2" />
                            Available Tools
                        </CardTitle>
                        <CardDescription>Select a tool to configure and run</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ScrollArea className="h-[500px] pr-4">
                            <div className="space-y-2">
                                {tools.map((tool) => (
                                    <Button
                                        key={tool.name}
                                        variant={selectedTool?.name === tool.name ? "secondary" : "ghost"}
                                        className="w-full justify-start text-left h-auto py-3 px-4"
                                        onClick={() => {
                                            setSelectedTool(tool);
                                            setArgs({});
                                            setResult(null);
                                        }}
                                    >
                                        <div className="flex flex-col">
                                            <span className="font-semibold">{tool.name}</span>
                                            <span className="text-xs text-muted-foreground line-clamp-1">{tool.description}</span>
                                        </div>
                                    </Button>
                                ))}
                            </div>
                        </ScrollArea>
                    </CardContent>
                </Card>

                {/* Tool Execution */}
                <Card className="md:col-span-2">
                    <CardHeader>
                        <CardTitle className="flex items-center">
                            <Play className="w-5 h-5 mr-2" />
                            {selectedTool ? `Run: ${selectedTool.name}` : 'Select a Tool'}
                        </CardTitle>
                        <CardDescription>
                            {selectedTool?.description || 'Pick a tool from the left to begin execution'}
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {selectedTool && (
                            <>
                                <div className="grid grid-cols-1 gap-4">
                                    {selectedTool.parameters.map((param) => (
                                        <div key={param.name} className="space-y-2">
                                            <div className="flex items-center justify-between">
                                                <Label htmlFor={param.name} className="font-semibold">
                                                    {param.name}
                                                    {param.required && <span className="text-destructive ml-1">*</span>}
                                                </Label>
                                                <Badge variant="secondary" className="text-[10px] h-4">
                                                    {param.type}
                                                </Badge>
                                            </div>
                                            <Input
                                                id={param.name}
                                                placeholder={param.description || `Enter ${param.name}`}
                                                onChange={(e) => {
                                                    let val: any = e.target.value;
                                                    if (param.type === 'integer' || param.type === 'number') {
                                                        val = Number(val);
                                                    } else if (param.type === 'array') {
                                                        try { val = JSON.parse(val); } catch { }
                                                    }
                                                    setArgs(prev => ({ ...prev, [param.name]: val }));
                                                }}
                                            />
                                            {param.description && (
                                                <p className="text-xs text-muted-foreground">{param.description}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>

                                <div className="flex justify-end">
                                    <Button
                                        onClick={handleCallTool}
                                        disabled={loading}
                                        className="w-full md:w-auto px-10"
                                    >
                                        {loading ? "Executing..." : "Execute Tool"}
                                    </Button>
                                </div>
                            </>
                        )}

                        {/* Results Console */}
                        {result && (
                            <div className="mt-6 space-y-2">
                                <Label className="flex items-center text-xs font-bold uppercase tracking-wider text-muted-foreground">
                                    <Terminal className="w-3 h-3 mr-2" />
                                    Execution Results
                                </Label>
                                <div className="bg-black/90 text-green-400 p-4 rounded-lg font-mono text-sm overflow-auto max-h-[300px] border border-white/10 shadow-inner">
                                    <pre>{JSON.stringify(result, null, 2)}</pre>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

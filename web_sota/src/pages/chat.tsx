import {
  Bot,
  Code,
  Download,
  Eraser,
  MessageSquare,
  Send,
  Settings2,
  User,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { API_BASE } from "../lib/api";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  ts?: string;
}

const STORAGE_KEY = "osc-mcp-chat-history";
const PERSONALITY_KEY = "osc-mcp-chat-personality";
const MAX_MESSAGES = 100;

const PERSONALITIES: Record<string, string> = {
  "Vitesse (Fast/Direct)":
    "You are Vitesse, a fast and direct OSC assistant. Keep responses brief and actionable.",
  "Architect (Detailed)":
    "You are an OSC Architect. Provide detailed explanations, signal flow analysis, and comprehensive routing advice.",
  "Code-Only (Technical)":
    "You are a technical OSC engineer. Respond with code, configuration snippets, and technical specifications only.",
  Custom: "You are a helpful OSC assistant.",
};

const EXAMPLE_PROMPTS = [
  "Send an OSC message to port 9000",
  "Start an OSC listener",
  "Discover OSC devices",
  "Map MIDI to OSC",
  "Create a VCV Rack workflow",
  "List available targets",
];

export function Chat() {
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0)
          return parsed.slice(-MAX_MESSAGES);
      }
    } catch {}
    return [];
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [personality, setPersonality] = useState(() => {
    try {
      return localStorage.getItem(PERSONALITY_KEY) || "Vitesse (Fast/Direct)";
    } catch {
      return "Vitesse (Fast/Direct)";
    }
  });
  const [skillLoaded, setSkillLoaded] = useState("");
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  const persist = useCallback((msgs: Message[]) => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(msgs.slice(-MAX_MESSAGES)),
      );
    } catch {}
  }, []);

  useEffect(() => {
    persist(messages);
  }, [messages, persist]);

  useEffect(() => {
    try {
      localStorage.setItem(PERSONALITY_KEY, personality);
    } catch {}
  }, [personality]);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/api/v1/skills`);
        if (r.ok) {
          const skills = await r.json();
          if (Array.isArray(skills) && skills.length > 0) {
            const name =
              typeof skills[0] === "string"
                ? skills[0]
                : skills[0].name || skills[0].id || "";
            if (name) {
              const sr = await fetch(
                `${API_BASE}/api/v1/skills/${encodeURIComponent(name)}`,
              );
              if (sr.ok) {
                const content = await sr.text();
                setSkillLoaded(content.slice(0, 200));
              }
            }
          }
        }
      } catch {}
    })();
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      role: "user",
      content: input,
      ts: new Date().toISOString(),
    };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");
    setLoading(true);

    try {
      const personalityPrompt =
        PERSONALITIES[personality] || PERSONALITIES["Vitesse (Fast/Direct)"];
      const systemContent = skillLoaded
        ? `${skillLoaded}\n\n---\n\n## Role\n${personalityPrompt}`
        : personalityPrompt;

      const r = await fetch(`${API_BASE}/api/v1/llm/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [
            { role: "system", content: systemContent },
            ...updated.map(({ role, content }) => ({ role, content })),
          ],
        }),
      });

      let reply = "";
      if (r.ok) {
        const data = await r.json();
        reply =
          data.response || data.message || data.content || JSON.stringify(data);
      } else {
        reply = `Error: HTTP ${r.status} — ${r.statusText}`;
      }

      const assistantMsg: Message = {
        role: "assistant",
        content: reply,
        ts: new Date().toISOString(),
      };
      const final = [...updated, assistantMsg];
      setMessages(final);
    } catch (error) {
      const errorMsg: Message = {
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : String(error)}`,
        ts: new Date().toISOString(),
      };
      setMessages([...updated, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (messages.length === 0) return;
    const lines = messages.map((m) => {
      const ts = m.ts ? new Date(m.ts).toISOString() : "";
      return `[${ts}] ${m.role.toUpperCase()}: ${m.content}`;
    });
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `osc-mcp-chat-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    setMessages([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {}
  };

  return (
    <div
      data-testid="chat-page"
      className="flex h-[calc(100vh-8rem)] flex-col space-y-4"
    >
      <div
        data-testid="chat-controls"
        className="flex items-center justify-between"
      >
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Bot className="h-6 w-6 text-blue-500" />
            Chat Orchestrator
          </h2>
          <p className="text-slate-400">
            Natural language patch and signal routing control
          </p>
        </div>
        <div className="flex items-center gap-2">
          {skillLoaded && (
            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">
              skill:{skillLoaded.slice(0, 30)}
            </span>
          )}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="border-slate-800 bg-slate-900 text-slate-300"
                data-testid="personality-select"
              >
                <Settings2 className="w-4 h-4 mr-2" />
                {personality}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56 bg-slate-900 border-slate-800 text-slate-200">
              {Object.keys(PERSONALITIES).map((p) => (
                <DropdownMenuItem key={p} onClick={() => setPersonality(p)}>
                  {p}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <Button
            variant="outline"
            className="border-slate-800 bg-slate-900 text-slate-300"
            onClick={handleExport}
            disabled={messages.length === 0}
            data-testid="chat-export"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>

          <Button
            variant="outline"
            className="border-slate-800 bg-slate-900 text-slate-300"
            onClick={handleClear}
            disabled={messages.length === 0}
            data-testid="chat-clear"
          >
            <Eraser className="w-4 h-4 mr-2" />
            Clear
          </Button>
        </div>
      </div>

      <Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden shadow-xl">
        <CardContent
          data-testid="chat-messages"
          className="flex-1 overflow-y-auto p-4 space-y-6 flex flex-col pt-6"
        >
          {messages.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500 space-y-4">
              <MessageSquare className="h-12 w-12 text-slate-700" />
              <p className="text-sm">
                No messages yet. Start a conversation or try an example below.
              </p>
              <div
                data-testid="example-prompts"
                className="flex flex-wrap gap-2 max-w-xl justify-center"
              >
                {EXAMPLE_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => setInput(p)}
                    className="px-3 py-1.5 text-xs rounded-full border border-slate-700 bg-slate-900/50 text-slate-400 hover:text-white hover:border-blue-500 transition-colors"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
            >
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center border shrink-0 ${
                  msg.role === "user"
                    ? "bg-indigo-900/20 border-indigo-800"
                    : msg.role === "system"
                      ? "bg-slate-800 border-slate-700"
                      : "bg-blue-900/20 border-blue-800"
                }`}
              >
                {msg.role === "user" ? (
                  <User className="h-4 w-4 text-indigo-400" />
                ) : msg.role === "system" ? (
                  <Code className="h-4 w-4 text-slate-400" />
                ) : (
                  <Zap className="h-4 w-4 text-blue-400" />
                )}
              </div>

              <div
                className={`flex flex-col space-y-1 max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"}`}
              >
                <div className="flex items-center gap-2 px-1">
                  <span
                    className={`text-xs font-medium ${
                      msg.role === "user"
                        ? "text-indigo-400"
                        : msg.role === "system"
                          ? "text-slate-400"
                          : "text-blue-400"
                    }`}
                  >
                    {msg.role === "user"
                      ? "Operator"
                      : msg.role === "system"
                        ? "System"
                        : "Assistant"}
                  </span>
                  {msg.ts && (
                    <span className="text-[10px] text-slate-600">
                      {new Date(msg.ts).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </span>
                  )}
                </div>

                <div
                  className={`text-sm p-3 rounded-xl border ${
                    msg.role === "user"
                      ? "bg-indigo-950/30 border-indigo-900/50 text-indigo-100 rounded-tr-sm"
                      : msg.role === "system"
                        ? "bg-slate-900/50 border-slate-800 text-slate-300 font-mono text-xs rounded-tl-sm"
                        : "bg-blue-950/10 border-blue-900/30 text-slate-200 rounded-tl-sm"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
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

          {!loading && messages.length === 0 && (
            <div
              data-testid="example-prompts"
              className="flex flex-wrap gap-2 justify-center pb-4"
            >
              {EXAMPLE_PROMPTS.map((p) => (
                <button
                  key={p}
                  onClick={() => setInput(p)}
                  className="px-3 py-1.5 text-xs rounded-full border border-slate-700 bg-slate-900/50 text-slate-400 hover:text-white hover:border-blue-500 transition-colors"
                >
                  {p}
                </button>
              ))}
            </div>
          )}

          <div ref={endOfMessagesRef} />
        </CardContent>

        <div className="p-4 bg-slate-900/40 border-t border-slate-800">
          <div className="flex gap-2">
            <Input
              data-testid="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              className="bg-slate-950 border-slate-700 text-white placeholder:text-slate-500 focus-visible:ring-blue-500 h-10"
              placeholder="Type a command to orchestrate the grid..."
            />
            <Button
              data-testid="chat-send"
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

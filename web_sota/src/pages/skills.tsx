import { API_BASE } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Code2, ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";

export function Skills() {
  const [skills, setSkills] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [contentLoading, setContentLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const r = await fetch(API_BASE + "/api/v1/skills");
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        const names = Array.isArray(data) ? data.map((s: any) => typeof s === "string" ? s : s.name || s.id || String(s)).filter(Boolean) : [];
        setSkills(names);
        if (names.length > 0) {
          setSelected(names[0]);
        }
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selected) return;
    (async () => {
      try {
        setContentLoading(true);
        const r = await fetch(API_BASE + "/api/v1/skills/" + encodeURIComponent(selected));
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const text = await r.text();
        setContent(text);
      } catch (e) {
        setContent("Error loading skill: " + (e instanceof Error ? e.message : String(e)));
      } finally {
        setContentLoading(false);
      }
    })();
  }, [selected]);

  return (
    <div data-testid="skills-page" className="space-y-6">
      <div className="flex items-center gap-2">
        <Code2 className="h-6 w-6 text-blue-500" />
        <h1 className="text-2xl font-bold text-white">Skills</h1>
      </div>
      <p className="text-sm text-slate-400">Available server skills — click to view full content.</p>

      {loading && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="p-6 text-center text-slate-500 text-sm">Loading skills...</CardContent>
        </Card>
      )}

      {err && (
        <Card className="border-red-800/50 bg-red-950/20">
          <CardContent className="p-4 text-xs text-red-400">{err}</CardContent>
        </Card>
      )}

      {!loading && !err && skills.length === 0 && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="p-6 text-center text-slate-500 text-sm">No skills available.</CardContent>
        </Card>
      )}

      {!loading && skills.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="md:col-span-1 border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-sm text-slate-200">Skill Index</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              {skills.map((name) => (
                <button
                  key={name}
                  onClick={() => setSelected(name)}
                  className={`w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors text-left ${selected === name ? "bg-blue-900/30 text-blue-300" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}
                >
                  <ChevronRight className={`h-3 w-3 ${selected === name ? "text-blue-400" : "text-transparent"}`} />
                  {name}
                </button>
              ))}
            </CardContent>
          </Card>

          <Card className="md:col-span-3 border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-sm text-slate-200">{selected}</CardTitle>
            </CardHeader>
            <CardContent>
              {contentLoading ? (
                <div className="text-sm text-slate-500">Loading...</div>
              ) : (
                <div className="prose prose-invert prose-sm max-w-none text-slate-300 whitespace-pre-wrap font-mono text-xs">
                  {content}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

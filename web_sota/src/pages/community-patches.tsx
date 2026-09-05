import {
  Activity,
  Download,
  ExternalLink,
  Eye,
  Globe,
  Heart,
  Search,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { API_BASE } from "../lib/api";

interface Platform {
  id: number;
  name: string;
  slug: string;
}

interface Patch {
  id: number;
  url: string;
  title: string;
  excerpt: string;
  artwork: { thumbnail_url: string | null } | null;
  view_count: number;
  like_count: number;
  download_count: number;
  author: { name: string };
  platform: { id: number; name: string } | null;
  state: { name: string; slug: string } | null;
}

interface PatchesResponse {
  patches: Patch[];
  total: number;
  page: number;
  per_page: number;
}

const PAGE_SIZE = 24;

const SORT_OPTIONS = [
  { value: "date:desc", label: "Newest" },
  { value: "like_count:desc", label: "Most liked" },
  { value: "download_count:desc", label: "Most downloaded" },
  { value: "view_count:desc", label: "Most viewed" },
] as const;

export function CommunityPatches() {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [platformId, setPlatformId] = useState<string>("");
  const [patches, setPatches] = useState<Patch[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<string>("date:desc");

  useEffect(() => {
    const fetchPlatforms = async () => {
      try {
        const r = await fetch(`${API_BASE}/api/v1/patchstorage/platforms`);
        if (r.ok) {
          const data: { platforms: Platform[] } = await r.json();
          setPlatforms(data.platforms);
          const vcv = data.platforms.find((p) => p.slug === "vcv-rack");
          if (vcv) setPlatformId(String(vcv.id));
        }
      } catch {
        // platform dropdown just stays empty ("All platforms")
      }
    };
    void fetchPlatforms();
  }, []);

  useEffect(() => {
    const fetchPatches = async () => {
      setLoading(true);
      const [orderby, order] = sort.split(":");
      try {
        const params = new URLSearchParams({
          q: query,
          orderby,
          order,
          page: String(page),
          per_page: String(PAGE_SIZE),
        });
        if (platformId) params.set("platform_id", platformId);
        const r = await fetch(
          `${API_BASE}/api/v1/patchstorage/patches?${params}`,
        );
        if (r.ok) {
          const data: PatchesResponse = await r.json();
          setPatches(data.patches);
          setTotal(data.total);
        }
      } catch {
        setPatches([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    };
    void fetchPatches();
  }, [platformId, query, sort, page]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Community Patches
        </h1>
        <p className="text-slate-400">
          Browse user-submitted patches from{" "}
          <a
            href="https://patchstorage.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300"
          >
            Patchstorage.com
          </a>{" "}
          across {platforms.length || "92"} platforms — VCV Rack, SuperCollider,
          Max for Live, TouchOSC, and more.
        </p>
      </div>

      <Card className="border-slate-800 bg-slate-950/30">
        <CardContent className="pt-4 text-xs text-slate-500">
          This browses Patchstorage's public API for search only — click a patch
          to open its real page and download it there.
        </CardContent>
      </Card>

      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 min-w-[240px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search patches…"
            className="pl-9 bg-slate-900 border-slate-800 text-white placeholder:text-slate-400"
            value={query}
            onChange={(e) => {
              setPage(1);
              setQuery(e.target.value);
            }}
          />
        </div>
        <select
          className="bg-slate-900 border border-slate-800 text-white text-sm rounded-md px-3 py-2"
          value={platformId}
          onChange={(e) => {
            setPage(1);
            setPlatformId(e.target.value);
          }}
        >
          <option value="">All platforms</option>
          {platforms.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <select
          className="bg-slate-900 border border-slate-800 text-white text-sm rounded-md px-3 py-2"
          value={sort}
          onChange={(e) => {
            setPage(1);
            setSort(e.target.value);
          }}
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2 text-slate-400">
            <Activity className="h-5 w-5 animate-pulse" />
            <span>Loading patches…</span>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {patches.map((p) => (
            <a
              key={p.id}
              href={p.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block"
            >
              <Card className="border-slate-800 bg-slate-950/50 hover:bg-slate-900/80 transition-colors h-full group">
                {p.artwork?.thumbnail_url && (
                  <div className="aspect-[3/2] overflow-hidden rounded-t-lg bg-slate-900 flex items-center justify-center">
                    <img
                      src={p.artwork.thumbnail_url}
                      alt={p.title}
                      loading="lazy"
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>
                )}
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-sm font-semibold text-white flex items-center gap-1.5 min-w-0">
                      <Globe className="w-4 h-4 text-blue-500 shrink-0" />
                      <span className="truncate">{p.title}</span>
                    </CardTitle>
                    <ExternalLink className="h-3.5 w-3.5 text-slate-600 group-hover:text-slate-300 shrink-0" />
                  </div>
                  <CardDescription className="text-slate-500 text-xs">
                    {p.author.name}
                    {p.platform && ` · ${p.platform.name}`}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <p className="text-xs text-slate-400 line-clamp-2">
                    {p.excerpt}
                  </p>
                  <div className="flex items-center gap-3 flex-wrap text-[10px] text-slate-500">
                    <span className="flex items-center gap-1">
                      <Heart className="w-3 h-3" /> {p.like_count}
                    </span>
                    <span className="flex items-center gap-1">
                      <Download className="w-3 h-3" /> {p.download_count}
                    </span>
                    <span className="flex items-center gap-1">
                      <Eye className="w-3 h-3" /> {p.view_count}
                    </span>
                    {p.state && p.state.slug !== "published" && (
                      <Badge className="bg-amber-950/40 text-amber-400 border border-amber-800 text-[10px]">
                        {p.state.name}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </a>
          ))}
        </div>
      )}

      {!loading && patches.length === 0 && (
        <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-slate-800 rounded-lg bg-slate-950/20">
          <Globe className="h-10 w-10 text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-300">
            No patches match these filters
          </h3>
          <p className="text-sm text-slate-500">
            Try a broader search or a different platform.
          </p>
        </div>
      )}

      {!loading && total > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            className="border-slate-700"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </Button>
          <span className="text-sm text-slate-400">
            Page {page} of {totalPages} · {total.toLocaleString()} patches
          </span>
          <Button
            variant="outline"
            size="sm"
            className="border-slate-700"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}

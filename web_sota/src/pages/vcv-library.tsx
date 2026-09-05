import {
  Activity,
  ExternalLink,
  Puzzle,
  RefreshCw,
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

interface VcvModule {
  plugin_slug: string;
  module_slug: string;
  brand: string;
  name: string;
  description: string;
  tags: string[];
  price: string | null;
  is_plus: boolean;
  screenshot_url: string | null;
  module_url: string;
}

interface ModulesResponse {
  modules: VcvModule[];
  total: number;
  page: number;
  limit: number;
}

interface StatusResponse {
  last_synced_at: number | null;
  total_modules: number;
  syncing: boolean;
}

interface BrandsResponse {
  brands: { brand: string; count: number }[];
}

const PAGE_SIZE = 30;

export function VcvLibrary() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [modules, setModules] = useState<VcvModule[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [query, setQuery] = useState("");
  const [brand, setBrand] = useState("");
  const [license, setLicense] = useState("");
  const [brands, setBrands] = useState<{ brand: string; count: number }[]>([]);

  const fetchStatus = async () => {
    try {
      const r = await fetch(`${API_BASE}/api/v1/vcv-library/status`);
      if (r.ok) setStatus(await r.json());
    } catch {
      // backend-offline state is shown elsewhere on the dashboard
    }
  };

  const fetchBrands = async () => {
    try {
      const r = await fetch(`${API_BASE}/api/v1/vcv-library/brands`);
      if (r.ok) setBrands(((await r.json()) as BrandsResponse).brands);
    } catch {
      // non-fatal - brand filter just stays empty
    }
  };

  const fetchModules = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: query,
        brand,
        license,
        page: String(page),
        limit: String(PAGE_SIZE),
      });
      const r = await fetch(`${API_BASE}/api/v1/vcv-library/modules?${params}`);
      if (r.ok) {
        const data: ModulesResponse = await r.json();
        setModules(data.modules);
        setTotal(data.total);
      }
    } catch {
      setModules([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchStatus();
    void fetchBrands();
  }, []);

  useEffect(() => {
    void fetchModules();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, brand, license, page]);

  const runSync = async () => {
    setSyncing(true);
    try {
      await fetch(`${API_BASE}/api/v1/vcv-library/sync`, { method: "POST" });
      const poll = setInterval(async () => {
        const r = await fetch(`${API_BASE}/api/v1/vcv-library/status`);
        if (r.ok) {
          const s: StatusResponse = await r.json();
          setStatus(s);
          if (!s.syncing) {
            clearInterval(poll);
            setSyncing(false);
            void fetchModules();
            void fetchBrands();
          }
        }
      }, 3000);
    } catch {
      setSyncing(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const lastSynced = status?.last_synced_at
    ? new Date(status.last_synced_at * 1000).toLocaleString()
    : null;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            VCV Module Library
          </h1>
          <p className="text-slate-400">
            The official VCV Rack module marketplace —{" "}
            {status?.total_modules ?? "?"} modules cataloged
            {lastSynced && ` · last synced ${lastSynced}`}
          </p>
        </div>
        <Button
          onClick={runSync}
          disabled={syncing || status?.syncing}
          variant="outline"
          className="border-slate-700 hover:bg-slate-800"
        >
          <RefreshCw
            className={`w-4 h-4 mr-2 ${syncing || status?.syncing ? "animate-spin" : ""}`}
          />
          {syncing || status?.syncing ? "Syncing…" : "Sync catalog"}
        </Button>
      </div>

      <Card className="border-slate-800 bg-slate-950/30">
        <CardContent className="pt-4 text-xs text-slate-500">
          This catalog is scraped from{" "}
          <a
            href="https://library.vcvrack.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300"
          >
            library.vcvrack.com
          </a>{" "}
          for browsing and search only. Actually installing a module still needs
          your own VCV account — click a module to open its real page and use
          the "Add" + Rack's own "Library → Update all" flow there.
        </CardContent>
      </Card>

      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 min-w-[240px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search modules, brands, descriptions…"
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
          value={brand}
          onChange={(e) => {
            setPage(1);
            setBrand(e.target.value);
          }}
        >
          <option value="">All brands</option>
          {brands.map((b) => (
            <option key={b.brand} value={b.brand}>
              {b.brand} ({b.count})
            </option>
          ))}
        </select>
        <select
          className="bg-slate-900 border border-slate-800 text-white text-sm rounded-md px-3 py-2"
          value={license}
          onChange={(e) => {
            setPage(1);
            setLicense(e.target.value);
          }}
        >
          <option value="">Any license</option>
          <option value="free">Free</option>
          <option value="premium">Premium</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2 text-slate-400">
            <Activity className="h-5 w-5 animate-pulse" />
            <span>Loading catalog…</span>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {modules.map((m) => (
            <a
              key={`${m.plugin_slug}/${m.module_slug}`}
              href={`https://library.vcvrack.com${m.module_url}`}
              target="_blank"
              rel="noopener noreferrer"
              className="block"
            >
              <Card className="border-slate-800 bg-slate-950/50 hover:bg-slate-900/80 transition-colors h-full group">
                {m.screenshot_url && (
                  <div className="aspect-[3/1] overflow-hidden rounded-t-lg bg-slate-900 flex items-center justify-center">
                    <img
                      src={m.screenshot_url}
                      alt={m.name}
                      loading="lazy"
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>
                )}
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-sm font-semibold text-white flex items-center gap-1.5 min-w-0">
                      <Puzzle className="w-4 h-4 text-blue-500 shrink-0" />
                      <span className="truncate">{m.name}</span>
                    </CardTitle>
                    <ExternalLink className="h-3.5 w-3.5 text-slate-600 group-hover:text-slate-300 shrink-0" />
                  </div>
                  <CardDescription className="text-slate-500 text-xs">
                    {m.brand}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <p className="text-xs text-slate-400 line-clamp-2">
                    {m.description}
                  </p>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {m.price ? (
                      <Badge className="bg-amber-950/40 text-amber-400 border border-amber-800 text-[10px]">
                        ${m.price}
                      </Badge>
                    ) : (
                      <Badge className="bg-emerald-950/40 text-emerald-400 border border-emerald-800 text-[10px]">
                        Free
                      </Badge>
                    )}
                    {m.is_plus && (
                      <Badge className="bg-purple-950/40 text-purple-400 border border-purple-800 text-[10px]">
                        VCV+
                      </Badge>
                    )}
                    {m.tags.slice(0, 2).map((t) => (
                      <Badge
                        key={t}
                        variant="secondary"
                        className="bg-slate-800 text-slate-400 text-[10px]"
                      >
                        {t}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </a>
          ))}
        </div>
      )}

      {!loading && modules.length === 0 && (
        <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-slate-800 rounded-lg bg-slate-950/20">
          <Puzzle className="h-10 w-10 text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-300">
            {status?.total_modules
              ? "No modules match these filters"
              : "Catalog not synced yet"}
          </h3>
          <p className="text-sm text-slate-500">
            {status?.total_modules
              ? "Try a broader search or clear the brand/license filters."
              : 'Click "Sync catalog" above to pull the full VCV Library.'}
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
            Page {page} of {totalPages} · {total} modules
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

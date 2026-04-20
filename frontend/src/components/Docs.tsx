import { useEffect, useState } from "react";
import { api } from "../api";
import { store } from "../store";
import { Skel, SkelCard } from "./Skeleton";

type Stats = {
  built: boolean;
  files_extracted: number;
  entities_indexed: number;
  by_entity_type: Record<string, number>;
  by_extractor: Record<string, number>;
  pending: number;
  top_jobs: { value: string; count: number }[];
  top_vendors: { value: string; count: number }[];
};

const LABELS: Record<string, string> = {
  job: "Jobs", vendor: "Vendors", customer: "Customers",
  po: "POs", ap_invoice: "AP Invoices",
};

export default function Docs() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [q, setQ] = useState("");
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  useEffect(() => {
    const load = () => api.docintelStats().then(setStats).catch(() => {});
    load();
    const t = setInterval(load, 10_000); // live refresh
    return () => clearInterval(t);
  }, []);

  async function doSearch() {
    if (!q.trim()) return;
    setSearching(true);
    try {
      const r = await api.docintelSearch(q.trim());
      setResults(r);
    } finally {
      setSearching(false);
    }
  }

  if (!stats) return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <Skel className="h-7 w-64 mb-2" />
        <Skel className="h-3 w-3/4" />
      </div>
      <SkelCard><Skel className="h-4 w-40 mb-3" /><Skel className="h-2 w-full" /></SkelCard>
      <SkelCard />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SkelCard /><SkelCard />
      </div>
    </div>
  );

  const total = stats.files_extracted + stats.pending;
  const pct = total > 0 ? Math.round((stats.files_extracted / total) * 100) : 0;

  return (
    <div className="h-full overflow-y-auto scrollbar p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Document intelligence</h1>
        <div className="text-sm text-gray-400">
          Reading every PDF, Excel, and Word file on the NAS to link them to Spectrum jobs, vendors, customers, POs, and invoices.
        </div>
      </div>

      {/* Progress */}
      <div className="glass rounded-2xl p-5">
        <div className="flex items-baseline justify-between mb-2">
          <div className="font-semibold">Extraction progress</div>
          <div className="text-sm text-gray-400">
            {stats.files_extracted.toLocaleString()} of {total.toLocaleString()} ({pct}%)
          </div>
        </div>
        <div className="h-2 bg-white/5 rounded overflow-hidden">
          <div
            className="h-full bg-accent transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <KV label="Extracted"     value={stats.files_extracted.toLocaleString()} />
          <KV label="Entities"      value={stats.entities_indexed.toLocaleString()} />
          <KV label="Pending"       value={stats.pending.toLocaleString()} />
          <KV label="By extractor"  value={Object.entries(stats.by_extractor).map(([k,v]) => `${k}: ${v}`).join(" · ") || "—"} />
        </div>
      </div>

      {/* Entity type breakdown */}
      <div className="glass rounded-2xl p-5">
        <div className="font-semibold mb-3">Entities linked</div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(stats.by_entity_type).map(([type, count]) => (
            <div key={type} className="px-3 py-2 bg-white/5 rounded-lg">
              <div className="text-xs text-gray-400">{LABELS[type] ?? type}</div>
              <div className="text-xl font-semibold">{count.toLocaleString()}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Top entities */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass rounded-2xl p-5">
          <div className="font-semibold mb-3">Top jobs by mention</div>
          <div className="space-y-1">
            {stats.top_jobs.map(j => (
              <button
                key={j.value}
                onClick={() => store.openJob(j.value)}
                className="w-full text-left flex items-center justify-between px-2 py-1 hover:bg-white/5 rounded"
              >
                <span className="font-mono text-accent">{j.value}</span>
                <span className="text-sm text-gray-400">{j.count} files</span>
              </button>
            ))}
          </div>
        </div>
        <div className="glass rounded-2xl p-5">
          <div className="font-semibold mb-3">Top vendors by mention</div>
          <div className="space-y-1">
            {stats.top_vendors.map(v => (
              <div key={v.value} className="flex items-center justify-between px-2 py-1">
                <span className="font-mono">{v.value}</span>
                <span className="text-sm text-gray-400">{v.count} files</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Full-text search */}
      <div className="glass rounded-2xl p-5">
        <div className="font-semibold mb-3">Search across all extracted content</div>
        <div className="flex gap-2 mb-3">
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            onKeyDown={e => e.key === "Enter" && doSearch()}
            placeholder="e.g. change order, permit, certificate of insurance…"
            className="flex-1 bg-transparent border border-line rounded-lg px-3 py-2 text-sm outline-none focus:border-accent"
          />
          <button
            onClick={doSearch}
            disabled={searching || !q.trim()}
            className="px-4 py-2 rounded-lg bg-accent text-ink text-sm font-medium disabled:opacity-40"
          >
            {searching ? "…" : "Search"}
          </button>
        </div>
        {results.length > 0 && (
          <div className="text-xs space-y-1 max-h-96 overflow-y-auto scrollbar">
            {results.map((r: any) => (
              <button
                key={r.path}
                onClick={() => store.openFolder(r.path.replace(/\/[^/]+$/, ""))}
                className="w-full text-left hover:bg-white/5 px-2 py-1 rounded flex items-baseline gap-2"
              >
                <span>📄</span>
                <span className="truncate flex-1">{r.name}</span>
                <span className="text-gray-500 truncate">{r.path.replace(/\/[^/]+$/, "")}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function KV({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-gray-400">{label}</div>
      <div className="mt-0.5">{value}</div>
    </div>
  );
}

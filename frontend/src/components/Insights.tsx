import { useEffect, useState } from "react";
import { api } from "../api";
import { store } from "../store";
import { Skel, SkelCard } from "./Skeleton";

type Insight = {
  id: string;
  rule: string;
  severity: "critical" | "high" | "medium" | "low";
  title: string;
  detail: string;
  job_number?: string;
  customer_code?: string;
  vendor_code?: string;
  amount?: number;
};

const SEVERITY_STYLE: Record<string, string> = {
  critical: "border-red-500/40 bg-red-500/5",
  high: "border-amber-500/40 bg-amber-500/5",
  medium: "border-blue-500/40 bg-blue-500/5",
  low: "border-gray-500/40 bg-white/5",
};

const SEVERITY_DOT: Record<string, string> = {
  critical: "bg-red-400",
  high: "bg-amber-400",
  medium: "bg-blue-400",
  low: "bg-gray-500",
};

const RULE_LABEL: Record<string, string> = {
  over_budget: "OVER BUDGET",
  stale_ar: "STALE AR",
  duplicate_ap: "DUPLICATE AP",
  idle_job: "IDLE JOB",
};

export default function Insights() {
  const [data, setData] = useState<{ insights: Insight[]; counts: Record<string, number> } | null>(null);
  const [err, setErr] = useState<string>();
  const [briefing, setBriefing] = useState<string>();
  const [briefingLoading, setBriefingLoading] = useState(false);
  const [filter, setFilter] = useState<string | null>(null);

  useEffect(() => {
    api.insights().then(setData).catch(e => setErr(e.message));
  }, []);

  async function genBriefing() {
    setBriefingLoading(true);
    try {
      const r = await api.insightsBriefing();
      setBriefing(r.briefing);
    } catch (e: any) {
      setBriefing(`Error: ${e.message}`);
    } finally {
      setBriefingLoading(false);
    }
  }

  if (err) return <div className="p-6 text-red-300">Error: {err}</div>;
  if (!data) return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <Skel className="h-7 w-48 mb-2" />
        <Skel className="h-3 w-3/4" />
      </div>
      <div className="flex gap-3 flex-wrap">
        {Array.from({length:4}).map((_,i)=>(
          <div key={i} className="glass rounded-xl px-4 py-3 w-36">
            <Skel className="h-2 w-12 mb-2" />
            <Skel className="h-5 w-16" />
          </div>
        ))}
      </div>
      <SkelCard />
      <div className="space-y-2">
        {Array.from({length:6}).map((_,i)=>(
          <div key={i} className="glass rounded-xl p-4">
            <Skel className="h-3 w-3/4 mb-2" />
            <Skel className="h-2 w-1/2" />
          </div>
        ))}
      </div>
    </div>
  );

  const shown = filter ? data.insights.filter(i => i.severity === filter) : data.insights;

  return (
    <div className="h-full overflow-y-auto scrollbar p-6 max-w-6xl mx-auto space-y-6">
      {/* Headline counts */}
      <div>
        <h1 className="text-2xl font-semibold">Today's signal</h1>
        <div className="text-sm text-gray-400">
          The things in your company that changed or need attention right now.
        </div>
      </div>

      <div className="flex gap-3 flex-wrap">
        {(["critical", "high", "medium", "low"] as const).map(s => (
          <button
            key={s}
            onClick={() => setFilter(filter === s ? null : s)}
            className={`glass rounded-xl px-4 py-3 flex items-center gap-3 transition ${
              filter === s ? "ring-2 ring-accent" : ""
            }`}
          >
            <span className={`w-2.5 h-2.5 rounded-full ${SEVERITY_DOT[s]}`} />
            <div className="text-left">
              <div className="text-xs text-gray-400 uppercase tracking-wider">{s}</div>
              <div className="text-xl font-semibold">{data.counts[s] ?? 0}</div>
            </div>
          </button>
        ))}
        {filter && (
          <button onClick={() => setFilter(null)} className="text-xs text-gray-400 self-center hover:text-white">
            Clear filter
          </button>
        )}
      </div>

      {/* Morning briefing */}
      <div className="glass rounded-2xl p-5 border border-accent/30">
        <div className="flex items-center justify-between mb-2">
          <div className="font-semibold flex items-center gap-2">
            <span>✦</span> Morning briefing
          </div>
          {!briefing && !briefingLoading && (
            <button
              onClick={genBriefing}
              className="text-xs px-3 py-1 rounded bg-accent/20 text-accent hover:bg-accent/30"
            >
              Generate
            </button>
          )}
          {briefing && !briefingLoading && (
            <button onClick={genBriefing} className="text-xs text-gray-400 hover:text-white">
              Regenerate
            </button>
          )}
        </div>
        {briefingLoading && <div className="text-sm text-gray-400 italic">Claude is reading today's insights…</div>}
        {briefing ? (
          <div className="text-sm leading-relaxed whitespace-pre-wrap">{briefing}</div>
        ) : !briefingLoading && (
          <div className="text-sm text-gray-500">
            Click Generate for a 60-second briefing on what to act on today.
          </div>
        )}
      </div>

      {/* Insights list */}
      <div className="space-y-2">
        {shown.length === 0 && (
          <div className="text-sm text-gray-400 py-8 text-center">No insights at this severity.</div>
        )}
        {shown.map(i => (
          <div key={i.id} className={`rounded-xl border p-4 ${SEVERITY_STYLE[i.severity] ?? ""}`}>
            <div className="flex items-start gap-3">
              <span className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${SEVERITY_DOT[i.severity]}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="text-[10px] uppercase tracking-widest text-gray-400 font-mono">
                    {RULE_LABEL[i.rule] ?? i.rule}
                  </span>
                  <span className="font-medium">{i.title}</span>
                </div>
                <div className="text-sm text-gray-300 mt-1">{i.detail}</div>
                <div className="flex gap-3 mt-2">
                  {i.job_number && (
                    <button
                      onClick={() => store.openJob(i.job_number!)}
                      className="text-xs text-accent hover:underline"
                    >
                      Open job {i.job_number} ↗
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

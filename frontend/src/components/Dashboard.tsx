import { useEffect, useState } from "react";
import { api } from "../api";
import { store } from "../store";
import { Skel, SkelTable } from "./Skeleton";

type Panel = { key: string; title: string; subtitle?: string };

const SUBTITLES: Record<string, string> = {
  active_jobs: "Active jobs ranked by contract value",
  ar_aging: "Unpaid invoices, oldest first",
  top_customers_ytd: "Biggest customers this year (from invoice history)",
  top_vendors_ytd: "Biggest vendor payments this year",
  jobs_over_budget: "Active jobs by % of contract spent",
  recent_billings: "AIA billing apps in the last 90 days",
  open_pos: "Open purchase orders",
};

export default function Dashboard() {
  const [panels, setPanels] = useState<Panel[]>([]);

  useEffect(() => {
    api.dashboardList().then(ps =>
      setPanels(ps.map(p => ({ ...p, subtitle: SUBTITLES[p.key] }))),
    );
  }, []);

  return (
    <div className="h-full overflow-y-auto scrollbar p-6 space-y-6">
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {panels.map(p => <PanelCard key={p.key} panel={p} />)}
      </div>
    </div>
  );
}

function PanelCard({ panel }: { panel: Panel }) {
  const [data, setData] = useState<{ columns: string[]; rows: any[] } | null>(null);
  const [err, setErr] = useState<string>();

  useEffect(() => {
    setData(null); setErr(undefined);
    api.dashboard(panel.key).then(setData).catch(e => setErr(e.message));
  }, [panel.key]);

  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-baseline justify-between mb-4">
        <div>
          <div className="font-semibold">{panel.title}</div>
          {panel.subtitle && <div className="text-xs text-gray-400">{panel.subtitle}</div>}
        </div>
        {data && <div className="text-xs text-gray-500">{data.rows.length} rows</div>}
      </div>
      {err && <div className="text-sm text-red-300">{err}</div>}
      {!err && !data && <SkelTable rows={5} cols={5} />}
      {data && data.rows.length === 0 && (
        <div className="text-sm text-gray-400">No matching records.</div>
      )}
      {data && data.rows.length > 0 && (
        <div className="overflow-x-auto scrollbar">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="text-left text-gray-400 border-b border-line">
                {data.columns.map(c => (
                  <th key={c} className="px-2 py-1 whitespace-nowrap">{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.slice(0, 20).map((r, i) => (
                <tr key={i} className="border-b border-line/50 hover:bg-white/5">
                  {data.columns.map(c => (
                    <td key={c} className="px-2 py-1 font-mono whitespace-nowrap">
                      {c === "Job_Number" && r[c]
                        ? <JobCell jobNumber={String(r[c])} />
                        : fmt(r[c], c)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function JobCell({ jobNumber }: { jobNumber: string }) {
  return (
    <button
      onClick={() => store.openJob(jobNumber)}
      className="text-accent hover:underline"
      title="Open Job Command Center"
    >
      {jobNumber.trim()} ↗
    </button>
  );
}

function fmt(v: any, col: string): string {
  if (v == null || v === "") return "";
  // Currency-ish columns
  if (typeof v === "number" && /amount|contract|cost|balance|paid|billed|variance|extension|total|due/i.test(col)) {
    return "$" + v.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }
  // Dates coming back as ISO strings
  if (typeof v === "string" && /^\d{4}-\d{2}-\d{2}T/.test(v)) {
    return v.slice(0, 10);
  }
  return String(v);
}

import { useEffect, useState } from "react";
import { api } from "../api";
import { store, useStore } from "../store";
import { Skel, SkelCard, SkelKpi, SkelListRow, SkelTable, SkelText } from "./Skeleton";

type AtRisk = {
  Job_Number: string;
  Job_Description: string;
  Project_Manager: string;
  Original_Contract: number;
  Revised_Contract: number;
  Actual_Cost: number;
  Pct_Spent: number;
  Days_Since_Cost: number;
};

export default function Jobs() {
  const { openJob } = useStore();
  const [atRisk, setAtRisk] = useState<AtRisk[]>([]);
  const [search, setSearch] = useState("");
  const [active, setActive] = useState<string | null>(openJob ?? null);

  useEffect(() => { api.jobsAtRisk().then(setAtRisk).catch(() => {}); }, []);
  useEffect(() => { if (openJob) setActive(openJob); }, [openJob]);

  return (
    <div className="h-full flex">
      <aside className="w-80 border-r border-line flex flex-col">
        <div className="p-3 border-b border-line">
          <div className="text-xs text-gray-400 mb-2">Jump to job</div>
          <div className="flex gap-2">
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              onKeyDown={e => e.key === "Enter" && search.trim() && setActive(search.trim())}
              placeholder="Job # (e.g. 26.07)"
              className="flex-1 glass rounded-lg px-3 py-2 text-sm outline-none"
            />
            <button
              onClick={() => search.trim() && setActive(search.trim())}
              className="px-3 py-2 rounded-lg bg-accent text-ink text-sm font-medium"
            >Go</button>
          </div>
        </div>
        <div className="p-3 border-b border-line text-xs uppercase tracking-wider text-gray-400">
          Jobs at risk
        </div>
        <div className="flex-1 overflow-y-auto scrollbar">
          {atRisk.length === 0 && (
            <>{Array.from({length: 8}).map((_, i) => <SkelListRow key={i} />)}</>
          )}
          {atRisk.map(j => (
            <button
              key={j.Job_Number}
              onClick={() => setActive(j.Job_Number)}
              className={`w-full text-left px-4 py-3 border-b border-line/50 hover:bg-white/5 ${
                active === j.Job_Number ? "bg-accent/10" : ""
              }`}
            >
              <div className="flex items-baseline justify-between">
                <div className="font-mono font-semibold text-sm">{j.Job_Number}</div>
                <div className={`text-xs ${j.Pct_Spent > 100 ? "text-red-400" : j.Pct_Spent > 85 ? "text-amber-400" : "text-gray-400"}`}>
                  {j.Pct_Spent}%
                </div>
              </div>
              <div className="text-xs text-gray-300 truncate">{j.Job_Description}</div>
              <div className="text-[10px] text-gray-500 mt-1">
                PM {j.Project_Manager} · {j.Days_Since_Cost ?? "—"}d idle
              </div>
            </button>
          ))}
        </div>
      </aside>

      <div className="flex-1 overflow-y-auto scrollbar">
        {active ? <JobDetail key={active} jobNumber={active} /> : <EmptyHint />}
      </div>
    </div>
  );
}

function EmptyHint() {
  return (
    <div className="h-full flex items-center justify-center text-gray-400">
      <div className="text-center">
        <div className="text-lg">Pick a job from the left, or search by number.</div>
        <div className="text-sm mt-2">e.g. 26.07 (Moxy Hotels) · 19.50 (Sutter Hotel)</div>
      </div>
    </div>
  );
}

function JobDetail({ jobNumber }: { jobNumber: string }) {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string>();
  const [narr, setNarr] = useState<string>();
  const [narrLoading, setNarrLoading] = useState(false);

  useEffect(() => {
    setData(null); setErr(undefined); setNarr(undefined);
    api.jobDetail(jobNumber).then(setData).catch(e => setErr(e.message));
  }, [jobNumber]);

  async function genNarrative() {
    setNarrLoading(true);
    try {
      const r = await api.jobNarrative(jobNumber);
      setNarr(r.narrative);
    } catch (e: any) { setNarr(`Error: ${e.message}`); }
    finally { setNarrLoading(false); }
  }

  if (err) return <div className="p-6 text-red-300">Error: {err}</div>;
  if (!data) return <JobDetailSkeleton />;
  if (!data.found) return <div className="p-6 text-gray-400">Job <b>{jobNumber}</b> not found.</div>;

  const m = data.master, f = data.financials, lb = data.last_billing, ar = data.ar, nas = data.nas;

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div>
        <div className="text-xs text-gray-400 font-mono">{m.Job_Number} · {m.Status_Code === "A" ? "Active" : m.Status_Code}</div>
        <h1 className="text-2xl font-semibold">{m.Job_Description}</h1>
        <div className="text-sm text-gray-400">
          {m.Location} · Customer <b>{data.customer?.Customer_Name ?? m.Customer_Code}</b> ·
          PM <b>{m.Project_Manager || "—"}</b>
          {m.Superintendent && <> · Super <b>{m.Superintendent}</b></>}
          {m.Estimator && <> · Est <b>{m.Estimator}</b></>}
        </div>
      </div>

      {/* Financial strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Kpi label="Contract" value={fmtMoney(f.original_contract)} />
        <Kpi label="Actual cost" value={fmtMoney(f.actual_cost)} />
        <Kpi
          label="% spent"
          value={`${f.pct_spent}%`}
          tone={f.pct_spent > 100 ? "bad" : f.pct_spent > 85 ? "warn" : "ok"}
        />
        <Kpi label="Hours" value={f.total_hours.toLocaleString(undefined, { maximumFractionDigits: 0 })} />
      </div>

      {/* AI narrative */}
      <div className="glass rounded-2xl p-5">
        <div className="flex items-center justify-between mb-2">
          <div className="font-semibold">State of the job</div>
          {!narr && !narrLoading && (
            <button onClick={genNarrative} className="text-xs px-3 py-1 rounded bg-accent/20 text-accent hover:bg-accent/30">
              ✦ Generate
            </button>
          )}
        </div>
        {narrLoading && <div className="text-sm text-gray-400 italic">Reading the job…</div>}
        {narr ? <div className="text-sm leading-relaxed whitespace-pre-wrap">{narr}</div>
              : !narrLoading && <div className="text-sm text-gray-500">Click Generate for a Claude-written briefing on this job.</div>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Section title="Cost by type">
          <MiniTable
            columns={["Cost_Type","Amount","Hours"]}
            rows={data.cost_by_type ?? []}
            fmtFn={(v,c) => c === "Amount" ? fmtMoney(v) : c === "Hours" ? v.toLocaleString(undefined, { maximumFractionDigits: 0 }) : String(v).trim()}
          />
        </Section>

        <Section title="Latest billing">
          {lb ? (
            <div className="text-sm space-y-1">
              <div>App #<b>{String(lb.Application_Number).trim()}</b> period ending {lb.Period_End_Date?.slice(0,10)}</div>
              <div>Revised contract: <b>{fmtMoney(lb.Revised_Contract_Amount)}</b></div>
              <div>Complete to date: <b>{fmtMoney(lb.Complete_To_Date)}</b></div>
              <div>Retention: <b>{fmtMoney(lb.Retention_Amount)}</b></div>
              <div>Amount due: <b className={lb.Amount_Due > 0 ? "text-amber-300" : ""}>{fmtMoney(lb.Amount_Due)}</b></div>
            </div>
          ) : <div className="text-sm text-gray-400">No billing applications yet.</div>}
        </Section>

        <Section title="Outstanding AR (this job)">
          <div className="text-sm">
            {ar.Open_Invoice_Count ?? 0} invoices, {fmtMoney(ar.Billed_Total ?? 0)} total ·
            oldest <b>{ar.Oldest_Age_Days ?? "—"}d</b>
          </div>
        </Section>

        <Section title="NAS folder">
          {nas.folder ? (
            <>
              <button
                onClick={() => store.openFolder(nas.folder)}
                className="text-accent hover:underline text-sm mb-2"
              >Open {nas.folder} ↗</button>
              <div className="text-xs text-gray-400 space-y-0.5">
                {nas.preview.map((e: any) => (
                  <div key={e.path} className="truncate">{e.is_dir ? "📁" : "📎"} {e.name}</div>
                ))}
              </div>
            </>
          ) : <div className="text-sm text-gray-400">No matching NAS folder for job {m.Job_Number}.</div>}
        </Section>

        <Section title="Spectrum DI (scanned docs)">
          {data.di?.counts_by_drawer?.length ? (
            <>
              <div className="flex flex-wrap gap-2 mb-3">
                {data.di.counts_by_drawer.map((c: any) => (
                  <span key={c.Drawer} className="text-xs glass rounded px-2 py-1">
                    <b>{c.N}</b> <span className="text-gray-400">{c.Drawer}</span>
                  </span>
                ))}
              </div>
              <div className="text-xs text-gray-400 space-y-0.5 max-h-40 overflow-y-auto scrollbar">
                {data.di.recent.slice(0, 15).map((r: any, i: number) => (
                  <div key={i} className="truncate">
                    <span className="text-gray-500">[{r.Drawer}]</span>{" "}
                    {r.Description || r.Reference}
                    {r.Filename && <span className="text-gray-500"> · {r.Filename}</span>}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="text-sm text-gray-400">No Spectrum DI records for this job.</div>
          )}
        </Section>
      </div>

      <Section title={`Linked NAS files (${data.linked_files?.length ?? 0})`}>
        <div className="text-xs text-gray-400 mb-2">
          Any NAS file whose content mentions this job OR anything tied to it in Spectrum
          (its POs, AP invoices, or customer). Each row shows why it matched.
        </div>
        {data.linked_files?.length ? (
          <div className="text-xs space-y-1 max-h-80 overflow-y-auto scrollbar">
            {data.linked_files.map((f: any) => (
              <button
                key={f.path}
                onClick={() => store.openFolder(f.path.replace(/\/[^/]+$/, ""))}
                className="w-full text-left hover:bg-white/5 px-2 py-1 rounded flex items-baseline gap-2"
              >
                <span>{f.primary_tag === "po" ? "📘" : f.primary_tag === "ap_invoice" ? "🧾" : f.primary_tag === "customer" ? "👤" : "📄"}</span>
                <span className="truncate flex-1">{f.name}</span>
                <span className="text-[10px] text-gray-500 whitespace-nowrap">
                  {(f.reasons ?? []).slice(0,2).join(" · ")}
                </span>
                <span className="text-gray-500 truncate hidden md:inline max-w-[30%]">{f.path.replace(/\/[^/]+$/, "")}</span>
              </button>
            ))}
          </div>
        ) : (
          <div className="text-xs text-gray-500">
            None yet — the document intelligence extractor hasn't reached these files.
            More appear as the background extractor runs.
          </div>
        )}
      </Section>

      {(() => {
        const allAp = (data.recent_ap ?? []) as any[];
        const vendorAp = allAp.filter((r: any) => !r.Is_Employee);
        const employeeAp = allAp.filter((r: any) => !!r.Is_Employee);
        const apV = data.ap_total_vendor ?? { amount: 0, invoice_count: 0 };
        const apE = data.ap_total_employee ?? { amount: 0, invoice_count: 0 };
        return (
          <>
            <Section title={`Vendor invoices — ${fmtMoney(apV.amount)} across ${apV.invoice_count} invoices (${vendorAp.length} shown)`}>
              <div className="text-xs text-gray-400 mb-2">
                True third-party vendor invoices posted to this job. Amount shown is the per-job
                share (from the invoice detail), not the invoice header total.
              </div>
              <APTable rows={vendorAp} />
            </Section>

            <Section title={`Employee expenses — ${fmtMoney(apE.amount)} across ${apE.invoice_count} invoices (${employeeAp.length} shown)`}>
              <div className="text-xs text-gray-400 mb-2">
                Employee expense reports posted as AP (vendor Type is <span className="font-mono">EMPL</span>/<span className="font-mono">1099</span> or has an SSN on file).
                These are reimbursements, not third-party purchases.
              </div>
              <APTable rows={employeeAp} />
            </Section>
          </>
        );
      })()}

      <Section title={`Labor last 30 days (${data.recent_labor.length})`}>
        <MiniTable
          columns={["Employee_Code","Hours","Pay","Last_Work_Date"]}
          rows={data.recent_labor}
          fmtFn={(v,c) => c === "Pay" ? fmtMoney(v) : c === "Hours" ? Number(v).toFixed(1) : c === "Last_Work_Date" && v ? String(v).slice(0,10) : String(v).trim()}
        />
      </Section>

      <Section title={`Open POs (${data.open_pos.length})`}>
        <MiniTable
          columns={["PO_Number","Vendor_Name","PO_Date","PO_Total","Received_Total"]}
          rows={data.open_pos}
          fmtFn={(v,c) => c.includes("Total") ? fmtMoney(v) : c === "PO_Date" && v ? String(v).slice(0,10) : String(v ?? "").trim()}
        />
      </Section>
    </div>
  );
}

function APTable({ rows }: { rows: any[] }) {
  const [trace, setTrace] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function openTrace(vendor: string, invoice: string) {
    setLoading(true);
    setTrace({ loading: true });
    try {
      const r = await api.invoiceTrace(vendor, invoice);
      setTrace(r);
    } catch (e: any) {
      setTrace({ error: e.message });
    } finally {
      setLoading(false);
    }
  }

  if (!rows.length) return <div className="text-sm text-gray-400">No AP postings.</div>;

  return (
    <>
      <div className="overflow-x-auto scrollbar">
        <table className="min-w-full text-xs">
          <thead>
            <tr className="text-left text-gray-400 border-b border-line">
              <th className="px-2 py-1 whitespace-nowrap">Check Date</th>
              <th className="px-2 py-1 whitespace-nowrap">Vendor</th>
              <th className="px-2 py-1 whitespace-nowrap">Invoice</th>
              <th className="px-2 py-1 whitespace-nowrap text-right">Job share</th>
              <th className="px-2 py-1 whitespace-nowrap text-right">Invoice total</th>
              <th className="px-2 py-1 whitespace-nowrap">Phase/Type</th>
              <th className="px-2 py-1 whitespace-nowrap">Check #</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r: any, i: number) => {
              const split = r.Invoice_Total > 0 && Math.abs(r.Job_Amount - r.Invoice_Total) > 0.5;
              return (
                <tr key={i} className="border-b border-line/50 hover:bg-white/5">
                  <td className="px-2 py-1 font-mono whitespace-nowrap">{r.Check_Date ? String(r.Check_Date).slice(0,10) : ""}</td>
                  <td className="px-2 py-1 whitespace-nowrap">{(r.Vendor_Name ?? "").trim() || r.Vendor_Code}</td>
                  <td className="px-2 py-1 font-mono whitespace-nowrap">
                    <button
                      onClick={() => openTrace(r.Vendor_Code, r.Invoice_Number)}
                      className="text-accent hover:underline"
                      title="Trace this invoice across all jobs"
                    >
                      {String(r.Invoice_Number).trim()} ↗
                    </button>
                  </td>
                  <td className="px-2 py-1 font-mono whitespace-nowrap text-right">{fmtMoney(r.Job_Amount)}</td>
                  <td className="px-2 py-1 font-mono whitespace-nowrap text-right text-gray-500">
                    {fmtMoney(r.Invoice_Total)}
                    {split && <span className="ml-1 text-[10px] text-amber-300" title="Invoice is split across jobs">split</span>}
                  </td>
                  <td className="px-2 py-1 font-mono whitespace-nowrap">{(r.Phase_Code ?? "").trim()} / {(r.Cost_Type ?? "").trim()}</td>
                  <td className="px-2 py-1 font-mono whitespace-nowrap">{(r.Check_Number ?? "").trim()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {trace && <InvoiceTraceModal trace={trace} onClose={() => setTrace(null)} />}
    </>
  );
}

function InvoiceTraceModal({ trace, onClose }: { trace: any; onClose: () => void }) {
  if (trace.loading) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
        <div className="glass rounded-2xl p-6 text-gray-300">Tracing invoice…</div>
      </div>
    );
  }
  if (trace.error) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
        <div className="glass rounded-2xl p-6 text-red-300">Error: {trace.error}</div>
      </div>
    );
  }
  if (!trace.found) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
        <div className="glass rounded-2xl p-6 text-gray-300">Invoice not found.</div>
      </div>
    );
  }
  const h = trace.header;
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-6" onClick={onClose}>
      <div className="glass rounded-2xl p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto scrollbar" onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="text-xs text-gray-400 font-mono">{String(h.Vendor_Code).trim()} · Invoice {String(h.Invoice_Number).trim()}</div>
            <h2 className="text-xl font-semibold">{String(h.Vendor_Name).trim()}</h2>
            <div className="text-sm text-gray-400">
              {fmtMoney(h.Invoice_Amount)} total
              {h.Check_Number?.trim() && <> · Check #{h.Check_Number.trim()}</>}
              {h.Check_Date && <> · Paid {String(h.Check_Date).slice(0,10)}</>}
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">✕</button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <div className="font-semibold text-sm mb-2">By job</div>
            <div className="text-xs space-y-1">
              {trace.rollup_by_job.map((r: any) => (
                <div key={r.job} className="flex justify-between px-2 py-1 bg-white/5 rounded">
                  <span className="font-mono">{r.job || "(unassigned)"}</span>
                  <span className="font-mono">{fmtMoney(r.amount)}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div className="font-semibold text-sm mb-2">By cost type</div>
            <div className="text-xs space-y-1">
              {trace.rollup_by_cost_type.map((r: any) => (
                <div key={r.cost_type} className="flex justify-between px-2 py-1 bg-white/5 rounded">
                  <span className="font-mono">{r.cost_type}</span>
                  <span className="font-mono">{fmtMoney(r.amount)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {trace.linked_files?.length > 0 && (
          <div className="mb-4">
            <div className="font-semibold text-sm mb-2">
              📎 NAS files mentioning this invoice ({trace.linked_files.length})
            </div>
            <div className="text-xs space-y-1 max-h-40 overflow-y-auto scrollbar">
              {trace.linked_files.map((f: any) => (
                <div key={f.path} className="px-2 py-1 bg-white/5 rounded flex items-baseline gap-2">
                  <span>📄</span>
                  <span className="truncate flex-1">{f.name}</span>
                  <span className="text-gray-500 truncate">{f.path.replace(/\/[^/]+$/, "")}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <details>
          <summary className="text-sm text-gray-400 cursor-pointer hover:text-white mb-2">
            All {trace.line_count} detail lines ({fmtMoney(trace.lines_total)} total
            {Math.abs(trace.reconciliation_delta) > 0.5 && <span className="text-amber-300"> · Δ vs header {fmtMoney(trace.reconciliation_delta)}</span>})
          </summary>
          <div className="overflow-x-auto scrollbar mt-2">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="text-left text-gray-400 border-b border-line">
                  <th className="px-2 py-1">Seq</th>
                  <th className="px-2 py-1">Job</th>
                  <th className="px-2 py-1">Phase</th>
                  <th className="px-2 py-1">Cost Type</th>
                  <th className="px-2 py-1 text-right">Amount</th>
                  <th className="px-2 py-1">Remarks</th>
                </tr>
              </thead>
              <tbody>
                {trace.lines.map((l: any, i: number) => (
                  <tr key={i} className="border-b border-line/50">
                    <td className="px-2 py-1 font-mono">{l.Sequence}</td>
                    <td className="px-2 py-1 font-mono">{l.Job_Number}</td>
                    <td className="px-2 py-1 font-mono">{l.Phase_Code}</td>
                    <td className="px-2 py-1 font-mono">{l.Cost_Type}</td>
                    <td className="px-2 py-1 font-mono text-right">{fmtMoney(l.Amount)}</td>
                    <td className="px-2 py-1">{l.Remarks || l.Item_Desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </div>
    </div>
  );
}

function JobDetailSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div>
        <Skel className="h-3 w-24 mb-2" />
        <Skel className="h-7 w-80 mb-2" />
        <Skel className="h-3 w-1/2" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({length: 4}).map((_, i) => <SkelKpi key={i} />)}
      </div>
      <SkelCard />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkelCard />
        <SkelCard />
        <SkelCard />
        <SkelCard />
      </div>
      <SkelCard>
        <Skel className="h-4 w-40 mb-3" />
        <SkelTable rows={5} cols={6} />
      </SkelCard>
    </div>
  );
}

function Kpi({ label, value, tone }: { label: string; value: string; tone?: "ok" | "warn" | "bad" }) {
  const color =
    tone === "bad" ? "text-red-400" :
    tone === "warn" ? "text-amber-300" : "text-white";
  return (
    <div className="glass rounded-xl p-4">
      <div className="text-xs text-gray-400">{label}</div>
      <div className={`text-2xl font-semibold mt-1 ${color}`}>{value}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="font-semibold mb-3">{title}</div>
      {children}
    </div>
  );
}

function MiniTable({ columns, rows, fmtFn }: {
  columns: string[]; rows: any[]; fmtFn: (v: any, c: string) => string;
}) {
  if (!rows.length) return <div className="text-sm text-gray-400">None.</div>;
  return (
    <div className="overflow-x-auto scrollbar">
      <table className="min-w-full text-xs">
        <thead>
          <tr className="text-left text-gray-400 border-b border-line">
            {columns.map(c => <th key={c} className="px-2 py-1 whitespace-nowrap">{c.replace(/_/g," ")}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 20).map((r, i) => (
            <tr key={i} className="border-b border-line/50">
              {columns.map(c => (
                <td key={c} className="px-2 py-1 font-mono whitespace-nowrap">{fmtFn(r[c], c)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function fmtMoney(v: any): string {
  if (v == null || isNaN(v)) return "—";
  return "$" + Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 });
}

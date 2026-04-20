import { useEffect, useState } from "react";
import { api } from "../api";
import { store, useStore } from "../store";
import { Skel, SkelCard, SkelKpi, SkelListRow, SkelTable } from "./Skeleton";

type Vendor = {
  Vendor_Code: string;
  Vendor_Name: string;
  Vendor_Type: string;
  Balance: number;
  Date_Last_Invoice: string | null;
  Has_SSN: number;
};

export default function Vendors() {
  const { openVendor } = useStore();
  const [list, setList] = useState<Vendor[]>([]);
  const [q, setQ] = useState("");
  const [empOnly, setEmpOnly] = useState(false);
  const [active, setActive] = useState<string | null>(openVendor ?? null);

  useEffect(() => {
    api.vendorList(q, empOnly).then(setList).catch(() => {});
  }, [q, empOnly]);
  useEffect(() => { if (openVendor) setActive(openVendor); }, [openVendor]);

  return (
    <div className="h-full flex">
      <aside className="w-80 border-r border-line flex flex-col">
        <div className="p-3 border-b border-line space-y-2">
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Search vendor / employee"
            className="w-full glass rounded-lg px-3 py-2 text-sm outline-none"
          />
          <label className="flex items-center gap-2 text-xs text-gray-400">
            <input type="checkbox" checked={empOnly} onChange={e => setEmpOnly(e.target.checked)} />
            Employees / expense-reimbursement vendors only
          </label>
        </div>
        <div className="flex-1 overflow-y-auto scrollbar">
          {list.map(v => (
            <button
              key={v.Vendor_Code}
              onClick={() => setActive(v.Vendor_Code)}
              className={`w-full text-left px-4 py-3 border-b border-line/50 hover:bg-white/5 ${active === v.Vendor_Code ? "bg-accent/10" : ""}`}
            >
              <div className="flex items-baseline justify-between gap-2">
                <div className="font-mono font-semibold text-sm truncate">{v.Vendor_Code}</div>
                {v.Has_SSN === 1 && <span className="text-[10px] text-emerald-300" title="Has SSN — likely employee/1099">person</span>}
              </div>
              <div className="text-xs text-gray-300 truncate">{v.Vendor_Name}</div>
              <div className="text-[10px] text-gray-500 mt-1">
                type {v.Vendor_Type || "—"} · bal {fmtMoney(v.Balance)}
                {v.Date_Last_Invoice && <> · last {String(v.Date_Last_Invoice).slice(0,10)}</>}
              </div>
            </button>
          ))}
          {list.length === 0 && (
            Array.from({length: 8}).map((_, i) => <SkelListRow key={i} />)
          )}
        </div>
      </aside>

      <div className="flex-1 overflow-y-auto scrollbar">
        {active ? <VendorDetail key={active} code={active} /> : (
          <div className="h-full flex items-center justify-center text-gray-400">
            Pick a vendor or employee from the list.
          </div>
        )}
      </div>
    </div>
  );
}

function VendorDetail({ code }: { code: string }) {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string>();
  const [traceOpen, setTraceOpen] = useState<{vendor: string; invoice: string} | null>(null);

  useEffect(() => {
    setData(null); setErr(undefined);
    api.vendorSpend(code).then(setData).catch(e => setErr(e.message));
  }, [code]);

  if (err) return <div className="p-6 text-red-300">Error: {err}</div>;
  if (!data) return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div>
        <Skel className="h-3 w-24 mb-2" />
        <Skel className="h-7 w-72 mb-2" />
        <Skel className="h-3 w-1/2" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({length:4}).map((_,i)=><SkelKpi key={i}/>)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkelCard /><SkelCard />
      </div>
      <SkelCard>
        <Skel className="h-4 w-32 mb-3" />
        <SkelTable rows={5} cols={6} />
      </SkelCard>
    </div>
  );

  const v = data.vendor;
  if (!v) return <div className="p-6 text-gray-400">Vendor not found.</div>;
  const t = data.totals ?? {};

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div>
        <div className="text-xs text-gray-400 font-mono">{v.Vendor_Code} · type {v.Vendor_Type || "—"}</div>
        <div className="flex items-baseline gap-3 flex-wrap">
          <h1 className="text-2xl font-semibold">{v.Vendor_Name}</h1>
          {data.is_employee_reimbursement && (
            <span className="text-xs px-2 py-1 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              Employee expense reimbursement
              {data.matched_employee && <> · emp {data.matched_employee.Employee_Code}</>}
            </span>
          )}
        </div>
        <div className="text-sm text-gray-400">
          Balance <b>{fmtMoney(v.Balance)}</b>
          {v.Date_Last_Invoice && <> · Last invoice {String(v.Date_Last_Invoice).slice(0,10)}</>}
          {v.Date_Last_Payment && <> · Last payment {String(v.Date_Last_Payment).slice(0,10)}</>}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Kpi label={`Spend (${data.window_days}d)`} value={fmtMoney(t.Total_Spend)} />
        <Kpi label="Invoices" value={String(t.Invoice_Count ?? 0)} />
        <Kpi label="Distinct jobs hit" value={String(t.Distinct_Jobs ?? 0)} />
        <Kpi label="Current balance" value={fmtMoney(v.Balance)} tone={v.Balance > 0 ? "warn" : "ok"} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Section title="By job">
          {data.by_job.length ? (
            <div className="text-xs space-y-1 max-h-72 overflow-y-auto scrollbar">
              {data.by_job.map((r: any) => (
                <button
                  key={r.Job_Number}
                  onClick={() => store.openJob(r.Job_Number)}
                  className="w-full flex items-baseline justify-between px-2 py-1 hover:bg-white/5 rounded"
                >
                  <span className="font-mono text-accent truncate">{r.Job_Number}</span>
                  <span className="font-mono">{fmtMoney(r.Amount)}</span>
                  <span className="text-gray-500 text-[10px]">{r.Invoices} inv</span>
                </button>
              ))}
            </div>
          ) : <div className="text-sm text-gray-400">No job-attributed spend.</div>}
        </Section>
        <Section title="By cost type">
          {data.by_cost_type.length ? (
            <div className="text-xs space-y-1">
              {data.by_cost_type.map((r: any) => (
                <div key={r.Cost_Type} className="flex items-baseline justify-between px-2 py-1 bg-white/5 rounded">
                  <span className="font-mono">{(r.Cost_Type ?? "").trim() || "(none)"}</span>
                  <span className="font-mono">{fmtMoney(r.Amount)}</span>
                  <span className="text-gray-500 text-[10px]">{r.Lines} lines</span>
                </div>
              ))}
            </div>
          ) : <div className="text-sm text-gray-400">—</div>}
        </Section>
      </div>

      <Section title={`Invoices (${data.invoices.length})`}>
        <div className="overflow-x-auto scrollbar">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="text-left text-gray-400 border-b border-line">
                <th className="px-2 py-1">Check Date</th>
                <th className="px-2 py-1">Invoice #</th>
                <th className="px-2 py-1 text-right">Header</th>
                <th className="px-2 py-1 text-right">Lines total</th>
                <th className="px-2 py-1 text-right">Jobs hit</th>
                <th className="px-2 py-1">Check #</th>
              </tr>
            </thead>
            <tbody>
              {data.invoices.map((r: any, i: number) => (
                <tr key={i} className="border-b border-line/50 hover:bg-white/5">
                  <td className="px-2 py-1 font-mono">{r.Check_Date ? String(r.Check_Date).slice(0,10) : ""}</td>
                  <td className="px-2 py-1 font-mono">
                    <button
                      onClick={() => setTraceOpen({vendor: v.Vendor_Code, invoice: String(r.Invoice_Number)})}
                      className="text-accent hover:underline"
                    >
                      {String(r.Invoice_Number).trim()} ↗
                    </button>
                  </td>
                  <td className="px-2 py-1 font-mono text-right">{fmtMoney(r.Invoice_Amount)}</td>
                  <td className="px-2 py-1 font-mono text-right">{fmtMoney(r.Line_Total)}</td>
                  <td className="px-2 py-1 font-mono text-right">{r.Jobs_Hit}</td>
                  <td className="px-2 py-1 font-mono">{(r.Check_Number ?? "").trim()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {data.linked_files?.length > 0 && (
        <Section title={`NAS files mentioning this vendor (${data.linked_files.length})`}>
          <div className="text-xs space-y-1 max-h-64 overflow-y-auto scrollbar">
            {data.linked_files.map((f: any) => (
              <div key={f.path} className="px-2 py-1 bg-white/5 rounded flex items-baseline gap-2">
                <span>📄</span>
                <span className="truncate flex-1">{f.name}</span>
                <span className="text-gray-500 truncate">{f.path.replace(/\/[^/]+$/, "")}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {traceOpen && (
        <InvoiceTraceOverlay
          vendor={traceOpen.vendor}
          invoice={traceOpen.invoice}
          onClose={() => setTraceOpen(null)}
        />
      )}
    </div>
  );
}

function InvoiceTraceOverlay({ vendor, invoice, onClose }: { vendor: string; invoice: string; onClose: () => void }) {
  const [trace, setTrace] = useState<any>({ loading: true });
  useEffect(() => {
    api.invoiceTrace(vendor, invoice).then(setTrace).catch(e => setTrace({ error: e.message }));
  }, [vendor, invoice]);

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-6" onClick={onClose}>
      <div className="glass rounded-2xl p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto scrollbar" onClick={e => e.stopPropagation()}>
        {trace.loading && <div className="text-gray-300">Tracing…</div>}
        {trace.error && <div className="text-red-300">Error: {trace.error}</div>}
        {trace.found && (() => {
          const h = trace.header;
          return (
            <>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="text-xs text-gray-400 font-mono">{String(h.Vendor_Code).trim()} · Invoice {String(h.Invoice_Number).trim()}</div>
                  <h2 className="text-xl font-semibold">{String(h.Vendor_Name).trim()}</h2>
                  <div className="text-sm text-gray-400">{fmtMoney(h.Invoice_Amount)} total · {trace.line_count} lines</div>
                </div>
                <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">✕</button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="font-semibold text-sm mb-2">By job</div>
                  <div className="text-xs space-y-1">
                    {trace.rollup_by_job.map((r: any) => (
                      <button
                        key={r.job}
                        onClick={() => { store.openJob(r.job); onClose(); }}
                        className="w-full flex justify-between px-2 py-1 bg-white/5 rounded hover:bg-white/10"
                      >
                        <span className="font-mono text-accent">{r.job || "(unassigned)"}</span>
                        <span className="font-mono">{fmtMoney(r.amount)}</span>
                      </button>
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
                  <div className="font-semibold text-sm mb-2">📎 NAS files mentioning this invoice ({trace.linked_files.length})</div>
                  <div className="text-xs space-y-1 max-h-40 overflow-y-auto scrollbar">
                    {trace.linked_files.map((f: any) => (
                      <div key={f.path} className="px-2 py-1 bg-white/5 rounded truncate">{f.name} <span className="text-gray-500">· {f.path}</span></div>
                    ))}
                  </div>
                </div>
              )}
            </>
          );
        })()}
      </div>
    </div>
  );
}

function Kpi({ label, value, tone }: { label: string; value: string; tone?: "ok" | "warn" | "bad" }) {
  const color = tone === "bad" ? "text-red-400" : tone === "warn" ? "text-amber-300" : "text-white";
  return (
    <div className="glass rounded-xl p-4">
      <div className="text-xs text-gray-400">{label}</div>
      <div className={`text-xl font-semibold mt-1 ${color}`}>{value}</div>
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

function fmtMoney(v: any): string {
  if (v == null || isNaN(v)) return "—";
  return "$" + Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 });
}

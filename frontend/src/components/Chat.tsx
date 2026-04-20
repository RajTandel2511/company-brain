import { useState } from "react";
import { api, type Citation } from "../api";
import { store } from "../store";

type Turn = {
  q: string;
  summary?: string;
  sql?: string;
  reasoning?: string;
  rows?: any[];
  columns?: string[];
  model?: string;
  cached?: boolean;
  citations?: Citation[];
  error?: string;
  loading?: boolean;
};

const ENTITY_LABEL: Record<string, string> = {
  ap_invoice: "Invoice",
  po: "PO",
  job: "Job",
  vendor: "Vendor",
  customer: "Customer",
};

function iconForFile(name: string) {
  const n = name.toLowerCase();
  if (n.endsWith(".pdf")) return "📄";
  if (/\.(xlsx?|csv)$/.test(n)) return "📊";
  if (/\.(docx?|txt|md)$/.test(n)) return "📝";
  if (/\.(png|jpe?g|gif|webp)$/.test(n)) return "🖼️";
  return "📎";
}

function JobLink({ jobNumber }: { jobNumber: string }) {
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

const SUGGESTIONS = [
  "Which open jobs are trending over budget?",
  "Top 10 customers by unpaid AR",
  "Total committed cost by job this month",
  "Show me the most expensive cost codes across all active jobs",
  "Jobs with the highest change order volume",
];

export default function Chat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<Citation | null>(null);

  async function ask(question: string) {
    if (!question.trim() || busy) return;
    const turn: Turn = { q: question, loading: true };
    setTurns(t => [...t, turn]);
    setQ("");
    setBusy(true);
    try {
      const r = await api.ask(question);
      setTurns(t =>
        t.map((x, i) =>
          i === t.length - 1
            ? {
                q: question,
                summary: r.summary,
                sql: r.plan.sql,
                reasoning: r.plan.reasoning,
                rows: r.result.rows,
                columns: r.result.columns,
                model: r.plan.model,
                cached: r.cached,
                citations: r.citations || [],
              }
            : x,
        ),
      );
    } catch (e: any) {
      setTurns(t => t.map((x, i) => (i === t.length - 1 ? { q: question, error: e.message } : x)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="h-full flex flex-col max-w-4xl mx-auto w-full">
      <div className="flex-1 overflow-y-auto scrollbar p-6 space-y-6">
        {turns.length === 0 && (
          <div className="text-center py-16">
            <div className="text-2xl font-semibold mb-2">Ask anything.</div>
            <div className="text-gray-400 mb-8">Your Spectrum data and NAS, in plain English.</div>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => ask(s)}
                  className="px-3 py-2 text-sm glass rounded-lg hover:border-accent/60 transition"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {turns.map((t, i) => (
          <div key={i} className="space-y-3">
            <div className="flex justify-end">
              <div className="bg-accent/10 border border-accent/30 rounded-2xl px-4 py-2 max-w-[80%]">{t.q}</div>
            </div>

            {t.loading && <div className="text-gray-400 text-sm italic">Thinking…</div>}
            {t.error && (
              <div className="glass rounded-xl p-4 border-red-500/40 text-red-300">Error: {t.error}</div>
            )}
            {t.summary && (
              <div className="glass rounded-2xl p-5">
                <div className="text-sm text-gray-400 mb-2 flex items-center gap-2">
                  <span>Answer</span>
                  {t.cached && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      cached · $0
                    </span>
                  )}
                  {t.model && !t.cached && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400 border border-line">
                      {t.model}
                    </span>
                  )}
                </div>
                <div className="leading-relaxed">{t.summary}</div>
                {t.citations && t.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-line">
                    <div className="text-xs text-gray-400 mb-2">
                      📎 Related documents ({t.citations.length})
                    </div>
                    <div className="space-y-1">
                      {t.citations.map(c => (
                        <button
                          key={c.file_id}
                          onClick={() => setPreview(c)}
                          className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 border border-line/50 hover:border-accent/50 flex items-center gap-3 transition"
                          title={c.path}
                        >
                          <span>{iconForFile(c.name)}</span>
                          <span className="flex-1 truncate text-sm">{c.name}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400 border border-line whitespace-nowrap">
                            {ENTITY_LABEL[c.entity_type] || c.entity_type} · {c.entity_value}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {t.rows && t.columns && t.rows.length > 0 && (
                  <details className="mt-4">
                    <summary className="text-sm text-gray-400 cursor-pointer hover:text-white">
                      View {t.rows.length} rows
                    </summary>
                    <div className="mt-3 overflow-x-auto scrollbar">
                      <table className="min-w-full text-xs">
                        <thead>
                          <tr className="text-left text-gray-400 border-b border-line">
                            {t.columns.map(c => <th key={c} className="px-2 py-1">{c}</th>)}
                          </tr>
                        </thead>
                        <tbody>
                          {t.rows.slice(0, 50).map((r, ri) => (
                            <tr key={ri} className="border-b border-line/50 hover:bg-white/5">
                              {t.columns!.map(c => (
                                <td key={c} className="px-2 py-1 font-mono">
                                  {c === "Job_Number" && r[c]
                                    ? <JobLink jobNumber={String(r[c])} />
                                    : String(r[c] ?? "")}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </details>
                )}
                {t.sql && (
                  <details className="mt-3">
                    <summary className="text-sm text-gray-400 cursor-pointer hover:text-white">View SQL</summary>
                    <pre className="mt-2 text-xs font-mono p-3 bg-black/30 rounded overflow-x-auto scrollbar">{t.sql}</pre>
                  </details>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {preview && (
        <div
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur flex items-center justify-center p-4"
          onClick={() => setPreview(null)}
        >
          <div
            className="glass rounded-2xl w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            <div className="p-4 border-b border-line flex items-center justify-between gap-3">
              <div className="truncate">
                <div className="font-medium truncate">{preview.name}</div>
                <div className="text-xs text-gray-400 truncate">{preview.path}</div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <a
                  href={api.fileUrl(preview.path)}
                  download
                  className="text-sm text-accent hover:underline"
                >
                  Download
                </a>
                <button
                  onClick={() => setPreview(null)}
                  className="w-8 h-8 rounded-lg hover:bg-white/10 text-gray-400"
                  aria-label="Close"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="flex-1 bg-black/30 overflow-hidden">
              {/\.pdf$/i.test(preview.name) ? (
                <iframe src={api.fileUrl(preview.path)} className="w-full h-full" />
              ) : /\.(png|jpe?g|gif|webp|svg)$/i.test(preview.name) ? (
                <img
                  src={api.fileUrl(preview.path)}
                  alt={preview.name}
                  className="max-w-full max-h-full mx-auto"
                />
              ) : (
                <div className="p-6 text-sm text-gray-400">
                  No inline preview for this file type. Use Download above.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <form
        onSubmit={e => { e.preventDefault(); ask(q); }}
        className="p-4 border-t border-line"
      >
        <div className="glass rounded-2xl flex items-center gap-2 px-4 py-3">
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Ask about jobs, AR, AP, cost codes, files…"
            className="flex-1 bg-transparent outline-none placeholder:text-gray-500"
            disabled={busy}
          />
          <button
            type="submit"
            disabled={busy || !q.trim()}
            className="px-4 py-1.5 rounded-lg bg-accent text-ink font-medium disabled:opacity-40"
          >
            {busy ? "…" : "Ask"}
          </button>
        </div>
      </form>
    </div>
  );
}

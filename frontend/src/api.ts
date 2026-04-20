const BASE = (import.meta.env.VITE_API_BASE as string) || "/api";

export type Citation = {
  file_id: number;
  path: string;
  name: string;
  size?: number;
  modified?: number;
  entity_type: string;
  entity_value: string;
  match?: string;
};

async function j<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export const api = {
  health: () => j<{ ok: boolean }>("/health"),
  ask: (question: string) =>
    j<{
      plan: { reasoning: string; sql: string; model?: string };
      result: { columns: string[]; rows: any[] };
      summary: string;
      citations?: Citation[];
      cached?: boolean;
    }>("/ask", { method: "POST", body: JSON.stringify({ question }) }),
  query: (sql: string) =>
    j<{ columns: string[]; rows: any[] }>("/query", {
      method: "POST",
      body: JSON.stringify({ sql }),
    }),
  tables: () => j<{ schema_name: string; table_name: string; kind: string }[]>("/schema/tables"),
  columns: (schema: string, table: string) =>
    j<{ name: string; type: string; nullable: string }[]>(`/schema/columns?schema=${schema}&table=${table}`),
  filesList: (path = "") => j<any[]>(`/files/list?path=${encodeURIComponent(path)}`),
  filesSearch: (q: string) => j<any[]>(`/files/search?q=${encodeURIComponent(q)}`),
  filesForJob: (jobNumber: string) =>
    j<{ job_number: string; folder: string | null; entries: any[] }>(
      `/files/job/${encodeURIComponent(jobNumber.trim())}`,
    ),
  fileUrl: (path: string) => `${BASE}/files/get?path=${encodeURIComponent(path)}`,
  dashboardList: () => j<{ key: string; title: string }[]>(`/dashboard`),
  dashboard: (key: string) => j<{ columns: string[]; rows: any[] }>(`/dashboard/${key}`),
  invoiceTrace: (vendor: string, invoice: string) =>
    j<any>(`/money/invoice/${encodeURIComponent(vendor.trim())}/${encodeURIComponent(invoice.trim())}`),
  vendorSpend: (vendor: string, days = 365) =>
    j<any>(`/money/vendor/${encodeURIComponent(vendor.trim())}?days=${days}`),
  vendorList: (search = "", employeesOnly = false) =>
    j<any[]>(`/money/vendors?search=${encodeURIComponent(search)}&employees_only=${employeesOnly}&limit=100`),
  docintelStats: () => j<any>(`/docintel/stats`),
  docintelSearch: (q: string) => j<any[]>(`/docintel/search?q=${encodeURIComponent(q)}`),
  docintelFiles: (type: string, value: string) =>
    j<any[]>(`/docintel/files?entity_type=${type}&entity_value=${encodeURIComponent(value)}`),
  insights: () => j<{ insights: any[]; counts: Record<string, number> }>(`/insights`),
  insightsBriefing: () => j<{ briefing: string }>(`/insights/briefing`),
  jobsAtRisk: () => j<any[]>(`/jobs/at-risk`),
  jobDetail: (n: string) => j<any>(`/jobs/${encodeURIComponent(n.trim())}`),
  jobNarrative: (n: string) =>
    j<{ job_number: string; narrative: string }>(`/jobs/${encodeURIComponent(n.trim())}/narrative`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
};

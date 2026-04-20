import { useSyncExternalStore } from "react";

type State = {
  tab: "insights" | "chat" | "dashboard" | "jobs" | "vendors" | "docs" | "files";
  filesPath: string;
  openJob?: string;
  openVendor?: string;
};

const LS_KEY = "company-brain:ui-state";
const DEFAULT_STATE: State = { tab: "insights", filesPath: "" };
const VALID_TABS: State["tab"][] = ["insights", "chat", "dashboard", "jobs", "vendors", "docs", "files"];

function loadState(): State {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return DEFAULT_STATE;
    const parsed = JSON.parse(raw) as Partial<State>;
    const tab = VALID_TABS.includes(parsed.tab as State["tab"]) ? parsed.tab as State["tab"] : DEFAULT_STATE.tab;
    return {
      tab,
      filesPath: typeof parsed.filesPath === "string" ? parsed.filesPath : "",
      openJob: typeof parsed.openJob === "string" ? parsed.openJob : undefined,
      openVendor: typeof parsed.openVendor === "string" ? parsed.openVendor : undefined,
    };
  } catch {
    return DEFAULT_STATE;
  }
}

let state: State = loadState();
const subs = new Set<() => void>();
const emit = () => {
  try { localStorage.setItem(LS_KEY, JSON.stringify(state)); } catch {}
  subs.forEach(cb => cb());
};

export const store = {
  get: () => state,
  subscribe: (cb: () => void) => { subs.add(cb); return () => subs.delete(cb); },
  setTab: (tab: State["tab"]) => { state = { ...state, tab }; emit(); },
  openFolder: (path: string) => { state = { ...state, tab: "files", filesPath: path }; emit(); },
  setFilesPath: (p: string) => { state = { ...state, filesPath: p }; emit(); },
  openJob: (jobNumber: string) => { state = { ...state, tab: "jobs", openJob: jobNumber }; emit(); },
  openVendor: (vendorCode: string) => { state = { ...state, tab: "vendors", openVendor: vendorCode }; emit(); },
};

export function useStore() {
  return useSyncExternalStore(store.subscribe, store.get);
}

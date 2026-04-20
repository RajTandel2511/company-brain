import Chat from "./components/Chat";
import Dashboard from "./components/Dashboard";
import Docs from "./components/Docs";
import Files from "./components/Files";
import Insights from "./components/Insights";
import Jobs from "./components/Jobs";
import Vendors from "./components/Vendors";
import { store, useStore } from "./store";

type Tab = "insights" | "chat" | "dashboard" | "jobs" | "vendors" | "docs" | "files";

export default function App() {
  const { tab } = useStore();

  return (
    <div className="h-full flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 border-b border-line">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-blue-500 flex items-center justify-center font-bold text-ink">
            ✦
          </div>
          <div>
            <div className="font-semibold tracking-tight">Company Brain</div>
            <div className="text-xs text-gray-400">Spectrum + NAS, one conversation</div>
          </div>
        </div>
        <nav className="flex gap-1 p-1 glass rounded-lg text-sm">
          {(["insights", "chat", "dashboard", "jobs", "vendors", "docs", "files"] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => store.setTab(t)}
              className={`px-3 py-1.5 rounded-md capitalize transition ${
                tab === t ? "bg-accent text-ink font-medium" : "text-gray-300 hover:text-white"
              }`}
            >
              {t}
            </button>
          ))}
        </nav>
      </header>

      <main className="flex-1 overflow-hidden">
        {tab === "insights" && <Insights />}
        {tab === "chat" && <Chat />}
        {tab === "dashboard" && <Dashboard />}
        {tab === "jobs" && <Jobs />}
        {tab === "vendors" && <Vendors />}
        {tab === "docs" && <Docs />}
        {tab === "files" && <Files />}
      </main>
    </div>
  );
}

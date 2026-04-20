import { useEffect, useState } from "react";
import { api } from "../api";
import { store, useStore } from "../store";

type Entry = { name: string; path: string; is_dir: boolean; size?: number; mime?: string };

export default function Files() {
  const { filesPath } = useStore();
  const [path, setPathLocal] = useState(filesPath);
  const setPath = (p: string) => { setPathLocal(p); store.setFilesPath(p); };
  useEffect(() => { setPathLocal(filesPath); }, [filesPath]);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [q, setQ] = useState("");
  const [searching, setSearching] = useState(false);
  const [preview, setPreview] = useState<Entry | null>(null);

  useEffect(() => {
    if (!searching) api.filesList(path).then(setEntries).catch(() => setEntries([]));
  }, [path, searching]);

  async function doSearch() {
    if (!q.trim()) { setSearching(false); return; }
    setSearching(true);
    const r = await api.filesSearch(q);
    setEntries(r);
  }

  const crumbs = path.split("/").filter(Boolean);

  return (
    <div className="h-full flex">
      <div className="w-1/2 border-r border-line flex flex-col">
        <div className="p-4 border-b border-line space-y-2">
          <div className="flex gap-2">
            <input
              value={q}
              onChange={e => setQ(e.target.value)}
              onKeyDown={e => e.key === "Enter" && doSearch()}
              placeholder="Search NAS (drawings, PDFs, job folders…)"
              className="flex-1 glass rounded-lg px-3 py-2 text-sm outline-none"
            />
            <button onClick={doSearch} className="px-3 py-2 rounded-lg bg-accent text-ink text-sm font-medium">
              Search
            </button>
            {searching && (
              <button onClick={() => { setSearching(false); setQ(""); }} className="px-3 py-2 text-sm text-gray-400">
                Clear
              </button>
            )}
          </div>
          {!searching && (
            <div className="text-xs text-gray-400 flex items-center gap-1 flex-wrap">
              <button onClick={() => setPath("")} className="hover:text-white">/ root</button>
              {crumbs.map((c, i) => (
                <span key={i}>
                  <span className="mx-1">/</span>
                  <button
                    onClick={() => setPath(crumbs.slice(0, i + 1).join("/"))}
                    className="hover:text-white"
                  >{c}</button>
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="flex-1 overflow-y-auto scrollbar p-2">
          {entries.map(e => (
            <button
              key={e.path}
              onClick={() => (e.is_dir ? (setPath(e.path), setSearching(false)) : setPreview(e))}
              className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 flex items-center gap-3"
            >
              <span className="text-lg">{e.is_dir ? "📁" : iconFor(e.name)}</span>
              <span className="flex-1 truncate text-sm">{e.name}</span>
              {e.size != null && <span className="text-xs text-gray-500">{fmt(e.size)}</span>}
            </button>
          ))}
          {entries.length === 0 && <div className="text-sm text-gray-500 p-4">Empty.</div>}
        </div>
      </div>

      <div className="w-1/2 flex flex-col">
        {preview ? (
          <>
            <div className="p-4 border-b border-line flex items-center justify-between">
              <div className="truncate">
                <div className="font-medium truncate">{preview.name}</div>
                <div className="text-xs text-gray-400 truncate">{preview.path}</div>
              </div>
              <a href={api.fileUrl(preview.path)} download className="text-sm text-accent hover:underline">
                Download
              </a>
            </div>
            <div className="flex-1 overflow-hidden bg-black/30">
              <Preview entry={preview} />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a file to preview
          </div>
        )}
      </div>
    </div>
  );
}

function Preview({ entry }: { entry: Entry }) {
  const url = api.fileUrl(entry.path);
  const n = entry.name.toLowerCase();
  if (/\.(png|jpe?g|gif|webp|svg)$/.test(n))
    return <img src={url} alt={entry.name} className="max-w-full max-h-full mx-auto" />;
  if (n.endsWith(".pdf")) return <iframe src={url} className="w-full h-full" />;
  if (/\.(txt|log|csv|md|json|xml|yaml|yml)$/.test(n))
    return <iframe src={url} className="w-full h-full bg-white" />;
  return <div className="p-6 text-sm text-gray-400">No inline preview. Use Download above.</div>;
}

function iconFor(name: string) {
  const n = name.toLowerCase();
  if (n.endsWith(".pdf")) return "📄";
  if (/\.(dwg|dxf|rvt)$/.test(n)) return "📐";
  if (/\.(xlsx?|csv)$/.test(n)) return "📊";
  if (/\.(png|jpe?g|gif|webp)$/.test(n)) return "🖼️";
  if (/\.(docx?|txt|md)$/.test(n)) return "📝";
  return "📎";
}

function fmt(b: number) {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  if (b < 1024 * 1024 * 1024) return `${(b / 1024 / 1024).toFixed(1)} MB`;
  return `${(b / 1024 / 1024 / 1024).toFixed(1)} GB`;
}

import { ReactNode } from "react";

export function Skel({ className = "", style }: { className?: string; style?: React.CSSProperties }) {
  return <div className={`skel rounded ${className}`} style={style} />;
}

/** Multi-line text skeleton — `lines` stacked bars of varying width. */
export function SkelText({ lines = 3, className = "" }: { lines?: number; className?: string }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skel
          key={i}
          className="h-3"
          style={{ width: `${60 + ((i * 37) % 40)}%` }}
        />
      ))}
    </div>
  );
}

/** Skeleton card — glass container + title + body lines. */
export function SkelCard({ children, className = "" }: { children?: ReactNode; className?: string }) {
  return (
    <div className={`glass rounded-2xl p-5 ${className}`}>
      {children ?? (
        <>
          <Skel className="h-4 w-1/3 mb-4" />
          <SkelText lines={3} />
        </>
      )}
    </div>
  );
}

/** Skeleton KPI cell. */
export function SkelKpi() {
  return (
    <div className="glass rounded-xl p-4">
      <Skel className="h-3 w-16 mb-3" />
      <Skel className="h-6 w-24" />
    </div>
  );
}

/** Skeleton table — N rows of columns placeholders. */
export function SkelTable({ rows = 6, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        {Array.from({ length: cols }).map((_, i) => (
          <Skel key={i} className="h-3 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-2">
          {Array.from({ length: cols }).map((_, c) => (
            <Skel key={c} className="h-3 flex-1" style={{ opacity: 0.7 }} />
          ))}
        </div>
      ))}
    </div>
  );
}

/** Skeleton list row (avatar + 2 text lines). */
export function SkelListRow() {
  return (
    <div className="px-4 py-3 border-b border-line/50 flex items-center gap-3">
      <Skel className="w-8 h-8 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-1.5">
        <Skel className="h-3 w-3/4" />
        <Skel className="h-2 w-1/2" />
      </div>
    </div>
  );
}

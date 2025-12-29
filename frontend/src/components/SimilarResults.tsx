import React, { useState } from "react";
import CodeBlock from "./CodeBlock";
import type { SearchResult } from "../types";
import { Icons, clsx, truncateLines, keyFor } from "../utils/constants";

interface SimilarResultsProps {
  similarResults: SearchResult[];
  similarLoading: boolean;
}

const SimilarResults: React.FC<SimilarResultsProps> = ({ similarResults, similarLoading }) => {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [copied, setCopied] = useState<Record<string, boolean>>({});

  const handleCopy = async (code: string, key: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(prev => ({ ...prev, [key]: true }));
      setTimeout(() => setCopied(prev => { const n = { ...prev }; delete n[key]; return n; }), 2000);
    } catch {}
  };

  const handleExpand = (key: string) => {
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="mt-6 pt-6 border-t border-emerald-900/20">
      <div className="flex items-center gap-2 mb-4">
        <h4 className="text-sm font-semibold text-emerald-300">Similar Code Patterns</h4>
        <span className="text-xs text-emerald-400 bg-emerald-900/10 px-2 py-0.5 rounded-full">{similarResults.length} {similarResults.length === 1 ? 'match' : 'matches'}</span>
      </div>

      {similarLoading ? (
        <div className="py-8 text-center text-sm text-muted">Finding similar code patterns...</div>
      ) : similarResults.length === 0 ? (
        <div className="py-8 text-center text-sm text-muted">No similar code patterns found.</div>
      ) : (
        <div className="space-y-3">
          {similarResults.map((similar, idx) => {
            const key = keyFor(similar, idx);
            const code = similar.code ?? "";
            const preview = truncateLines(code, 12);
            const isExpanded = !!expanded[key];
            const isCopied = !!copied[key];

            return (
              <div key={key} className="rounded-md border border-slate-800/30 p-4 bg-slate-900/30">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="text-sm font-medium text-slate-200 truncate">{similar.symbol_name ?? "<unknown>"}</div>
                      <div className="text-xs text-emerald-400 px-2 py-0.5 rounded-full bg-emerald-900/10">{(similar.score ?? 0).toFixed(3)}</div>
                    </div>
                    <div className="text-xs text-muted">
                      <span className="mr-2">{Icons.File}</span>
                      <span className="font-mono break-all">{similar.file_path}</span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 items-end">
                    <button onClick={() => handleCopy(code, key)} className={clsx("text-xs rounded-md px-2 py-1", isCopied ? "bg-green-800/30" : "bg-slate-800/30")}>
                      {isCopied ? `${Icons.Check} Copied` : `${Icons.Copy} Copy`}
                    </button>
                    {preview.truncated && (
                      <button onClick={() => handleExpand(key)} className="text-xs rounded-md px-2 py-1 bg-slate-800/30">
                        {isExpanded ? "Less" : "More"}
                      </button>
                    )}
                  </div>
                </div>

                <CodeBlock code={isExpanded ? code : preview.text} language={similar.language} />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SimilarResults;
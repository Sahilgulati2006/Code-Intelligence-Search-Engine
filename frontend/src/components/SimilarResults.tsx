import React, { useState } from "react";
import CodeBlock from "./CodeBlock";
import type { SearchResult } from "../types";
import { clsx, truncateLines, keyFor } from "../utils/constants";

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

  if (similarLoading) {
    return (
      <div className="py-8 px-4 text-center">
        <div className="inline-flex items-center gap-2 text-sm text-slate-300">
          <span className="animate-spin">⚙️</span>
          <span>Finding similar code patterns...</span>
        </div>
      </div>
    );
  }

  if (similarResults.length === 0) {
    return (
      <div className="py-8 px-4 text-center rounded-lg bg-slate-900/30 border border-slate-800/50">
        <p className="text-sm text-slate-400">📭 No similar code patterns found</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 px-1">
        <span className="text-sm font-semibold text-cyan-300">🔗 Similar Patterns</span>
        <span className="text-xs text-cyan-400 bg-cyan-900/20 px-2.5 py-1 rounded-full border border-cyan-800/30">
          {similarResults.length} {similarResults.length === 1 ? 'match' : 'matches'}
        </span>
      </div>

      <div className="space-y-3">
        {similarResults.map((similar, idx) => {
          const key = keyFor(similar, idx);
          const code = similar.code ?? "";
          const preview = truncateLines(code, 12);
          const isExpanded = !!expanded[key];
          const isCopied = !!copied[key];
          const scorePercentage = Math.round((similar.score ?? 0) * 100);

          return (
            <div
              key={key}
              className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-4 hover:border-slate-700/80 transition-colors duration-200 animate-slideInLeft"
            >
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-3 pb-3 border-b border-slate-800/50">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <div className="text-sm font-semibold text-slate-200 truncate">
                      {similar.symbol_name ?? "<unknown>"}
                    </div>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      scorePercentage >= 80 ? 'bg-green-900/30 text-green-300 border border-green-700/40' :
                      scorePercentage >= 60 ? 'bg-yellow-900/30 text-yellow-300 border border-yellow-700/40' :
                      'bg-orange-900/30 text-orange-300 border border-orange-700/40'
                    }`}>
                      ⭐ {scorePercentage}%
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 flex items-center gap-1.5">
                    <span>📄</span>
                    <code className="font-mono break-all">{similar.file_path}</code>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleCopy(code, key)}
                    className={clsx(
                      "text-xs px-2.5 py-1.5 rounded-lg font-medium transition-all duration-200 whitespace-nowrap",
                      isCopied
                        ? "bg-green-900/30 border border-green-700/50 text-green-300"
                        : "bg-slate-800/40 border border-slate-700/50 text-slate-300 hover:bg-slate-800/60"
                    )}
                  >
                    {isCopied ? "✓ Copied" : "📋 Copy"}
                  </button>
                  {preview.truncated && (
                    <button
                      onClick={() => handleExpand(key)}
                      className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-800/40 border border-slate-700/50 text-slate-300 hover:bg-slate-800/60 font-medium transition-all duration-200 whitespace-nowrap"
                    >
                      {isExpanded ? "▲ Less" : "▼ More"}
                    </button>
                  )}
                </div>
              </div>

              {/* Code */}
              <CodeBlock code={isExpanded ? code : preview.text} language={similar.language} />
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SimilarResults;
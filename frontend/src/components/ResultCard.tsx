import React, { useState } from "react";
import CodeBlock from "./CodeBlock";
import type { SearchResult } from "../types";
import { clsx, truncateLines, keyFor } from "../utils/constants";
import SimilarResults from "./SimilarResults";

interface ResultCardProps {
  result: SearchResult;
  index: number;
  onFindSimilar: (result: SearchResult, resultKey: string) => Promise<void>;
  similarLoading: Record<string, boolean>;
  similarResults: Record<string, SearchResult[]>;
  expandedSimilar: Record<string, boolean>;
}

const ResultCard: React.FC<ResultCardProps> = ({
  result,
  index,
  onFindSimilar,
  similarLoading,
  similarResults,
  expandedSimilar,
}) => {
  const resultKey = keyFor(result, index);
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const code = result.code ?? "";
  const { text: preview, truncated } = truncateLines(code, 25);

  const handleCopy = async () => {
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const scorePercentage = Math.round((result.score ?? 0) * 100);
  const scoreColor = scorePercentage >= 80 ? 'text-green-400' : scorePercentage >= 60 ? 'text-yellow-400' : 'text-orange-400';

  return (
    <div className="card-surface p-6 sm:p-7 shadow-md hover:shadow-lg transition-shadow duration-300 group animate-fadeIn">
      {/* Header with metadata */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6 pb-4 border-b border-slate-800/50">
        <div className="min-w-0 flex-1">
          {/* Title and badges */}
          <div className="flex items-center gap-3 mb-3 flex-wrap">
            <h3 className="text-lg sm:text-xl font-bold text-slate-100 truncate group-hover:text-cyan-300 transition-colors">
              {result.symbol_name ?? "<unknown>"}
            </h3>

            {/* Type badge */}
            {result.symbol_type && (
              <span className="text-[11px] font-medium px-2.5 py-1 rounded-full bg-purple-900/25 text-purple-300 border border-purple-700/40 flex-shrink-0">
                {result.symbol_type}
              </span>
            )}

            {/* Language badge */}
            {result.language && (
              <span className="text-[11px] font-medium px-2.5 py-1 rounded-full bg-cyan-900/25 text-cyan-300 border border-cyan-700/40 flex-shrink-0">
                {result.language}
              </span>
            )}

            {/* Score badge */}
            <div className={`text-[11px] font-semibold px-2.5 py-1 rounded-full bg-slate-800/40 border border-slate-700/40 flex-shrink-0 flex items-center gap-1 ${scoreColor}`}>
              <span>⭐</span>
              <span>{scorePercentage}%</span>
            </div>
          </div>

          {/* File path and line numbers */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <span className="text-sm opacity-70">📄</span>
              <code className="font-mono text-slate-400 break-all">{result.file_path}</code>
              {result.start_line != null && result.end_line != null && (
                <span className="text-slate-500 whitespace-nowrap">
                  · <span className="text-cyan-400">L{result.start_line}</span>-<span className="text-cyan-400">L{result.end_line}</span>
                </span>
              )}
            </div>

            {/* Repository */}
            {result.repo_id && (
              <div className="text-xs text-slate-400">
                <span className="opacity-70">📦</span>{" "}
                <code className="font-mono text-cyan-400">{result.repo_id}</code>
              </div>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-2 sm:flex-col sm:items-end">
          {/* Find Similar button */}
          <button
            type="button"
            onClick={() => onFindSimilar(result, resultKey)}
            disabled={similarLoading[resultKey]}
            className={clsx(
              "inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap",
              expandedSimilar[resultKey]
                ? "bg-emerald-900/30 border border-emerald-700/50 text-emerald-300 hover:bg-emerald-900/40"
                : "bg-slate-800/40 border border-slate-700/50 text-slate-300 hover:bg-slate-800/60"
            )}
            aria-label={expandedSimilar[resultKey] ? "Hide similar code" : "Find similar code"}
          >
            {similarLoading[resultKey] ? (
              <>
                <span className="animate-spin">⚙️</span>
                <span>Searching...</span>
              </>
            ) : (
              <>
                <span>{expandedSimilar[resultKey] ? "✓" : "🔗"}</span>
                <span>{expandedSimilar[resultKey] ? "Similar Found" : "Find Similar"}</span>
              </>
            )}
          </button>

          {/* Copy button */}
          <button
            type="button"
            onClick={handleCopy}
            className={clsx(
              "inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap",
              copied
                ? "bg-green-900/30 border border-green-700/50 text-green-300"
                : "bg-slate-800/40 border border-slate-700/50 text-slate-300 hover:bg-slate-800/60"
            )}
            aria-label="Copy code to clipboard"
          >
            <span>{copied ? "✓" : "📋"}</span>
            <span>{copied ? "Copied!" : "Copy"}</span>
          </button>

          {/* Expand button */}
          {truncated && (
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-slate-800/40 border border-slate-700/50 text-slate-300 hover:bg-slate-800/60 transition-all duration-200 whitespace-nowrap"
              aria-label={isExpanded ? "Collapse code" : "Expand code"}
            >
              <span>{isExpanded ? "▲" : "▼"}</span>
              <span>{isExpanded ? "Collapse" : "Expand"}</span>
            </button>
          )}
        </div>
      </div>

      {/* Code preview */}
      <div className="relative">
        <CodeBlock code={isExpanded ? code : preview} language={result.language} />

        {/* Truncation message */}
        {truncated && !isExpanded && (
          <div className="mt-3 px-4 py-3 text-center text-xs text-slate-400 bg-slate-900/40 border border-slate-800/50 rounded-lg">
            Showing first 25 lines of{" "}
            <span className="font-semibold text-cyan-400">{code.split("\n").length}</span> total lines
            <button
              onClick={() => setIsExpanded(true)}
              className="ml-2 text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
            >
              Expand to view all
            </button>
          </div>
        )}
      </div>

      {/* Similar results section */}
      {expandedSimilar[resultKey] && (
        <div className="mt-6 pt-6 border-t border-slate-800/50">
          <p className="text-xs font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <span>🔍</span>
            <span>Similar Code Patterns</span>
          </p>
          <SimilarResults similarResults={similarResults[resultKey] || []} similarLoading={!!similarLoading[resultKey]} />
        </div>
      )}
    </div>
  );
};

export default ResultCard;
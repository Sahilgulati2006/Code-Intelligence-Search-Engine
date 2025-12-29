import React, { useState } from "react";
import CodeBlock from "./CodeBlock";
import type { SearchResult } from "../types";
import { Icons, clsx, truncateLines, keyFor } from "../utils/constants";
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

  return (
    <div className="card-surface p-6 shadow-md">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold truncate">{result.symbol_name ?? "<unknown>"}</h3>
            {result.symbol_type && (
              <span className="text-[11px] rounded-full px-2 py-0.5 bg-slate-800/40 text-slate-200 border border-slate-700/40">
                {result.symbol_type}
              </span>
            )}
            {result.language && (
              <span className="text-[11px] rounded-full px-2 py-0.5 bg-blue-900/25 text-blue-200 border border-blue-800/30">
                {result.language}
              </span>
            )}
            <div className="ml-2 text-xs text-muted px-2 py-0.5 rounded-full">
              score: <span className="font-mono text-slate-200 ml-1">{(result.score ?? 0).toFixed(3)}</span>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <span className="text-sm">{Icons.File}</span>
            <span className="font-mono break-all text-slate-300">{result.file_path}</span>
            {result.start_line != null && result.end_line != null && (
              <span className="text-muted">· lines {result.start_line}–{result.end_line}</span>
            )}
          </div>

          {result.repo_id && (
            <div className="mt-2 text-xs text-muted">
              <span className="text-xs">{Icons.Folder}</span>{" "}
              <span className="font-mono ml-1">{result.repo_id}</span>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-2 items-end">
          <button
            type="button"
            onClick={() => onFindSimilar(result, resultKey)}
            disabled={similarLoading[resultKey]}
            className={clsx(
              "rounded-md px-3 py-2 text-xs font-medium",
              expandedSimilar[resultKey] ? "bg-emerald-900/40 border border-emerald-700/40 text-emerald-200" : "bg-slate-800/40 border border-slate-700/40 text-slate-200"
            )}
          >
            {similarLoading[resultKey] ? "Searching..." : (expandedSimilar[resultKey] ? "Hide Similar" : "Find Similar")}
          </button>

          <button
            type="button"
            onClick={handleCopy}
            className={clsx(
              "rounded-md px-3 py-2 text-xs font-medium",
              copied ? "bg-green-900/40 border border-green-700/30 text-green-200" : "bg-slate-800/30 border border-slate-700/30 text-slate-200"
            )}
          >
            {copied ? `${Icons.Check} Copied` : `${Icons.Copy} Copy`}
          </button>

          {truncated && (
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="rounded-md px-3 py-2 text-xs text-slate-200 bg-slate-800/30 border border-slate-700/30"
            >
              {isExpanded ? "Collapse" : "Expand"}
            </button>
          )}
        </div>
      </div>

      <div>
        <CodeBlock code={isExpanded ? code : preview} language={result.language} />
        {truncated && !isExpanded && (
          <div className="mt-3 text-xs text-muted text-center py-2 border-t border-slate-800/30">
            Showing first 25 lines of {code.split("\n").length} total lines.
            <button onClick={() => setIsExpanded(true)} className="ml-2 underline text-sky-400">Expand to view full code</button>
          </div>
        )}
      </div>

      {expandedSimilar[resultKey] && (
        <div className="mt-5">
          <SimilarResults similarResults={similarResults[resultKey] || []} similarLoading={!!similarLoading[resultKey]} />
        </div>
      )}
    </div>
  );
};

export default ResultCard;
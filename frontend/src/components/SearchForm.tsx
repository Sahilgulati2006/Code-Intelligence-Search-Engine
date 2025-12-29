import React from "react";
import { Icons, clsx } from "../utils/constants";

interface SearchFormProps {
  query: string;
  repoId: string;
  language: string;
  topK: number;
  loading: boolean;
  error: string | null;
  onQueryChange: (value: string) => void;
  onRepoIdChange: (value: string) => void;
  onLanguageChange: (value: string) => void;
  onTopKChange: (value: number) => void;
  onSubmit: (e: React.FormEvent) => void;
  canSearch: boolean;
}

const SearchForm: React.FC<SearchFormProps> = ({
  query,
  repoId,
  language,
  topK,
  loading,
  error,
  onQueryChange,
  onRepoIdChange,
  onLanguageChange,
  onTopKChange,
  onSubmit,
  canSearch,
}) => {
  const quickExamples = ["render template", "json response", "error handler"];

  return (
    <form onSubmit={onSubmit} className="app-container card-surface p-6 sm:p-8 shadow-lg">
      <div className="flex flex-col sm:flex-row sm:items-start sm:gap-6">
        <div className="flex-1">
          <label className="block text-sm font-semibold text-slate-200 mb-2">Search</label>
          <div className="relative">
            <input
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              placeholder='Try: "render HTML template", "handle request", "json response"'
              aria-label="Search query"
              className="w-full rounded-lg border border-slate-700/50 bg-transparent px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-shadow"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">
              <span className="text-lg">{Icons.Search}</span>
            </div>
          </div>
          {error && (
            <div className="mt-3 px-4 py-2 rounded-md bg-red-900/40 border border-red-800/50 text-sm text-red-300">
              {error}
            </div>
          )}
        </div>

        <div className="w-full sm:w-auto mt-4 sm:mt-0 flex items-start gap-3">
          <button
            type="submit"
            disabled={!canSearch}
            className={clsx(
              "rounded-lg px-6 py-3 text-sm font-semibold flex items-center gap-3",
              "bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-md hover:scale-[1.02] transition-transform",
              loading && "opacity-80 disabled:opacity-80",
              !canSearch && "opacity-50 cursor-not-allowed"
            )}
            aria-label="Search"
          >
            {loading ? (
              <>
                <svg className="w-4 h-4 animate-spin text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.3)" strokeWidth="4"></circle>
                  <path d="M22 12a10 10 0 0 0-10-10" stroke="white" strokeWidth="4" strokeLinecap="round"></path>
                </svg>
                Searching...
              </>
            ) : (
              <>
                <span>{Icons.Search}</span>
                <span>Search</span>
              </>
            )}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-5">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Repository</label>
          <input
            value={repoId}
            onChange={(e) => onRepoIdChange(e.target.value)}
            placeholder="e.g. github.com/user/repo"
            aria-label="Repository id"
            className="w-full rounded-md border border-slate-700/50 bg-transparent px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
          />
          <p className="text-[11px] text-muted mt-1">Leave empty for all repos</p>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Language</label>
          <input
            value={language}
            onChange={(e) => onLanguageChange(e.target.value)}
            placeholder="e.g. python, javascript"
            aria-label="Language filter"
            className="w-full rounded-md border border-slate-700/50 bg-transparent px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
          />
          <p className="text-[11px] text-muted mt-1">Leave empty for all languages</p>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Results</label>
          <input
            type="number"
            min={1}
            max={50}
            value={topK}
            onChange={(e) => onTopKChange(Number(e.target.value) || 5)}
            aria-label="Results count"
            className="w-full rounded-md border border-slate-700/50 bg-transparent px-3 py-2 text-sm text-slate-100 focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
          />
          <p className="text-[11px] text-muted mt-1">Number of results to return</p>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {quickExamples.map((ex, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onQueryChange(ex)}
            className="text-[12px] px-3 py-1.5 rounded-md bg-slate-700/40 hover:bg-slate-700/60 text-slate-200 font-medium transition-transform hover:scale-[1.02]"
          >
            {ex}
          </button>
        ))}
      </div>
    </form>
  );
};

export default SearchForm;


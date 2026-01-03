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
  const quickExamples = [
    { text: "Render template", icon: "🎨" },
    { text: "JSON response", icon: "📋" },
    { text: "Error handler", icon: "⚠️" }
  ];

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading && canSearch) {
      onSubmit(e as any);
    }
  };

  return (
    <form onSubmit={onSubmit} className="card-surface p-6 sm:p-8 shadow-lg space-y-6">
      {/* Main search input */}
      <div>
        <label className="block text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
          <span className="text-lg">🔍</span>
          <span>Search Code</span>
        </label>
        <div className="relative group">
          <input
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="What are you looking for? (e.g., 'render HTML template', 'handle JSON')"
            disabled={loading}
            aria-label="Search query"
            className="w-full rounded-xl border border-slate-700/50 bg-slate-900/30 px-5 py-4 text-base text-slate-100 placeholder:text-slate-500 focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all duration-200 group-hover:border-slate-700/80 disabled:opacity-60 disabled:cursor-not-allowed"
          />
          <div className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-cyan-400 transition-colors duration-200">
            {loading ? (
              <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.2)" strokeWidth="4"></circle>
                <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" strokeWidth="4" strokeLinecap="round"></path>
              </svg>
            ) : (
              <span className="text-lg">{Icons.Search}</span>
            )}
          </div>
        </div>

        {/* Error display */}
        {error && (
          <div className="mt-3 px-4 py-3 rounded-lg bg-red-900/20 border border-red-800/50 text-sm text-red-300 flex items-start gap-3 animate-slideInLeft">
            <span className="text-lg mt-0.5">⚠️</span>
            <div>{error}</div>
          </div>
        )}
      </div>

      {/* Quick examples */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-slate-400 font-medium self-center">Quick examples:</span>
        {quickExamples.map((ex, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onQueryChange(ex.text)}
            disabled={loading}
            className="text-xs px-3 py-2 rounded-lg bg-slate-800/40 hover:bg-slate-700/60 active:bg-slate-700/80 text-slate-200 font-medium transition-all duration-200 border border-slate-700/30 hover:border-cyan-500/40 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            <span>{ex.icon}</span>
            <span>{ex.text}</span>
          </button>
        ))}
      </div>

      {/* Filters section */}
      <div className="border-t border-slate-800/50 pt-6">
        <p className="text-xs font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <span>⚙️</span>
          <span>Filters & Options</span>
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Repository filter */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Repository</label>
            <input
              value={repoId}
              onChange={(e) => onRepoIdChange(e.target.value)}
              placeholder="e.g. owner/repo"
              disabled={loading}
              aria-label="Repository id"
              className="w-full rounded-lg border border-slate-700/50 bg-slate-900/30 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
            />
            <p className="text-[11px] text-slate-500 mt-1.5">Leave empty to search all</p>
          </div>

          {/* Language filter */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Language</label>
            <input
              value={language}
              onChange={(e) => onLanguageChange(e.target.value)}
              placeholder="e.g. python"
              disabled={loading}
              aria-label="Language filter"
              className="w-full rounded-lg border border-slate-700/50 bg-slate-900/30 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
            />
            <p className="text-[11px] text-slate-500 mt-1.5">python, javascript, etc.</p>
          </div>

          {/* Results count */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Results</label>
            <input
              type="number"
              min={1}
              max={50}
              value={topK}
              onChange={(e) => onTopKChange(Math.max(1, Math.min(50, Number(e.target.value) || 5)))}
              disabled={loading}
              aria-label="Results count"
              className="w-full rounded-lg border border-slate-700/50 bg-slate-900/30 px-4 py-2.5 text-sm text-slate-100 focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
            />
            <p className="text-[11px] text-slate-500 mt-1.5">1-50 results</p>
          </div>

          {/* Search button */}
          <div className="flex flex-col">
            <label className="block text-xs font-semibold text-slate-300 mb-2 invisible">Action</label>
            <button
              type="submit"
              disabled={!canSearch}
              className={clsx(
                "px-5 py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-2",
                "bg-gradient-to-r from-cyan-500 to-blue-500 text-white",
                "hover:shadow-lg hover:shadow-cyan-500/20 transition-all duration-200",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                loading && "opacity-80"
              )}
              aria-label="Search"
            >
              {loading ? (
                <>
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.2)" strokeWidth="4"></circle>
                    <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" strokeWidth="4" strokeLinecap="round"></path>
                  </svg>
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <span>🔎</span>
                  <span>Search</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
};

export default SearchForm;


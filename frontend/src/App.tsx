import React, { useMemo, useState } from "react";
import Header from "./components/Header";
import SearchForm from "./components/SearchForm";
import ResultCard from "./components/ResultCard";
import { LoadingSkeleton } from "./components/LoadingSkeleton";
import { useSearch } from "./hooks/useSearch";
import { useSimilarSearch } from "./hooks/useSimilarSearch";
import type { SearchResult } from "./types";
import { DEFAULT_REPO_ID, keyFor } from "./utils/constants";

const App: React.FC = () => {
  const [query, setQuery] = useState("");
  const [repoId, setRepoId] = useState<string | null>(null);
  const [language, setLanguage] = useState("python");
  const [topK, setTopK] = useState(5);

  React.useEffect(() => {
    const last = localStorage.getItem("lastIndexedRepo");
    if (last) setRepoId(last);
    else setRepoId(DEFAULT_REPO_ID);

    const handler = (e: any) => {
      const ownerRepo = e?.detail?.ownerRepo;
      if (ownerRepo) setRepoId(ownerRepo);
    };

    window.addEventListener('repoIndexed', handler as EventListener);
    return () => window.removeEventListener('repoIndexed', handler as EventListener);
  }, []);

  const { loading, results, error, search } = useSearch();
  const {
    similarLoading,
    similarResults,
    expandedSimilar,
    findSimilar,
    clearSimilarResults,
  } = useSimilarSearch();

  const canSearch = useMemo(() => query.trim().length > 0 && !loading, [query, loading]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    clearSimilarResults();
    await search({
      query,
      top_k: topK,
      repo_id: repoId || undefined,
      language,
    });
  };

  const handleFindSimilar = async (result: SearchResult, resultKey: string) => {
    if (!result.code) return;
    await findSimilar(result.code, resultKey, repoId || "", language, topK);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100 relative overflow-hidden">
      {/* Animated background decoration */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
        <div className="absolute -bottom-32 -right-32 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '6s', animationDelay: '2s' }}></div>
      </div>

      {/* Main container */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 lg:py-16 space-y-10">
        {/* Header */}
        <Header />

        {/* Search Form */}
        <SearchForm
          query={query}
          repoId={repoId || ""}
          language={language}
          topK={topK}
          loading={loading}
          error={error}
          onQueryChange={setQuery}
          onRepoIdChange={setRepoId}
          onLanguageChange={setLanguage}
          onTopKChange={setTopK}
          onSubmit={handleSearch}
          canSearch={canSearch}
        />

        {/* Results Section */}
        <section className="space-y-6">
          {/* Results header */}
          {results.length > 0 && (
            <div className="flex items-center justify-between pb-5 border-b border-slate-800/50">
              <div>
                <h2 className="text-2xl sm:text-3xl font-bold text-slate-100 tracking-tight">
                  🔍 Search Results
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  Found <span className="text-cyan-400 font-semibold">{results.length}</span> {results.length === 1 ? "result" : "results"}
                </p>
              </div>
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="space-y-4">
              <LoadingSkeleton />
            </div>
          )}

          {/* No results state */}
          {results.length === 0 && !loading && (
            <div className="relative rounded-2xl border-2 border-dashed border-slate-800/50 bg-gradient-to-br from-slate-900/30 to-slate-800/20 backdrop-blur-sm p-16 sm:p-24 text-center animate-fadeIn overflow-hidden">
              {/* Background gradient */}
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 rounded-2xl"></div>

              {/* Content */}
              <div className="relative space-y-4">
                <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 flex items-center justify-center text-5xl backdrop-blur-md shadow-xl border border-slate-700/50">
                  🔎
                </div>
                <div>
                  <h3 className="text-xl sm:text-2xl font-bold text-slate-200 mb-2">
                    No results yet
                  </h3>
                  <p className="text-sm text-slate-400 max-w-sm mx-auto leading-relaxed">
                    Enter a search query above to explore your indexed codebase. Try searching for functions, patterns, or concepts.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Results list */}
          {!loading && results.length > 0 && (
            <div className="space-y-5">
              {results.map((result, idx) => {
                const resultKey = keyFor(result, idx);
                return (
                  <ResultCard
                    key={resultKey}
                    result={result}
                    index={idx}
                    onFindSimilar={handleFindSimilar}
                    similarLoading={similarLoading}
                    similarResults={similarResults}
                    expandedSimilar={expandedSimilar}
                  />
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default App;

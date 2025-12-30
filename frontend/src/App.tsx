import React, { useMemo, useState } from "react";
import Header from "./components/Header";
import SearchForm from "./components/SearchForm";
import ResultCard from "./components/ResultCard";
import { LoadingSkeleton } from "./components/LoadingSkeleton";
import { useSearch } from "./hooks/useSearch";
import { useSimilarSearch } from "./hooks/useSimilarSearch";
import type { SearchResult } from "./types";
import { DEFAULT_REPO_ID, keyFor, Icons } from "./utils/constants";

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
      repo_id: repoId,
      language,
    });
  };

  const handleFindSimilar = async (result: SearchResult, resultKey: string) => {
    if (!result.code) return;
    await findSimilar(result.code, resultKey, repoId, language, topK);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 via-slate-950 to-slate-950 text-slate-100 relative overflow-hidden">
      {/* Background decoration */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-sky-500/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl"></div>
      </div>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 sm:py-16 space-y-10 relative z-10">
        <Header />

        <SearchForm
          query={query}
          repoId={repoId}
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
          {results.length > 0 && (
            <div className="flex items-center justify-between pb-4 border-b-2 border-slate-800/60">
              <h2 className="text-2xl font-extrabold text-slate-100 tracking-tight">
                Search Results
                <span className="ml-3 text-base font-semibold text-slate-400">
                  ({results.length} {results.length === 1 ? "result" : "results"})
                </span>
              </h2>
            </div>
          )}

          {loading && <LoadingSkeleton />}

          {results.length === 0 && !loading && (
            <div className="relative rounded-3xl border-2 border-dashed border-slate-800/70 bg-gradient-to-br from-slate-900/50 to-slate-800/30 backdrop-blur-xl p-20 text-center animate-in fade-in shadow-2xl">
              <div className="absolute inset-0 bg-gradient-to-br from-sky-500/5 to-blue-500/5 rounded-3xl"></div>
              <div className="relative">
                <div className="w-24 h-24 mx-auto mb-8 rounded-2xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 flex items-center justify-center text-5xl backdrop-blur-md shadow-xl border border-slate-700/50">
                  {Icons.Search}
                </div>
                <p className="text-xl font-bold text-slate-200 mb-3">No results yet</p>
                <p className="text-sm text-slate-400 max-w-md mx-auto leading-relaxed">
                  Enter a query above to search your indexed codebase using semantic search
                </p>
              </div>
            </div>
          )}

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
        </section>
      </div>
    </div>
  );
};

export default App;

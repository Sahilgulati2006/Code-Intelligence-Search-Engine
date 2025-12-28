import React, { useMemo, useState } from "react";
import CodeBlock from "./components/CodeBlock";

type SearchResult = {
  score: number;
  repo_id?: string;
  file_path?: string;
  language?: string;
  symbol_type?: string;
  symbol_name?: string;
  start_line?: number;
  end_line?: number;
  code?: string;
};

const API_BASE = "http://127.0.0.1:8000";
const DEFAULT_REPO_ID = "fastapi-lib"; // Match the repo_id in the database

function truncateLines(code: string, maxLines: number) {
  const lines = code.split("\n");
  if (lines.length <= maxLines) return { text: code, truncated: false };
  return { text: lines.slice(0, maxLines).join("\n"), truncated: true };
}

function clsx(...xs: Array<string | false | undefined>) {
  return xs.filter(Boolean).join(" ");
}

const App: React.FC = () => {
  const [query, setQuery] = useState("");
  const [repoId, setRepoId] = useState(DEFAULT_REPO_ID);
  const [language, setLanguage] = useState("python");
  const [topK, setTopK] = useState(5);

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [similarLoading, setSimilarLoading] = useState<Record<string, boolean>>({});
  const [similarResults, setSimilarResults] = useState<Record<string, SearchResult[]>>({});
  const [expandedSimilar, setExpandedSimilar] = useState<Record<string, boolean>>({});

  const canSearch = useMemo(() => query.trim().length > 0 && !loading, [query, loading]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          top_k: topK,
          repo_id: repoId.trim() ? repoId.trim() : null,
          language: language.trim() ? language.trim() : null,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error ${res.status}: ${text}`);
      }

      const data = await res.json();
      setResults(data.results || []);
      setExpanded({});
      setSimilarResults({});
      setExpandedSimilar({});
    } catch (err: any) {
      setError(err?.message ?? "Something went wrong");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text?: string) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {}
  };

  const handleFindSimilar = async (result: SearchResult, resultKey: string) => {
    if (!result.code) return;

    // Toggle expanded state
    const isCurrentlyExpanded = !!expandedSimilar[resultKey];
    if (isCurrentlyExpanded) {
      setExpandedSimilar((prev) => {
        const newState = { ...prev };
        delete newState[resultKey];
        return newState;
      });
      return;
    }

    // If results already loaded, just expand
    if (similarResults[resultKey]?.length > 0) {
      setExpandedSimilar((prev) => ({ ...prev, [resultKey]: true }));
      return;
    }

    // Load similar results
    setSimilarLoading((prev) => ({ ...prev, [resultKey]: true }));

    try {
      const res = await fetch(`${API_BASE}/search/similar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: result.code,
          top_k: 5,
          repo_id: repoId.trim() ? repoId.trim() : null,
          language: language.trim() ? language.trim() : null,
          exclude_self: true,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error ${res.status}: ${text}`);
      }

      const data = await res.json();
      setSimilarResults((prev) => ({ ...prev, [resultKey]: data.results || [] }));
      setExpandedSimilar((prev) => ({ ...prev, [resultKey]: true }));
    } catch (err: any) {
      console.error("Error finding similar code:", err);
      setSimilarResults((prev) => ({ ...prev, [resultKey]: [] }));
    } finally {
      setSimilarLoading((prev) => {
        const newState = { ...prev };
        delete newState[resultKey];
        return newState;
      });
    }
  };

  const keyFor = (r: SearchResult, idx: number) =>
    `${r.repo_id ?? "repo"}:${r.file_path ?? "file"}:${r.start_line ?? 0}:${idx}`;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 to-slate-900 text-slate-100">
      <div className="mx-auto max-w-6xl px-4 py-10 space-y-8">
        {/* Header */}
        <header className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center">
              <span className="text-sky-300 font-bold">CI</span>
            </div>
            <div>
              <h1 className="text-3xl font-semibold tracking-tight">
                Code Intelligence Search
              </h1>
              <p className="text-sm text-slate-400">
                Privacy-first semantic search over indexed code.
              </p>
            </div>
          </div>

          <div className="text-xs text-slate-500">
            Backend: <span className="font-mono">{API_BASE}</span>
          </div>
        </header>

        {/* Search Card */}
        <form
          onSubmit={handleSearch}
          className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow-lg shadow-black/20"
        >
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <div className="lg:col-span-12">
              <label className="text-xs font-medium text-slate-300">
                Query
              </label>
              <div className="mt-1 flex gap-2">
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder='e.g. "render HTML template", "before request hook"'
                  className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
                <button
                  type="submit"
                  disabled={!canSearch}
                  className={clsx(
                    "rounded-xl px-5 py-3 text-sm font-semibold",
                    "bg-sky-600 hover:bg-sky-500",
                    "disabled:opacity-50 disabled:hover:bg-sky-600"
                  )}
                >
                  {loading ? "Searching..." : "Search"}
                </button>
              </div>
              {error && (
                <div className="mt-2 text-xs text-red-400">{error}</div>
              )}
            </div>

            <div className="lg:col-span-6">
              <label className="text-xs font-medium text-slate-300">Repo ID</label>
              <input
                value={repoId}
                onChange={(e) => setRepoId(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div className="lg:col-span-4">
              <label className="text-xs font-medium text-slate-300">Language</label>
              <input
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div className="lg:col-span-2">
              <label className="text-xs font-medium text-slate-300">Top K</label>
              <input
                type="number"
                min={1}
                max={50}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value) || 5)}
                className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div className="lg:col-span-12 text-xs text-slate-500">
              Try:{" "}
              <span className="font-mono text-slate-300">jinja loader</span>,{" "}
              <span className="font-mono text-slate-300">blueprint registration</span>,{" "}
              <span className="font-mono text-slate-300">before request</span>
            </div>
          </div>
        </form>

        {/* Results */}
        <section className="space-y-4">
          <div className="flex items-baseline justify-between">
            <h2 className="text-sm font-semibold text-slate-200">
              Results <span className="text-slate-400">({results.length})</span>
            </h2>
          </div>

          {results.length === 0 && !loading && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 text-sm text-slate-400">
              No results yet. Run a search above.
            </div>
          )}

          <div className="space-y-4">
            {results.map((r, idx) => {
              const k = keyFor(r, idx);
              const isExpanded = !!expanded[k];
              const code = r.code ?? "";
              const { text: preview, truncated } = truncateLines(code, 22);

              return (
                <div
                  key={k}
                  className="rounded-2xl border border-slate-800 bg-slate-900/35 p-5"
                >
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <div className="text-lg font-semibold truncate">
                          {r.symbol_name ?? "<unknown>"}
                        </div>
                        {r.symbol_type && (
                          <span className="text-[11px] rounded-full border border-slate-700 bg-slate-950 px-2 py-0.5 text-slate-300">
                            {r.symbol_type}
                          </span>
                        )}
                        {r.language && (
                          <span className="text-[11px] rounded-full border border-slate-700 bg-slate-950 px-2 py-0.5 text-slate-300">
                            {r.language}
                          </span>
                        )}
                      </div>

                      <div className="mt-1 text-xs text-slate-400 break-all">
                        <span className="font-mono">{r.file_path}</span>
                        {r.start_line != null && r.end_line != null && (
                          <span className="text-slate-500">
                            {" "}
                            · lines {r.start_line}–{r.end_line}
                          </span>
                        )}
                      </div>

                      {r.repo_id && (
                        <div className="mt-2 text-[11px] text-slate-500 font-mono break-all">
                          {r.repo_id}
                        </div>
                      )}
                    </div>

                    <div className="flex shrink-0 items-center gap-2">
                      <div className="text-xs text-slate-400">
                        score{" "}
                        <span className="font-mono text-slate-100">
                          {(r.score ?? 0).toFixed(3)}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleFindSimilar(r, k)}
                        disabled={similarLoading[k]}
                        className={clsx(
                          "rounded-xl border border-emerald-700 bg-emerald-950/50 px-3 py-2 text-xs text-emerald-200 hover:bg-emerald-900/50",
                          "disabled:opacity-50 disabled:cursor-not-allowed",
                          expandedSimilar[k] && "bg-emerald-900/70 border-emerald-600"
                        )}
                      >
                        {similarLoading[k] ? "..." : expandedSimilar[k] ? "Hide Similar" : "Find Similar"}
                      </button>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(code)}
                        className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-200 hover:bg-slate-800"
                      >
                        Copy
                      </button>
                      {truncated && (
                        <button
                          type="button"
                          onClick={() =>
                            setExpanded((prev) => ({ ...prev, [k]: !prev[k] }))
                          }
                          className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-200 hover:bg-slate-800"
                        >
                          {isExpanded ? "Collapse" : "Expand"}
                        </button>
                      )}
                    </div>
                  </div>

                  <CodeBlock
                  code={isExpanded ? code : preview}
                  language={r.language}
                  />


                  {truncated && !isExpanded && (
                    <div className="mt-2 text-xs text-slate-500">
                      Showing first 22 lines. Click <span className="text-slate-300">Expand</span> to view full snippet.
                    </div>
                  )}

                  {/* Similar Results Section */}
                  {expandedSimilar[k] && (
                    <div className="mt-4 pt-4 border-t border-slate-800">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-semibold text-emerald-300">
                          Similar Code ({similarResults[k]?.length || 0})
                        </h3>
                      </div>

                      {similarLoading[k] ? (
                        <div className="text-xs text-slate-400 py-4">Finding similar code...</div>
                      ) : similarResults[k]?.length === 0 ? (
                        <div className="text-xs text-slate-500 py-4">No similar code found.</div>
                      ) : (
                        <div className="space-y-3">
                          {similarResults[k]?.map((similar, similarIdx) => {
                            const similarKey = keyFor(similar, similarIdx);
                            const similarCode = similar.code ?? "";
                            const similarIsExpanded = !!expanded[similarKey];
                            const { text: similarPreview, truncated: similarTruncated } = truncateLines(similarCode, 15);

                            return (
                              <div
                                key={similarKey}
                                className="rounded-xl border border-emerald-900/50 bg-slate-950/50 p-4"
                              >
                                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-2 mb-2">
                                  <div className="min-w-0">
                                    <div className="flex flex-wrap items-center gap-2">
                                      <div className="text-sm font-medium text-slate-200 truncate">
                                        {similar.symbol_name ?? "<unknown>"}
                                      </div>
                                      {similar.symbol_type && (
                                        <span className="text-[10px] rounded-full border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-400">
                                          {similar.symbol_type}
                                        </span>
                                      )}
                                      <span className="text-xs text-emerald-400">
                                        similarity: {(similar.score ?? 0).toFixed(3)}
                                      </span>
                                    </div>
                                    <div className="mt-1 text-[11px] text-slate-500 break-all">
                                      <span className="font-mono">{similar.file_path}</span>
                                      {similar.start_line != null && similar.end_line != null && (
                                        <span className="text-slate-600">
                                          {" "}
                                          · lines {similar.start_line}–{similar.end_line}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  <div className="flex shrink-0 items-center gap-2">
                                    <button
                                      type="button"
                                      onClick={() => copyToClipboard(similarCode)}
                                      className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-[10px] text-slate-300 hover:bg-slate-800"
                                    >
                                      Copy
                                    </button>
                                    {similarTruncated && (
                                      <button
                                        type="button"
                                        onClick={() =>
                                          setExpanded((prev) => ({ ...prev, [similarKey]: !prev[similarKey] }))
                                        }
                                        className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-[10px] text-slate-300 hover:bg-slate-800"
                                      >
                                        {similarIsExpanded ? "Collapse" : "Expand"}
                                      </button>
                                    )}
                                  </div>
                                </div>

                                <CodeBlock
                                  code={similarIsExpanded ? similarCode : similarPreview}
                                  language={similar.language}
                                />
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
};

export default App;

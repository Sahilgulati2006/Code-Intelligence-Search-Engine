import { useState, useCallback } from "react";
import type { SearchResult, SearchParams } from "../types";
import { API_BASE } from "../utils/constants";

export const useSearch = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (params: SearchParams) => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: params.query,
          top_k: params.top_k,
          repo_id: params.repo_id?.trim() || null,
          language: params.language?.trim() || null,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error ${res.status}: ${text}`);
      }

      const data = await res.json();
      setResults(data.results || []);
    } catch (err: any) {
      setError(err?.message ?? "Something went wrong");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setResults([]);
    setError(null);
  }, []);

  return { loading, results, error, search, clearResults };
};


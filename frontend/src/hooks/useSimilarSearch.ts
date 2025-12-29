import { useState, useCallback, useRef } from "react";
import type { SearchResult } from "../types";
import { API_BASE } from "../utils/constants";

export const useSimilarSearch = () => {
  const [similarLoading, setSimilarLoading] = useState<Record<string, boolean>>({});
  const [similarResults, setSimilarResults] = useState<Record<string, SearchResult[]>>({});
  const [expandedSimilar, setExpandedSimilar] = useState<Record<string, boolean>>({});
  const stateRef = useRef({ similarResults, expandedSimilar });

  // Keep ref in sync
  stateRef.current = { similarResults, expandedSimilar };

  const findSimilar = useCallback(async (
    code: string,
    resultKey: string,
    repoId: string,
    language: string,
    topK: number = 5
  ) => {
    const currentState = stateRef.current;
    const isCurrentlyExpanded = !!currentState.expandedSimilar[resultKey];
    const hasResults = currentState.similarResults[resultKey]?.length > 0;

    // Toggle collapsed if currently expanded
    if (isCurrentlyExpanded) {
      setExpandedSimilar((prev) => {
        const newState = { ...prev };
        delete newState[resultKey];
        return newState;
      });
      return;
    }

    // If results already exist, just expand
    if (hasResults) {
      setExpandedSimilar((prev) => ({ ...prev, [resultKey]: true }));
      return;
    }

    // Expand and start loading
    setExpandedSimilar((prev) => ({ ...prev, [resultKey]: true }));
    setSimilarLoading((prev) => ({ ...prev, [resultKey]: true }));

    try {
      const res = await fetch(`${API_BASE}/search/similar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code,
          top_k: topK,
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
  }, []);

  const clearSimilarResults = useCallback(() => {
    setSimilarResults({});
    setExpandedSimilar({});
  }, []);

  return {
    similarLoading,
    similarResults,
    expandedSimilar,
    findSimilar,
    clearSimilarResults,
  };
};

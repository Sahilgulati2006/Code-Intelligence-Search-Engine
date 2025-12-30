import React, { useState, useEffect, useRef } from "react";
import { API_BASE } from "../utils/constants";

const Header: React.FC = () => {
  const [repoUrl, setRepoUrl] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const pollingRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pollingRef.current) window.clearInterval(pollingRef.current);
    };
  }, []);

  const submitIndex = async () => {
    setMessage(null);
    if (!repoUrl) return setMessage("Enter a GitHub repo URL first");

    try {
      const res = await fetch(`${API_BASE}/index`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl }),
      });

      if (res.status === 202) {
        const data = await res.json();
        setJobId(data.job_id);
        setJobStatus("queued");
        setMessage("Queued for indexing — polling status...");

        pollingRef.current = window.setInterval(async () => {
          const s = await fetch(`${API_BASE}/index/status/${data.job_id}`);
          if (!s.ok) return;
          const js = await s.json();
          setJobStatus(js.status);

          // If completed, remember owner/repo and show chunks
          if (js.status === "completed") {
            const chunks = js.indexed_chunks ?? null;
            setMessage(js.message ? `${js.message}${chunks ? ` — ${chunks} chunks` : ''}` : (chunks ? `Indexed ${chunks} chunks` : 'Completed'));
            try {
              const parsed = new URL(repoUrl);
              const parts = parsed.pathname.split('/').filter(Boolean);
              if (parts.length >= 2) {
                const ownerRepo = `${parts[0]}/${parts[1].replace(/\.git$/, '')}`;
                localStorage.setItem('lastIndexedRepo', ownerRepo);
                // Notify listeners (e.g., App) about the new indexed repo
                try {
                  window.dispatchEvent(new CustomEvent('repoIndexed', { detail: { ownerRepo } }));
                } catch (e) {}
              }
            } catch (e) {}
          } else {
            setMessage(js.message || null);
          }

          if (js.status === "completed" || js.status === "failed") {
            if (pollingRef.current) {
              window.clearInterval(pollingRef.current);
              pollingRef.current = null;
            }
          }
        }, 1500);
      } else {
        const err = await res.text();
        setMessage(`Index request failed: ${err}`);
      }
    } catch (err: any) {
      setMessage(`Error: ${err?.message ?? err}`);
    }
  };

  return (
    <header className="app-container flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 py-4">
      <div className="flex items-center gap-4">
        <div className="relative flex-shrink-0">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-sky-500/15 to-blue-600/12 border border-slate-700/20 flex items-center justify-center shadow-sm">
            <svg width="20" height="20" className="h-5 w-5 text-sky-300" viewBox="0 0 24 24" fill="none" role="img" aria-label="logo">
              <path d="M8 10l-4 4 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"></path>
              <path d="M16 10l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"></path>
            </svg>
          </div>
        </div>
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Code Intelligence Search
          </h1>
          <p className="text-sm text-muted mt-1">
            Semantic search powered by CodeBERT • <span className="text-sky-400">Privacy-first</span>
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-xs text-muted bg-slate-900/40 px-3 py-2 rounded-lg border border-slate-800/50">
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-green-400/10 animate-pulse mix-blend-screen"></div>
            <div className="relative w-2.5 h-2.5 rounded-full bg-green-400 shadow-sm"></div>
          </div>
          <span className="font-medium">Backend: <span className="font-mono text-sky-300">{API_BASE}</span></span>
        </div>

        <div className="ml-4 flex items-center gap-2">
          <input
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            className="rounded-md border border-slate-700/50 bg-transparent px-3 py-2 text-sm text-slate-200 placeholder:text-slate-500 w-64"
            aria-label="Repository URL"
          />
          <button onClick={submitIndex} className="rounded-md px-3 py-2 bg-sky-600 text-white text-sm font-medium">
            Index Repo
          </button>
        </div>
      </div>

      {jobId && (
        <div className="mt-3 sm:mt-0 text-xs text-muted">
          <div>Job: <span className="font-mono">{jobId}</span></div>
          <div>Status: <span className="font-semibold text-slate-200">{jobStatus}</span></div>
          {message && <div className="mt-1 text-[12px] text-slate-400">{message}</div>}
        </div>
      )}
    </header>
  );
};

export default Header;
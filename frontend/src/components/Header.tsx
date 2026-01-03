import React, { useState, useEffect, useRef } from "react";
import { API_BASE } from "../utils/constants";

const Header: React.FC = () => {
  const [repoUrl, setRepoUrl] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const pollingRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pollingRef.current) window.clearInterval(pollingRef.current);
    };
  }, []);

  const submitIndex = async () => {
    setMessage(null);
    if (!repoUrl.trim()) {
      setMessage("Enter a GitHub repo URL first");
      return;
    }

    setIsIndexing(true);
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

          if (js.status === "completed") {
            const chunks = js.indexed_chunks ?? null;
            setMessage(js.message ? `${js.message}${chunks ? ` — ${chunks} chunks` : ''}` : (chunks ? `Indexed ${chunks} chunks` : 'Completed'));
            setIsIndexing(false);
            try {
              const parsed = new URL(repoUrl);
              const parts = parsed.pathname.split('/').filter(Boolean);
              if (parts.length >= 2) {
                const ownerRepo = `${parts[0]}/${parts[1].replace(/\.git$/, '')}`;
                localStorage.setItem('lastIndexedRepo', ownerRepo);
                try {
                  window.dispatchEvent(new CustomEvent('repoIndexed', { detail: { ownerRepo } }));
                } catch (e) {}
              }
            } catch (e) {}
          } else if (js.status === "failed") {
            setIsIndexing(false);
            setMessage(js.message || "Indexing failed");
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
        setIsIndexing(false);
        const err = await res.text();
        setMessage(`Index request failed: ${err}`);
      }
    } catch (err: any) {
      setIsIndexing(false);
      setMessage(`Error: ${err?.message ?? err}`);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isIndexing) {
      submitIndex();
    }
  };

  return (
    <header className="relative">
      {/* Main header section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 pb-8 border-b border-slate-800/50">
        <div className="flex items-center gap-4">
          {/* Logo */}
          <div className="flex-shrink-0">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 flex items-center justify-center shadow-lg hover:shadow-cyan-500/10 transition-shadow duration-300">
              <svg width="24" height="24" className="h-6 w-6 text-cyan-300" viewBox="0 0 24 24" fill="none" role="img" aria-label="logo">
                <path d="M8 10l-4 4 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"></path>
                <path d="M16 10l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"></path>
              </svg>
            </div>
          </div>

          {/* Title and subtitle */}
          <div className="flex flex-col">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-slate-100 to-slate-200 bg-clip-text text-transparent">
              Code Intelligence
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Semantic code search with neural networks
            </p>
          </div>
        </div>

        {/* Backend status indicator */}
        <div className="flex items-center gap-2 text-xs text-slate-300 bg-slate-900/50 px-4 py-2 rounded-xl border border-slate-800/60 backdrop-blur-sm hover:border-cyan-500/30 transition-colors duration-200">
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-green-400/20 animate-pulse"></div>
            <div className="relative w-2 h-2 rounded-full bg-green-400 shadow-md shadow-green-400/50"></div>
          </div>
          <span className="font-medium">Backend</span>
          <span className="font-mono text-cyan-300 text-[11px]">{API_BASE.replace('http://', '')}</span>
        </div>
      </div>

      {/* Index repo section */}
      <div className="mt-6 card-surface p-5 sm:p-6">
        <div className="flex flex-col gap-4">
          <div>
            <label className="block text-sm font-semibold text-slate-200 mb-2 flex items-center gap-2">
              <span>📦 Index Repository</span>
              {isIndexing && <span className="animate-spin inline-block">⚙️</span>}
            </label>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="https://github.com/owner/repo"
                disabled={isIndexing}
                className="flex-1 rounded-lg border border-slate-700/50 bg-slate-900/20 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Repository URL"
              />
              <button
                onClick={submitIndex}
                disabled={isIndexing || !repoUrl.trim()}
                className="px-5 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white text-sm font-semibold rounded-lg hover:shadow-lg hover:shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 whitespace-nowrap"
              >
                {isIndexing ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    Indexing...
                  </>
                ) : (
                  <>
                    <span>🚀</span>
                    Index Repo
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Status and message display */}
          {jobId && (
            <div className="rounded-lg bg-slate-900/30 border border-slate-700/50 p-4 space-y-2 animate-slideInRight">
              <div className="flex flex-wrap gap-4 text-xs">
                <div>
                  <span className="text-slate-400">Job ID:</span>
                  <span className="ml-2 font-mono text-cyan-300">{jobId.substring(0, 8)}...</span>
                </div>
                <div>
                  <span className="text-slate-400">Status:</span>
                  <span className={`ml-2 font-semibold ${
                    jobStatus === 'completed' ? 'text-green-400' :
                    jobStatus === 'failed' ? 'text-red-400' :
                    'text-yellow-400'
                  }`}>
                    {jobStatus}
                  </span>
                </div>
              </div>
              {message && (
                <div className={`text-xs leading-relaxed ${
                  jobStatus === 'completed' ? 'text-green-300' :
                  jobStatus === 'failed' ? 'text-red-300' :
                  'text-slate-300'
                }`}>
                  {message}
                </div>
              )}
            </div>
          )}

          {message && !jobId && (
            <div className="rounded-lg bg-red-900/20 border border-red-800/50 p-3 text-xs text-red-300 animate-slideInRight">
              {message}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
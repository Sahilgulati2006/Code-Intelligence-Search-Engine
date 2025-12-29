import React from "react";
import { API_BASE } from "../utils/constants";

const Header: React.FC = () => {
  return (
    <header className="app-container flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 pb-6">
      <div className="flex items-center gap-4">
        <div className="relative">
          <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-sky-500/20 to-blue-600/20 border border-slate-700/40 flex items-center justify-center shadow-sm">
            <span className="text-sky-200 font-bold text-lg">CI</span>
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

      <div className="flex items-center gap-2.5 text-xs text-muted bg-slate-900/40 px-3 py-2 rounded-lg border border-slate-800/50">
        <div className="relative">
          <div className="absolute inset-0 rounded-full bg-green-400/10 animate-pulse mix-blend-screen"></div>
          <div className="relative w-2.5 h-2.5 rounded-full bg-green-400 shadow-sm"></div>
        </div>
        <span className="font-medium">Backend: <span className="font-mono text-sky-300">{API_BASE}</span></span>
      </div>
    </header>
  );
};

export default Header;
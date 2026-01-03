import React from "react";

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 animate-fadeIn">
      {/* Animated spinner */}
      <div className="relative mb-10">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-full blur-2xl"></div>
        <div className="relative w-24 h-24">
          <div className="absolute inset-0 border-3 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin"></div>
          <div className="absolute inset-2 border-3 border-transparent border-r-blue-500/40 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
          <div className="absolute inset-4 border-2 border-transparent border-b-cyan-400/30 rounded-full animate-spin" style={{ animationDuration: '2.5s' }}></div>
        </div>
      </div>

      {/* Status text */}
      <div className="text-center space-y-2">
        <h3 className="text-lg font-bold text-slate-100">🔍 Searching codebase</h3>
        <p className="text-sm text-slate-400">Indexing and analyzing semantic patterns</p>
      </div>

      {/* Progress dots */}
      <div className="mt-8 flex gap-2">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"
            style={{ animationDelay: `${i * 0.15}s` }}
          ></div>
        ))}
      </div>
    </div>
  );
};

export const ResultCardSkeleton: React.FC = () => {
  return (
    <div className="card-surface p-6 sm:p-7 animate-pulse">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4 pb-4 border-b border-slate-800/50">
        {/* Title skeleton */}
        <div className="flex-1 space-y-3">
          <div className="h-6 bg-slate-800/50 rounded-lg w-2/3"></div>
          <div className="flex gap-2 flex-wrap">
            <div className="h-5 bg-slate-800/50 rounded-full w-24"></div>
            <div className="h-5 bg-slate-800/50 rounded-full w-20"></div>
            <div className="h-5 bg-slate-800/50 rounded-full w-16"></div>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-slate-800/40 rounded w-1/2"></div>
            <div className="h-4 bg-slate-800/40 rounded w-2/5"></div>
          </div>
        </div>

        {/* Button skeleton */}
        <div className="flex gap-2 sm:flex-col">
          <div className="h-9 bg-slate-800/50 rounded-lg w-28"></div>
          <div className="h-9 bg-slate-800/50 rounded-lg w-20"></div>
        </div>
      </div>

      {/* Code block skeleton */}
      <div className="space-y-2 mb-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-5 bg-slate-900/50 rounded w-full" style={{ width: `${85 + (i % 3) * 5}%` }}></div>
        ))}
      </div>
    </div>
  );
};


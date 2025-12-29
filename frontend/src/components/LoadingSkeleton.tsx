import React from "react";

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-4">
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-sky-500/20 rounded-full blur-xl"></div>
        <div className="relative w-20 h-20 border-4 border-sky-500/30 border-t-sky-500 rounded-full animate-spin"></div>
        <div className="absolute inset-0 w-20 h-20 border-4 border-transparent border-r-blue-500/40 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
      </div>
      <p className="text-base text-slate-300 font-bold mb-2">Searching codebase...</p>
      <p className="text-sm text-slate-500">This may take a few seconds</p>
    </div>
  );
};

export const ResultCardSkeleton: React.FC = () => {
  return (
    <div className="rounded-2xl border border-slate-800/60 bg-slate-900/50 backdrop-blur-sm p-6 shadow-lg animate-pulse">
      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-3">
            <div className="h-6 bg-slate-800/50 rounded-lg w-3/4"></div>
            <div className="flex gap-2">
              <div className="h-5 bg-slate-800/50 rounded-full w-20"></div>
              <div className="h-5 bg-slate-800/50 rounded-full w-16"></div>
            </div>
            <div className="h-4 bg-slate-800/50 rounded w-1/2"></div>
          </div>
        </div>
        <div className="h-32 bg-slate-950/50 rounded-xl"></div>
      </div>
    </div>
  );
};


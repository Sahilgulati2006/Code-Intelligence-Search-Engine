import { useEffect } from "react";
import Prism from "prismjs";
import "prismjs/components/prism-python";
import "prismjs/components/prism-javascript";
import "prismjs/components/prism-typescript";
import "prismjs/components/prism-bash";
import "prismjs/components/prism-json";

interface CodeBlockProps {
  code: string;
  language?: string;
}

export default function CodeBlock({ code, language = "python" }: CodeBlockProps) {
  useEffect(() => {
    Prism.highlightAll();
  }, [code]);

  const languageLabel = language && language !== 'unknown' ? language.charAt(0).toUpperCase() + language.slice(1) : 'Code';

  return (
    <div className="relative group">
      <pre className="rounded-xl border border-slate-800/60 bg-gradient-to-br from-slate-950/95 to-slate-900/90 backdrop-blur-sm p-4 sm:p-5 overflow-auto max-h-[600px] shadow-lg scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900/50">
        <code
          className={`language-${language} text-sm leading-relaxed font-mono text-slate-100`}
        >
          {code}
        </code>
      </pre>

      {/* Language badge */}
      <div className="absolute top-3 right-3 opacity-60 group-hover:opacity-100 transition-opacity duration-200">
        <div className="bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-300 border border-slate-700/50 shadow-lg">
          {languageLabel}
        </div>
      </div>
    </div>
  );
}

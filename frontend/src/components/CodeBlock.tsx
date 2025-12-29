import { useEffect } from "react";
import Prism from "prismjs";
import "prismjs/components/prism-python";

interface CodeBlockProps {
  code: string;
  language?: string;
}

export default function CodeBlock({ code, language = "python" }: CodeBlockProps) {
  useEffect(() => {
    Prism.highlightAll();
  }, [code]);

  return (
    <div className="relative group">
      <pre className="rounded-xl border border-slate-800/60 bg-slate-950/90 backdrop-blur-sm p-4 sm:p-5 overflow-auto max-h-[600px] shadow-inner scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900">
        <code className={`language-${language} text-sm leading-relaxed`}>{code}</code>
      </pre>
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="bg-slate-900/80 backdrop-blur-sm px-2 py-1 rounded text-xs text-slate-400 border border-slate-700/50">
          {language}
        </div>
      </div>
    </div>
  );
}

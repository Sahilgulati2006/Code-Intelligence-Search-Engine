import { useEffect } from "react";
import Prism from "prismjs";

import "prismjs/components/prism-python";

type Props = {
  code: string;
  language?: string;
};

export default function CodeBlock({ code, language = "python" }: Props) {
  useEffect(() => {
    Prism.highlightAll();
  }, [code]);

  return (
    <pre className="rounded-2xl border border-slate-800 bg-slate-950 p-4 overflow-auto">
      <code className={`language-${language}`}>{code}</code>
    </pre>
  );
}

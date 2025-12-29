export const API_BASE = "http://127.0.0.1:8000";
export const DEFAULT_REPO_ID = "fastapi-lib";

export const Icons = {
  Search: "🔍",
  Copy: "📋",
  Check: "✓",
  Expand: "▼",
  Collapse: "▲",
  Similar: "🔄",
  File: "📄",
  Folder: "📁",
} as const;

export function clsx(...xs: Array<string | false | undefined>): string {
  return xs.filter(Boolean).join(" ");
}

export function truncateLines(code: string, maxLines: number): { text: string; truncated: boolean } {
  const lines = code.split("\n");
  if (lines.length <= maxLines) return { text: code, truncated: false };
  return { text: lines.slice(0, maxLines).join("\n"), truncated: true };
}

export function keyFor(result: { repo_id?: string; file_path?: string; start_line?: number }, idx: number): string {
  return `${result.repo_id ?? "repo"}:${result.file_path ?? "file"}:${result.start_line ?? 0}:${idx}`;
}


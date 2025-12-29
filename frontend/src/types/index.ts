export type SearchResult = {
  score: number;
  repo_id?: string;
  file_path?: string;
  language?: string;
  symbol_type?: string;
  symbol_name?: string;
  start_line?: number;
  end_line?: number;
  code?: string;
};

export type SearchParams = {
  query: string;
  repo_id?: string | null;
  language?: string | null;
  top_k: number;
};


import ast
from pathlib import Path
from typing import List, Dict, Any

def extract_python_functions(repo_path: str) -> List[Dict[str, Any]]:
    repo = Path(repo_path)
    chunks: List[Dict[str, Any]] = []

    for py_file in repo.rglob("*.py"):
        rel_path = py_file.relative_to(repo)

        # 🔥 Skip test files & test directories
        if "tests" in rel_path.parts or rel_path.name.startswith("test_"):
            continue

        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", None)

                if end_line is None:
                    continue

                # extract code block text
                lines = source.splitlines()
                code_text = "\n".join(lines[start_line - 1:end_line])

                chunks.append({
                    "language": "python",
                    "symbol_type": "function",
                    "symbol_name": node.name,
                    "file_path": str(rel_path),
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": code_text,
                })

    return chunks

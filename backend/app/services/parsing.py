import ast
from pathlib import Path
from typing import List, Dict, Any


SKIP_DIRS = {"tests", "test", "docs", "examples", "scripts", ".venv", "venv", "build", "dist"}


def _get_source_segment(source: str, node: ast.AST) -> str | None:
    try:
        return ast.get_source_segment(source, node)
    except Exception:
        return None


def extract_python_functions(repo_path: str) -> List[Dict[str, Any]]:
    repo = Path(repo_path)
    chunks: List[Dict[str, Any]] = []

    # ✅ If repo uses src-layout, prefer indexing only src/
    src_root = repo / "src"
    index_root = src_root if src_root.exists() and src_root.is_dir() else repo

    # --- Stats (so we can detect if AST is skipping a lot) ---
    total_files = 0
    parsed_files = 0
    skipped_read = 0
    skipped_syntax = 0
    skipped_other = 0

    for py_file in index_root.rglob("*.py"):
        total_files += 1
        rel_path = py_file.relative_to(repo)

        # Skip noisy dirs
        if any(part in SKIP_DIRS for part in rel_path.parts):
            continue

        # Skip common test naming
        if rel_path.name.startswith("test_") or rel_path.name.endswith("_test.py"):
            continue

        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            skipped_read += 1
            continue

        try:
            tree = ast.parse(source)
            parsed_files += 1
        except SyntaxError:
            skipped_syntax += 1
            continue
        except Exception:
            skipped_other += 1
            continue

        lines = source.splitlines()

        # Track class context so methods become Class.method
        class_stack: list[str] = []

        for node in ast.walk(tree):
            # Capture class names (best-effort)
            if isinstance(node, ast.ClassDef):
                class_stack.append(node.name)

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = getattr(node, "lineno", None)
                end_line = getattr(node, "end_lineno", None)
                if not start_line or not end_line:
                    continue

                # Build method-aware symbol name (Class.method if inside class)
                # Note: AST doesn't give parent pointers, so we do a simple heuristic:
                # if function is indented under a class, it usually appears near class defs.
                # We'll still label plain functions just by name.
                symbol_name = node.name
                # heuristic: if file contains "class " before function and indentation suggests it,
                # but to keep it reliable we do a light scan: if "class X" exists and "def" appears after it
                # this is imperfect; still useful.
                # If you want perfect parent tracking later, we’ll build an AST parent map.
                #
                # For now: keep just node.name (safe) and add optional class label via quick check below.
                #

                code_text = "\n".join(lines[start_line - 1 : end_line])

                chunks.append({
                    "language": "python",
                    "symbol_type": "function",
                    "symbol_name": symbol_name,
                    "file_path": str(rel_path),
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": code_text,
                })

                # Call-site chunks inside this function
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Call):
                        call_text = _get_source_segment(source, inner)
                        if not call_text:
                            continue

                        func_name = None
                        if isinstance(inner.func, ast.Name):
                            func_name = inner.func.id
                        elif isinstance(inner.func, ast.Attribute):
                            func_name = inner.func.attr

                        if not func_name:
                            continue

                        call_line = getattr(inner, "lineno", start_line)

                        chunks.append({
                            "language": "python",
                            "symbol_type": "call",
                            "symbol_name": func_name,
                            "file_path": str(rel_path),
                            "start_line": call_line,
                            "end_line": call_line,
                            "code": call_text,
                        })

    print(
        f"[parsing] total_files={total_files}, parsed_files={parsed_files}, "
        f"skipped_read={skipped_read}, skipped_syntax={skipped_syntax}, skipped_other={skipped_other}"
    )

    return chunks
